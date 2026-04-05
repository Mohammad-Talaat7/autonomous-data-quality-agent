use ratatui::{
    layout::{Constraint, Direction, Layout, Margin, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Scrollbar, ScrollbarOrientation, ScrollbarState, Table, TableState, Row, Cell, Wrap, Clear, Gauge, Sparkline, ListState},
    Frame,
};

use crate::app::{App, View, VisibleItem};

pub fn render(f: &mut Frame, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Header
            Constraint::Min(0),    // Content
            Constraint::Length(3), // Footer
        ])
        .split(f.area());

    // 1. Header
    let header = Paragraph::new(Line::from(vec![
        Span::styled(" ADQA ", Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Span::raw(" Autonomous Data Quality Agent | "),
        Span::styled(app.version.clone(), Style::default().fg(Color::DarkGray)),
    ]))
    .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::Cyan)));
    f.render_widget(header, chunks[0]);

    // 2. Main Content
    let content_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Length(20), // Sidebar
            Constraint::Min(0),    // Body
        ])
        .split(chunks[1]);

    // Sidebar with Icons removed
    let sidebar_items = [
        ListItem::new(" Dashboard "),
        ListItem::new(" Repair Shop "),
        ListItem::new(" Trace Monitor "),
        ListItem::new(" Lineage "),
        ListItem::new(" Settings "),
    ];
    let selected_index = match app.current_view {
        View::Dashboard => 0,
        View::RepairShop => 1,
        View::TraceMonitor => 2,
        View::Lineage => 3,
        View::Settings => 4,
    };

    let sidebar = List::new(sidebar_items)
        .block(Block::default().borders(Borders::ALL).title(" Navigation "))
        .highlight_style(Style::default().bg(Color::DarkGray).fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .highlight_symbol(">> ");
    
    let mut sidebar_state = ListState::default();
    sidebar_state.select(Some(selected_index));
    f.render_stateful_widget(sidebar, content_chunks[0], &mut sidebar_state);

    // Body
    match app.current_view {
        View::Dashboard => {
            let body_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3), // Progress Bar
                    Constraint::Length(10), // Quality Stats + Trend
                    Constraint::Min(0),    // Detailed Status + Ticker
                ])
                .split(content_chunks[1]);

            // 1. Progress Bar
            let progress = (app.analysis_progress * 100.0) as u16;
            let gauge = Gauge::default()
                .block(Block::default().borders(Borders::ALL).title(" Analysis Progress "))
                .gauge_style(Style::default().fg(Color::Cyan).bg(Color::Black).add_modifier(Modifier::BOLD))
                .percent(progress);
            f.render_widget(gauge, body_chunks[0]);

            // 2. Stats & Trend
            let stats_chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([
                    Constraint::Percentage(40), // Score Gauge
                    Constraint::Percentage(60), // Sparkline Trend
                ])
                .split(body_chunks[1]);

            let score_val = (app.quality_score * 100.0) as u16;
            let score_color = if app.quality_score < 0.2 { Color::Green } 
                             else if app.quality_score < 0.5 { Color::Yellow } 
                             else { Color::Red };
            
            let score_gauge = Gauge::default()
                .block(Block::default().borders(Borders::ALL).title(" Global Quality Risk "))
                .gauge_style(Style::default().fg(score_color).bg(Color::Black).add_modifier(Modifier::BOLD))
                .percent(score_val)
                .label(format!("{:.1}% Risk", app.quality_score * 100.0));
            f.render_widget(score_gauge, stats_chunks[0]);

            let sparkline = Sparkline::default()
                .block(Block::default().borders(Borders::ALL).title(" Risk Trend (Last 50 Runs) "))
                .data(&app.quality_history)
                .style(Style::default().fg(Color::Yellow));
            f.render_widget(sparkline, stats_chunks[1]);

            // 3. Status/Summary & Activity Ticker
            let ticker_layout = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(6), // Summary
                    Constraint::Min(0),    // Ticker
                ])
                .split(body_chunks[2]);

            let text = if let Some(summary) = &app.analysis_summary {
                summary.clone()
            } else {
                "Ready for analysis. Use 'r' to start, 'tab' to navigate.".to_string()
            };
            
            let status_msg = if app.active_plan.is_some() {
                "\n\n[PAUSED] Human review required in Repair tab."
            } else if app.last_plan_status.is_some() {
                "\n\n[HEALED] Previous remediation plan applied."
            } else {
                ""
            };

            let status_color = if app.active_plan.is_some() { Color::Yellow } else { Color::White };

            let body = Paragraph::new(format!("{}{}", text, status_msg))
                .block(Block::default().borders(Borders::ALL).title(" System Reasoning ")
                .border_style(Style::default().fg(status_color)))
                .wrap(Wrap { trim: true });
            f.render_widget(body, ticker_layout[0]);

            // Activity Ticker (Latest 10 events)
            let ticker_layout = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([
                    Constraint::Percentage(50), // Journey
                    Constraint::Percentage(50), // Ticker
                ])
                .split(ticker_layout[1]);

            // Journey Timeline
            let journey_items: Vec<ListItem> = app.remediation_timeline.iter().map(|s| {
                let symbol = match s.status.as_str() {
                    "completed" => ("✔", Color::Green),
                    "active" => ("●", Color::Yellow),
                    "failed" => ("✘", Color::Red),
                    _ => ("○", Color::DarkGray),
                };
                ListItem::new(Line::from(vec![
                    Span::styled(format!(" {} ", symbol.0), Style::default().fg(symbol.1).add_modifier(Modifier::BOLD)),
                    Span::raw(&s.label),
                ]))
            }).collect();
            
            let journey = List::new(journey_items)
                .block(Block::default().borders(Borders::ALL).title(" Remediation Journey "));
            f.render_widget(journey, ticker_layout[0]);

            let ticker_items: Vec<ListItem> = app.logs.iter().rev().take(10).map(|e| {
                let color = match e.event_type.as_str() {
                    "error" => Color::Red,
                    "result" => Color::Green,
                    "ui" => Color::Cyan,
                    _ => Color::DarkGray,
                };
                ListItem::new(Line::from(vec![
                    Span::styled(format!("[{}] ", e.event_type.to_uppercase()), Style::default().fg(color)),
                    Span::raw(&e.name),
                ]))
            }).collect();
            
            let ticker = List::new(ticker_items)
                .block(Block::default().borders(Borders::ALL).title(" Live Activity Ticker "));
            f.render_widget(ticker, ticker_layout[1]);
        }
        View::Lineage => {
            let lineage_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3), // Search Bar
                    Constraint::Min(0),    // Table + Inspector
                ])
                .split(content_chunks[1]);

            // 1. Search Bar
            let search_style = if app.search_mode {
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::Gray)
            };

            let search_bar = Paragraph::new(Line::from(vec![
                Span::styled(" SEARCH: ", search_style),
                Span::raw(&app.lineage_search),
                if app.search_mode { Span::styled("█", Style::default().add_modifier(Modifier::SLOW_BLINK)) } else { Span::raw("") },
                Span::raw(" | "),
                Span::styled(" [/] Search | [Enter] Popup ", Style::default().fg(Color::DarkGray)),
            ]))
            .block(Block::default().borders(Borders::ALL).title(" Controls "));
            
            f.render_widget(search_bar, lineage_chunks[0]);

            let body_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Min(0),    // Table
                    Constraint::Length(8), // Inspector
                ])
                .split(lineage_chunks[1]);

            let header_cells = ["Operation", "Inputs", "Outputs"]
                .iter()
                .map(|h| Cell::from(*h).style(Style::default().fg(Color::Cyan)));
            let header = Row::new(header_cells)
                .style(Style::default().add_modifier(Modifier::BOLD))
                .height(1)
                .bottom_margin(1);

            let query = app.lineage_search.to_lowercase();
            let filtered_nodes: Vec<&crate::app::LineageNode> = app.lineage_nodes.iter()
                .filter(|n| {
                    if query.is_empty() { return true; }
                    n.operation.to_lowercase().contains(&query) || 
                    serde_json::to_string(&n.metadata).unwrap_or_default().to_lowercase().contains(&query)
                })
                .collect();

            let rows = filtered_nodes.iter().map(|n| {
                Row::new(vec![
                    Cell::from(n.operation.clone()).style(Style::default().fg(Color::Yellow)),
                    Cell::from(serde_json::to_string(&n.inputs).unwrap_or_default()),
                    Cell::from(serde_json::to_string(&n.outputs).unwrap_or_default()),
                ])
            });

            let table = Table::new(rows, [
                Constraint::Length(20),
                Constraint::Percentage(40),
                Constraint::Percentage(40),
            ])
            .header(header)
            .row_highlight_style(Style::default().bg(Color::DarkGray).fg(Color::Yellow).add_modifier(Modifier::BOLD))
            .highlight_symbol(">> ")
            .block(Block::default().borders(Borders::ALL).title(" Data Lineage Flow "));

            let mut table_state = TableState::default();
            table_state.select(Some(app.lineage_selected_index));
            f.render_stateful_widget(table, body_chunks[0], &mut table_state);

            let inspector_text = if !filtered_nodes.is_empty() {
                let node = filtered_nodes[app.lineage_selected_index.min(filtered_nodes.len().saturating_sub(1))];
                format!(
                    "Operation: {}\nTimestamp: {}\nMetadata: {}",
                    node.operation, node.timestamp, serde_json::to_string_pretty(&node.metadata).unwrap_or_default()
                )
            } else {
                "No lineage data available. Run analysis to track data flow.".to_string()
            };

            let inspector = Paragraph::new(inspector_text)
                .block(Block::default().borders(Borders::ALL).title(" Node Details (Enter for full popup) "))
                .wrap(Wrap { trim: true });
            f.render_widget(inspector, body_chunks[1]);

            if app.show_lineage_popup && !filtered_nodes.is_empty() {
                let node = filtered_nodes[app.lineage_selected_index.min(filtered_nodes.len().saturating_sub(1))];
                let popup_area = centered_rect(80, 80, f.area());
                f.render_widget(Clear, popup_area);
                
                let details = format!(
                    "Operation: {}\nTimestamp: {}\n\nInputs:\n{}\n\nOutputs:\n{}\n\nMetadata:\n{}",
                    node.operation,
                    node.timestamp,
                    serde_json::to_string_pretty(&node.inputs).unwrap_or_default(),
                    serde_json::to_string_pretty(&node.outputs).unwrap_or_default(),
                    serde_json::to_string_pretty(&node.metadata).unwrap_or_default()
                );
                
                let popup_block = Block::default()
                    .title(format!(" Lineage Node: {} ", node.operation))
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(Color::Yellow));
                
                let details_para = Paragraph::new(details)
                    .block(popup_block)
                    .scroll((app.popup_scroll as u16, 0))
                    .wrap(Wrap { trim: false });
                f.render_widget(details_para, popup_area);
            }
        }
        View::TraceMonitor => {
            let trace_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3), // Search/Filter Bar
                    Constraint::Min(0),    // Table + Inspector
                ])
                .split(content_chunks[1]);

            // 1. Search & Filter Bar
            let filter_text = app.filter_type.as_deref().unwrap_or("ALL");
            let sort_text = match app.sort_order {
                crate::app::SortOrder::NewestFirst => "NEWEST",
                crate::app::SortOrder::OldestFirst => "OLDEST",
            };
            
            let search_style = if app.search_mode {
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::Gray)
            };

            let search_bar = Paragraph::new(Line::from(vec![
                Span::styled(" SEARCH: ", search_style),
                Span::raw(&app.search_query),
                if app.search_mode { Span::styled("█", Style::default().add_modifier(Modifier::SLOW_BLINK)) } else { Span::raw("") },
                Span::raw(" | "),
                Span::styled(" FILTER: ", Style::default().fg(Color::Cyan)),
                Span::raw(format!("{:<10}", filter_text)),
                Span::raw(" | "),
                Span::styled(" SORT: ", Style::default().fg(Color::Cyan)),
                Span::raw(format!("{:<10}", sort_text)),
                Span::raw(" | "),
                Span::styled(" [f] Filter | [s] Sort | [/] Search ", Style::default().fg(Color::DarkGray)),
            ]))
            .block(Block::default().borders(Borders::ALL).title(" Controls "));
            
            f.render_widget(search_bar, trace_chunks[0]);

            let body_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Percentage(70), // Table
                    Constraint::Percentage(30), // Metadata Inspector (Compact)
                ])
                .split(trace_chunks[1]);

            let height = body_chunks[0].height as usize - 3;
            
            let header_cells = ["Time", "Type", "Event"]
                .iter()
                .map(|h| Cell::from(*h).style(Style::default().fg(Color::Cyan)));
            let header = Row::new(header_cells)
                .style(Style::default().add_modifier(Modifier::BOLD))
                .height(1)
                .bottom_margin(1);

            let rows = app.visible_items.iter().map(|item| {
                match item {
                    VisibleItem::Single(idx) | VisibleItem::GroupMember(idx) => {
                        let idx = *idx;
                        let event = &app.logs[idx];
                        let time = if event.timestamp.len() > 19 {
                            &event.timestamp[11..19]
                        } else {
                            &event.timestamp
                        };
                        
                        let type_color = match event.event_type.as_str() {
                            "start" => Color::Green,
                            "error" => Color::Red,
                            "data_ingress" => Color::Blue,
                            "profiling" => Color::Magenta,
                            "privacy" => Color::Yellow,
                            "bias" => Color::LightRed,
                            _ => Color::White,
                        };

                        let mut name = event.name.clone();
                        let mut status_prefix = "";

                        // Check for .success pairing
                        if idx + 1 < app.logs.len() {
                            let next = &app.logs[idx + 1];
                            if (next.name == format!("{}.success", event.name) || next.name == format!("{}.failure", event.name)) 
                                && next.parent_event_id == event.event_id 
                            {
                                if next.name.ends_with(".success") {
                                    status_prefix = "✔ ";
                                } else {
                                    status_prefix = "✘ ";
                                }
                            }
                        }

                        if event.parent_event_id.is_some() || matches!(item, VisibleItem::GroupMember(_)) {
                            name = format!("  ↳ {}", name);
                        }
                        
                        let final_name = format!("{}{}", status_prefix, name);

                        Row::new(vec![
                            Cell::from(time.to_string()),
                            Cell::from(event.event_type.clone()).style(Style::default().fg(type_color)),
                            Cell::from(final_name),
                        ])
                    },
                    VisibleItem::GroupHeader { name, indices, expanded } => {
                        let first_idx = indices[0];
                        let event = &app.logs[first_idx];
                        let time = if event.timestamp.len() > 19 {
                            &event.timestamp[11..19]
                        } else {
                            &event.timestamp
                        };
                        
                        let icon = if *expanded { "▼" } else { "▶" };
                        let event_count = indices.iter().filter(|&&idx| !app.logs[idx].name.contains(".")).count();

                        Row::new(vec![
                            Cell::from(time.to_string()),
                            Cell::from("group".to_string()).style(Style::default().fg(Color::Cyan)),
                            Cell::from(format!("{} [Group] {} ({} events)", icon, name, event_count)).style(Style::default().fg(Color::Yellow)),
                        ])
                    }
                }
            });

            let table = Table::new(rows, [
                Constraint::Length(10),
                Constraint::Length(15),
                Constraint::Min(30),
            ])
            .header(header)
            .row_highlight_style(Style::default().bg(Color::DarkGray).fg(Color::Yellow).add_modifier(Modifier::BOLD))
            .highlight_symbol(">> ")
            .block(Block::default().borders(Borders::ALL).title(" Trace Events "));

            let mut table_state = TableState::default();
            table_state.select(Some(app.selected_index));

            f.render_stateful_widget(table, body_chunks[0], &mut table_state);

            let inspector_text = if !app.visible_items.is_empty() {
                match &app.visible_items[app.selected_index] {
                    VisibleItem::Single(idx) | VisibleItem::GroupMember(idx) => {
                        let event = &app.logs[*idx];
                        format!("Event: {}\nType: {}\nMetadata: {}", event.name, event.event_type, serde_json::to_string(&event.metadata).unwrap_or_default())
                    },
                    VisibleItem::GroupHeader { name, indices, .. } => {
                        format!("Group: {}\nEvents: {}\n(Press Enter to expand/collapse)", name, indices.len())
                    }
                }
            } else {
                "No metadata to display.".to_string()
            };

            let inspector = Paragraph::new(inspector_text)
                .block(Block::default().borders(Borders::ALL).title(" Quick Info (Enter for full details) "))
                .wrap(Wrap { trim: true });
            f.render_widget(inspector, body_chunks[1]);

            let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight);
            let mut scrollbar_state = ScrollbarState::new(app.visible_items.len().saturating_sub(height))
                .position(app.selected_index);
            f.render_stateful_widget(
                scrollbar,
                body_chunks[0].inner(Margin { vertical: 1, horizontal: 0 }),
                &mut scrollbar_state,
            );

            // RENDER POPUP
            if app.show_trace_popup && !app.visible_items.is_empty() {
                let popup_area = centered_rect(80, 80, f.area());
                f.render_widget(Clear, popup_area); // Clear background

                match &app.visible_items[app.selected_index] {
                    VisibleItem::Single(idx) | VisibleItem::GroupMember(idx) => {
                        let event = &app.logs[*idx];
                        let details = serde_json::to_string_pretty(&event.metadata).unwrap_or_default();
                        let popup_block = Block::default()
                            .title(format!(" Trace Details: {} ", event.name))
                            .borders(Borders::ALL)
                            .border_style(Style::default().fg(Color::Yellow));
                        
                        let details_para = Paragraph::new(format!("Timestamp: {}\nType: {}\n\nMetadata:\n{}", event.timestamp, event.event_type, details))
                            .block(popup_block)
                            .scroll((app.popup_scroll as u16, 0))
                            .wrap(Wrap { trim: false });
                        
                        f.render_widget(details_para, popup_area);
                    },
                    _ => {} // Headers don't have popups, they expand
                }
            }
        }
        View::RepairShop => {
            let plan_to_show = if let Some(plan) = &app.active_plan {
                Some((plan, " PENDING APPROVAL ", Color::Yellow))
            } else if let Some(plan) = &app.last_plan {
                let status = app.last_plan_status.as_deref().unwrap_or(" EXECUTED ");
                Some((plan, status, Color::Green))
            } else {
                None
            };

            // Show table if we have a plan OR if we have history
            if plan_to_show.is_some() || !app.all_executed_actions.is_empty() {
                let chunks = Layout::default()
                    .direction(Direction::Vertical)
                    .constraints([
                        Constraint::Length(3), // Summary
                        Constraint::Min(0),    // Table
                        Constraint::Length(3), // Prompt
                    ])
                    .split(content_chunks[1]);

                let summary_text = if let Some((plan, status_text, _)) = &plan_to_show {
                    format!("{}: {}", status_text.trim(), plan.summary)
                } else {
                    format!("Session History: {} fixes applied.", app.all_executed_actions.len())
                };
                
                let status_color = plan_to_show.as_ref().map(|(_, _, c)| *c).unwrap_or(Color::Green);
                let status_title = plan_to_show.as_ref().map(|(_, s, _)| *s).unwrap_or(" HISTORY ");

                let summary = Paragraph::new(summary_text)
                    .block(Block::default().borders(Borders::ALL).title(Span::styled(status_title, Style::default().fg(status_color).add_modifier(Modifier::BOLD))));
                f.render_widget(summary, chunks[0]);

                let table_chunks = Layout::default()
                    .direction(Direction::Horizontal)
                    .constraints([
                        Constraint::Percentage(60), // Actions Table
                        Constraint::Percentage(40), // Deltas Table
                    ])
                    .split(chunks[1]);

                let mut all_rows = Vec::new();
                
                // 1. Show history first
                for action in &app.all_executed_actions {
                    all_rows.push(Row::new(vec![
                        Cell::from("[DONE]").style(Style::default().fg(Color::Green)),
                        Cell::from(action.action_type.clone()).style(Style::default().fg(Color::Green)),
                        Cell::from(action.reason.clone()),
                    ]));
                }

                // 2. Show current active plan or last proposed plan
                let empty_vec = Vec::new();
                let current_actions: &[crate::app::Action] = if let Some((plan, _, _)) = &plan_to_show {
                    &plan.actions
                } else {
                    &empty_vec
                };

                for action in current_actions {
                    let is_active = app.active_plan.is_some();
                    let style = if is_active {
                        if action.selected { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::DarkGray) }
                    } else {
                        Style::default().fg(Color::Gray)
                    };
                    
                    let status = if is_active {
                        if action.selected { "[X]" } else { "[ ]" }
                    } else {
                        "[PROP]"
                    };

                    all_rows.push(Row::new(vec![
                        Cell::from(status).style(style),
                        Cell::from(action.action_type.clone()).style(style),
                        Cell::from(action.reason.clone()),
                    ]));
                }

                let table = Table::new(all_rows, [
                    Constraint::Length(8),
                    Constraint::Length(12),
                    Constraint::Min(20),
                ])
                .header(Row::new(vec!["Status", "Action", "Reason"]).style(Style::default().fg(Color::Cyan)))
                .row_highlight_style(Style::default().bg(Color::DarkGray))
                .block(Block::default().borders(Borders::ALL).title(" Fix History (Session) "));

                let mut state = TableState::default();
                state.select(Some(app.plan_selected_row));
                f.render_stateful_widget(table, table_chunks[0], &mut state);

                // DELTAS TABLE
                let delta_rows: Vec<Row> = app.metric_deltas.iter().map(|d| {
                    Row::new(vec![
                        Cell::from(d.column.clone()).style(Style::default().fg(Color::Yellow)),
                        Cell::from(d.metric.clone()),
                        Cell::from(d.before.clone()).style(Style::default().fg(Color::Red)),
                        Cell::from(format!("→ {}", d.after)).style(Style::default().fg(Color::Green)),
                    ])
                }).collect();

                let deltas_table = Table::new(delta_rows, [
                    Constraint::Percentage(30),
                    Constraint::Percentage(30),
                    Constraint::Percentage(20),
                    Constraint::Percentage(20),
                ])
                .header(Row::new(vec!["Column", "Metric", "Before", "After"]).style(Style::default().fg(Color::Cyan)))
                .block(Block::default().borders(Borders::ALL).title(" Before & After Metrics "));
                
                f.render_widget(deltas_table, table_chunks[1]);

                let prompt_text = if app.active_plan.is_some() {
                    " [Space] Toggle Action | [Enter] View Details | [a] APPROVE "
                } else {
                    " Fixes applied. Press 'r' to re-analyze the healed data. "
                };

                let prompt = Paragraph::new(prompt_text)
                    .block(Block::default().borders(Borders::ALL).style(Style::default().fg(status_color).add_modifier(Modifier::BOLD)));
                f.render_widget(prompt, chunks[2]);

                // RENDER ACTION DETAILS POPUP
                if app.show_action_details {
                    let history_len = app.all_executed_actions.len();
                    let maybe_action = if app.plan_selected_row < history_len {
                        app.all_executed_actions.get(app.plan_selected_row)
                    } else if let Some((plan, _, _)) = &plan_to_show {
                        plan.actions.get(app.plan_selected_row - history_len)
                    } else {
                        None
                    };

                    if let Some(action) = maybe_action {
                        let popup_area = centered_rect(60, 40, f.area());
                        f.render_widget(Clear, popup_area);

                        let details = serde_json::to_string_pretty(&action.metadata).unwrap_or_default();
                        let popup_block = Block::default()
                            .title(format!(" Action Details: {} ", action.action_type))
                            .borders(Borders::ALL)
                            .border_style(Style::default().fg(Color::Yellow));

                        let details_para = Paragraph::new(format!(
                            "Reason: {}\nRequires Approval: {}\n\nMetadata:\n{}",
                            action.reason, action.requires_approval, details
                        ))
                        .block(popup_block)
                        .scroll((app.popup_scroll as u16, 0))
                        .wrap(Wrap { trim: false });

                        f.render_widget(details_para, popup_area);
                    }
                }

            } else {
                let body = Paragraph::new("No remediation history. Run analysis in HUMAN mode to propose fixes.")
                    .block(Block::default().borders(Borders::ALL).title(" Repair Shop "));
                f.render_widget(body, content_chunks[1]);
            }
        }
        View::Settings => {
            let settings_chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Min(0),    // List
                    Constraint::Length(8), // Description Panel
                ])
                .split(content_chunks[1]);

            let mut items_data = vec![
                ("Advanced Settings", if app.settings.advanced_mode { "ON".to_string() } else { "OFF".to_string() }),
                ("Execution Mode", app.settings.execution_mode.to_uppercase()),
                ("ML Detection", if app.settings.ml_enabled { "ON".to_string() } else { "OFF".to_string() }),
                ("Tracing", if app.settings.tracing_enabled { "ON".to_string() } else { "OFF".to_string() }),
            ];

            if app.settings.advanced_mode {
                items_data.push(("Lineage Recording", if app.settings.lineage_enabled { "ON".to_string() } else { "OFF".to_string() }));
                items_data.push(("Stop on Block", if app.settings.stop_on_block { "ON".to_string() } else { "OFF".to_string() }));
                items_data.push(("Profiling ML", if app.settings.profiling_ml { "ON".to_string() } else { "OFF".to_string() }));
                
                // Profiling
                items_data.push(("Sample Size", app.settings.sample_size.to_string()));
                items_data.push(("Rounding Precision", app.settings.rounding_precision.to_string()));
                
                // Detection
                items_data.push(("Missing Threshold", format!("{:.2}", app.settings.missing_threshold)));
                items_data.push(("Outlier Threshold", format!("{:.2}", app.settings.outlier_threshold)));
                items_data.push(("Constant Threshold", format!("{:.2}", app.settings.constant_threshold)));
                items_data.push(("Duplicate Threshold", format!("{:.2}", app.settings.duplicate_threshold)));
                items_data.push(("Imbalance Threshold", format!("{:.2}", app.settings.imbalance_threshold)));
                items_data.push(("Skewness Threshold", format!("{:.2}", app.settings.skewness_threshold)));
                items_data.push(("Correlation Threshold", format!("{:.2}", app.settings.correlation_threshold)));
                items_data.push(("Pattern Threshold", format!("{:.2}", app.settings.pattern_threshold)));
                
                // ML
                items_data.push(("ML Confidence", format!("{:.2}", app.settings.semantic_min_confidence)));
                items_data.push(("ML Contamination", format!("{:.3}", app.settings.anomaly_contamination)));
                items_data.push(("ML Estimators", app.settings.anomaly_n_estimators.to_string()));
                items_data.push(("Default SQL Limit", app.settings.default_sql_limit.to_string()));
            }

            let items: Vec<ListItem> = items_data.iter().enumerate().map(|(i, (name, val))| {
                let style = if i == app.settings.selected_setting {
                    Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
                } else {
                    Style::default().fg(Color::White)
                };
                
                let val_color = match val.as_str() {
                    "ON" | "AUTOMATIC" => Color::Green,
                    "OFF" => Color::Red,
                    "HUMAN" => Color::Yellow,
                    "ADVISORY" => Color::Blue,
                    _ => Color::Cyan,
                };
                
                let prefix = if i == app.settings.selected_setting { ">> " } else { "   " };
                
                ListItem::new(Line::from(vec![
                    Span::styled(format!("{}{:<22}", prefix, name), style),
                    Span::styled(format!(" [ {} ]", val), Style::default().fg(val_color).add_modifier(Modifier::BOLD)),
                ]))
            }).collect();

            let title = if app.settings.advanced_mode { " Configuration (Advanced) " } else { " Configuration (Simple) " };
            let list = List::new(items)
                .block(Block::default().borders(Borders::ALL).title(title))
                .highlight_style(Style::default().bg(Color::DarkGray).add_modifier(Modifier::BOLD));
            
            let mut state = ListState::default();
            state.select(Some(app.settings.selected_setting));
            f.render_stateful_widget(list, settings_chunks[0], &mut state);

            // Add Scrollbar for Settings
            let settings_height = settings_chunks[0].height as usize - 2;
            if items_data.len() > settings_height {
                let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight);
                let mut scrollbar_state = ScrollbarState::new(items_data.len().saturating_sub(settings_height))
                    .position(app.settings.selected_setting);
                f.render_stateful_widget(
                    scrollbar,
                    settings_chunks[0].inner(Margin { vertical: 1, horizontal: 0 }),
                    &mut scrollbar_state,
                );
            }

            // Description Panel
            let descriptions = [
                "ADVANCED MODE: Toggle between simple and advanced configuration views to expose more granular controls.",
                "EXECUTION MODE: advisory (info only), human (approval required), automatic (autonomous self-healing).",
                "ML DETECTION: Enable AI-powered detection for data drift, anomalies, and complex semantic risks.",
                "TRACING: Enable detailed execution tracing to see exactly what the agent is doing at every step.",
                "LINEAGE: Track data transformations and lineage throughout the pipeline for full auditability.",
                "STOP ON BLOCK: Halt pipeline execution immediately if a CRITICAL quality risk is detected.",
                "PROFILING ML: Use ML classifiers during initial profiling for deeper semantic and privacy insights.",
                "SAMPLE SIZE: The number of rows to sample for expensive metrics (correlations, deep profiling).",
                "ROUNDING PRECISION: Number of decimal places to keep for numeric metrics and signals.",
                "MISSING THRESHOLD: Sensitivity to null values. Ratio of nulls allowed before flagging a risk.",
                "OUTLIER THRESHOLD: Sensitivity to statistical outliers. Ratio of anomalies allowed per column.",
                "CONSTANT THRESHOLD: Ratio of the most frequent value. If higher, column is considered constant.",
                "DUPLICATE THRESHOLD: Ratio of duplicate rows allowed in the dataset before flagging.",
                "IMBALANCE THRESHOLD: Maximum allowed ratio for a single category in sensitive columns.",
                "SKEWNESS THRESHOLD: Maximum allowed Fisher-Pearson skewness coefficient for numeric columns.",
                "CORRELATION THRESHOLD: Maximum allowed Pearson correlation between two numeric columns.",
                "PATTERN THRESHOLD: Minimum ratio of values that must match the inferred regex pattern.",
                "ML CONFIDENCE: Minimum confidence score (0-1) required for ML semantic labels to be accepted.",
                "ML CONTAMINATION: Expected ratio of anomalies in the dataset for Isolation Forest (0.0 - 0.5).",
                "ML ESTIMATORS: Number of trees in the Isolation Forest anomaly detection model (higher is more precise).",
                "DEFAULT SQL LIMIT: The default LIMIT clause used when auto-generating SQL queries for databases.",
            ];

            let desc_text = descriptions.get(app.settings.selected_setting).unwrap_or(&"No description available.");
            let description = Paragraph::new(format!("\n{}", desc_text))
                .block(Block::default().borders(Borders::ALL).title(" Setting Description & Impact ").border_style(Style::default().fg(Color::Cyan)))
                .wrap(Wrap { trim: true })
                .alignment(ratatui::layout::Alignment::Center);
            
            f.render_widget(description, settings_chunks[1]);
        }
    }

    // 3. Footer
    let mut footer_text = vec![
        Span::styled(" [q] Quit ", Style::default().fg(Color::Red)),
        Span::raw(" [tab] Next View "),
    ];

    let has_popup = app.show_export_popup || app.show_remediation_history_popup || 
                    app.show_local_open_popup || app.show_remote_open_popup || 
                    app.show_numeric_popup || app.show_help || app.show_trace_popup || 
                    app.show_lineage_popup || app.show_action_details;

    if has_popup {
        footer_text.push(Span::styled(" [Esc] Close/Cancel ", Style::default().fg(Color::Yellow)));
        
        if app.show_local_open_popup {
            footer_text.push(Span::raw(" [↑/↓] Navigate "));
            footer_text.push(Span::raw(" [Enter] Open/Select "));
        } else if app.show_remote_open_popup {
            if app.show_sql_query_input {
                footer_text.push(Span::raw(" [Tab] Switch Fields "));
            }
            footer_text.push(Span::raw(" [Enter] Load "));
        } else if app.show_numeric_popup {
            footer_text.push(Span::raw(" [←/→] Slide "));
            footer_text.push(Span::raw(" [Enter] Confirm "));
        } else if app.show_export_popup {
            footer_text.push(Span::raw(" [Tab] Format "));
            footer_text.push(Span::raw(" [Enter] Export "));
        } else {
            footer_text.push(Span::raw(" [Enter] Action "));
        }
    } else if app.search_mode {
        footer_text.push(Span::styled(" [Esc/Enter] Exit Search ", Style::default().fg(Color::Yellow)));
    } else {
        footer_text.push(Span::raw(" [r] Run "));
        footer_text.push(Span::raw(" [c] Clear "));
        footer_text.push(Span::raw(" [o] Open "));
        footer_text.push(Span::raw(" [h] Help "));

        match app.current_view {
            View::TraceMonitor => {
                footer_text.push(Span::raw(" [/] Search "));
                footer_text.push(Span::raw(" [f] Filter "));
                footer_text.push(Span::raw(" [s] Sort "));
                footer_text.push(Span::styled(" [Enter] Details ", Style::default().fg(Color::Yellow)));
            },
            View::Lineage => {
                footer_text.push(Span::raw(" [/] Search "));
                footer_text.push(Span::styled(" [Enter] Details ", Style::default().fg(Color::Yellow)));
            },
            View::RepairShop => {
                footer_text.push(Span::raw(" [Space] Toggle "));
                footer_text.push(Span::raw(" [a] Approve "));
                footer_text.push(Span::styled(" [Enter] Details ", Style::default().fg(Color::Yellow)));
            },
            View::Settings => {
                footer_text.push(Span::styled(" [Enter] Adjust ", Style::default().fg(Color::Yellow)));
            },
            View::Dashboard => {
                // Dashboard specifically might not have standard Enter details
            }
        }
    }

    let footer = Paragraph::new(Line::from(footer_text))
        .block(Block::default().borders(Borders::ALL).title(" Contextual Keybindings "));
    f.render_widget(footer, chunks[2]);

    // 5. Export Overlays
    if app.show_export_popup {
        render_export_popup(f, app);
    }
    if app.show_remediation_history_popup {
        render_remediation_history_popup(f, app);
    }
    if app.show_local_open_popup || app.show_remote_open_popup {
        render_load_popup(f, app);
    }
    if app.show_numeric_popup {
        render_numeric_popup(f, app);
    }

    // 6. Help Overlay
    if app.show_help {
        render_help(f);
    }
}

