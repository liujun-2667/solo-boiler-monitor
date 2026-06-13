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


@app.callback(
    Output("trend-chart", "figure"),
    [Input("history-query-btn", "n_clicks")],
    [
        State("history-boiler-select", "value"),
        State("history-time-range", "value"),
        State("history-start-date", "date"),
        State("history-start-time", "value"),
        State("history-end-date", "date"),
        State("history-end-time", "value"),
        State("trend-y1-params", "value"),
        State("trend-y2-params", "value"),
    ],
)
def update_trend_chart(_, boiler_id, time_range, sd, st, ed, et, y1_params, y2_params):
    start_iso, end_iso = _parse_time_range(time_range, sd, st, ed, et)
    data = db.get_aggregated_range(boiler_id or "Boiler-1", start_iso, end_iso)
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
    [
        Output("efficiency-histogram", "figure"),
    ],
    [Input("history-query-btn", "n_clicks")],
    [
        State("history-boiler-select", "value"),
        State("history-time-range", "value"),
        State("history-start-date", "date"),
        State("history-start-time", "value"),
        State("history-end-date", "date"),
        State("history-end-time", "value"),
    ],
)
def update_efficiency_stats(_, boiler_id, time_range, sd, st, ed, et):
    start_iso, end_iso = _parse_time_range(time_range, sd, st, ed, et)
    data = db.get_aggregated_range(boiler_id or "Boiler-1", start_iso, end_iso)
    fig = go.Figure()
    if not data:
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return [fig]
    eff_vals = [d.get("efficiency") for d in data if d.get("efficiency") is not None]
    if eff_vals:
        fig.add_trace(go.Histogram(x=eff_vals, nbinsx=12, marker_color=ACCENT_GREEN, opacity=0.8))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=False, zeroline=False),
        yaxis=dict(tickfont=dict(color=TEXT_SECONDARY), showgrid=True, gridcolor=BORDER_COLOR, zeroline=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=100,
    )
    return [fig]


@app.callback(
    Output("corr-scatter-chart", "figure"),
    Output("corr-pearson-value", "children"),
    Output("corr-strength-label", "children"),
    [Input("corr-x-param", "value"), Input("corr-y-param", "value"), Input("history-query-btn", "n_clicks")],
    [
        State("history-boiler-select", "value"),
        State("history-time-range", "value"),
        State("history-start-date", "date"),
        State("history-start-time", "value"),
        State("history-end-date", "date"),
        State("history-end-time", "value"),
    ],
)
def update_correlation(x_param, y_param, _, boiler_id, time_range, sd, st, ed, et):
    start_iso, end_iso = _parse_time_range(time_range, sd, st, ed, et)
    data = db.get_aggregated_range(boiler_id or "Boiler-1", start_iso, end_iso)
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


if __name__ == "__main__":
    print("=" * 60)
    print("工业锅炉燃烧效率优化与排放监测平台启动中...")
    print("  Dash UI:    http://127.0.0.1:8050/")
    print("  API 接口:   POST http://127.0.0.1:8050/api/ingest")
    print("  启动模拟器: python data_simulator.py")
    print("=" * 60)
    app.run_server(debug=False, host="0.0.0.0", port=8050)
