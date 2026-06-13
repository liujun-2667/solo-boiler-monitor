import os
import sys
import json
import math
import statistics
from datetime import datetime, timedelta

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from flask import request, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
from engine import engine
from layouts import (
    build_dashboard_layout,
    build_history_layout,
    build_config_layout,
    register_config_callbacks,
    build_report_layout,
)
from layouts.dashboard import (
    KEY_PARAMS,
    EMISSION_PARAMS,
    build_mini_sparkline,
    build_param_card,
    build_efficiency_gauge,
    build_heat_loss_chart,
    build_emission_gauge,
    build_suggestion_card,
    DARK_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_YELLOW,
    ACCENT_RED,
)

db.init_db()

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.DARKLY],
    title="工业锅炉监控平台",
)

server = app.server


@server.route("/api/ingest", methods=["POST"])
def api_ingest():
    try:
        payload = request.get_json(force=True)
        boiler_id = payload.get("boiler_id", "Boiler-1")
        timestamp = payload.get("timestamp", datetime.now().isoformat())
        data = payload.get("data", {})
        engine.ingest(boiler_id, timestamp, data)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def build_main_navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Span("🔥", style={"fontSize": "22px", "marginRight": "8px"}),
                        html.Span(
                            "工业锅炉燃烧效率优化与排放监测平台",
                            style={"color": "#fff", "fontSize": "18px", "fontWeight": "700"},
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("实时监控", href="/", active="exact", style={"color": "#fff"})),
                        dbc.NavItem(dbc.NavLink("历史分析", href="/history", active="exact", style={"color": "#fff"})),
                        dbc.NavItem(dbc.NavLink("合规报告", href="/report", active="exact", style={"color": "#fff"})),
                        dbc.NavItem(dbc.NavLink("系统配置", href="/config", active="exact", style={"color": "#fff"})),
                    ],
                    pills=True,
                ),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        style={
            "borderBottom": "1px solid #1E3A5F",
            "backgroundColor": "#0A1929",
            "padding": "8px 24px",
        },
    )


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        build_main_navbar(),
        html.Div(id="page-content"),
    ],
    style={"backgroundColor": DARK_BG, "minHeight": "100vh"},
)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/history":
        return build_history_layout()
    elif pathname == "/report":
        return build_report_layout()
    elif pathname == "/config":
        return build_config_layout()
    else:
        return build_dashboard_layout()


register_config_callbacks(app)


@app.callback(
    Output("dashboard-current-time", "children"),
    Input("dashboard-interval", "n_intervals"),
)
def update_time(_):
    return datetime.now().strftime("%H:%M:%S")


@app.callback(
    [Output(f"param-value-{p['key']}", "children") for p in KEY_PARAMS]
    + [Output(f"param-status-bar-{p['key']}", "style") for p in KEY_PARAMS]
    + [Output(f"param-sparkline-{p['key']}", "figure") for p in KEY_PARAMS],
    [Input("dashboard-interval", "n_intervals"), Input("dashboard-boiler-select", "value")],
)
def update_key_params(_, boiler_id):
    latest = engine.get_latest(boiler_id)
    history = db.get_recent_aggregated(boiler_id, minutes=30)
    values = []
    bar_styles = []
    spark_figs = []
    for param_cfg in KEY_PARAMS:
        key = param_cfg["key"]
        val = None
        if latest and latest.get("data"):
            val = latest["data"].get(key)
        if val is None:
            values.append("--")
            bar_styles.append(
                {"height": "4px", "width": "100%", "backgroundColor": TEXT_SECONDARY, "borderRadius": "2px", "marginBottom": "8px"}
            )
        else:
            values.append(f"{val:.2f}" if isinstance(val, float) else str(val))
            if val < param_cfg["alarm_low"] or val > param_cfg["alarm_high"]:
                c = ACCENT_RED
            elif val < param_cfg["warning_low"] or val > param_cfg["warning_high"]:
                c = ACCENT_YELLOW
            else:
                c = ACCENT_GREEN
            bar_styles.append(
                {"height": "4px", "width": "100%", "backgroundColor": c, "borderRadius": "2px", "marginBottom": "8px"}
            )
        series = [h.get(key) for h in history if h.get(key) is not None]
        spark_figs.append(build_mini_sparkline(series))
    return values + bar_styles + spark_figs