fn render_export_popup(f: &mut Frame, app: &crate::app::App) {
    let area = centered_rect(60, 30, f.area());
    f.render_widget(Clear, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Path Input
            Constraint::Length(3), // Format Toggle
            Constraint::Min(0),    // Instructions
        ])
        .margin(1)
        .split(area);

    let block = Block::default()
        .title(" Export Data Configuration ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Green));
    f.render_widget(block, area);

    let path_para = Paragraph::new(app.export_path_input.clone())
        .block(Block::default().borders(Borders::ALL).title(" Destination Path "));
    f.render_widget(path_para, chunks[0]);

    let csv_style = if app.export_format == crate::app::ExportFormat::Csv { Style::default().fg(Color::Black).bg(Color::Green) } else { Style::default().fg(Color::Gray) };
    let json_style = if app.export_format == crate::app::ExportFormat::Data { Style::default().fg(Color::Black).bg(Color::Green) } else { Style::default().fg(Color::Gray) };

    let format_para = Paragraph::new(Line::from(vec![
        Span::raw(" Format: "),
        Span::styled(" CSV ", csv_style),
        Span::raw("  "),
        Span::styled(" JSON (Data) ", json_style),
        Span::raw("  (Press [Tab] to toggle)"),
    ]))
    .block(Block::default().borders(Borders::ALL));
    f.render_widget(format_para, chunks[1]);

    let inst_para = Paragraph::new("\n [Enter] to Export | [Esc] to Cancel")
        .alignment(ratatui::layout::Alignment::Center);
    f.render_widget(inst_para, chunks[2]);
}

