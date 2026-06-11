// Prevent console window in addition to Slint window in Windows release builds
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::collections::HashMap;

use anyhow::Result;
use i_slint_backend_winit::{EventResult, WinitWindowAccessor};
use pyo3::prelude::*;
use slint::{ComponentHandle, Model, SharedString};
use std::env;
use winit::window::ResizeDirection;
use copypasta::{ClipboardContext, ClipboardProvider};
use std::sync::Mutex;

static CLIPBOARD: Mutex<Option<ClipboardContext>> = Mutex::new(None);

slint::include_modules!();

fn main() -> Result<()> {
    pyo3::prepare_freethreaded_python();

    #[cfg(not(target_os = "macos"))]
    slint::platform::set_platform(Box::new(i_slint_backend_winit::Backend::new().unwrap()))?;

    #[cfg(target_os = "macos")]
    {
        use winit::platform::macos::WindowAttributesExtMacOS;
        let mut backend = i_slint_backend_winit::Backend::new().unwrap();
        backend.window_attributes_hook = Some(Box::new(|attr| {
            attr.with_fullsize_content_view(true)
                .with_title_hidden(true)
                .with_titlebar_transparent(true)
        }));
        slint::platform::set_platform(Box::new(backend))?;
    }

    let ui = MainWindow::new()?;
    wire_window_control(&ui);

    // Probe the adqa Python package via the bridge.ping() entry point.
    // This gives us a clean error message (instead of a raw ModuleNotFoundError)
    // when the system Python can't import adqa.
    let (version, py_info): (String, String) = match Python::with_gil(|py| {
        let m = py.import("adqa.bridge")?;
        let json: String = m.call_method0("ping")?.extract()?;
        Ok::<_, PyErr>((json, "ok".to_string()))
    }) {
        Ok((json, _)) => {
            let v = serde_json::from_str::<serde_json::Value>(&json)
                .ok()
                .and_then(|v| v.get("version").and_then(|s| s.as_str()).map(String::from))
                .unwrap_or_else(|| "dev".into());
            let py = serde_json::from_str::<serde_json::Value>(&json)
                .ok()
                .and_then(|v| v.get("python").and_then(|s| s.as_str()).map(String::from))
                .unwrap_or_default();
            (v, py)
        }
        Err(e) => {
            let msg = format!("Python bridge not available: {}. Run `pip install -e .` to install adqa.", e);
            let a = ui.global::<AdqaBridge>();
            a.set_status("error".into());
            a.set_status_message(msg.clone().into());
            eprintln!("[adqa] {}", msg);
            ("missing".into(), String::new())
        }
    };
    let sys_info = ui.global::<SystemInfoBridge>();
    sys_info.set_version(version.into());
    sys_info.set_os(SharedString::from(std::env::consts::OS));
    sys_info.set_info(format!("{} ({}) on {}", std::env::consts::ARCH, std::env::consts::FAMILY, std::env::consts::OS).into());
    sys_info.on_open_link(|url| { let _ = open::that(url.as_str()); });
    if !py_info.is_empty() {
        eprintln!("[adqa] using python: {}", py_info);
    }

    ui.global::<SettingsBridge>().on_change_language(|_lang| {});
    ui.global::<UiState>().on_change_page(|_page| {});

    wire_adqa_bridge(&ui);

    let args: Vec<String> = env::args().collect();
    if let Some(pos) = args.iter().position(|a| a == "--path") {
        if let Some(path) = args.get(pos + 1) {
            ui.global::<AdqaBridge>().set_data_path(path.clone().into());
        }
    }

    ui.show()?;
    slint::run_event_loop()?;
    ui.hide()?;
    Ok(())
}