@app.callback(
    Output("efficiency-gauge", "figure"),
    Output("heat-loss-chart", "figure"),
    [Input("dashboard-interval", "n_intervals"), Input("dashboard-boiler-select", "value")],
)
def update_efficiency(_, boiler_id):
    latest = engine.get_latest(boiler_id)
    metrics = {}
    if latest and latest.get("metrics"):
        metrics = latest["metrics"]
    eff = metrics.get("efficiency", 90)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=eff,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [80, 100],
                "tickvals": [80, 85, 90, 95, 100],
                "ticktext": ["80", "85", "90", "95", "100"],
                "tickfont": {"color": TEXT_SECONDARY, "size": 11},
            },
            "bar": {"color": ACCENT_GREEN if eff >= 90 else ACCENT_YELLOW if eff >= 85 else ACCENT_RED, "thickness": 0.35},
            "steps": [
                {"range": [80, 85], "color": "rgba(255, 77, 109, 0.3)"},
                {"range": [85, 90], "color": "rgba(255, 184, 0, 0.3)"},
                {"range": [90, 97], "color": "rgba(0, 255, 136, 0.3)"},
                {"range": [97, 100], "color": "rgba(255, 184, 0, 0.3)"},
            ],
            "threshold": {"line": {"color": ACCENT_CYAN, "width": 2}, "thickness": 0.8, "value": eff},
        },
        number={
            "font": {"color": TEXT_PRIMARY, "size": 42, "family": "Consolas, monospace"},
            "suffix": "%",
            "valueformat": ".1f",
        },
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=30, b=0), height=260)

    q2 = metrics.get("q2", 6.5)
    q3 = metrics.get("q3", 0.8)
    q4 = metrics.get("q4", 2.5)
    q5 = metrics.get("q5", 1.6)
    fig2 = go.Figure()
    losses = [
        {"name": "q2 排烟热损失", "color": ACCENT_RED, "value": q2},
        {"name": "q3 气体未完全燃烧", "color": ACCENT_YELLOW, "value": q3},
        {"name": "q4 固体未完全燃烧", "color": ACCENT_YELLOW, "value": q4},
        {"name": "q5 散热损失", "color": ACCENT_CYAN, "value": q5},
    ]
    for loss in losses:
        fig2.add_trace(go.Bar(
            y=[loss["name"]],
            x=[loss["value"]],
            orientation="h",
            marker=dict(color=loss["color"]),
            text=[f"{loss['value']:.2f}%"],
            textposition="outside",
            textfont=dict(color=TEXT_PRIMARY, size=13),
            width=0.55,
        ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=30, t=10, b=0),
        xaxis=dict(range=[0, 12], tickfont=dict(color=TEXT_SECONDARY, size=11), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False,
                   title=dict(text="热损失 (%)", font=dict(color=TEXT_SECONDARY, size=11))),
        yaxis=dict(tickfont=dict(color=TEXT_PRIMARY, size=12), showgrid=False, zeroline=False),
        showlegend=False,
        height=260,
        bargap=0.3,
    )
    return fig, fig2


