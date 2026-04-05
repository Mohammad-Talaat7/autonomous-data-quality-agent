use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum View {
    Dashboard,
    RepairShop,
    TraceMonitor,
    Lineage,
    Settings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LineageNode {
    pub node_id: String,
    pub operation: String,
    pub inputs: serde_json::Value,
    pub outputs: serde_json::Value,
    pub metadata: serde_json::Value,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceEvent {
    #[serde(default)]
    pub event_id: Option<String>,
    pub name: String,
    pub event_type: String,
    pub timestamp: String,
    pub metadata: serde_json::Value,
    #[serde(default)]
    pub parent_event_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub action_type: String,
    pub reason: String,
    pub requires_approval: bool,
    #[serde(default = "default_selected")]
    pub selected: bool,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

fn default_selected() -> bool { true }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionPlan {
    pub actions: Vec<Action>,
    pub summary: String,
}

pub struct Settings {
    pub execution_mode: String,
    pub ml_enabled: bool,
    pub tracing_enabled: bool,
    pub advanced_mode: bool,
    pub lineage_enabled: bool,
    pub stop_on_block: bool,
    pub profiling_ml: bool,
    
    // Hyper-parameters: Profiling
    pub sample_size: usize,
    pub rounding_precision: usize,
    
    // Hyper-parameters: Detection Thresholds
    pub missing_threshold: f64,
    pub outlier_threshold: f64,
    pub constant_threshold: f64,
    pub duplicate_threshold: f64,
    pub imbalance_threshold: f64,
    pub skewness_threshold: f64,
    pub correlation_threshold: f64,
    pub pattern_threshold: f64,
    
    // Hyper-parameters: ML
    pub semantic_min_confidence: f64,
    pub anomaly_contamination: f64,
    pub anomaly_n_estimators: usize,

    pub default_sql_limit: usize,

    pub selected_setting: usize,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum VisibleItem {
    Single(usize),
    GroupHeader {
        name: String,
        indices: Vec<usize>,
        expanded: bool,
    },
    GroupMember(usize),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricDelta {
    pub column: String,
    pub metric: String,
    pub before: String,
    pub after: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimelineStep {
    pub label: String,
    pub status: String, // "pending", "active", "completed", "failed"
}

#[derive(Debug, Clone)]
pub struct FileBrowserEntry {
    pub name: String,
    pub path: PathBuf,
    pub is_dir: bool,
}

pub struct FileBrowser {
    pub current_dir: PathBuf,
    pub entries: Vec<FileBrowserEntry>,
    pub selected_index: usize,
}

impl FileBrowser {
    pub fn new() -> Self {
        let current_dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let mut browser = Self {
            current_dir,
            entries: Vec::new(),
            selected_index: 0,
        };
        browser.refresh();
        browser
    }

    pub fn refresh(&mut self) {
        self.entries.clear();
        
        // Add ".." entry if not at root
        if let Some(parent) = self.current_dir.parent() {
            self.entries.push(FileBrowserEntry {
                name: "..".to_string(),
                path: parent.to_path_buf(),
                is_dir: true,
            });
        }

        if let Ok(read_dir) = fs::read_dir(&self.current_dir) {
            let mut items: Vec<FileBrowserEntry> = read_dir
                .filter_map(|entry| {
                    let entry = entry.ok()?;
                    let path = entry.path();
                    let metadata = entry.metadata().ok()?;
                    let name = entry.file_name().to_string_lossy().to_string();
                    
                    // Basic hidden file filtering
                    if name.starts_with('.') && name != ".." {
                        return None;
                    }

                    Some(FileBrowserEntry {
                        name,
                        path,
                        is_dir: metadata.is_dir(),
                    })
                })
                .collect();

            // Sort: Directories first, then alphabetically
            items.sort_by(|a, b| {
                if a.is_dir != b.is_dir {
                    b.is_dir.cmp(&a.is_dir)
                } else {
                    a.name.to_lowercase().cmp(&b.name.to_lowercase())
                }
            });

            self.entries.extend(items);
        }

        if self.selected_index >= self.entries.len() {
            self.selected_index = self.entries.len().saturating_sub(1);
        }
    }

    pub fn scroll_up(&mut self) {
        if self.selected_index > 0 {
            self.selected_index -= 1;
        }
    }

    pub fn scroll_down(&mut self) {
        if !self.entries.is_empty() && self.selected_index + 1 < self.entries.len() {
            self.selected_index += 1;
        }
    }

    pub fn enter(&mut self) -> Option<PathBuf> {
        if self.entries.is_empty() {
            return None;
        }
        let entry = &self.entries[self.selected_index];
        if entry.is_dir {
            self.current_dir = entry.path.clone();
            self.selected_index = 0;
            self.refresh();
            None
        } else {
            Some(entry.path.clone())
        }
    }
}

pub struct App {
    pub version: String,
    pub current_view: View,
    pub logs: Vec<TraceEvent>,
    pub visible_items: Vec<VisibleItem>,
    pub expanded_groups: std::collections::HashSet<usize>,
    pub selected_index: usize,
    pub show_trace_popup: bool,
    pub show_action_details: bool,
    pub show_help: bool,
    pub analysis_summary: Option<String>,
    pub active_plan: Option<ActionPlan>,
    pub last_plan: Option<ActionPlan>,
    pub last_plan_status: Option<String>,
    pub plan_selected_row: usize,
    pub settings: Settings,
    
    // History
    pub all_executed_actions: Vec<Action>,
    pub seen_lineage_ids: std::collections::HashSet<String>,
    
    // Lineage State
    pub lineage_nodes: Vec<LineageNode>,
    pub lineage_selected_index: usize,
    pub show_lineage_popup: bool,
    
    pub popup_scroll: usize,
    
    // Dashboard Stats
    pub analysis_progress: f64,
    pub quality_score: f64,
    pub quality_history: Vec<u64>,
    pub row_count: usize,
    pub col_count: usize,
    pub issue_count: usize,
    pub remediations_count: usize,

    pub metric_deltas: Vec<MetricDelta>,
    pub remediation_timeline: Vec<TimelineStep>,

    // Search & Filter & Sort
    pub search_query: String,
    pub search_mode: bool,
    pub filter_type: Option<String>, // e.g., "error", "profiling", "ml"
    pub sort_order: SortOrder,

    // Lineage Search/Filter
    pub lineage_search: String,

    // Export Popup
    pub show_export_popup: bool,
    pub show_remediation_history_popup: bool,
    pub export_path_input: String,
    pub export_format: ExportFormat,

    // Open Popup
    pub show_local_open_popup: bool,
    pub show_remote_open_popup: bool,
    pub show_sql_query_input: bool,
    pub show_numeric_popup: bool,
    pub open_input: String,
    pub sql_query_input: String,
    pub numeric_input: String,
    pub editing_setting_idx: usize,

    // File Browser
    pub file_browser: FileBrowser,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportFormat {
    Csv,
    Data, // DataFrame as JSON
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SortOrder {
    NewestFirst,
    OldestFirst,
}

impl App {
    pub fn new() -> Self {
        Self {
            version: "v0.1.0-dev".to_string(),
            current_view: View::Dashboard,
            logs: Vec::new(),
            visible_items: Vec::new(),
            expanded_groups: std::collections::HashSet::new(),
            selected_index: 0,
            show_trace_popup: false,
            show_action_details: false,
            show_help: false,
            analysis_summary: None,
            active_plan: None,
            last_plan: None,
            last_plan_status: None,
            plan_selected_row: 0,
            all_executed_actions: Vec::new(),
            seen_lineage_ids: std::collections::HashSet::new(),
            settings: Settings {
                execution_mode: "advisory".to_string(),
                ml_enabled: true,
                tracing_enabled: true,
                advanced_mode: false,
                lineage_enabled: true,
                stop_on_block: false,
                profiling_ml: true,

                // Profiling
                sample_size: 10000,
                rounding_precision: 4,

                // Detection
                missing_threshold: 0.2,
                outlier_threshold: 0.05,
                constant_threshold: 1.0, 
                duplicate_threshold: 0.1,
                imbalance_threshold: 0.9,
                skewness_threshold: 1.0,
                correlation_threshold: 0.9,
                pattern_threshold: 0.8,

                // ML
                semantic_min_confidence: 0.4,
                anomaly_contamination: 0.05,
                anomaly_n_estimators: 50,

                default_sql_limit: 1000,

                selected_setting: 0,
            },

            analysis_progress: 0.0,
            quality_score: 0.0,
            quality_history: Vec::new(),
            row_count: 0,
            col_count: 0,
            issue_count: 0,
            remediations_count: 0,
            lineage_nodes: Vec::new(),
            lineage_selected_index: 0,
            show_lineage_popup: false,
            popup_scroll: 0,
            metric_deltas: Vec::new(),
            remediation_timeline: vec![
                TimelineStep { label: "Initialize".to_string(), status: "pending".to_string() },
                TimelineStep { label: "Read Data".to_string(), status: "pending".to_string() },
                TimelineStep { label: "Profile".to_string(), status: "pending".to_string() },
                TimelineStep { label: "Detect Risks".to_string(), status: "pending".to_string() },
                TimelineStep { label: "Heal Data".to_string(), status: "pending".to_string() },
            ],
            search_query: String::new(),
            search_mode: false,
            filter_type: None,
            sort_order: SortOrder::OldestFirst,
            lineage_search: String::new(),
            show_export_popup: false,
            show_remediation_history_popup: false,
            export_path_input: "adqa_export.csv".to_string(),
            export_format: ExportFormat::Csv,
            show_local_open_popup: false,
            show_remote_open_popup: false,
            show_sql_query_input: false,
            show_numeric_popup: false,
            open_input: String::new(),
            sql_query_input: format!("SELECT * FROM data LIMIT 1000"),
            numeric_input: String::new(),
            editing_setting_idx: 0,
            file_browser: FileBrowser::new(),
        }
    }


    pub fn add_trace(&mut self, event: TraceEvent) {
        let was_at_end = self.selected_index + 1 >= self.visible_items.len();
        self.logs.push(event);
        self.rebuild_visible_indices();
        if was_at_end && !self.visible_items.is_empty() {
            self.selected_index = self.visible_items.len() - 1;
        }
    }

    pub fn rebuild_visible_indices(&mut self) {
        self.visible_items.clear();
        
        // 1. Filter and Sort the base indices
        let mut filtered_indices: Vec<usize> = (0..self.logs.len()).filter(|&idx| {
            let event = &self.logs[idx];
            
            // Skip .success/.failure markers from main list (they are pairs)
            if event.name.ends_with(".success") || event.name.ends_with(".failure") {
                return false;
            }

            // Type Filter
            if let Some(ref f) = self.filter_type {
                if event.event_type.to_lowercase() != f.to_lowercase() {
                    return false;
                }
            }
            
            // Search Query (case-insensitive)
            if !self.search_query.is_empty() {
                let q = self.search_query.to_lowercase();
                let matches_name = event.name.to_lowercase().contains(&q);
                let matches_meta = serde_json::to_string(&event.metadata).unwrap_or_default().to_lowercase().contains(&q);
                if !matches_name && !matches_meta {
                    return false;
                }
            }
            
            true
        }).collect();

        if self.sort_order == SortOrder::NewestFirst {
            filtered_indices.reverse();
        }

        // 2. Build visible items with grouping logic
        let mut i = 0;
        while i < filtered_indices.len() {
            let idx = filtered_indices[i];
            let event = &self.logs[idx];
            
            // Determine if this event should start a group
            let group_type = if event.name.starts_with("COLUMN_PROFILING") || event.name.starts_with("PROFILE_") {
                Some("Profiling")
            } else if event.name.starts_with("CHECK_") || event.name.starts_with("RULE_") || event.name.contains("DETECTION") || event.name.contains("DETECTOR") || event.name.starts_with("rule.") {
                Some("Quality Checks")
            } else if event.name.starts_with("ML_") || event.name.contains("MODEL") || event.name.starts_with("metric.") {
                Some("ML Analysis")
            } else if event.name.starts_with("fix.") || event.name.contains("REMEDIATION") {
                Some("Remediation")
            } else {
                None
            };

            if let Some(g_name) = group_type {
                let mut group_indices = vec![idx];
                let mut j = i + 1;
                
                // Look ahead for similar events, allow some "noise" like UI logs to be absorbed into the group
                // or just keep it consecutive for strictness but with broader matching.
                // Let's keep it consecutive for now but with the same broad matching.
                while j < filtered_indices.len() {
                    let next_idx = filtered_indices[j];
                    let next_event = &self.logs[next_idx];
                    let next_group_type = if next_event.name.starts_with("COLUMN_PROFILING") || next_event.name.starts_with("PROFILE_") {
                        Some("Profiling")
                    } else if next_event.name.starts_with("CHECK_") || next_event.name.starts_with("RULE_") || next_event.name.contains("DETECTION") || next_event.name.contains("DETECTOR") || next_event.name.starts_with("rule.") {
                        Some("Quality Checks")
                    } else if next_event.name.starts_with("ML_") || next_event.name.contains("MODEL") || next_event.name.starts_with("metric.") {
                        Some("ML Analysis")
                    } else if next_event.name.starts_with("fix.") || next_event.name.contains("REMEDIATION") {
                        Some("Remediation")
                    } else {
                        None
                    };

                    if next_group_type == Some(g_name) {
                        group_indices.push(next_idx);
                        j += 1;
                    } else if next_event.event_type == "ui" {
                        // Absorb minor UI logs into the current group to keep it cohesive
                        group_indices.push(next_idx);
                        j += 1;
                    } else {
                        break;
                    }
                }

                if group_indices.len() > 1 {
                    let expanded = self.expanded_groups.contains(&idx);
                    self.visible_items.push(VisibleItem::GroupHeader {
                        name: g_name.to_string(),
                        indices: group_indices.clone(),
                        expanded,
                    });

                    if expanded {
                        for &g_idx in &group_indices {
                            self.visible_items.push(VisibleItem::GroupMember(g_idx));
                        }
                    }
                    i = j;
                    continue;
                }
            }

            // Default: Single item
            self.visible_items.push(VisibleItem::Single(idx));
            i += 1;
        }

        // 3. Safety Check: Clamp selected_index
        if !self.visible_items.is_empty() {
            if self.selected_index >= self.visible_items.len() {
                self.selected_index = self.visible_items.len() - 1;
            }
        } else {
            self.selected_index = 0;
        }
    }

    pub fn log(&mut self, message: String, metadata: Option<serde_json::Value>) {
        let timestamp = chrono::Local::now().format("%Y-%m-%dT%H:%M:%S%.6f").to_string();
        self.add_trace(TraceEvent {
            event_id: Some(uuid::Uuid::new_v4().to_string()),
            name: message,
            event_type: "ui".to_string(),
            timestamp,
            metadata: metadata.unwrap_or(serde_json::Value::Null),
            parent_event_id: None,
        });
    }

    pub fn scroll_up(&mut self) {
        if self.show_local_open_popup {
            self.file_browser.scroll_up();
            return;
        }

        if self.show_trace_popup || self.show_lineage_popup {
            if self.popup_scroll > 0 {
                self.popup_scroll -= 1;
            }
            return;
        }

        if self.current_view == View::Settings {
            if self.settings.selected_setting > 0 {
                self.settings.selected_setting -= 1;
            }
        } else if self.current_view == View::RepairShop {
            if self.plan_selected_row > 0 {
                self.plan_selected_row -= 1;
            }
        } else if self.current_view == View::Lineage {
            if self.lineage_selected_index > 0 {
                self.lineage_selected_index -= 1;
            }
        } else if self.selected_index > 0 {
            self.selected_index -= 1;
        }
    }

    pub fn clear_logs(&mut self) {
        self.logs.clear();
        self.visible_items.clear();
        self.expanded_groups.clear();
        self.selected_index = 0;
        
        // Reset dashboard stats
        self.analysis_progress = 0.0;
        self.quality_score = 0.0;
        self.quality_history.clear();
        self.row_count = 0;
        self.col_count = 0;
        self.issue_count = 0;
        self.remediations_count = 0;
        self.analysis_summary = None;
        self.lineage_nodes.clear();
        self.lineage_selected_index = 0;
        self.all_executed_actions.clear();
        self.seen_lineage_ids.clear();
        self.metric_deltas.clear();
        for step in &mut self.remediation_timeline {
            step.status = "pending".to_string();
        }
    }

    pub fn scroll_down(&mut self) {
        if self.show_local_open_popup {
            self.file_browser.scroll_down();
            return;
        }

        if self.show_trace_popup || self.show_lineage_popup {
            if self.popup_scroll < 100 { // Limit for safety
                self.popup_scroll += 1;
            }
            return;
        }

        if self.current_view == View::Settings {
            let max = if self.settings.advanced_mode { 20 } else { 3 };
            if self.settings.selected_setting < max {
                self.settings.selected_setting += 1;
            }
        } else if self.current_view == View::RepairShop {
            let history_count = self.all_executed_actions.len();
            let current_count = if let Some(plan) = &self.active_plan {
                plan.actions.len()
            } else if let Some(plan) = &self.last_plan {
                plan.actions.len()
            } else {
                0
            };

            let total_count = history_count + current_count;
            if total_count > 0 && self.plan_selected_row + 1 < total_count {
                self.plan_selected_row += 1;
            }

        } else if self.current_view == View::Lineage {
            if self.lineage_selected_index + 1 < self.lineage_nodes.len() {
                self.lineage_selected_index += 1;
            }
        } else if self.selected_index + 1 < self.visible_items.len() {
            self.selected_index += 1;
        }
    }

    pub fn handle_enter(&mut self) {
        if self.current_view == View::Settings {
            self.toggle_setting();
        } else if self.current_view == View::RepairShop {
            self.show_action_details = !self.show_action_details;
            self.popup_scroll = 0;
        } else if self.current_view == View::Lineage {
            if !self.lineage_nodes.is_empty() {
                self.show_lineage_popup = !self.show_lineage_popup;
                self.popup_scroll = 0;
            }
        } else if self.current_view == View::TraceMonitor && !self.visible_items.is_empty() {
            match &self.visible_items[self.selected_index] {
                VisibleItem::GroupHeader { indices, .. } => {
                    let start_idx = indices[0];
                    if self.expanded_groups.contains(&start_idx) {
                        self.expanded_groups.remove(&start_idx);
                    } else {
                        self.expanded_groups.insert(start_idx);
                    }
                    self.rebuild_visible_indices();
                }
                _ => {
                    self.show_trace_popup = !self.show_trace_popup;
                    self.popup_scroll = 0;
                }
            }
        }
    }

    pub fn toggle_action(&mut self) {
        if let Some(plan) = &mut self.active_plan {
            let history_offset = self.all_executed_actions.len();
            if self.plan_selected_row >= history_offset {
                let plan_idx = self.plan_selected_row - history_offset;
                if let Some(action) = plan.actions.get_mut(plan_idx) {
                    action.selected = !action.selected;
                }
            }
        }
    }

    pub fn toggle_setting(&mut self) {
        match self.settings.selected_setting {
            0 => self.settings.advanced_mode = !self.settings.advanced_mode,
            1 => {
                self.settings.execution_mode = match self.settings.execution_mode.as_str() {
                    "advisory" => "human".to_string(),
                    "human" => "automatic".to_string(),
                    _ => "advisory".to_string(),
                };
            }
            2 => self.settings.ml_enabled = !self.settings.ml_enabled,
            3 => self.settings.tracing_enabled = !self.settings.tracing_enabled,
            4 => self.settings.lineage_enabled = !self.settings.lineage_enabled,
            5 => self.settings.stop_on_block = !self.settings.stop_on_block,
            6 => self.settings.profiling_ml = !self.settings.profiling_ml,
            
            // Numeric fields trigger popup
            7..=20 => {
                self.editing_setting_idx = self.settings.selected_setting;
                self.numeric_input = match self.editing_setting_idx {
                    7 => self.settings.sample_size.to_string(),
                    8 => self.settings.rounding_precision.to_string(),
                    9 => format!("{:.2}", self.settings.missing_threshold),
                    10 => format!("{:.2}", self.settings.outlier_threshold),
                    11 => format!("{:.2}", self.settings.constant_threshold),
                    12 => format!("{:.2}", self.settings.duplicate_threshold),
                    13 => format!("{:.2}", self.settings.imbalance_threshold),
                    14 => format!("{:.2}", self.settings.skewness_threshold),
                    15 => format!("{:.2}", self.settings.correlation_threshold),
                    16 => format!("{:.2}", self.settings.pattern_threshold),
                    17 => format!("{:.2}", self.settings.semantic_min_confidence),
                    18 => format!("{:.3}", self.settings.anomaly_contamination),
                    19 => self.settings.anomaly_n_estimators.to_string(),
                    20 => self.settings.default_sql_limit.to_string(),
                    _ => String::new(),
                };
                self.show_numeric_popup = true;
            }
            _ => {}
        }
    }

    pub fn confirm_numeric_input(&mut self) {
        let val = self.numeric_input.parse::<f64>().unwrap_or(0.0);
        match self.editing_setting_idx {
            7 => self.settings.sample_size = (val as usize).clamp(100, 1000000),
            8 => self.settings.rounding_precision = (val as usize).clamp(0, 10),
            9 => self.settings.missing_threshold = val.clamp(0.0, 1.0),
            10 => self.settings.outlier_threshold = val.clamp(0.0, 1.0),
            11 => self.settings.constant_threshold = val.clamp(0.0, 1.0),
            12 => self.settings.duplicate_threshold = val.clamp(0.0, 1.0),
            13 => self.settings.imbalance_threshold = val.clamp(0.0, 1.0),
            14 => self.settings.skewness_threshold = val.clamp(0.0, 10.0),
            15 => self.settings.correlation_threshold = val.clamp(0.0, 1.0),
            16 => self.settings.pattern_threshold = val.clamp(0.0, 1.0),
            17 => self.settings.semantic_min_confidence = val.clamp(0.0, 1.0),
            18 => self.settings.anomaly_contamination = val.clamp(0.0, 0.5),
            19 => self.settings.anomaly_n_estimators = (val as usize).clamp(1, 1000),
            20 => self.settings.default_sql_limit = (val as usize).clamp(1, 1000000),
            _ => {}
        }
        self.show_numeric_popup = false;
    }

    pub fn adjust_numeric_by_step(&mut self, increase: bool) {
        let step = match self.editing_setting_idx {
            7 => 1000.0,
            8 => 1.0,
            19 => 10.0,
            20 => 500.0,
            18 => 0.005,
            _ => 0.05,
        };
        
        let current = self.numeric_input.parse::<f64>().unwrap_or(0.0);
        let next = if increase { current + step } else { current - step };
        
        // Format based on precision
        self.numeric_input = match self.editing_setting_idx {
            7 | 8 | 19 | 20 => (next as i64).to_string(),
            18 => format!("{:.3}", next),
            _ => format!("{:.2}", next),
        };
        
        // Auto-confirm to feel like a "slider"
        self.confirm_numeric_input();
        self.show_numeric_popup = true; // Keep it open
    }

    pub fn next_view(&mut self) {
        self.current_view = match self.current_view {
            View::Dashboard => View::RepairShop,
            View::RepairShop => View::TraceMonitor,
            View::TraceMonitor => View::Lineage,
            View::Lineage => View::Settings,
            View::Settings => View::Dashboard,
        };
        self.show_trace_popup = false; // Close popup on view change
        self.show_action_details = false;
        self.show_lineage_popup = false;
    }
}