fn wire_window_control(ui: &MainWindow) {
    use i_slint_backend_winit::winit::event::WindowEvent;
    let resize_map: HashMap<String, ResizeDirection> = HashMap::from([
        ("r".into(), ResizeDirection::East),
        ("t".into(), ResizeDirection::North),
        ("tr".into(), ResizeDirection::NorthEast),
        ("tl".into(), ResizeDirection::NorthWest),
        ("b".into(), ResizeDirection::South),
        ("br".into(), ResizeDirection::SouthEast),
        ("bl".into(), ResizeDirection::SouthWest),
        ("l".into(), ResizeDirection::West),
    ]);

    let uw = ui.as_weak();
    ui.window().on_winit_window_event(move |w, e| {
        match e {
            WindowEvent::RedrawRequested => {
                if let Some(u) = uw.upgrade() {
                    if u.get_main_window_maximized() != w.is_maximized() { u.set_main_window_maximized(w.is_maximized()); }
                    if u.get_main_window_minimized() != w.is_minimized() { u.set_main_window_minimized(w.is_minimized()); }
                }
                EventResult::Propagate
            }
            WindowEvent::CloseRequested => {
                if let Some(u) = uw.upgrade() { let _ = u.hide(); }
                EventResult::PreventDefault
            }
            _ => EventResult::Propagate,
        }
    });

    let uw = ui.as_weak();
    ui.on_main_window_resize(move |d| {
        if let Some(dir) = resize_map.get(&d.to_lowercase()) {
            if let Some(u) = uw.upgrade() { u.window().with_winit_window(|w| { let _ = w.drag_resize_window(*dir); }); }
        }
    });

    let b = ui.global::<WindowControlBridge>();
    let uw = ui.as_weak();
    b.on_start_drag(move || { if let Some(u) = uw.upgrade() { u.window().with_winit_window(|w| w.drag_window().ok()); } });
    let uw = ui.as_weak();
    b.on_close(move || { if let Some(u) = uw.upgrade() { let _ = u.hide(); } });
    let uw = ui.as_weak();
    b.on_maximize(move || { if let Some(u) = uw.upgrade() { u.window().with_winit_window(|w| w.set_maximized(!w.is_maximized())); } });
    let uw = ui.as_weak();
    b.on_minimize(move || { if let Some(u) = uw.upgrade() { u.window().with_winit_window(|w| w.set_minimized(!w.is_minimized().unwrap_or(false))); } });
}