@app.callback(
    [Output(f"emission-gauge-{p['key']}", "figure") for p in EMISSION_PARAMS]
    + [Output(f"emission-current-{p['key']}", "children") for p in EMISSION_PARAMS]
    + [Output(f"emission-hourly-{p['key']}", "children") for p in EMISSION_PARAMS]
    + [Output(f"emission-pct-{p['key']}", "children") for p in EMISSION_PARAMS]
    + [Output(f"emission-limit-bar-{p['key']}", "style") for p in EMISSION_PARAMS],
    [Input("dashboard-interval", "n_intervals"), Input("dashboard-boiler-select", "value")],
)
def update_emissions(_, boiler_id):
    latest = engine.get_latest(boiler_id)
    history_1h = db.get_recent_aggregated(boiler_id, minutes=60)
    limits = db.get_emission_limits()
    figures = []
    currents = []
    hourlies = []
    pcts = []
    bars = []
    for param_cfg in EMISSION_PARAMS:
        key = param_cfg["key"]
        lim = limits.get(key, {"hourly": 100, "peak": 200})
        current = 0
        hourly = 0
        if latest and latest.get("data"):
            current = latest["data"].get(key, 0) or 0
        hour_vals = [h.get(key) for h in history_1h if h.get(key) is not None]
        if hour_vals:
            hourly = statistics.mean(hour_vals)
        pct = min(100.0, (current / max(1, lim["hourly"])) * 100)
        if pct >= 100:
            bar_c = ACCENT_RED
        elif pct >= 80:
            bar_c = ACCENT_YELLOW
        else:
            bar_c = ACCENT_GREEN
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current,
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "shape": "angular",
                "axis": {
                    "range": [0, lim["hourly"] * 1.5],
                    "tickvals": [0, lim["hourly"] * 0.5, lim["hourly"], lim["hourly"] * 1.5],
                    "ticktext": ["0", f"{int(lim['hourly']*0.5)}", f"{int(lim['hourly'])}", f"{int(lim['hourly']*1.5)}"],
                    "tickfont": {"color": TEXT_SECONDARY, "size": 9},
                },
                "bar": {"color": bar_c, "thickness": 0.4},
                "steps": [
                    {"range": [0, lim["hourly"] * 0.8], "color": "rgba(0, 255, 136, 0.2)"},
                    {"range": [lim["hourly"] * 0.8, lim["hourly"]], "color": "rgba(255, 184, 0, 0.25)"},
                    {"range": [lim["hourly"], lim["hourly"] * 1.5], "color": "rgba(255, 77, 109, 0.3)"},
                ],
                "threshold": {"line": {"color": ACCENT_RED, "width": 2}, "thickness": 0.9, "value": lim["hourly"]},
            },
            number={"font": {"color": TEXT_PRIMARY, "size": 22, "family": "Consolas, monospace"}, "valueformat": ".1f"},
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=0), height=150)
        figures.append(fig)
        currents.append(f"{current:.1f}")
        hourlies.append(f"{hourly:.1f}")
        pcts.append(f"{pct:.0f}")
        bars.append({"height": "4px", "width": f"{min(100, pct)}%", "backgroundColor": bar_c, "borderRadius": "2px", "transition": "width 0.5s"})
    return figures + currents + hourlies + pcts + bars


@app.callback(
    Output("suggestions-container", "children"),
    [Input("dashboard-interval", "n_intervals"), Input("dashboard-boiler-select", "value")],
)
def update_suggestions(_, boiler_id):
    sugs = db.get_active_suggestions(boiler_id)
    if not sugs:
        return html.Div(
            "系统运行正常，暂无调优建议 🟢",
            style={"color": ACCENT_GREEN, "textAlign": "center", "padding": "40px 20px", "fontSize": "14px"},
        )
    cards = []
    for i, s in enumerate(sugs):
        cards.append(build_suggestion_card(s, i))
    return cards


def _parse_time_range(time_range, start_date, start_time, end_date, end_time):
    now = datetime.now()
    if time_range == "1h":
        return (now - timedelta(hours=1)).isoformat(), now.isoformat()
    elif time_range == "6h":
        return (now - timedelta(hours=6)).isoformat(), now.isoformat()
    elif time_range == "24h":
        return (now - timedelta(hours=24)).isoformat(), now.isoformat()
    elif time_range == "7d":
        return (now - timedelta(days=7)).isoformat(), now.isoformat()
    else:
        try:
            s = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            e = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            return s.isoformat(), e.isoformat()
        except Exception:
            return (now - timedelta(hours=6)).isoformat(), now.isoformat()


@app.callback(
    Output("history-custom-time-container", "style"),
    Input("history-time-range", "value"),
)
def toggle_custom_time(v):
    if v == "custom":
        return {"display": "flex", "alignItems": "flex-end"}
    return {"display": "none"}


STAT_CARD_IDS = ["avg-eff", "max-eff", "min-eff", "std-eff", "avg-q2", "avg-q3", "avg-q4", "avg-q5"]


