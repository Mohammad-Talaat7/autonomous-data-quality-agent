use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{env, ffi::CString, io, sync::mpsc, thread, time::Duration};

mod app;
mod ui;

use crate::app::{App, TraceEvent, Settings, ActionPlan};

enum TuiEvent {
    Input(KeyCode),
    Tick,
    Trace(TraceEvent),
    ApprovalRequired(ActionPlan),
    AnalysisComplete(String, Option<ActionPlan>),
    AnalysisError(String),
    Stats { rows: usize, cols: usize, issues: Option<usize>, score: Option<f64> },
    LineageUpdate(Vec<crate::app::LineageNode>),
    ExportSuccess(String),
    ExportError(String),
    Deltas(Vec<crate::app::MetricDelta>),
    LoadSuccess(String),
    LoadError(String),
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Setup Python environment
    // Add local src to PYTHONPATH if it exists (for dev), otherwise rely on installed package
    if let Ok(current_dir) = env::current_dir() {
        if let Some(parent) = current_dir.parent() {
            let src_path = parent.join("src");
            if src_path.exists() {
                let existing = env::var("PYTHONPATH").unwrap_or_default();
                let separator = if cfg!(windows) { ";" } else { ":" };
                let new_path = if existing.is_empty() {
                    src_path.to_string_lossy().to_string()
                } else {
                    format!("{}{}{}", src_path.to_string_lossy(), separator, existing)
                };
                env::set_var("PYTHONPATH", new_path);
            }
        }
    }

    // 2. Setup Terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // 3. Create App State and Event Channel
    let mut app = App::new();
    
    // Try to get dynamic version from Python environment
    let _ = Python::with_gil(|py| -> PyResult<()> {
        if let Ok(metadata) = py.import("importlib.metadata") {
            if let Ok(version) = metadata.call_method1("version", ("adqa",)) {
                app.version = format!("v{}", version.extract::<String>()?);
            }
        }
        Ok(())
    });

    let (tx, rx) = mpsc::channel();

    // Input thread
    let tx_input = tx.clone();
    thread::spawn(move || {
        loop {
            if let Ok(ready) = event::poll(Duration::from_millis(100)) {
                if ready {
                    if let Ok(Event::Key(key)) = event::read() {
                        if tx_input.send(TuiEvent::Input(key.code)).is_err() {
                            break;
                        }
                    }
                }
            }
            if tx_input.send(TuiEvent::Tick).is_err() {
                break;
            }
        }
    });