fn wire_adqa_bridge(ui: &MainWindow) {
    let adqa = ui.global::<AdqaBridge>();

    // int setters
    {
        let w = ui.as_weak();
        adqa.on_set_llm_timeout(move |t| { if let Ok(v) = t.parse::<i32>() { if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_llm_timeout(v); } } });
    }
    {
        let w = ui.as_weak();
        adqa.on_set_llm_max_input_chars(move |t| { if let Ok(v) = t.parse::<i32>() { if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_llm_max_input_chars(v); } } });
    }
    {
        let w = ui.as_weak();
        adqa.on_set_sample_size(move |t| { if let Ok(v) = t.parse::<i32>() { if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_sample_size(v); } } });
    }
    {
        let w = ui.as_weak();
        adqa.on_set_rounding_precision(move |t| { if let Ok(v) = t.parse::<i32>() { if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_rounding_precision(v); } } });
    }

    // Threshold setters (all f32)
    macro_rules! wthresh { ($on:ident, $set:ident) => { { let w = ui.as_weak(); adqa.$on(move |t| { if let Ok(v) = t.parse::<f32>() { if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().$set(v); } } }); } } }
    wthresh!(on_set_missing_threshold, set_missing_threshold);
    wthresh!(on_set_outlier_threshold, set_outlier_threshold);
    wthresh!(on_set_constant_threshold, set_constant_threshold);
    wthresh!(on_set_duplicate_threshold, set_duplicate_threshold);
    wthresh!(on_set_imbalance_threshold, set_imbalance_threshold);
    wthresh!(on_set_skewness_threshold, set_skewness_threshold);
    wthresh!(on_set_correlation_threshold, set_correlation_threshold);
    wthresh!(on_set_pattern_threshold, set_pattern_threshold);

    // run-analysis
    {
        let w = ui.as_weak();
        adqa.on_run_analysis(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() {
                let a = u.global::<AdqaBridge>();
                a.set_status("running".into());
                a.set_status_message("Running analysis...".into());
                a.set_progress(0.0);
                let cfg = snapshot_config(&u);
                std::thread::spawn(move || { run_analysis_python(cfg, w); });
            }
        });
    }

    // run-explain
    {
        let w = ui.as_weak();
        adqa.on_run_explain(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_status_message("Explain: analysing...".into()); }
            std::thread::spawn(move || { explain_python(w); });
        });
    }

    // run-llm-explain
    {
        let w = ui.as_weak();
        adqa.on_run_llm_explain(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() {
                let a = u.global::<AdqaBridge>();
                a.set_status_message("Generating LLM explanation...".into());
                let api_key = a.get_llm_api_key().trim().to_string();
                let api_base = a.get_llm_api_base().trim().to_string();
                let provider = a.get_llm_provider().trim().to_string();
                let model = a.get_llm_model().trim().to_string();
                let api_key = if api_key.is_empty() { None } else { Some(api_key) };
                let api_base = if api_base.is_empty() { None } else { Some(api_base) };
                let provider = if provider.is_empty() { None } else { Some(provider) };
                let model = if model.is_empty() { None } else { Some(model) };
                std::thread::spawn(move || { llm_explain_python(w, api_key, api_base, provider, model); });
            }
        });
    }

    // run-remediation
    {
        let w = ui.as_weak();
        adqa.on_run_remediation(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() { u.global::<AdqaBridge>().set_status_message("Remediation: generating...".into()); }
            std::thread::spawn(move || { remediation_python(w); });
        });
    }

    // run-heal  (auto-saves to <data_path>_healed.csv)
    {
        let w = ui.as_weak();
        adqa.on_run_heal(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() {
                let a = u.global::<AdqaBridge>();
                a.set_status_message("Healing data...".into());
                let api_key = a.get_llm_api_key().trim().to_string();
                let api_base = a.get_llm_api_base().trim().to_string();
                let provider = a.get_llm_provider().trim().to_string();
                let model = a.get_llm_model().trim().to_string();
                let api_key = if api_key.is_empty() { None } else { Some(api_key) };
                let api_base = if api_base.is_empty() { None } else { Some(api_base) };
                let provider = if provider.is_empty() { None } else { Some(provider) };
                let model = if model.is_empty() { None } else { Some(model) };
                std::thread::spawn(move || {
                    let res: PyResult<String> = Python::with_gil(|py| {
                        py.import("adqa.bridge")?.call_method1("run_heal", (api_key, api_base, provider, model))?.extract()
                    });
                    match res {
                        Ok(json) => {
                            let _ = slint::invoke_from_event_loop(move || {
                                if let Some(u) = w.upgrade() {
                                    let a = u.global::<AdqaBridge>();
                                    let v: serde_json::Value = serde_json::from_str(&json).unwrap_or_default();
                                    if let Some(p) = v.get("preview").and_then(|x| x.as_str()) {
                                        a.set_result_healed_preview(p.into());
                                    }
                                    let out_path = {
    let dp = a.get_data_path();
    let stem = dp.strip_suffix(".csv").unwrap_or(&dp);
    format!("{}_healed.csv", stem)
};
                                    a.set_result_healed_path(out_path.clone().into());
                                    // Auto-save the healed data to the computed path
                                    a.set_status_message("Saving healed data...".into());
                                    let wi2 = u.as_weak();
                                    let w2 = w.clone();
                                    std::thread::spawn(move || {
                                        let res2: PyResult<String> = Python::with_gil(|py| {
                                            py.import("adqa.bridge")?.call_method1("save_healed", (out_path,))?.extract()
                                        });
                                        match res2 {
                                            Ok(json2) => {
                                                let _ = slint::invoke_from_event_loop(move || {
                                                    if let Some(u2) = wi2.upgrade() {
                                                        let a2 = u2.global::<AdqaBridge>();
                                                        if let Ok(v2) = serde_json::from_str::<serde_json::Value>(&json2) {
                                                            if v2.get("ok").and_then(|x| x.as_bool()).unwrap_or(false) {
                                                                a2.set_status("ok".into());
                                                                a2.set_status_message(format!("Saved {} rows to {}",
                                                                    v2.get("rows").and_then(|x| x.as_u64()).unwrap_or(0),
                                                                    a2.get_result_healed_path()).into());
                                                            } else if let Some(err) = v2.get("error").and_then(|x| x.as_str()) {
                                                                a2.set_status("error".into());
                                                                a2.set_status_message(err.into());
                                                            }
                                                        }
                                                    }
                                                });
                                            }
                                            Err(e) => update_status(w2, Err(e)),
                                        }
                                    });
                                }
                            });
                        }
                        Err(e) => update_status(w, Err(e)),
                    }
                });
            }
        });
    }


    // send-chat
    {
        let w = ui.as_weak();
        adqa.on_send_chat(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() {
                let a = u.global::<AdqaBridge>();
                let input = a.get_chat_input().to_string();
                if input.trim().is_empty() { return; }
                // Credentials
                let api_key = a.get_llm_api_key().trim().to_string();
                let api_base = a.get_llm_api_base().trim().to_string();
                let provider = a.get_llm_provider().trim().to_string();
                let model = a.get_llm_model().trim().to_string();
                let api_key = if api_key.is_empty() { None } else { Some(api_key) };
                let api_base = if api_base.is_empty() { None } else { Some(api_base) };
                let provider = if provider.is_empty() { None } else { Some(provider) };
                let model = if model.is_empty() { None } else { Some(model) };
                // Push user message
                {
                    let msgs = a.get_chat_messages();
                    let vec_model = slint::VecModel::default();
                    for msg in msgs.iter() { vec_model.push(msg); }
                    vec_model.push(ChatMessage { text: input.clone().into(), is_user: true });
                    a.set_chat_messages(std::rc::Rc::new(vec_model).into());
                }
                a.set_chat_output("".into());
                a.set_chat_input("".into());
                a.set_status_message("Chat: thinking...".into());
                std::thread::spawn(move || {
                    let res: PyResult<String> = Python::with_gil(|py| {
                        py.import("adqa.bridge")?.call_method1("run_chat", (input, api_key, api_base, provider, model))?.extract()
                    });
                    match res {
                        Ok(reply) => {
                            let _ = slint::invoke_from_event_loop(move || {
                                if let Some(u) = w.upgrade() {
                                    let a = u.global::<AdqaBridge>();
                                    let msgs = a.get_chat_messages();
                                    let vec_model = slint::VecModel::default();
                                    for msg in msgs.iter() { vec_model.push(msg); }
                                    vec_model.push(ChatMessage { text: reply.clone().into(), is_user: false });
                                    a.set_chat_messages(std::rc::Rc::new(vec_model).into());
                                    a.set_chat_output(reply.into());
                                    a.set_status_message("Chat: replied.".into());
                                }
                            });
                        }
                        Err(e) => update_status(w, Err(e)),
                    }
                });
            }
        });
    }

    // reset-chat-session
    {
        adqa.on_reset_chat_session(move || {
            Python::with_gil(|py| {
                if let Ok(m) = py.import("adqa.bridge") {
                    let _: Result<String, _> = m.call_method0("reset_chat_session").and_then(|r| r.extract());
                }
            });
        });
    }

    // upload-data
    {
        let w = ui.as_weak();
        adqa.on_upload_data(move || {
            let w = w.clone();
            if let Some(u) = w.upgrade() {
                // Always open a native file picker. The current path (if any)
                // is used as the starting directory + suggested filename so
                // the user can either re-confirm the same file or browse to
                // a different one.
                let current = u.global::<AdqaBridge>().get_data_path().to_string();
                let mut dialog = rfd::FileDialog::new()
                    .set_title("Select data file")
                    .add_filter(
                        "Data files",
                        &["csv", "parquet", "pq", "xls", "xlsx", "json", "db", "sqlite"],
                    )
                    .add_filter("All files", &["*"]);
                if !current.trim().is_empty() {
                    let p = std::path::Path::new(current.trim());
                    if p.is_dir() {
                        dialog = dialog.set_directory(p);
                    } else if let Some(parent) = p.parent() {
                        if !parent.as_os_str().is_empty() {
                            dialog = dialog.set_directory(parent);
                        }
                        if let Some(name) = p.file_name() {
                            dialog = dialog.set_file_name(name.to_string_lossy().as_ref());
                        }
                    }
                }
                let path = match dialog.pick_file() {
                    Some(picked) => picked.to_string_lossy().to_string(),
                    None => return, // user cancelled the dialog
                };
                u.global::<AdqaBridge>().set_data_path(path.clone().into());
                std::thread::spawn(move || {
                    let res: PyResult<String> = Python::with_gil(|py| { py.import("adqa.bridge")?.call_method1("preview_data", (path,))?.extract() });
                    match res {
                        Ok(json) => {
                            let _ = slint::invoke_from_event_loop(move || {
                                if let Some(u) = w.upgrade() {
                                    let a = u.global::<AdqaBridge>();
                                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&json) {
                                        if let Some(err) = v.get("error").and_then(|e| e.as_str()) {
                                            a.set_status("error".into());
                                            a.set_status_message(err.into());
                                        } else {
                                            let rows = v.get("rows").and_then(|r| r.as_u64()).unwrap_or(0);
                                            let cols = v.get("cols").and_then(|c| c.as_u64()).unwrap_or(0);
                                            let columns: Vec<String> = v.get("columns")
                                                .and_then(|c| c.as_array())
                                                .map(|arr| arr.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                                                .unwrap_or_default();
                                            let head = v.get("head").and_then(|h| h.as_str()).unwrap_or("");
                                            let resolved = v.get("resolved_path").and_then(|s| s.as_str()).unwrap_or("");
                                            let stats = if resolved.is_empty() {
                                                format!("{} rows × {} cols  •  {} columns", rows, cols, columns.len())
                                            } else {
                                                format!("{} rows × {} cols  •  {} columns  •  {}", rows, cols, columns.len(), resolved)
                                            };
                                            a.set_data_stats(stats.into());
                                            a.set_data_preview(head.into());
                                            if let Some(schema_str) = v.get("schema").and_then(|s| s.as_str()) {
                                                a.set_data_schema(schema_str.into());
                                            }
                                            a.set_status_message("Data loaded.".into());
                                        }
                                    } else {
                                        a.set_data_preview(json.into());
                                        a.set_status_message("Preview loaded.".into());
                                    }
                                }
                            });
                        }
                        Err(e) => update_status(w, Err(e)),
                    }
                });
            }
        });
    }

    adqa.on_refresh_providers(|| {});

    // copy-to-clipboard
    adqa.on_copy_to_clipboard(|text| {
        let t = text.to_string();
        let mut guard = CLIPBOARD.lock().unwrap();
        if guard.is_none() {
            *guard = ClipboardContext::new().ok();
        }
        if let Some(ref mut ctx) = *guard {
            let _ = ctx.set_contents(t);
        }
    });

    // apply-llm-credentials
    adqa.on_apply_llm_credentials(|api_key, api_base| {
        std::env::set_var("OPENAI_API_KEY", api_key.as_str());
        std::env::set_var("OPENAI_API_BASE", api_base.as_str());
    });

    // calculate-cost
    {
        let w = ui.as_weak();
        adqa.on_calculate_cost(move || {
            if let Some(u) = w.upgrade() {
                let a = u.global::<AdqaBridge>();
                let provider = a.get_llm_provider().trim().to_string();
                let model_str = a.get_llm_model().trim().to_string();
                let flex = a.get_llm_flex();
                let provider = if provider.is_empty() { None } else { Some(provider) };
                let model_str = if model_str.is_empty() { None } else { Some(model_str) };
                let wi = u.as_weak();
                std::thread::spawn(move || {
                    let res: PyResult<String> = Python::with_gil(|py| {
                        py.import("adqa.bridge")?.call_method1("get_cost_info", (provider, model_str, flex))?.extract()
                    });
                    if let Ok(cost) = res {
                        let _ = slint::invoke_from_event_loop(move || {
                            if let Some(u2) = wi.upgrade() {
                                u2.global::<AdqaBridge>().set_cost_info(cost.into());
                            }
                        });
                    }
                });
            }
        });
    }
    
}