@app.callback(
    Output("history-query-store", "data"),
    [Input("history-query-btn", "n_clicks"), Input("history-boiler-select", "value"), Input("history-time-range", "value")],
    [
        State("history-start-date", "date"),
        State("history-start-time", "value"),
        State("history-end-date", "date"),
        State("history-end-time", "value"),
    ],
)
def fetch_history_data(n_clicks, boiler_id, time_range, sd, st, ed, et):
    start_iso, end_iso = _parse_time_range(time_range, sd, st, ed, et)
    data = db.get_aggregated_range(boiler_id or "Boiler-1", start_iso, end_iso)
    return data


@app.callback(
    Output("trend-chart", "figure"),
    [Input("history-query-store", "data")],
    [State("trend-y1-params", "value"), State("trend-y2-params", "value")],
)
def update_trend_chart(data, y1_params, y2_params):
    point_limits = db.get_point_limits()
    fig = go.Figure()
    if not data:
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    x = [datetime.fromisoformat(d["window_start"]) for d in data]
    colors = [ACCENT_CYAN, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED, "#98c379", "#c678dd"]
    for i, p in enumerate(y1_params or []):
        vals = [d.get(p) for d in data]
        info = point_limits.get(p, {"name": p, "unit": ""})
        fig.add_trace(go.Scatter(
            x=x, y=vals, mode="lines", name=f"{info.get('name', p)} ({info.get('unit','')})",
            line=dict(color=colors[i % len(colors)], width=1.8), yaxis="y",
        ))
    for i, p in enumerate(y2_params or []):
        vals = [d.get(p) for d in data]
        info = point_limits.get(p, {"name": p, "unit": ""})
        fig.add_trace(go.Scatter(
            x=x, y=vals, mode="lines", name=f"{info.get('name', p)} ({info.get('unit','')})",
            line=dict(color=colors[(i + 3) % len(colors)], width=1.8, dash="dot"), yaxis="y2",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        yaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        yaxis2=dict(tickfont=dict(color=TEXT_SECONDARY), overlaying="y", side="right", showgrid=False, zeroline=False),
        legend=dict(font=dict(color=TEXT_PRIMARY), orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=40, t=40, b=40),
        height=380,
    )
    return fig


@app.callback(
    [Output("efficiency-histogram", "figure")]
    + [Output(f"stat-value-{cid}", "children") for cid in STAT_CARD_IDS]
    + [Output("stat-sub-max-eff", "children"), Output("stat-sub-min-eff", "children")],
    [Input("history-query-store", "data")],
)
def update_efficiency_stats(data):
    fig = go.Figure()
    card_defaults = ["-- %"] * 8
    sub_max, sub_min = "--:--:--", "--:--:--"
    if not data:
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=100)
        return [fig] + card_defaults + [sub_max, sub_min]
    eff_pairs = [(d.get("efficiency"), d.get("window_start")) for d in data if d.get("efficiency") is not None]
    q2_vals = [d.get("q2") for d in data if d.get("q2") is not None]
    q3_vals = [d.get("q3") for d in data if d.get("q3") is not None]
    q4_vals = [d.get("q4") for d in data if d.get("q4") is not None]
    q5_vals = [d.get("q5") for d in data if d.get("q5") is not None]
    if eff_pairs:
        eff_vals = [p[0] for p in eff_pairs]
        avg_eff = statistics.mean(eff_vals)
        max_eff = max(eff_vals)
        min_eff = min(eff_vals)
        std_eff = statistics.stdev(eff_vals) if len(eff_vals) > 1 else 0
        max_ts = next(p[1] for p in eff_pairs if p[0] == max_eff)
        min_ts = next(p[1] for p in eff_pairs if p[0] == min_eff)
        try:
            sub_max = datetime.fromisoformat(max_ts).strftime("%H:%M:%S")
        except Exception:
            sub_max = max_ts[11:19] if len(max_ts) > 19 else max_ts
        try:
            sub_min = datetime.fromisoformat(min_ts).strftime("%H:%M:%S")
        except Exception:
            sub_min = min_ts[11:19] if len(min_ts) > 19 else min_ts
        card_defaults = [
            f"{avg_eff:.2f} %",
            f"{max_eff:.2f} %",
            f"{min_eff:.2f} %",
            f"{std_eff:.3f}",
            f"{statistics.mean(q2_vals):.2f} %" if q2_vals else "-- %",
            f"{statistics.mean(q3_vals):.2f} %" if q3_vals else "-- %",
            f"{statistics.mean(q4_vals):.2f} %" if q4_vals else "-- %",
            f"{statistics.mean(q5_vals):.2f} %" if q5_vals else "-- %",
        ]
        fig.add_trace(go.Histogram(x=eff_vals, nbinsx=12, marker_color=ACCENT_GREEN, opacity=0.8))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=False, zeroline=False),
        yaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=100,
    )
    return [fig] + card_defaults + [sub_max, sub_min]


