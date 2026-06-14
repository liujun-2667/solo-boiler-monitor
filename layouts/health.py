import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go

from health_engine import TREND_PARAMS


DARK_BG = "#0B1A2B"
DARK_BG_CARD = "#112240"
DARK_BG_INPUT = "#1A2E4D"
ACCENT_CYAN = "#00D4FF"
ACCENT_GREEN = "#00FF88"
ACCENT_YELLOW = "#FFB800"
ACCENT_ORANGE = "#FFB800"
ACCENT_RED = "#FF4D6D"
ACCENT_BLUE = "#4D9BFF"
TEXT_PRIMARY = "#E6F1FF"
TEXT_SECONDARY = "#88A0C0"
BORDER_COLOR = "#1E3A5F"


SUBSYSTEM_INFO = [
    {"key": "combustion", "name": "燃烧系统", "icon": "🔥", "detail_key": "combustion"},
    {"key": "steam_water", "name": "汽水系统", "icon": "💧", "detail_key": "steam_water"},
    {"key": "emission", "name": "排放系统", "icon": "🏭", "detail_key": "emission"},
    {"key": "efficiency", "name": "整体效率", "icon": "⚡", "detail_key": "efficiency"},
]


TREND_PARAM_OPTIONS = [
    {"label": f"{cfg['name']} ({cfg['unit']})", "value": k}
    for k, cfg in TREND_PARAMS.items()
]

TREND_PARAM_COLORS = {
    "main_steam_temp": "#00D4FF",
    "exhaust_temp": "#FFB800",
    "nox": "#FF4D6D",
    "efficiency": "#00FF88",
}


def build_time_range_selector(prefix):
    return html.Div(
        [
            html.Div(
                "日期",
                style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"},
            ),
            dcc.DatePickerSingle(
                id=f"health-compare-{prefix}-date",
                date=datetime.now().date(),
                style={"backgroundColor": DARK_BG_INPUT, "color": TEXT_PRIMARY},
            ),
        ],
        style={"marginRight": "16px"},
    )