fn render_remediation_history_popup(f: &mut Frame, app: &crate::app::App) {
    let area = centered_rect(60, 25, f.area());
    f.render_widget(Clear, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Path Input
            Constraint::Min(0),    // Instructions
        ])
        .margin(1)
        .split(area);

    let block = Block::default()
        .title(" Export Fix History (JSON) ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Magenta));
    f.render_widget(block, area);

    let path_para = Paragraph::new(app.export_path_input.clone())
        .block(Block::default().borders(Borders::ALL).title(" Destination Path "));
    f.render_widget(path_para, chunks[0]);

    let inst_para = Paragraph::new(format!("\n Ready to export {} session fixes.\n [Enter] to Save | [Esc] to Cancel", app.all_executed_actions.len()))
        .alignment(ratatui::layout::Alignment::Center);
    f.render_widget(inst_para, chunks[1]);
}

fn render_load_popup(f: &mut Frame, app: &crate::app::App) {
    if app.show_local_open_popup {
        render_file_browser(f, app);
        return;
    }

    let is_db = app.show_sql_query_input;
    let area = if is_db { centered_rect(60, 45, f.area()) } else { centered_rect(60, 25, f.area()) };
    f.render_widget(Clear, area);

    let mut constraints = vec![
        Constraint::Length(3), // URI Input
    ];
    if is_db {
        constraints.push(Constraint::Length(3)); // SQL Input
    }
    constraints.push(Constraint::Min(0)); // Instructions

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints(constraints)
        .margin(1)
        .split(area);

    let block = Block::default()
        .title(" Open Remote Data Source (URI) ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Blue));
    f.render_widget(block, area);

    let uri_title = if is_db { " Connection URI (Database Detected) " } else { " Connection URI " };
    let input_para = Paragraph::new(app.open_input.clone())
        .block(Block::default().borders(Borders::ALL).title(uri_title));
    f.render_widget(input_para, chunks[0]);

    if is_db {
        let sql_para = Paragraph::new(app.sql_query_input.clone())
            .block(Block::default().borders(Borders::ALL).title(" SQL Query ").border_style(Style::default().fg(Color::Yellow)));
        f.render_widget(sql_para, chunks[1]);
    }

    let example = "Example: s3://bucket/key.parquet or postgresql://user:pass@host:port/db";
    let help_msg = if is_db {
        " [Tab] Switch Fields | [Enter] Load | [Esc] Cancel "
    } else {
        " [Enter] to Load | [Esc] to Cancel "
    };

    let inst_para = Paragraph::new(format!("\n{}\n{}", example, help_msg))
        .alignment(ratatui::layout::Alignment::Center);
    f.render_widget(inst_para, if is_db { chunks[2] } else { chunks[1] });
}

fn render_numeric_popup(f: &mut Frame, app: &crate::app::App) {
    let area = centered_rect(50, 25, f.area());
    f.render_widget(Clear, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Input
            Constraint::Min(0),    // Instructions
        ])
        .margin(1)
        .split(area);

    let setting_name = match app.editing_setting_idx {
        7 => "Sample Size",
        8 => "Rounding Precision",
        9 => "Missing Threshold",
        10 => "Outlier Threshold",
        11 => "Constant Threshold",
        12 => "Duplicate Threshold",
        13 => "Imbalance Threshold",
        14 => "Skewness Threshold",
        15 => "Correlation Threshold",
        16 => "Pattern Threshold",
        17 => "ML Confidence",
        18 => "ML Contamination",
        19 => "ML Estimators",
        20 => "Default SQL Limit",
        _ => "Unknown Setting",
    };

    let block = Block::default()
        .title(format!(" Adjust Setting: {} ", setting_name))
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Yellow));
    f.render_widget(block, area);

    let input_para = Paragraph::new(app.numeric_input.clone())
        .block(Block::default().borders(Borders::ALL).title(" Value (Type or use ←/→) "));
    f.render_widget(input_para, chunks[0]);

    let inst_para = Paragraph::new("\n [←/→] Slide | [0-9.] Type | [Enter] Confirm | [Esc] Cancel")
        .alignment(ratatui::layout::Alignment::Center);
    f.render_widget(inst_para, chunks[1]);
}