@app.callback(
    Output("corr-scatter-chart", "figure"),
    Output("corr-pearson-value", "children"),
    Output("corr-strength-label", "children"),
    [Input("corr-x-param", "value"), Input("corr-y-param", "value"), Input("history-query-store", "data")],
)
def update_correlation(x_param, y_param, data):
    fig = go.Figure()
    pearson = "--"
    strength = "--"
    if not data or not x_param or not y_param:
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=360)
        return fig, pearson, strength
    xs = [d.get(x_param) for d in data if d.get(x_param) is not None and d.get(y_param) is not None]
    ys = [d.get(y_param) for d in data if d.get(x_param) is not None and d.get(y_param) is not None]
    point_limits = db.get_point_limits()
    x_info = point_limits.get(x_param, {"name": x_param, "unit": ""})
    y_info = point_limits.get(y_param, {"name": y_param, "unit": ""})
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(color=ACCENT_CYAN, size=7, opacity=0.7),
        name=f"{x_info.get('name')} vs {y_info.get('name')}",
    ))
    if len(xs) >= 2:
        try:
            r = statistics.correlation(xs, ys)
            pearson = f"{r:.3f}"
            ar = abs(r)
            if ar >= 0.8:
                strength = "强相关"
            elif ar >= 0.5:
                strength = "中等相关"
            elif ar >= 0.3:
                strength = "弱相关"
            else:
                strength = "基本无关"
        except Exception:
            pass
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=dict(text=f"{x_info.get('name')} ({x_info.get('unit')})", font=dict(color=TEXT_SECONDARY, size=11)),
                   tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        yaxis=dict(title=dict(text=f"{y_info.get('name')} ({y_info.get('unit')})", font=dict(color=TEXT_SECONDARY, size=11)),
                   tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        margin=dict(l=50, r=20, t=20, b=50),
        height=360,
    )
    return fig, pearson, strength


@app.callback(
    Output("report-content", "children"),
    Output("report-status", "children"),
    Output("report-pdf-link", "href"),
    [Input("report-generate-btn", "n_clicks")],
    [
        State("report-boiler-select", "value"),
        State("report-year", "value"),
        State("report-month", "value"),
    ],
)
def generate_report(_, boiler_id, year, month):
    if not year or not month:
        return html.Div(), "请选择年份和月份", "#"
    report_data = _compute_report_data(boiler_id, year, month)
    if report_data is None:
        return html.Div("该时间段内无运行数据", style={"color": ACCENT_RED, "padding": "20px"}), "无数据", "#"
    content = _build_report_html(boiler_id, year, month, report_data)
    pdf_href = f"/api/report/pdf?boiler_id={boiler_id}&year={year}&month={month}"
    return content, f"报告已生成：{year}年{month}月", pdf_href


def _compute_report_data(boiler_id, year, month):
    from emissions import EmissionMonitor
    em = EmissionMonitor(boiler_id)
    report = em.get_monthly_report(boiler_id, year, month)
    if report is None:
        return None
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    data = db.get_aggregated_range(boiler_id, start.isoformat(), end.isoformat())
    eff_vals = [d.get("efficiency") for d in data if d.get("efficiency") is not None]
    q2_vals = [d.get("q2") for d in data if d.get("q2") is not None]
    report["avg_efficiency"] = statistics.mean(eff_vals) if eff_vals else 0
    report["avg_q2"] = statistics.mean(q2_vals) if q2_vals else 0
    report["data_points"] = len(data)
    limits = db.get_emission_limits()
    report["limits"] = limits
    alerts = db.get_recent_alerts(boiler_id, minutes=60 * 24 * 31)
    report["alert_list"] = alerts[:20]
    return report