def build_time_selector(prefix):
    return html.Div(
        [
            html.Div(
                "时间范围",
                style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"},
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id=f"health-compare-{prefix}-start",
                        options=[
                            {"label": "00:00", "value": "00:00"},
                            {"label": "06:00", "value": "06:00"},
                            {"label": "08:00", "value": "08:00"},
                            {"label": "10:00", "value": "10:00"},
                            {"label": "12:00", "value": "12:00"},
                            {"label": "14:00", "value": "14:00"},
                            {"label": "16:00", "value": "16:00"},
                            {"label": "18:00", "value": "18:00"},
                            {"label": "20:00", "value": "20:00"},
                            {"label": "22:00", "value": "22:00"},
                        ],
                        value="08:00",
                        clearable=False,
                        style={
                            "backgroundColor": DARK_BG_INPUT,
                            "color": TEXT_PRIMARY,
                            "width": "100px",
                        },
                    ),
                    html.Span(" - ", style={"color": TEXT_SECONDARY, "margin": "0 4px"}),
                    dcc.Dropdown(
                        id=f"health-compare-{prefix}-end",
                        options=[
                            {"label": "06:00", "value": "06:00"},
                            {"label": "08:00", "value": "08:00"},
                            {"label": "10:00", "value": "10:00"},
                            {"label": "12:00", "value": "12:00"},
                            {"label": "14:00", "value": "14:00"},
                            {"label": "16:00", "value": "16:00"},
                            {"label": "18:00", "value": "18:00"},
                            {"label": "20:00", "value": "20:00"},
                            {"label": "22:00", "value": "22:00"},
                            {"label": "24:00", "value": "24:00"},
                        ],
                        value="12:00",
                        clearable=False,
                        style={
                            "backgroundColor": DARK_BG_INPUT,
                            "color": TEXT_PRIMARY,
                            "width": "100px",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        style={"marginRight": "16px"},
    )


DEFAULT_CARD_STYLE = {
    "backgroundColor": DARK_BG_CARD,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "16px",
}


def _make_section_title(text, color=ACCENT_CYAN):
    return html.Div(
        [
            html.Span(
                style={
                    "display": "inline-block",
                    "width": "3px",
                    "height": "16px",
                    "backgroundColor": color,
                    "marginRight": "8px",
                    "verticalAlign": "middle",
                }
            ),
            html.Span(
                text,
                style={
                    "color": TEXT_PRIMARY,
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "verticalAlign": "middle",
                },
            ),
        ],
        style={"marginBottom": "12px"},
    )


def _score_color(score):
    if score >= 80:
        return ACCENT_GREEN
    elif score >= 60:
        return ACCENT_YELLOW
    return ACCENT_RED


def _build_ring_figure(score, color):
    bg_color = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)"
    fig = go.Figure(data=[go.Pie(
        values=[score, max(0.1, 100 - score)],
        hole=0.72,
        sort=False,
        direction="clockwise",
        rotation=90,
        marker=dict(
            colors=[color, "rgba(255,255,255,0.04)"],
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        showlegend=False,
        hoverinfo="none",
        textinfo="none",
    )])
    fig.add_annotation(
        x=0.5, y=0.55,
        text=f"<b style='font-size:30px;font-family:Consolas,monospace;color:{color};'>{score:.0f}</b><span style='font-size:14px;color:{color};'>分</span>",
        showarrow=False,
        xref="paper", yref="paper",
        align="center",
    )
    fig.add_annotation(
        x=0.5, y=0.22,
        text="<span style='font-size:10px;color:#88A0C0;'>0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 100</span>",
        showarrow=False,
        xref="paper", yref="paper",
        align="center",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=2, r=2, t=2, b=2),
        height=170,
        width=170,
        showlegend=False,
    )
    return fig


def _build_health_ring_gauge(sub_key, name, icon, score=0):
    color = _score_color(score)
    fig = _build_ring_figure(score, color)
    gauge_id = f"health-gauge-{sub_key}"
    tooltip_id = f"health-tooltip-{sub_key}"
    tooltip_target = f"health-gauge-card-{sub_key}"
    return dbc.Col(
        html.Div(
            id=tooltip_target,
            children=[
                html.Div(
                    [
                        html.Span(icon, style={"fontSize": "18px", "marginRight": "6px"}),
                        html.Span(name, style={"color": TEXT_PRIMARY, "fontSize": "14px", "fontWeight": "600"}),
                    ],
                    style={"marginBottom": "4px", "textAlign": "center"},
                ),
                html.Div(
                    dcc.Graph(
                        id=gauge_id,
                        figure=fig,
                        config={"displayModeBar": False, "staticPlot": True},
                        style={"height": "170px", "width": "170px", "margin": "0 auto"},
                    ),
                    style={"display": "flex", "justifyContent": "center"},
                ),
                html.Div(
                    id=f"health-detail-store-{sub_key}",
                    style={"display": "none"},
                ),
                dbc.Tooltip(
                    id=tooltip_id,
                    target=tooltip_target,
                    placement="top",
                    trigger="hover focus",
                    style={
                        "backgroundColor": DARK_BG_CARD,
                        "border": f"1px solid {BORDER_COLOR}",
                        "color": TEXT_PRIMARY,
                        "fontSize": "12px",
                        "maxWidth": "280px",
                        "padding": "10px 14px",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 16px rgba(0,0,0,0.5)",
                    },
                ),
            ],
            style={
                **DEFAULT_CARD_STYLE,
                "padding": "12px",
                "position": "relative",
                "cursor": "pointer",
                "transition": "transform 0.2s ease, box-shadow 0.2s ease",
            },
        ),
        width=6,
        lg=3,
        style={"padding": "6px"},
    )


def build_health_gauges_section():
    gauges = []
    for info in SUBSYSTEM_INFO:
        gauges.append(_build_health_ring_gauge(info["key"], info["name"], info["icon"], 0))
    return html.Div(
        [
            _make_section_title("子系统健康度评分", ACCENT_GREEN),
            dbc.Row(gauges, style={"margin": "-6px"}),
            html.Div(
                id="health-overall-bar-container",
                children=[
                    html.Div(
                        [
                            html.Span("总健康度", style={"color": TEXT_PRIMARY, "fontSize": "14px", "fontWeight": "600", "marginRight": "12px"}),
                            html.Span(id="health-overall-score-text", children="--", style={"color": ACCENT_CYAN, "fontSize": "22px", "fontWeight": "700", "fontFamily": "Consolas, monospace"}),
                            html.Span(" / 100", style={"color": TEXT_SECONDARY, "fontSize": "13px"}),
                        ],
                        style={"marginBottom": "8px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                id="health-overall-bar",
                                style={
                                    "height": "8px",
                                    "width": "0%",
                                    "backgroundColor": ACCENT_GREEN,
                                    "borderRadius": "4px",
                                    "transition": "width 0.6s ease",
                                },
                            ),
                        ],
                        style={
                            "width": "100%",
                            "height": "8px",
                            "backgroundColor": DARK_BG_INPUT,
                            "borderRadius": "4px",
                            "overflow": "hidden",
                        },
                    ),
                ],
                style={"marginTop": "12px", "padding": "0 6px"},
            ),
        ],
        style={
            "backgroundColor": DARK_BG_CARD,
            "border": f"1px solid {BORDER_COLOR}",
            "borderRadius": "8px",
            "padding": "16px",
            "marginBottom": "16px",
        },
    )


def build_health_compare_section():
    return html.Div(
        [
            _make_section_title("时段对比", ACCENT_BLUE),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "时段A",
                                style={"color": ACCENT_BLUE, "fontSize": "14px", "fontWeight": "600", "marginBottom": "10px"},
                            ),
                            build_time_range_selector("a"),
                            build_time_selector("a"),
                        ],
                        style={"display": "flex", "flexWrap": "wrap", "alignItems": "flex-end", "paddingRight": "24px", "borderRight": f"1px solid {BORDER_COLOR}"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "时段B",
                                style={"color": ACCENT_ORANGE, "fontSize": "14px", "fontWeight": "600", "marginBottom": "10px"},
                            ),
                            build_time_range_selector("b"),
                            build_time_selector("b"),
                        ],
                        style={"display": "flex", "flexWrap": "wrap", "alignItems": "flex-end", "paddingLeft": "24px"},
                    ),
                    html.Div(
                        dbc.Button(
                            "生成对比",
                            id="health-compare-btn",
                            color="primary",
                            style={
                                "backgroundColor": ACCENT_CYAN,
                                "borderColor": ACCENT_CYAN,
                                "color": DARK_BG,
                                "fontWeight": "600",
                            },
                        ),
                        style={"alignSelf": "flex-end"},
                    ),
                ],
                style={"display": "flex", "flexWrap": "wrap", "alignItems": "flex-end", "marginBottom": "16px"},
            ),
            dcc.Graph(
                id="health-compare-chart",
                style={"height": "300px"},
                config={"displayModeBar": True, "displaylogo": False},
            ),
        ],
        style={
            **DEFAULT_CARD_STYLE,
            "marginBottom": "16px",
        },
    )