// ── Python call helpers ──────────────────────────────────────────────

fn snapshot_config(ui: &MainWindow) -> pyo3::Py<pyo3::types::PyDict> {
    Python::with_gil(|py| {
        let a = ui.global::<AdqaBridge>();
        let cfg = pyo3::types::PyDict::new(py);
        let _ = cfg.set_item("data_path", a.get_data_path().to_string());
        let _ = cfg.set_item("mode", "advisory");
        let _ = cfg.set_item("output_path", a.get_output_path().to_string());
        let _ = cfg.set_item("tracing_enabled", a.get_tracing_enabled());
        let _ = cfg.set_item("lineage_enabled", a.get_lineage_enabled());
        let _ = cfg.set_item("ml_enabled", a.get_ml_enabled());
        let _ = cfg.set_item("stop_on_block", false);
        let llm = pyo3::types::PyDict::new(py);
        let _ = llm.set_item("enabled", a.get_llm_enabled());
        let _ = llm.set_item("provider", a.get_llm_provider().to_string());
        let _ = llm.set_item("model", a.get_llm_model().to_string());
        let _ = llm.set_item("api_key", a.get_llm_api_key().to_string());
        let _ = llm.set_item("api_base", a.get_llm_api_base().to_string());

        let _ = llm.set_item("timeout_seconds", a.get_llm_timeout());
        let _ = llm.set_item("max_input_chars", a.get_llm_max_input_chars());
        let _ = llm.set_item("redact_samples", a.get_llm_redact());
        let _ = cfg.set_item("llm", llm);
        let profiling = pyo3::types::PyDict::new(py);
        let _ = profiling.set_item("sample_size", a.get_sample_size());
        let _ = profiling.set_item("rounding_precision", a.get_rounding_precision());
        let _ = cfg.set_item("profiling", profiling);
        let thresholds = pyo3::types::PyDict::new(py);
        let _ = thresholds.set_item("missing", a.get_missing_threshold());
        let _ = thresholds.set_item("outlier", a.get_outlier_threshold());
        let _ = thresholds.set_item("constant", a.get_constant_threshold());
        let _ = thresholds.set_item("duplicate", a.get_duplicate_threshold());
        let _ = thresholds.set_item("imbalance", a.get_imbalance_threshold());
        let _ = thresholds.set_item("skewness", a.get_skewness_threshold());
        let _ = thresholds.set_item("correlation", a.get_correlation_threshold());
        let _ = thresholds.set_item("pattern", a.get_pattern_threshold());
        let _ = cfg.set_item("thresholds", thresholds);
        cfg.into()
    })
}