def _build_report_html(boiler_id, year, month, r):
    CARD = {
        "backgroundColor": DARK_BG_CARD,
        "border": f"1px solid {BORDER_COLOR}",
        "borderRadius": "8px",
        "padding": "16px",
        "marginBottom": "16px",
    }
    poll_labels = {"nox": "NOx", "so2": "SO₂", "co": "CO", "dust": "粉尘"}
    daily_rows = []
    for day in sorted(r.get("daily_stats", {}).keys()):
        ds = r["daily_stats"][day]
        cells = [html.Td(day, style={"color": TEXT_SECONDARY, "padding": "6px 10px", "borderBottom": f"1px solid {BORDER_COLOR}"})]
        for p in ["nox", "so2", "co", "dust"]:
            v = ds.get(p, {})
            mean_v = v.get("mean", 0)
            max_v = v.get("max", 0)
            cells.append(html.Td(f"{mean_v:.1f} / {max_v:.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px", "borderBottom": f"1px solid {BORDER_COLOR}", "textAlign": "center"}))
        daily_rows.append(html.Tr(cells))

    alert_rows = []
    for a in r.get("alert_list", []):
        alert_rows.append(html.Tr([
            html.Td(a.get("timestamp", "")[:19], style={"color": TEXT_SECONDARY, "padding": "6px 10px"}),
            html.Td(a.get("pollutant", ""), style={"color": ACCENT_ORANGE if a.get("level") == "warning" else ACCENT_RED, "padding": "6px 10px"}),
            html.Td(a.get("level", ""), style={"color": ACCENT_RED if a.get("level") == "alarm" else ACCENT_ORANGE, "padding": "6px 10px"}),
            html.Td(f"{a.get('value', 0):.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px"}),
            html.Td(f"{a.get('limit_val', 0):.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px"}),
        ]))

    children = [
        html.Div([
            html.Div(f"锅炉编号: {boiler_id}", style={"color": TEXT_SECONDARY, "fontSize": "14px", "marginRight": "24px"}),
            html.Div(f"报告周期: {year}年{month}月", style={"color": TEXT_SECONDARY, "fontSize": "14px", "marginRight": "24px"}),
            html.Div(f"数据点数: {r.get('data_points', 0)}", style={"color": TEXT_SECONDARY, "fontSize": "14px"}),
        ], style={"marginBottom": "16px", "display": "flex"}),

        html.Div("合规概览", style={"color": ACCENT_CYAN, "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"}),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("合规率评分", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                html.Div(f"{r.get('compliance_rate', 0):.1f}%", style={"color": ACCENT_GREEN if r.get('compliance_rate', 0) >= 90 else ACCENT_RED, "fontSize": "36px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
                html.Div(f"达标小时数/总运行小时数", style={"color": TEXT_SECONDARY, "fontSize": "11px", "marginTop": "4px"}),
            ], style=CARD), width=3),
            dbc.Col(html.Div([
                html.Div("平均燃烧效率", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                html.Div(f"{r.get('avg_efficiency', 0):.2f}%", style={"color": ACCENT_GREEN, "fontSize": "36px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
            ], style=CARD), width=3),
            dbc.Col(html.Div([
                html.Div("超标告警次数", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                html.Div(str(r.get("alert_count", 0)), style={"color": ACCENT_RED if r.get("alert_count", 0) > 0 else ACCENT_GREEN, "fontSize": "36px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
            ], style=CARD), width=3),
            dbc.Col(html.Div([
                html.Div("总运行时长", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                html.Div(f"{r.get('total_hours', 0):.1f}h", style={"color": ACCENT_CYAN, "fontSize": "36px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
            ], style=CARD), width=3),
        ], style={"marginBottom": "16px"}),

        html.Div("排放指标日均趋势", style={"color": ACCENT_CYAN, "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"}),
        html.Div([
            html.Table([
                html.Tr([
                    html.Th("日期", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                    *[html.Th(f"{poll_labels.get(p, p)} 均值/峰值", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "center"}) for p in ["nox", "so2", "co", "dust"]],
                ]),
                *daily_rows,
            ], style={"width": "100%", "borderCollapse": "collapse"}),
        ], style=CARD),

        html.Div("排放总量估算 (kg)", style={"color": ACCENT_CYAN, "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px", "marginTop": "8px"}),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(poll_labels.get(p, p), style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "4px"}),
                html.Div(f"{r.get('total_emission_kg', {}).get(p, 0):.1f}", style={"color": ACCENT_ORANGE, "fontSize": "22px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
            ], style=CARD), width=3) for p in ["nox", "so2", "co", "dust"]
        ], style={"marginBottom": "16px"}),

        html.Div("超标记录", style={"color": ACCENT_CYAN, "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"}),
        html.Div([
            html.Table([
                html.Tr([
                    html.Th("时间", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                    html.Th("指标", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                    html.Th("级别", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                    html.Th("实测值", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                    html.Th("限值", style={"color": TEXT_PRIMARY, "padding": "8px 10px", "borderBottom": f"2px solid {ACCENT_CYAN}"}),
                ]),
                *(alert_rows if alert_rows else [html.Tr(html.Td("暂无超标记录", colSpan=5, style={"color": ACCENT_GREEN, "padding": "12px", "textAlign": "center"}))]),
            ], style={"width": "100%", "borderCollapse": "collapse"}),
        ], style=CARD),
    ]
    return html.Div(children)


@server.route("/api/report/pdf")
def api_report_pdf():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm
        import io

        boiler_id = request.args.get("boiler_id", "Boiler-1")
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))

        report = _compute_report_data(boiler_id, year, month)
        if report is None:
            return jsonify({"error": "no data"}), 404

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=12)
        heading_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, spaceAfter=8, spaceBefore=12)
        normal_style = ParagraphStyle("Normal2", parent=styles["Normal"], fontSize=10)

        elements = []
        elements.append(Paragraph(f"排放合规月度报告 - {boiler_id}", title_style))
        elements.append(Paragraph(f"报告周期: {year}年{month}月 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("合规概览", heading_style))
        overview_data = [
            ["指标", "数值"],
            ["合规率", f"{report.get('compliance_rate', 0):.1f}%"],
            ["平均燃烧效率", f"{report.get('avg_efficiency', 0):.2f}%"],
            ["超标告警次数", str(report.get('alert_count', 0))],
            ["总运行时长(h)", f"{report.get('total_hours', 0):.1f}"],
        ]
        t = Table(overview_data, colWidths=[80 * mm, 80 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("排放总量估算 (kg)", heading_style))
        em_data = [["指标", "排放总量(kg)"]]
        for p in ["nox", "so2", "co", "dust"]:
            em_data.append([p.upper(), f"{report.get('total_emission_kg', {}).get(p, 0):.1f}"])
        t2 = Table(em_data, colWidths=[80 * mm, 80 * mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("日均排放趋势", heading_style))
        daily_data = [["日期", "NOx均值/峰值", "SO2均值/峰值", "CO均值/峰值", "粉尘均值/峰值"]]
        for day in sorted(report.get("daily_stats", {}).keys()):
            ds = report["daily_stats"][day]
            row = [day]
            for p in ["nox", "so2", "co", "dust"]:
                v = ds.get(p, {})
                row.append(f"{v.get('mean', 0):.1f}/{v.get('max', 0):.1f}")
            daily_data.append(row)
        t3 = Table(daily_data, colWidths=[30 * mm, 35 * mm, 35 * mm, 35 * mm, 35 * mm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(t3)

        doc.build(elements)
        buf.seek(0)
        from flask import Response
        return Response(
            buf.getvalue(),
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment;filename=emission_report_{boiler_id}_{year}{month:02d}.pdf"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("工业锅炉燃烧效率优化与排放监测平台启动中...")
    print("  Dash UI:    http://127.0.0.1:8050/")
    print("  API 接口:   POST http://127.0.0.1:8050/api/ingest")
    print("  启动模拟器: python data_simulator.py")
    print("=" * 60)
    app.run_server(debug=False, host="0.0.0.0", port=8050)