def build_trend_prediction_section():
    return html.Div(
        [
            _make_section_title("趋势预测分析", ACCENT_CYAN),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "选择参数",
                                style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"},
                            ),
                            html.Div(
                                [
                                    dbc.Checklist(
                                        options=TREND_PARAM_OPTIONS,
                                        value=["main_steam_temp"],
                                        id="health-trend-param-checklist",
                                        inline=True,
                                        switch=True,
                                        style={"color": TEXT_PRIMARY},
                                    ),
                                ],
                                style={"display": "flex", "flexWrap": "wrap", "gap": "16px"},
                            ),
                        ],
                        style={"flex": 1},
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start", "marginBottom": "12px"},
            ),
            dcc.Graph(
                id="health-trend-chart",
                style={"height": "400px"},
                config={"displayModeBar": True, "displaylogo": False},
            ),
        ],
        style={
            **DEFAULT_CARD_STYLE,
            "marginBottom": "16px",
        },
    )


def build_predictive_alerts_section():
    return html.Div(
        [
            _make_section_title("预测性告警", ACCENT_RED),
            html.Div(
                [
                    html.Span(
                        "只看未确认",
                        style={"color": TEXT_SECONDARY, "fontSize": "13px", "marginRight": "8px"},
                    ),
                    dbc.Checklist(
                        options=[{"label": "", "value": "only_unconfirmed"}],
                        value=[],
                        id="health-alerts-only-unconfirmed",
                        switch=True,
                        style={"display": "inline-block"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": "12px"},
            ),
            html.Div(
                id="health-predictive-alerts-list",
                children=[
                    html.Div(
                        "暂无预测性告警",
                        style={"color": TEXT_SECONDARY, "textAlign": "center", "padding": "24px", "fontSize": "13px"},
                    ),
                ],
                style={"maxHeight": "320px", "overflowY": "auto"},
            ),
        ],
        style={
            **DEFAULT_CARD_STYLE,
            "marginBottom": "16px",
        },
    )


def build_predictive_alert_card(alert):
    is_confirmed = alert.get("confirmed_at") is not None
    card_style = {
        "backgroundColor": "#1a1a1a" if is_confirmed else DARK_BG_INPUT,
        "border": f"1px solid {BORDER_COLOR}",
        "borderRadius": "8px",
        "padding": "12px",
        "marginBottom": "8px",
        "opacity": 0.7 if is_confirmed else 1,
    }
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "⚠️" if not is_confirmed else "✅",
                                style={"fontSize": "16px", "marginRight": "8px"},
                            ),
                            html.Span(
                                alert.get("param_name", "未知参数"),
                                style={"color": ACCENT_YELLOW if not is_confirmed else TEXT_SECONDARY, "fontSize": "14px", "fontWeight": "600"},
                            ),
                            html.Span(
                                " · 已确认" if is_confirmed else "",
                                style={"color": TEXT_SECONDARY, "fontSize": "12px"},
                            ),
                        ],
                        style={"marginBottom": "6px"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"当前值: {alert.get('current_value', 0):.2f} | 预测峰值: {alert.get('predicted_peak', 0):.2f} | 阈值: {alert.get('threshold_value', 0):.2f}",
                                style={"color": TEXT_SECONDARY, "fontSize": "12px"},
                            ),
                        ],
                        style={"marginBottom": "4px"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"预计 {alert.get('minutes_to_exceed', 0):.0f} 分钟后超出阈值",
                                style={"color": ACCENT_RED if not is_confirmed else TEXT_SECONDARY, "fontSize": "12px"},
                            ),
                        ],
                    ),
                ],
                style={"flex": 1},
            ),
            html.Div(
                [
                    dbc.Button(
                        "确认",
                        id=f"alert-confirm-btn-{alert['id']}",
                        size="sm",
                        color="secondary",
                        style={
                            "marginRight": "8px",
                            "fontSize": "11px",
                            "padding": "4px 12px",
                        },
                    ),
                    dbc.Button(
                        "静默30分钟",
                        id=f"alert-mute-btn-{alert['id']}",
                        size="sm",
                        color="dark",
                        style={
                            "fontSize": "11px",
                            "padding": "4px 12px",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        style={**card_style, "display": "flex", "justifyContent": "space-between", "alignItems": "center"},
    )


def build_health_layout():
    return html.Div(
        [
            dcc.Store(id="health-trend-data-store"),
            dcc.Interval(id="health-alerts-update-trigger", interval=10000, n_intervals=0),
            html.Div(
                "工业锅炉 · 设备健康度与趋势预测",
                style={
                    "color": TEXT_PRIMARY,
                    "fontSize": "20px",
                    "fontWeight": "700",
                    "marginBottom": "16px",
                    "paddingLeft": "4px",
                },
            ),
            build_health_gauges_section(),
            build_health_compare_section(),
            build_trend_prediction_section(),
            build_predictive_alerts_section(),
            dcc.Interval(
                id="health-interval",
                interval=30000,
                n_intervals=0,
            ),
        ],
        style={
            "backgroundColor": DARK_BG,
            "minHeight": "100vh",
            "padding": "20px 24px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
    )


layout = build_health_layout()