fn run_analysis_python(cfg: pyo3::Py<pyo3::types::PyDict>, ui: slint::Weak<MainWindow>) {
    let res: PyResult<String> = Python::with_gil(|py| { py.import("adqa.bridge")?.call_method1("run_analysis", (cfg.bind(py),))?.extract() });
    match res {
        Ok(json) => {
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(u) = ui.upgrade() {
                    let a = u.global::<AdqaBridge>();
                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&json) {
                        a.set_result_summary(serde_json::to_string_pretty(&v).unwrap_or(json).into());
                        if let Some(d) = v.get("decision") {
                            a.set_result_advisory(format!("Decision: {} (score: {})", d.get("decision").and_then(|s| s.as_str()).unwrap_or("?"), d.get("score").and_then(|s| s.as_f64()).unwrap_or(0.0)).into());
                        }
                        if let Some(e) = v.get("explanation") {
                            a.set_result_explain(format!("{} | {} | Next: {}", e.get("short_summary").and_then(|s| s.as_str()).unwrap_or(""), e.get("top_issues").and_then(|s| s.as_str()).unwrap_or(""), e.get("next_steps").and_then(|s| s.as_str()).unwrap_or("")).into());
                        }
                        if let Some(d) = v.get("dataframe") {
                            a.set_data_stats(format!("{} rows x {} cols", d.get("rows").and_then(|r| r.as_u64()).unwrap_or(0), d.get("cols").and_then(|c| c.as_u64()).unwrap_or(0)).into());
                        }
                        if let Some(det) = v.get("detections").and_then(|d| d.get("rule_count")) { a.set_cost_info(format!("{} issues found", det).into()); }
                    }
                    a.set_status("done".into());
                    a.set_status_message("Analysis complete.".into());
                    a.set_progress(1.0);
                }
            });
        }
        Err(e) => update_status(ui, Err(e)),
    }
}