fn render_file_browser(f: &mut Frame, app: &crate::app::App) {
    let area = centered_rect(80, 80, f.area());
    f.render_widget(Clear, area);

    let block = Block::default()
        .title(format!(" Open Local File: {} ", app.file_browser.current_dir.display()))
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));
    f.render_widget(block, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(0),
            Constraint::Length(3),
        ])
        .margin(1)
        .split(area);

    let items: Vec<Row> = app.file_browser.entries.iter().enumerate().map(|(i, entry)| {
        let style = if i == app.file_browser.selected_index {
            Style::default().fg(Color::Black).bg(Color::Cyan)
        } else {
            Style::default()
        };

        let icon = if entry.is_dir { "📁" } else { "📄" };
        Row::new(vec![
            Cell::from(icon),
            Cell::from(entry.name.clone()),
        ]).style(style)
    }).collect();

    let table = Table::new(items, [
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .header(Row::new(vec!["", "Name"]).style(Style::default().add_modifier(Modifier::BOLD)));

    f.render_widget(table, chunks[0]);

    let help = Paragraph::new(" [↑/↓] Navigate | [Enter] Open/Select | [Esc] Cancel ")
        .alignment(ratatui::layout::Alignment::Center)
        .block(Block::default().borders(Borders::TOP));
    f.render_widget(help, chunks[1]);
}

fn render_help(f: &mut Frame) {
    let area = centered_rect(60, 85, f.area());
    f.render_widget(Clear, area); // Clear background

    let help_text = vec![
        Row::new(vec![Cell::from("Global"), Cell::from("")]).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Row::new(vec![Cell::from("  q"), Cell::from("Quit ADQA")]),
        Row::new(vec![Cell::from("  Tab"), Cell::from("Cycle Views (Dashboard, Repair Shop, Trace, Lineage, Settings)")]),
        Row::new(vec![Cell::from("  r"), Cell::from("Run/Re-run analysis on current data")]),
        Row::new(vec![Cell::from("  c"), Cell::from("Clear session logs and history")]),
        Row::new(vec![Cell::from("  h / ?"), Cell::from("Toggle this help menu")]),
        Row::new(vec![Cell::from("  o"), Cell::from("Browse local files to open (CSV, Parquet, JSON, DB)")]),
        Row::new(vec![Cell::from("  O"), Cell::from("Open remote data source (S3, Postgres, BigQuery, etc)")]),
        Row::new(vec![Cell::from("  e"), Cell::from("Export current data (remediated or analysis results)")]),
        Row::new(vec![Cell::from("  E"), Cell::from("Export session fix history (REMEDIATION JOURNEY)")]),
        
        Row::new(vec![Cell::from("Navigation"), Cell::from("")]).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Row::new(vec![Cell::from("  ↑ / k"), Cell::from("Move selection up / Scroll up")]),
        Row::new(vec![Cell::from("  ↓ / j"), Cell::from("Move selection down / Scroll down")]),
        Row::new(vec![Cell::from("  Enter"), Cell::from("Open Details popup / Expand group / Toggle setting")]),
        Row::new(vec![Cell::from("  Esc"), Cell::from("Close any open popup / Exit search mode")]),

        Row::new(vec![Cell::from("Trace Monitor"), Cell::from("")]).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Row::new(vec![Cell::from("  /"), Cell::from("Enter search mode (filter traces by name/meta)")]),
        Row::new(vec![Cell::from("  f"), Cell::from("Cycle through type filters (Ingress, Profiling, Check, Error)")]),
        Row::new(vec![Cell::from("  s"), Cell::from("Toggle Sort Order (Newest First / Oldest First)")]),

        Row::new(vec![Cell::from("Repair Shop"), Cell::from("")]).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Row::new(vec![Cell::from("  Space"), Cell::from("Toggle selection of a specific fix")]),
        Row::new(vec![Cell::from("  a"), Cell::from("Approve and execute selected fixes")]),

        Row::new(vec![Cell::from("Settings Adjustment"), Cell::from("")]).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Row::new(vec![Cell::from("  ← / →"), Cell::from("Slide/Adjust numeric values in real-time")]),
        Row::new(vec![Cell::from("  0-9 / ."), Cell::from("Directly type numeric values in adjustment popup")]),
        Row::new(vec![Cell::from("  Enter"), Cell::from("Confirm and save the new value")]),
    ];

    let help_table = Table::new(help_text, [
        Constraint::Percentage(30),
        Constraint::Percentage(70),
    ])
    .block(Block::default()
        .title(" ADQA Quick Reference ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan)))
    .header(Row::new(vec!["Key", "Action"]).style(Style::default().add_modifier(Modifier::UNDERLINED)));

    f.render_widget(help_table, area);
}

fn centered_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}