    // 4. Run App Loop
    loop {
        terminal.draw(|f| ui::render(f, &mut app))?;

        match rx.recv_timeout(Duration::from_millis(10)) {
            Ok(TuiEvent::Input(key)) => {
                if app.show_export_popup {
                    match key {
                        KeyCode::Enter => {
                            let path = app.export_path_input.clone();
                            let format = app.export_format;
                            let tx_export = tx.clone();
                            app.show_export_popup = false;
                            app.log(format!("Exporting to {}...", path), None);
                            thread::spawn(move || {
                                run_export_worker(tx_export, path, format);
                            });
                        }
                        KeyCode::Esc => app.show_export_popup = false,
                        KeyCode::Tab => {
                            app.export_format = match app.export_format {
                                crate::app::ExportFormat::Csv => {
                                    app.export_path_input = app.export_path_input.replace(".csv", ".json");
                                    if !app.export_path_input.ends_with(".json") { app.export_path_input.push_str(".json"); }
                                    crate::app::ExportFormat::Data
                                },
                                crate::app::ExportFormat::Data => {
                                    app.export_path_input = app.export_path_input.replace(".json", ".csv");
                                    if !app.export_path_input.ends_with(".csv") { app.export_path_input.push_str(".csv"); }
                                    crate::app::ExportFormat::Csv
                                }
                            };
                        }
                        KeyCode::Backspace => { app.export_path_input.pop(); }
                        KeyCode::Char(c) => { app.export_path_input.push(c); }
                        _ => {}
                    }
                } else if app.show_local_open_popup {
                    match key {
                        KeyCode::Enter => {
                            if let Some(path) = app.file_browser.enter() {
                                // A file was selected
                                let source = path.to_string_lossy().to_string();
                                
                                // Auto-detect if it's a DB file to show query input
                                let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("").to_lowercase();
                                if ext == "db" || ext == "sqlite" {
                                    app.show_local_open_popup = false;
                                    app.show_remote_open_popup = true;
                                    app.show_sql_query_input = true;
                                    app.open_input = format!("sqlite:///{}", source);
                                    app.sql_query_input = format!("SELECT * FROM data LIMIT {}", app.settings.default_sql_limit);
                                } else {
                                    app.show_local_open_popup = false;
                                    app.log(format!("Loading from {}...", source), None);
                                    let tx_load = tx.clone();
                                    let s = clone_settings(&app);
                                    thread::spawn(move || {
                                        run_load_worker(tx_load, source, s, None);
                                    });
                                }
                            }
                        }
                        KeyCode::Esc => {
                            app.show_local_open_popup = false;
                        }
                        KeyCode::Up | KeyCode::Char('k') => {
                            app.file_browser.scroll_up();
                        }
                        KeyCode::Down | KeyCode::Char('j') => {
                            app.file_browser.scroll_down();
                        }
                        _ => {}
                    }
                } else if app.show_remote_open_popup {
                    match key {
                        KeyCode::Enter => {
                            let source = app.open_input.clone();
                            let query = if app.show_sql_query_input { Some(app.sql_query_input.clone()) } else { None };
                            let tx_load = tx.clone();
                            let s = clone_settings(&app);
                            app.show_remote_open_popup = false;
                            app.show_sql_query_input = false;
                            app.log(format!("Loading from {}...", source), None);
                            thread::spawn(move || {
                                run_load_worker(tx_load, source, s, query);
                            });
                        }
                        KeyCode::Esc => {
                            app.show_remote_open_popup = false;
                            app.show_sql_query_input = false;
                        }
                        KeyCode::Tab => {
                            if app.open_input.contains("://") {
                                let db_prefixes = ["postgresql://", "postgres://", "mysql://", "sqlite://", "oracle://", "mssql://", "duckdb://", "snowflake://", "bigquery://", "redshift://"];
                                if db_prefixes.iter().any(|p| app.open_input.starts_with(p)) {
                                    app.show_sql_query_input = !app.show_sql_query_input;
                                }
                            }
                        }
                        KeyCode::Backspace => {
                            if app.show_sql_query_input {
                                app.sql_query_input.pop();
                            } else {
                                app.open_input.pop();
                                // Auto-hide SQL if we delete the prefix
                                let db_prefixes = ["postgresql://", "postgres://", "mysql://", "sqlite://", "oracle://", "mssql://", "duckdb://", "snowflake://", "bigquery://", "redshift://"];
                                if !db_prefixes.iter().any(|p| app.open_input.starts_with(p)) {
                                    app.show_sql_query_input = false;
                                }
                            }
                        }
                        KeyCode::Char(c) => {
                            if app.show_sql_query_input {
                                app.sql_query_input.push(c);
                            } else {
                                app.open_input.push(c);
                                // Auto-show SQL if we type a prefix
                                let db_prefixes = ["postgresql://", "postgres://", "mysql://", "sqlite://", "oracle://", "mssql://", "duckdb://", "snowflake://", "bigquery://", "redshift://"];
                                if db_prefixes.iter().any(|p| app.open_input.starts_with(p)) {
                                    app.show_sql_query_input = true;
                                }
                            }
                        }
                        _ => {}
                    }
                } else if app.show_numeric_popup {
                    match key {
                        KeyCode::Enter => app.confirm_numeric_input(),
                        KeyCode::Esc => app.show_numeric_popup = false,
                        KeyCode::Left => app.adjust_numeric_by_step(false),
                        KeyCode::Right => app.adjust_numeric_by_step(true),
                        KeyCode::Backspace => { app.numeric_input.pop(); }
                        KeyCode::Char(c) if c.is_digit(10) || c == '.' => {
                            app.numeric_input.push(c);
                        }
                        _ => {}
                    }
                } else if app.show_remediation_history_popup {
                    match key {
                        KeyCode::Enter => {
                            let path = app.export_path_input.clone();
                            let actions = app.all_executed_actions.clone();
                            let tx_export = tx.clone();
                            app.show_remediation_history_popup = false;
                            app.log(format!("Exporting fix history to {}...", path), None);
                            thread::spawn(move || {
                                run_history_export_worker(tx_export, path, actions);
                            });
                        }
                        KeyCode::Esc => app.show_remediation_history_popup = false,
                        KeyCode::Backspace => { app.export_path_input.pop(); }
                        KeyCode::Char(c) => { app.export_path_input.push(c); }
                        _ => {}
                    }
                } else if app.search_mode {
                    match key {
                        KeyCode::Enter | KeyCode::Esc => {
                            app.search_mode = false;
                        }
                        KeyCode::Backspace => {
                            if app.current_view == crate::app::View::TraceMonitor {
                                app.search_query.pop();
                            } else if app.current_view == crate::app::View::Lineage {
                                app.lineage_search.pop();
                            }
                            app.rebuild_visible_indices();
                        }
                        KeyCode::Char(c) => {
                            if app.current_view == crate::app::View::TraceMonitor {
                                app.search_query.push(c);
                            } else if app.current_view == crate::app::View::Lineage {
                                app.lineage_search.push(c);
                            }
                            app.rebuild_visible_indices();
                        }
                        _ => {}
                    }
                } else {
                    match key {
                        KeyCode::Char('q') => break,
                        KeyCode::Char('/') => {
                            if app.current_view == crate::app::View::TraceMonitor || app.current_view == crate::app::View::Lineage {
                                app.search_mode = true;
                            }
                        }
                        KeyCode::Char('f') => {
                            if app.current_view == crate::app::View::TraceMonitor {
                                app.filter_type = match app.filter_type.as_deref() {
                                    None => Some("data_ingress".to_string()),
                                    Some("data_ingress") => Some("profiling".to_string()),
                                    Some("profiling") => Some("check".to_string()),
                                    Some("check") => Some("error".to_string()),
                                    Some("error") => Some("ui".to_string()),
                                    _ => None,
                                };
                                app.rebuild_visible_indices();
                            }
                        }
                        KeyCode::Char('s') => {
                            if app.current_view == crate::app::View::TraceMonitor {
                                app.sort_order = match app.sort_order {
                                    crate::app::SortOrder::NewestFirst => crate::app::SortOrder::OldestFirst,
                                    crate::app::SortOrder::OldestFirst => crate::app::SortOrder::NewestFirst,
                                };
                                app.rebuild_visible_indices();
                            }
                        }
                        KeyCode::Char('?') | KeyCode::Char('h') => app.show_help = !app.show_help,
                        KeyCode::Esc => {
                            app.show_help = false;
                            app.show_trace_popup = false;
                            app.show_lineage_popup = false;
                            app.show_action_details = false;
                            app.search_mode = false;
                            app.show_export_popup = false;
                            app.show_remediation_history_popup = false;
                            app.show_local_open_popup = false;
                            app.show_remote_open_popup = false;
                        }
                        KeyCode::Tab => app.next_view(),
                        KeyCode::Up | KeyCode::Char('k') => app.scroll_up(),
                        KeyCode::Down | KeyCode::Char('j') => app.scroll_down(),
                        KeyCode::Char(' ') => {
                            if app.current_view == crate::app::View::RepairShop {
                                app.toggle_action();
                            }
                        }
                        KeyCode::Char('c') => {
                            app.clear_logs();
                            app.search_query.clear();
                            app.filter_type = None;
                        }
                        KeyCode::Char('e') => {
                            app.export_path_input = "adqa_export.csv".to_string();
                            app.export_format = crate::app::ExportFormat::Csv;
                            app.show_export_popup = !app.show_export_popup;
                            app.show_remediation_history_popup = false;
                        }
                        KeyCode::Char('E') => {
                            app.export_path_input = "adqa_remediation_history.json".to_string();
                            app.show_remediation_history_popup = !app.show_remediation_history_popup;
                            app.show_export_popup = false;
                        }
                        KeyCode::Char('o') => {
                            app.file_browser.refresh();
                            app.show_local_open_popup = !app.show_local_open_popup;
                            app.show_remote_open_popup = false;
                        }
                        KeyCode::Char('O') => {
                            app.open_input = String::new();
                            app.sql_query_input = format!("SELECT * FROM data LIMIT {}", app.settings.default_sql_limit);
                            app.show_remote_open_popup = !app.show_remote_open_popup;
                            app.show_local_open_popup = false;
                        }
                        KeyCode::Enter => app.handle_enter(),
                        KeyCode::Char('r') => {
                            app.active_plan = None;
                            app.last_plan = None;
                            app.last_plan_status = None;
                            // Don't clear deltas here to maintain session history
                            for step in &mut app.remediation_timeline { step.status = "pending".to_string(); }
                            app.analysis_progress = 0.05; // Immediate feedback
                            app.current_view = crate::app::View::Dashboard; // Auto-switch to see progress
                            app.log("--- STARTING NEW ANALYSIS RUN ---".to_string(), Some(serde_json::json!({
                                "mode": app.settings.execution_mode,
                                "ml_enabled": app.settings.ml_enabled,
                            })));
                            let tx_analysis = tx.clone();
                            let s = clone_settings(&app);
                            thread::spawn(move || {
                                run_adqa_worker(tx_analysis, s);
                            });
                        }
                        KeyCode::Char('a') => {
                            if let Some(plan) = &app.active_plan {
                                let selected_indices: Vec<usize> = plan.actions.iter().enumerate()
                                    .filter(|(_, a)| a.selected)
                                    .map(|(i, _)| i)
                                    .collect();
                                
                                if selected_indices.is_empty() {
                                    app.log("No actions selected for approval.".to_string(), None);
                                } else {
                                    app.log(format!("Approving {} selected actions...", selected_indices.len()), Some(serde_json::json!({
                                        "indices": selected_indices
                                    })));
                                    let tx_rem = tx.clone();
                                    thread::spawn(move || {
                                        run_remediation_worker(tx_rem, selected_indices);
                                    });
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
            Ok(TuiEvent::Trace(event)) => {
                // Update progress and timeline based on event name
                match event.name.as_str() {
                    "ENGINE_INITIALIZING" => {
                        app.analysis_progress = 0.1;
                        app.remediation_timeline[0].status = "completed".to_string();
                        app.remediation_timeline[1].status = "active".to_string();
                    }
                    "READ_DATA.success" | "READ_DATA_END" => {
                        app.analysis_progress = 0.2;
                        app.remediation_timeline[1].status = "completed".to_string();
                        app.remediation_timeline[2].status = "active".to_string();
                    }
                    "COLUMN_PROFILING.success" => {
                        app.analysis_progress = 0.4;
                        app.remediation_timeline[2].status = "completed".to_string();
                        app.remediation_timeline[3].status = "active".to_string();
                    }
                    "ML_PROFILE_RUN" => app.analysis_progress = 0.5,
                    "RULE_BASED_DETECTION.success" | "ML_BASED_DETECTION.success" => {
                        app.analysis_progress = 0.8;
                        app.remediation_timeline[3].status = "completed".to_string();
                        app.remediation_timeline[4].status = "active".to_string();
                    }
                    "QUALITY_DECISION" => {
                        app.analysis_progress = 0.9;
                    }
                    _ => {}
                }
                app.add_trace(event);
            }
            Ok(TuiEvent::Stats { rows, cols, issues, score }) => {
                app.row_count = rows;
                app.col_count = cols;
                
                if let Some(s) = score {
                    app.quality_score = s;
                    app.quality_history.push((s * 100.0) as u64);
                    if app.quality_history.len() > 50 {
                        app.quality_history.remove(0);
                    }
                }
                
                if let Some(i) = issues {
                    app.issue_count = i;
                }
            }
            Ok(TuiEvent::LineageUpdate(nodes)) => {
                for n in nodes {
                    if app.seen_lineage_ids.insert(n.node_id.clone()) {
                        app.lineage_nodes.push(n);
                    }
                }
            }
            Ok(TuiEvent::ApprovalRequired(plan)) => {
                app.analysis_progress = 1.0;
                app.active_plan = Some(plan);
                app.plan_selected_row = 0;
                app.current_view = crate::app::View::RepairShop;
                app.log("REMEDIATION PLAN RECEIVED. Approval required.".to_string(), None);
            }
            Ok(TuiEvent::AnalysisComplete(summary, maybe_plan)) => {
                app.analysis_progress = 1.0;
                app.analysis_summary = Some(summary);
                app.remediation_timeline[4].status = "completed".to_string();
                
                let mut has_actions = false;
                if let Some(plan) = app.active_plan.take() {
                    app.last_plan = Some(plan.clone());
                    app.last_plan_status = Some("EXECUTED (HUMAN APPROVED)".to_string());
                    for action in plan.actions {
                        if action.selected {
                            app.all_executed_actions.push(action);
                        }
                    }
                    has_actions = true;
                } else if let Some(plan) = maybe_plan {
                    app.last_plan = Some(plan.clone());
                    let is_advisory = app.settings.execution_mode == "advisory";
                    let status = if is_advisory {
                        "ADVISORY (PROPOSED ACTIONS)"
                    } else {
                        "AUTOMATICALLY APPLIED"
                    };
                    app.last_plan_status = Some(status.to_string());
                    
                    if !is_advisory {
                        for action in plan.actions {
                            app.all_executed_actions.push(action);
                        }
                    }
                    has_actions = true;
                }

                // Auto-switch to Repair Shop if anything interesting happened 
                // AND we're not in human mode (human mode switches on ApprovalRequired)
                if has_actions && app.settings.execution_mode != "human" {
                    app.current_view = crate::app::View::RepairShop;
                }
            }
            Ok(TuiEvent::AnalysisError(err)) => {
                app.add_trace(TraceEvent {
                    event_id: None,
                    name: "ERROR".to_string(),
                    event_type: "error".to_string(),
                    timestamp: "".to_string(),
                    metadata: serde_json::json!({"error": err}),
                    parent_event_id: None,
                });
            }
            Ok(TuiEvent::ExportSuccess(path)) => {
                app.log(format!("DATA EXPORTED SUCCESSFULLY to {}", path), None);
            }
            Ok(TuiEvent::ExportError(err)) => {
                app.log(format!("EXPORT FAILED: {}", err), None);
            }
            Ok(TuiEvent::Deltas(mut deltas)) => {
                app.metric_deltas.append(&mut deltas);
            }
            Ok(TuiEvent::LoadSuccess(path)) => {
                app.clear_logs(); // Clear old traces first
                app.log(format!("DATA LOADED SUCCESSFULLY from {}", path), None);
                app.current_view = crate::app::View::Dashboard;
            }
            Ok(TuiEvent::LoadError(err)) => {
                app.log(format!("LOAD FAILED: {}", err), None);
            }
            _ => {}
        }
    }

    // 5. Restore Terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    Ok(())
}

fn clone_settings(app: &App) -> Settings {
    Settings {
        execution_mode: app.settings.execution_mode.clone(),
        ml_enabled: app.settings.ml_enabled,
        tracing_enabled: app.settings.tracing_enabled,
        advanced_mode: app.settings.advanced_mode,
        lineage_enabled: app.settings.lineage_enabled,
        stop_on_block: app.settings.stop_on_block,
        profiling_ml: app.settings.profiling_ml,
        sample_size: app.settings.sample_size,
        rounding_precision: app.settings.rounding_precision,
        missing_threshold: app.settings.missing_threshold,
        outlier_threshold: app.settings.outlier_threshold,
        constant_threshold: app.settings.constant_threshold,
        duplicate_threshold: app.settings.duplicate_threshold,
        imbalance_threshold: app.settings.imbalance_threshold,
        skewness_threshold: app.settings.skewness_threshold,
        correlation_threshold: app.settings.correlation_threshold,
        pattern_threshold: app.settings.pattern_threshold,
        semantic_min_confidence: app.settings.semantic_min_confidence,
        anomaly_contamination: app.settings.anomaly_contamination,
        anomaly_n_estimators: app.settings.anomaly_n_estimators,
        default_sql_limit: app.settings.default_sql_limit,
        selected_setting: 0,
    }
}

fn run_load_worker(tx: mpsc::Sender<TuiEvent>, source_str: String, s: Settings, query: Option<String>) {
    let normalized_source = if !source_str.contains("://") {
        std::path::Path::new(&source_str)
            .canonicalize()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or(source_str.clone())
    } else {
        source_str.clone()
    };

    let res = Python::with_gil(|py| -> PyResult<(String, usize, usize)> {
        let main = py.import("__main__")?;
        let globals = main.dict();

        if globals.get_item("results_container")?.is_none() {
            let rc = pyo3::types::PyDict::new(py);
            globals.set_item("results_container", rc)?;
        }
        if globals.get_item("q")?.is_none() {
            let queue_mod = py.import("queue")?;
            let q_class = queue_mod.getattr("Queue")?;
            globals.set_item("q", q_class.call0()?)?;
        }

        globals.set_item("load_path", &normalized_source)?;
        globals.set_item("load_query", query)?;
        globals.set_item("ui_mode", s.execution_mode)?;
        globals.set_item("ui_ml", s.ml_enabled)?;
        globals.set_item("ui_tracing", s.tracing_enabled)?;
        globals.set_item("ui_lineage", s.lineage_enabled)?;
        globals.set_item("ui_stop_block", s.stop_on_block)?;
        globals.set_item("ui_prof_ml", s.profiling_ml)?;
        globals.set_item("ui_sample", s.sample_size)?;
        globals.set_item("ui_precision", s.rounding_precision)?;
        globals.set_item("ui_missing", s.missing_threshold)?;
        globals.set_item("ui_outlier", s.outlier_threshold)?;
        globals.set_item("ui_constant", s.constant_threshold)?;
        globals.set_item("ui_duplicate", s.duplicate_threshold)?;
        globals.set_item("ui_imbalance", s.imbalance_threshold)?;
        globals.set_item("ui_skewness", s.skewness_threshold)?;
        globals.set_item("ui_correlation", s.correlation_threshold)?;
        globals.set_item("ui_pattern", s.pattern_threshold)?;
        globals.set_item("ui_ml_conf", s.semantic_min_confidence)?;
        globals.set_item("ui_ml_contam", s.anomaly_contamination)?;
        globals.set_item("ui_ml_estimators", s.anomaly_n_estimators)?;

        py.run(CString::new(r#"
from adqa import DataSource, ADQA, ADQAConfig
from adqa.data_ingress.factory import DataReaderFactory
from adqa.trace.store.queue import QueueTraceStore
from adqa.trace.emitter import TraceEmitter
from adqa.trace.noop import NoOpTraceEmitter
from queue import Queue
from datetime import datetime

try:
    # 1. Load Data
    source = DataSource.load(load_path, query=load_query)
    reader = DataReaderFactory.create(source)
    df = reader.read()
    results_container['df'] = df
    
    # 2. Re-initialize Agent with new data and current UI settings
    mode_map = {
        "advisory": ADQAConfig.Mode.ADVISORY,
        "human": ADQAConfig.Mode.HUMAN_IN_LOOP,
        "automatic": ADQAConfig.Mode.AUTOMATIC
    }

    config = ADQAConfig(
        execution_mode=mode_map.get(ui_mode, ADQAConfig.Mode.ADVISORY),
        ml_enabled=ui_ml,
        tracing_enabled=ui_tracing,
        lineage_enabled=ui_lineage,
        execution={"stop_on_block": ui_stop_block},
        profiling={
            "enable_ml": ui_prof_ml, 
            "sample_size": ui_sample,
            "rounding_precision": ui_precision,
            "thresholds": {
                "semantic_min_confidence": ui_ml_conf,
                "anomaly_contamination": ui_ml_contam,
                "anomaly_n_estimators": ui_ml_estimators,
            }
        },
        detection={
            "enable_ml": ui_ml,
            "thresholds": {
                "missing_values_threshold": ui_missing, 
                "constant_column_threshold": ui_constant, 
                "duplicate_rows_threshold": ui_duplicate,
                "outlier_ratio_threshold": ui_outlier,
                "imbalance_threshold": ui_imbalance,
                "skewness_threshold": ui_skewness,
                "correlation_threshold": ui_correlation,
                "pattern_match_threshold": ui_pattern,
            }
        }
    )

    agent = ADQA(data_source=source, config=config)
    
    if ui_tracing:
        store = QueueTraceStore(q)
        agent._create_emitter = lambda ctx: TraceEmitter(context=ctx, store=store, store_traces=True)
    else:
        agent._create_emitter = lambda ctx: NoOpTraceEmitter()
        
    results_container['agent'] = agent
    
    # Reset history
    if 'last_result' in results_container: del results_container['last_result']
    if 'last_profiles' in results_container: del results_container['last_profiles']
    if 'error' in results_container: del results_container['error']
    
    # Update the global agent variable for the analysis thread
    globals().update({'agent': agent})
    
except Exception as e:
    raise e
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;

        let rc = globals.get_item("results_container")?.expect("rc missing").downcast_into::<pyo3::types::PyDict>()?;
        let df = rc.get_item("df")?.expect("df missing");
        let shape = df.getattr("shape")?.extract::<(usize, usize)>()?;
        Ok((source_str, shape.0, shape.1))
    });

    match res {
        Ok((path, rows, cols)) => { 
            let _ = tx.send(TuiEvent::Stats { rows, cols, issues: None, score: None });
            let _ = tx.send(TuiEvent::LoadSuccess(path)); 
        }
        Err(e) => { let _ = tx.send(TuiEvent::LoadError(e.to_string())); }
    }
}

fn run_export_worker(tx: mpsc::Sender<TuiEvent>, path: String, format: crate::app::ExportFormat) {
    let res = Python::with_gil(|py| -> PyResult<String> {
        let main = py.import("__main__")?;
        let globals = main.dict();
        
        globals.set_item("export_path", &path)?;

        match format {
            crate::app::ExportFormat::Csv => {
                py.run(CString::new(r#"
if 'results_container' in globals() and 'df' in results_container:
    results_container['df'].to_csv(export_path, index=False)
else:
    raise Exception("No data available to export. Run analysis first.")
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;
            },
            crate::app::ExportFormat::Data => {
                py.run(CString::new(r#"
if 'results_container' in globals() and 'df' in results_container:
    results_container['df'].to_json(export_path, orient='records', indent=2)
else:
    raise Exception("No data available to export.")
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;
            }
        }

        Ok(path)
    });

    match res {
        Ok(path) => { let _ = tx.send(TuiEvent::ExportSuccess(path)); }
        Err(e) => { let _ = tx.send(TuiEvent::ExportError(e.to_string())); }
    }
}

fn run_history_export_worker(tx: mpsc::Sender<TuiEvent>, path: String, actions: Vec<crate::app::Action>) {
    let res = (|| -> Result<String, Box<dyn std::error::Error>> {
        let json_str = serde_json::to_string_pretty(&actions)?;
        std::fs::write(&path, json_str)?;
        Ok(path)
    })();

    match res {
        Ok(path) => { let _ = tx.send(TuiEvent::ExportSuccess(path)); }
        Err(e) => { let _ = tx.send(TuiEvent::ExportError(e.to_string())); }
    }
}

fn run_adqa_worker(tx: mpsc::Sender<TuiEvent>, s: Settings) {
    let res = Python::with_gil(|py| -> PyResult<()> {
        let main = py.import("__main__")?;
        let globals = main.dict();

        if globals.get_item("results_container")?.is_none() {
            let rc = pyo3::types::PyDict::new(py);
            globals.set_item("results_container", rc)?;
        }
        if globals.get_item("q")?.is_none() {
            let queue_mod = py.import("queue")?;
            let q_class = queue_mod.getattr("Queue")?;
            globals.set_item("q", q_class.call0()?)?;
        }
        
        globals.set_item("ui_mode", s.execution_mode)?;
        globals.set_item("ui_ml", s.ml_enabled)?;
        globals.set_item("ui_tracing", s.tracing_enabled)?;
        globals.set_item("ui_lineage", s.lineage_enabled)?;
        globals.set_item("ui_stop_block", s.stop_on_block)?;
        globals.set_item("ui_prof_ml", s.profiling_ml)?;
        globals.set_item("ui_sample", s.sample_size)?;
        globals.set_item("ui_precision", s.rounding_precision)?;
        globals.set_item("ui_missing", s.missing_threshold)?;
        globals.set_item("ui_outlier", s.outlier_threshold)?;
        globals.set_item("ui_constant", s.constant_threshold)?;
        globals.set_item("ui_duplicate", s.duplicate_threshold)?;
        globals.set_item("ui_imbalance", s.imbalance_threshold)?;
        globals.set_item("ui_skewness", s.skewness_threshold)?;
        globals.set_item("ui_correlation", s.correlation_threshold)?;
        globals.set_item("ui_pattern", s.pattern_threshold)?;
        globals.set_item("ui_ml_conf", s.semantic_min_confidence)?;
        globals.set_item("ui_ml_contam", s.anomaly_contamination)?;
        globals.set_item("ui_ml_estimators", s.anomaly_n_estimators)?;

        py.run(CString::new(r#"
from adqa import ADQA, ADQAConfig, DataSource
from adqa.trace.store.queue import QueueTraceStore
from adqa.profiling.models.column_profile import SemanticTag
import pandas as pd
import numpy as np
from queue import Queue
import threading
import json
import dataclasses
from datetime import datetime

# Drain queue for new run
while not q.empty(): q.get()
if 'error' in results_container: del results_container['error']
if 'last_result' in results_container: del results_container['last_result']

if 'df' in results_container:
    df = results_container['df']
    source = DataSource.from_df(df)

    mode_map = {
        "advisory": ADQAConfig.Mode.ADVISORY,
        "human": ADQAConfig.Mode.HUMAN_IN_LOOP,
        "automatic": ADQAConfig.Mode.AUTOMATIC
    }

    config = ADQAConfig(
        execution_mode=mode_map.get(ui_mode, ADQAConfig.Mode.ADVISORY),
        ml_enabled=ui_ml, # Master ML toggle
        tracing_enabled=ui_tracing,
        lineage_enabled=ui_lineage,
        execution={"stop_on_block": ui_stop_block},
        profiling={
            "enable_ml": ui_prof_ml, 
            "enable_correlation": True, 
            "sample_size": ui_sample,
            "rounding_precision": ui_precision,
            "thresholds": {
                "semantic_min_confidence": ui_ml_conf,
                "anomaly_contamination": ui_ml_contam,
                "anomaly_n_estimators": ui_ml_estimators,
            }
        },
        detection={
            "enable_ml": ui_ml,
            "thresholds": {
                "missing_values_threshold": ui_missing, 
                "constant_column_threshold": ui_constant, 
                "duplicate_rows_threshold": ui_duplicate,
                "outlier_ratio_threshold": ui_outlier,
                "imbalance_threshold": ui_imbalance,
                "skewness_threshold": ui_skewness,
                "correlation_threshold": ui_correlation,
                "pattern_match_threshold": ui_pattern,
                "rare_category_threshold": 0.1,
                "min_rows_anomaly_detection": 10
            }
        }
    )

    hist = results_container.get('last_profiles')

    agent = ADQA(data_source=source, config=config, historical_profiles=hist)

    from adqa.trace.emitter import TraceEmitter
    from adqa.trace.noop import NoOpTraceEmitter
    if ui_tracing:
        store = QueueTraceStore(q)
        agent._create_emitter = lambda ctx: TraceEmitter(context=ctx, store=store, store_traces=True)
    else:
        agent._create_emitter = lambda ctx: NoOpTraceEmitter()
else:
    agent = None

def run_it():
    try:
        if agent is None:
            raise Exception("No data source opened. Please press [o] or [O] first.")
            
        # 0. Early feedback
        from datetime import datetime
        q.put({
            "name": "ENGINE_INITIALIZING",
            "event_type": "start",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"status": "starting_pipeline"}
        })

        # Run full Phase 3 pipeline
        res = agent.analyze()
        
        results_container['last_result'] = res
        results_container['agent'] = agent
        
        # Store for next run drift baseline
        if res.profiles:
            results_container['last_profiles'] = res.profiles
        
        # PERSIST fixed data if in automatic mode so next 'r' press is on clean data
        if res.execution_mode == "automatic" and res.dataframe is not None:
            results_container['df'] = res.dataframe
    except Exception as e:
        results_container['error'] = str(e)

t = threading.Thread(target=run_it)
t.start()
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;

        py.run(CString::new(r#"
import json
def get_deltas_json(old_profiles, new_df):
    if old_profiles is None or new_df is None:
        return "[]"
    
    from adqa.profiling.engine import ProfilingEngine
    from adqa.config.model import ADQAConfig as AC
    new_profiles = ProfilingEngine(AC()).run(new_df)
    
    def get_metric(obj, attr, default=0):
        if obj is None: return default
        if isinstance(obj, dict): return obj.get(attr, default)
        return getattr(obj, attr, default)

    deltas = []
    old_cols = {p.name if hasattr(p, 'name') else p['name']: p for p in old_profiles.dataset_profile.columns}
    new_cols = {p.name: p for p in new_profiles.dataset_profile.columns}
    
    all_cols = set(old_cols.keys()) | set(new_cols.keys())
    for col in all_cols:
        if col not in new_cols:
            deltas.append({"column": col, "metric": "Presence", "before": "Exists", "after": "Dropped"})
            continue
        if col not in old_cols:
            deltas.append({"column": col, "metric": "Presence", "before": "None", "after": "Added"})
            continue
            
        old_p = old_cols[col]
        new_p = new_cols[col]
        
        # Null ratio delta
        old_struct = getattr(old_p, 'structural_metrics', None) or (old_p.get('structural_metrics') if isinstance(old_p, dict) else None)
        new_struct = new_p.structural_metrics
        
        old_null = get_metric(old_struct, 'null_ratio', 0)
        new_null = get_metric(new_struct, 'null_ratio', 0)
        if abs(old_null - new_null) > 0.001:
            deltas.append({"column": col, "metric": "Null Ratio", "before": f"{old_null:.1%}", "after": f"{new_null:.1%}"})
            
        # Outlier ratio delta
        old_beh = getattr(old_p, 'behavioral_metrics', None) or (old_p.get('behavioral_metrics') if isinstance(old_p, dict) else None)
        new_beh = new_p.behavioral_metrics
        
        old_out = get_metric(old_beh, 'outlier_ratio', 0)
        new_out = get_metric(new_beh, 'outlier_ratio', 0)
        if abs(old_out - new_out) > 0.001:
            deltas.append({"column": col, "metric": "Outlier Ratio", "before": f"{old_out:.1%}", "after": f"{new_out:.1%}"})

    return json.dumps(deltas)
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;

        let q = globals.get_item("q")?.expect("q missing");
        let t = globals.get_item("t")?.expect("t missing");
        let results_container = globals.get_item("results_container")?.expect("results_container missing").downcast_into::<PyDict>()?;
        let json_mod = py.import("json")?;

        loop {
            while let Ok(empty_val) = q.call_method0("empty") {
                if empty_val.extract::<bool>()? {
                    break;
                }
                let item = q.call_method0("get")?.downcast_into::<PyDict>()?;
                let json_str: String = json_mod.call_method1("dumps", (item,))?.extract()?;
                if let Ok(event) = serde_json::from_str::<TraceEvent>(&json_str) {
                    let _ = tx.send(TuiEvent::Trace(event));
                }
            }

            if !t.call_method0("is_alive")?.extract::<bool>()? {
                break;
            }
            thread::sleep(Duration::from_millis(50));
        }

        if let Some(error_bound) = results_container.get_item("error")? {
            let error: String = error_bound.extract()?;
            let _ = tx.send(TuiEvent::AnalysisError(error));
        } else if let Some(result_bound) = results_container.get_item("last_result")? {
            // Extract stats safely
            let df_bound = result_bound.getattr("dataframe")?;
            let (rows, cols) = if !df_bound.is_none() {
                let shape = df_bound.getattr("shape")?.extract::<(usize, usize)>()?;
                (shape.0, shape.1)
            } else { (0, 0) };

            let mut score = None;
            let mut issues = None;

            let decision_bound = result_bound.getattr("decision")?;
            if !decision_bound.is_none() {
                score = Some(decision_bound.getattr("score")?.extract()?);
            }
            
            let detections_bound = result_bound.getattr("detections")?;
            if !detections_bound.is_none() {
                let detections_list = detections_bound.getattr("detections")?.downcast_into::<pyo3::types::PyList>()?;
                let ml_list = detections_bound.getattr("ml_evidence")?.downcast_into::<pyo3::types::PyList>()?;
                issues = Some(detections_list.len() + ml_list.len());
            }

            let _ = tx.send(TuiEvent::Stats { rows, cols, issues, score });

            // Calculate Deltas
            let old_profiles = results_container.get_item("last_profiles")?;
            let new_df = result_bound.getattr("dataframe")?;
            if let Some(old_p) = old_profiles {
                if !new_df.is_none() {
                    let s_deltas: String = globals.get_item("get_deltas_json")?.unwrap().call1((old_p, new_df))?.extract()?;
                    if let Ok(rust_deltas) = serde_json::from_str::<Vec<crate::app::MetricDelta>>(&s_deltas) {
                        let _ = tx.send(TuiEvent::Deltas(rust_deltas));
                    }
                }
            }

            // Extract Lineage
            let agent_bound = results_container.get_item("agent")?.expect("agent missing");
            let lineage_recorder = agent_bound.getattr("_lineage")?;
            let trace_id = result_bound.getattr("trace_id")?;
            if !trace_id.is_none() {
                let uuid_mod = py.import("uuid")?;
                let trace_uuid = uuid_mod.call_method1("UUID", (trace_id,))?;
                let nodes_bound = lineage_recorder.call_method1("get", (trace_uuid,))?;
                
                let s_lineage: String = py.run(CString::new(r#"
import json
def get_lineage_json(nodes):
    return json.dumps([n.to_dict() for n in nodes])
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))
                    .and_then(|_| {
                        globals.get_item("get_lineage_json")?.unwrap().call1((nodes_bound,))?.extract()
                    })?;

                if let Ok(rust_nodes) = serde_json::from_str::<Vec<crate::app::LineageNode>>(&s_lineage) {
                    let _ = tx.send(TuiEvent::LineageUpdate(rust_nodes));
                }
            }

            // Extract Plan (if any)
            let extract_plan = |result_bound: &Bound<'_, PyAny>| -> PyResult<Option<ActionPlan>> {
                let plan_bound = result_bound.getattr("plan")?;
                if plan_bound.is_none() {
                    return Ok(None);
                }
                let actions_list = plan_bound.getattr("actions")?.downcast_into::<pyo3::types::PyList>()?;
                let mut rust_actions = Vec::new();
                for a in actions_list.iter() {
                    let metadata: String = json_mod.call_method1("dumps", (a.getattr("metadata")?,))?.extract()?;
                    rust_actions.push(crate::app::Action {
                        action_type: a.getattr("action_type")?.extract()?,
                        reason: a.getattr("reason")?.extract()?,
                        requires_approval: a.getattr("requires_approval")?.extract()?,
                        selected: true,
                        metadata: serde_json::from_str(&metadata).unwrap_or(serde_json::Value::Null),
                    });
                }
                Ok(Some(ActionPlan {
                    actions: rust_actions,
                    summary: plan_bound.getattr("summary")?.extract()?,
                }))
            };

            let maybe_rust_plan = extract_plan(&result_bound)?;

            let approval_payload = result_bound.getattr("approval_payload")?;
            if !approval_payload.is_none() {
                if let Some(plan) = maybe_rust_plan {
                    let _ = tx.send(TuiEvent::ApprovalRequired(plan));
                }
            } else {
                let summary: String = result_bound.call_method0("summary")?.extract()?;
                let _ = tx.send(TuiEvent::AnalysisComplete(summary, maybe_rust_plan));
            }
        }

        Ok(())
    });

    if let Err(e) = res {
        let _ = tx.send(TuiEvent::AnalysisError(e.to_string()));
    }
}

fn run_remediation_worker(tx: mpsc::Sender<TuiEvent>, selected_indices: Vec<usize>) {
    let res = Python::with_gil(|py| -> PyResult<()> {
        let main = py.import("__main__")?;
        let globals = main.dict();
        
        globals.set_item("ui_selected_indices", selected_indices)?;

        py.run(CString::new(r#"
import threading

def approve_it():
    if 'error' in results_container: del results_container['error']
    try:
        if 'agent' not in results_container or results_container['agent'] is None:
            raise Exception("No active agent. Open data source first.")
            
        agent = results_container['agent']
        result = results_container['last_result']
        plan = result.plan
        
        filtered_actions = []
        for i, action in enumerate(plan.actions):
            if i in ui_selected_indices:
                filtered_actions.append(action)
        
        plan.actions = filtered_actions
        plan.approved = True
        
        final_result = agent.execute_plan(plan, df=result.dataframe)
        
        results_container['df'] = final_result.dataframe
        results_container['last_result'] = final_result
    except Exception as e:
        results_container['error'] = str(e)

t_rem = threading.Thread(target=approve_it)
t_rem.start()
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))?;

        let t_rem = globals.get_item("t_rem")?.expect("t_rem missing");
        let results_container: Bound<'_, PyDict> = globals.get_item("results_container")?.expect("rc missing").downcast_into()?;
        let json_mod = py.import("json")?;

        while t_rem.call_method0("is_alive")?.extract::<bool>()? {
            thread::sleep(Duration::from_millis(50));
        }

        if let Some(error_bound) = results_container.get_item("error")? {
            let error: String = error_bound.extract()?;
            let _ = tx.send(TuiEvent::AnalysisError(error));
        } else if let Some(final_result_bound) = results_container.get_item("last_result")? {
            // Extract stats safely
            let df_bound = final_result_bound.getattr("dataframe")?;
            let (rows, cols) = if !df_bound.is_none() {
                let shape = df_bound.getattr("shape")?.extract::<(usize, usize)>()?;
                (shape.0, shape.1)
            } else { (0, 0) };

            let mut score = None;
            let mut issues = None;

            let decision_bound = final_result_bound.getattr("decision")?;
            if !decision_bound.is_none() {
                score = Some(decision_bound.getattr("score")?.extract()?);
            }
            
            let detections_bound = final_result_bound.getattr("detections")?;
            if !detections_bound.is_none() {
                let detections_list = detections_bound.getattr("detections")?.downcast_into::<pyo3::types::PyList>()?;
                let ml_list = detections_bound.getattr("ml_evidence")?.downcast_into::<pyo3::types::PyList>()?;
                issues = Some(detections_list.len() + ml_list.len());
            }

            let _ = tx.send(TuiEvent::Stats { rows, cols, issues, score });

            // Calculate Deltas after manual remediation
            let old_profiles = results_container.get_item("last_profiles")?;
            let new_df = final_result_bound.getattr("dataframe")?;
            if let Some(old_p) = old_profiles {
                if !new_df.is_none() {
                    let s_deltas: String = globals.get_item("get_deltas_json")?.unwrap().call1((old_p, new_df))?.extract()?;
                    if let Ok(rust_deltas) = serde_json::from_str::<Vec<crate::app::MetricDelta>>(&s_deltas) {
                        let _ = tx.send(TuiEvent::Deltas(rust_deltas));
                    }
                }
            }

            // Extract Lineage after remediation
            let agent_bound = results_container.get_item("agent")?.expect("agent missing");
            let lineage_recorder = agent_bound.getattr("_lineage")?;
            let trace_id = final_result_bound.getattr("trace_id")?;
            if !trace_id.is_none() {
                let uuid_mod = py.import("uuid")?;
                let trace_uuid = uuid_mod.call_method1("UUID", (trace_id,))?;
                let nodes_bound = lineage_recorder.call_method1("get", (trace_uuid,))?;
                
                let s_lineage: String = py.run(CString::new(r#"
import json
def get_lineage_json(nodes):
    return json.dumps([n.to_dict() for n in nodes])
"#).unwrap().as_c_str(), Some(&globals), Some(&globals))
                    .and_then(|_| {
                        globals.get_item("get_lineage_json")?.unwrap().call1((nodes_bound,))?.extract()
                    })?;

                if let Ok(rust_nodes) = serde_json::from_str::<Vec<crate::app::LineageNode>>(&s_lineage) {
                    let _ = tx.send(TuiEvent::LineageUpdate(rust_nodes));
                }
            }

            // Extract Plan after remediation
            let extract_plan = |result_bound: &Bound<'_, PyAny>| -> PyResult<Option<ActionPlan>> {
                let plan_bound = result_bound.getattr("plan")?;
                if plan_bound.is_none() {
                    return Ok(None);
                }
                let actions_list = plan_bound.getattr("actions")?.downcast_into::<pyo3::types::PyList>()?;
                let mut rust_actions = Vec::new();
                for a in actions_list.iter() {
                    let metadata: String = json_mod.call_method1("dumps", (a.getattr("metadata")?,))?.extract()?;
                    rust_actions.push(crate::app::Action {
                        action_type: a.getattr("action_type")?.extract()?,
                        reason: a.getattr("reason")?.extract()?,
                        requires_approval: a.getattr("requires_approval")?.extract()?,
                        selected: true,
                        metadata: serde_json::from_str(&metadata).unwrap_or(serde_json::Value::Null),
                    });
                }
                Ok(Some(ActionPlan {
                    actions: rust_actions,
                    summary: plan_bound.getattr("summary")?.extract()?,
                }))
            };

            let maybe_rust_plan = extract_plan(&final_result_bound)?;

            let summary: String = final_result_bound.call_method0("summary")?.extract()?;
            let _ = tx.send(TuiEvent::AnalysisComplete(summary, maybe_rust_plan));
        }

        Ok(())
    });

    if let Err(e) = res {
        let _ = tx.send(TuiEvent::AnalysisError(e.to_string()));
    }
}