fn explain_python(ui: slint::Weak<MainWindow>) {
    let res: PyResult<String> = Python::with_gil(|py| { py.import("adqa.bridge")?.call_method0("run_explain")?.extract() });
    match res {
        Ok(json) => {
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(u) = ui.upgrade() {
                    u.global::<AdqaBridge>().set_result_explain(format!("Root causes:\n{}", json).into());
                    u.global::<AdqaBridge>().set_status_message("Explain: root causes ready.".into());
                }
            });
        }
        Err(e) => update_status(ui, Err(e)),
    }
}

fn llm_explain_python(ui: slint::Weak<MainWindow>, api_key: Option<String>, api_base: Option<String>, provider: Option<String>, model: Option<String>) {
    let res: PyResult<String> = Python::with_gil(|py| { py.import("adqa.bridge")?.call_method1("run_llm_explain", (api_key, api_base, provider, model))?.extract() });
    match res {
        Ok(text) => {
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(u) = ui.upgrade() {
                    u.global::<AdqaBridge>().set_result_llm_explain(text.into());
                    u.global::<AdqaBridge>().set_status_message("LLM explanation ready.".into());
                }
            });
        }
        Err(e) => update_status(ui, Err(e)),
    }
}

fn remediation_python(ui: slint::Weak<MainWindow>) {
    let res: PyResult<String> = Python::with_gil(|py| { py.import("adqa.bridge")?.call_method0("run_remediation")?.extract() });
    match res {
        Ok(json) => {
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(u) = ui.upgrade() {
                    u.global::<AdqaBridge>().set_result_remediation(format!("Proposals:\n{}", json).into());
                    u.global::<AdqaBridge>().set_status_message("Remediation: proposals ready.".into());
                }
            });
        }
        Err(e) => update_status(ui, Err(e)),
    }
}

fn update_status(ui: slint::Weak<MainWindow>, result: PyResult<String>) {
    let msg = match result {
        Ok(json) => {
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&json) {
                {
                if let Some(err_str) = v.get("error").and_then(|e| e.as_str()) {
                    err_str.to_string()
                } else {
                    return;
                }
            }
            } else { return; }
        }
        Err(e) => e.to_string(),
    };
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(u) = ui.upgrade() {
            let a = u.global::<AdqaBridge>();
            a.set_status("error".into());
            a.set_status_message(msg.into());
        }
    });
}
