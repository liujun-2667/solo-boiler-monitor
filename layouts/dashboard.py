import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

from database import DEFAULT_POINT_LIMITS, DEFAULT_EMISSION_LIMITS


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


BOILER_OPTIONS = [
    {"label": "Boiler-1", "value": "Boiler-1"},
    {"label": "Boiler-2", "value": "Boiler-2"},
    {"label": "Boiler-3", "value": "Boiler-3"},
]


KEY_PARAMS = [
    {"key": "main_steam_temp", "name": "主蒸汽温度", "unit": "℃", "warning_low": 510, "warning_high": 560, "alarm_low": 480, "alarm_high": 575},
    {"key": "main_steam_press", "name": "主蒸汽压力", "unit": "MPa", "warning_low": 15.0, "warning_high": 18.0, "alarm_low": 13.0, "alarm_high": 19.5},
    {"key": "main_steam_flow", "name": "主蒸汽流量", "unit": "t/h", "warning_low": 400, "warning_high": 900, "alarm_low": 200, "alarm_high": 1100},
    {"key": "o2", "name": "氧量", "unit": "%", "warning_low": 2.5, "warning_high": 6.0, "alarm_low": 1.5, "alarm_high": 8.0},
    {"key": "exhaust_temp", "name": "排烟温度", "unit": "℃", "warning_low": 100, "warning_high": 150, "alarm_low": 80, "alarm_high": 180},
    {"key": "coal_feed", "name": "给煤量", "unit": "t/h", "warning_low": 40, "warning_high": 130, "alarm_low": 20, "alarm_high": 170},
]


EMISSION_PARAMS = [
    {"key": "nox", "name": "氮氧化物 NOx", "unit": "mg/m³"},
    {"key": "so2", "name": "二氧化硫 SO₂", "unit": "mg/m³"},
    {"key": "co", "name": "一氧化碳 CO", "unit": "ppm"},
    {"key": "dust", "name": "粉尘", "unit": "mg/m³"},
]


URGENCY_COLORS = {
    "高": ACCENT_RED,
    "中": ACCENT_YELLOW,
    "低": ACCENT_BLUE,
}


DEFAULT_CARD_STYLE = {
    "backgroundColor": DARK_BG_CARD,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "16px",
}


def _get_status_color(value, param_cfg):
    if value is None:
        return TEXT_SECONDARY
    if value < param_cfg["alarm_low"] or value > param_cfg["alarm_high"]:
        return ACCENT_RED
    if value < param_cfg["warning_low"] or value > param_cfg["warning_high"]:
        return ACCENT_YELLOW
    return ACCENT_GREEN


def _get_status_bar_color(value, param_cfg):
    if value is None:
        return TEXT_SECONDARY
    if value < param_cfg["alarm_low"] or value > param_cfg["alarm_high"]:
        return ACCENT_RED
    if value < param_cfg["warning_low"] or value > param_cfg["warning_high"]:
        return ACCENT_YELLOW
    return ACCENT_GREEN


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


def build_mini_sparkline(data_series, color=ACCENT_CYAN):
    if data_series is None or len(data_series) == 0:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False, showgrid=False),
            yaxis=dict(visible=False, showgrid=False),
            height=40,
        )
        return fig
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(len(data_series))),
            y=data_series,
            mode="lines",
            line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        height=40,
    )
    return fig


def build_param_card(param_cfg):
    key = param_cfg["key"]
    return dbc.Col(
        html.Div(
            [
                html.Div(
                    param_cfg["name"],
                    style={
                        "color": TEXT_SECONDARY,
                        "fontSize": "13px",
                        "marginBottom": "4px",
                    },
                ),
                html.Div(
                    [
                        html.Span(
                            id=f"param-value-{key}",
                            children="--",
                            style={
                                "color": TEXT_PRIMARY,
                                "fontSize": "32px",
                                "fontWeight": "700",
                                "fontFamily": "Consolas, monospace",
                            },
                        ),
                        html.Span(
                            param_cfg["unit"],
                            style={
                                "color": TEXT_SECONDARY,
                                "fontSize": "14px",
                                "marginLeft": "6px",
                            },
                        ),
                    ],
                    style={"marginBottom": "6px"},
                ),
                html.Div(
                    id=f"param-status-bar-{key}",
                    style={
                        "height": "4px",
                        "width": "100%",
                        "backgroundColor": ACCENT_GREEN,
                        "borderRadius": "2px",
                        "marginBottom": "8px",
                    },
                ),
                dcc.Graph(
                    id=f"param-sparkline-{key}",
                    figure=build_mini_sparkline(None),
                    config={"displayModeBar": False},
                    style={"height": "40px"},
                ),
            ],
            style=DEFAULT_CARD_STYLE,
        ),
        width=4,
        lg=2,
        style={"padding": "6px"},
    )


def build_key_params_section():
    return html.Div(
        [
            _make_section_title("关键运行参数", ACCENT_CYAN),
            dbc.Row(
                [build_param_card(p) for p in KEY_PARAMS],
                style={"margin": "-6px"},
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


def build_efficiency_gauge():
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=90,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [80, 100],
                "tickvals": [80, 85, 90, 95, 100],
                "ticktext": ["80", "85", "90", "95", "100"],
                "tickfont": {"color": TEXT_SECONDARY, "size": 11},
                "ticks": "outside",
            },
            "bar": {"color": ACCENT_GREEN, "thickness": 0.35},
            "steps": [
                {"range": [80, 85], "color": "rgba(255, 77, 109, 0.3)"},
                {"range": [85, 90], "color": "rgba(255, 184, 0, 0.3)"},
                {"range": [90, 97], "color": "rgba(0, 255, 136, 0.3)"},
                {"range": [97, 100], "color": "rgba(255, 184, 0, 0.3)"},
            ],
            "threshold": {
                "line": {"color": ACCENT_CYAN, "width": 2},
                "thickness": 0.8,
                "value": 90,
            },
        },
        number={
            "font": {"color": ACCENT_GREEN, "size": 42, "family": "Consolas, monospace"},
            "suffix": "%",
            "valueformat": ".1f",
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=0),
        height=260,
    )
    return fig


def build_heat_loss_chart():
    fig = go.Figure()
    losses = [
        {"name": "q2 排烟热损失", "color": ACCENT_RED, "value": 6.5},
        {"name": "q3 气体未完全燃烧", "color": ACCENT_ORANGE, "value": 0.8},
        {"name": "q4 固体未完全燃烧", "color": ACCENT_YELLOW, "value": 2.5},
        {"name": "q5 散热损失", "color": ACCENT_CYAN, "value": 1.6},
    ]
    for loss in losses:
        fig.add_trace(go.Bar(
            y=[loss["name"]],
            x=[loss["value"]],
            orientation="h",
            marker=dict(color=loss["color"]),
            text=[f"{loss['value']:.2f}%"],
            textposition="outside",
            textfont=dict(color=TEXT_PRIMARY, size=13),
            width=0.55,
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=30, t=10, b=0),
        xaxis=dict(
            range=[0, 12],
            tickfont=dict(color=TEXT_SECONDARY, size=11),
            showgrid=True,
            gridcolor=BORDER_COLOR,
            gridwidth=1,
            zeroline=False,
            title=dict(text="热损失 (%)", font=dict(color=TEXT_SECONDARY, size=11)),
        ),
        yaxis=dict(
            tickfont=dict(color=TEXT_PRIMARY, size=12),
            showgrid=False,
            zeroline=False,
        ),
        showlegend=False,
        height=260,
        bargap=0.3,
    )
    return fig


def build_efficiency_section():
    return html.Div(
        [
            _make_section_title("燃烧效率与热损失分析", ACCENT_GREEN),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    "燃烧效率",
                                    style={
                                        "color": TEXT_SECONDARY,
                                        "fontSize": "13px",
                                        "textAlign": "center",
                                        "marginBottom": "-10px",
                                    },
                                ),
                                dcc.Graph(
                                    id="efficiency-gauge",
                                    figure=build_efficiency_gauge(),
                                    config={"displayModeBar": False},
                                ),
                            ],
                            style={
                                **DEFAULT_CARD_STYLE,
                                "padding": "8px 16px 0px 16px",
                            },
                        ),
                        width=12,
                        lg=5,
                        style={"padding": "6px"},
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "8px",
                                                "height": "8px",
                                                "backgroundColor": ACCENT_RED,
                                                "borderRadius": "50%",
                                                "marginRight": "4px",
                                            },
                                        ),
                                        html.Span("q2排烟", style={"color": TEXT_SECONDARY, "fontSize": "11px", "marginRight": "12px"}),
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "8px",
                                                "height": "8px",
                                                "backgroundColor": ACCENT_ORANGE,
                                                "borderRadius": "50%",
                                                "marginRight": "4px",
                                            },
                                        ),
                                        html.Span("q3气体", style={"color": TEXT_SECONDARY, "fontSize": "11px", "marginRight": "12px"}),
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "8px",
                                                "height": "8px",
                                                "backgroundColor": ACCENT_YELLOW,
                                                "borderRadius": "50%",
                                                "marginRight": "4px",
                                            },
                                        ),
                                        html.Span("q4固体", style={"color": TEXT_SECONDARY, "fontSize": "11px", "marginRight": "12px"}),
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "8px",
                                                "height": "8px",
                                                "backgroundColor": ACCENT_CYAN,
                                                "borderRadius": "50%",
                                                "marginRight": "4px",
                                            },
                                        ),
                                        html.Span("q5散热", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                                    ],
                                    style={"marginBottom": "4px"},
                                ),
                                dcc.Graph(
                                    id="heat-loss-chart",
                                    figure=build_heat_loss_chart(),
                                    config={"displayModeBar": False},
                                ),
                            ],
                            style=DEFAULT_CARD_STYLE,
                        ),
                        width=12,
                        lg=7,
                        style={"padding": "6px"},
                    ),
                ],
                style={"margin": "-6px"},
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


def build_emission_gauge(param_cfg, current_value=0, hourly_mean=0, limit=100):
    pct = min(100.0, (current_value / max(1, limit)) * 100) if limit > 0 else 0
    if pct >= 100:
        bar_color = ACCENT_RED
    elif pct >= 80:
        bar_color = ACCENT_YELLOW
    else:
        bar_color = ACCENT_GREEN
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_value,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [0, limit * 1.5],
                "tickvals": [0, limit * 0.5, limit, limit * 1.5],
                "ticktext": ["0", f"{int(limit*0.5)}", f"{int(limit)}", f"{int(limit*1.5)}"],
                "tickfont": {"color": TEXT_SECONDARY, "size": 9},
                "ticks": "outside",
            },
            "bar": {"color": bar_color, "thickness": 0.4},
            "steps": [
                {"range": [0, limit * 0.8], "color": "rgba(0, 255, 136, 0.2)"},
                {"range": [limit * 0.8, limit], "color": "rgba(255, 184, 0, 0.25)"},
                {"range": [limit, limit * 1.5], "color": "rgba(255, 77, 109, 0.3)"},
            ],
            "threshold": {
                "line": {"color": ACCENT_RED, "width": 2},
                "thickness": 0.9,
                "value": limit,
            },
        },
        number={
            "font": {"color": TEXT_PRIMARY, "size": 22, "family": "Consolas, monospace"},
            "valueformat": ".1f",
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=5, r=5, t=5, b=0),
        height=150,
    )
    return fig, pct


def build_emission_item(param_cfg):
    key = param_cfg["key"]
    limits = DEFAULT_EMISSION_LIMITS.get(key, {"hourly": 100, "peak": 200, "unit": param_cfg["unit"]})
    fig, _ = build_emission_gauge(param_cfg, 0, 0, limits.get("hourly", 100))
    return dbc.Col(
        html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            param_cfg["name"],
                            style={
                                "color": TEXT_PRIMARY,
                                "fontSize": "12px",
                                "fontWeight": "500",
                            },
                        ),
                        html.Span(
                            f"限值 {limits.get('hourly', '--')}{limits.get('unit', '')}",
                            style={
                                "color": TEXT_SECONDARY,
                                "fontSize": "11px",
                                "marginLeft": "auto",
                            },
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginBottom": "2px"},
                ),
                dcc.Graph(
                    id=f"emission-gauge-{key}",
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "150px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("当前值 ", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                                html.Span(
                                    id=f"emission-current-{key}",
                                    children="--",
                                    style={"color": TEXT_PRIMARY, "fontSize": "13px", "fontWeight": "600", "fontFamily": "Consolas, monospace"},
                                ),
                                html.Span(f" {param_cfg['unit']}", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                            ],
                        ),
                        html.Div(
                            [
                                html.Span("小时均 ", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                                html.Span(
                                    id=f"emission-hourly-{key}",
                                    children="--",
                                    style={"color": ACCENT_CYAN, "fontSize": "13px", "fontWeight": "600", "fontFamily": "Consolas, monospace"},
                                ),
                                html.Span(f" {param_cfg['unit']}", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                            ],
                        ),
                        html.Div(
                            [
                                html.Span("限值占比 ", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                                html.Span(
                                    id=f"emission-pct-{key}",
                                    children="--",
                                    style={"color": ACCENT_GREEN, "fontSize": "13px", "fontWeight": "600", "fontFamily": "Consolas, monospace"},
                                ),
                                html.Span("%", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                            ],
                        ),
                    ],
                    style={"display": "flex", "justifyContent": "space-between", "gap": "8px"},
                ),
                html.Div(
                    [
                        html.Div(
                            id=f"emission-limit-bar-{key}",
                            style={
                                "height": "4px",
                                "width": "0%",
                                "backgroundColor": ACCENT_GREEN,
                                "borderRadius": "2px",
                                "transition": "width 0.5s",
                            },
                        ),
                    ],
                    style={
                        "width": "100%",
                        "backgroundColor": DARK_BG_INPUT,
                        "borderRadius": "2px",
                        "marginTop": "6px",
                        "height": "4px",
                        "overflow": "hidden",
                    },
                ),
            ],
            style={
                **DEFAULT_CARD_STYLE,
                "padding": "12px",
            },
        ),
        width=6,
        lg=3,
        style={"padding": "6px"},
    )


def build_emission_section():
    return html.Div(
        [
            _make_section_title("污染物排放监控", ACCENT_ORANGE),
            dbc.Row(
                [build_emission_item(p) for p in EMISSION_PARAMS],
                style={"margin": "-6px"},
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


def build_suggestion_card(suggestion, index):
    urgency = suggestion.get("urgency", "低")
    color = URGENCY_COLORS.get(urgency, ACCENT_BLUE)
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        urgency,
                        style={
                            "display": "inline-block",
                            "padding": "2px 10px",
                            "backgroundColor": f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
                            "color": color,
                            "fontSize": "11px",
                            "fontWeight": "600",
                            "borderRadius": "3px",
                            "border": f"1px solid {color}",
                        },
                    ),
                    html.Span(
                        f"#{index + 1}",
                        style={
                            "color": TEXT_SECONDARY,
                            "fontSize": "11px",
                            "marginLeft": "8px",
                            "fontFamily": "Consolas, monospace",
                        },
                    ),
                ],
                style={"marginBottom": "8px"},
            ),
            html.Div(
                [
                    html.Span("诊断：", style={"color": TEXT_SECONDARY, "fontSize": "12px"}),
                    html.Span(
                        suggestion.get("diagnosis", "--"),
                        style={"color": TEXT_PRIMARY, "fontSize": "12px"},
                    ),
                ],
                style={"marginBottom": "6px"},
            ),
            html.Div(
                [
                    html.Span("建议：", style={"color": ACCENT_CYAN, "fontSize": "12px", "fontWeight": "500"}),
                    html.Span(
                        suggestion.get("action", "--"),
                        style={"color": TEXT_PRIMARY, "fontSize": "12px"},
                    ),
                ],
                style={"marginBottom": "6px"},
            ),
            html.Div(
                [
                    html.Span("预期：", style={"color": ACCENT_GREEN, "fontSize": "12px", "fontWeight": "500"}),
                    html.Span(
                        suggestion.get("expected_effect", "--"),
                        style={"color": TEXT_SECONDARY, "fontSize": "12px"},
                    ),
                ],
            ),
        ],
        style={
            "backgroundColor": DARK_BG_INPUT,
            "border": f"1px solid {BORDER_COLOR}",
            "borderLeft": f"3px solid {color}",
            "borderRadius": "6px",
            "padding": "12px",
            "marginBottom": "10px",
        },
    )


def build_suggestions_section():
    placeholder_cards = []
    for i in range(3):
        placeholder = {
            "urgency": "低",
            "diagnosis": "系统运行正常，待检测异常...",
            "action": "持续监测运行状态",
            "expected_effect": "保持当前高效运行",
        }
        placeholder_cards.append(build_suggestion_card(placeholder, i))
    return html.Div(
        [
            _make_section_title("智能调优建议", ACCENT_RED),
            html.Div(
                id="suggestions-container",
                children=placeholder_cards,
                style={
                    "maxHeight": "380px",
                    "overflowY": "auto",
                    "paddingRight": "4px",
                },
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


def build_top_navbar():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "🔥",
                        style={
                            "fontSize": "24px",
                            "marginRight": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                "工业锅炉实时监控中心",
                                style={
                                    "color": TEXT_PRIMARY,
                                    "fontSize": "18px",
                                    "fontWeight": "700",
                                    "lineHeight": "1.2",
                                },
                            ),
                            html.Div(
                                "Industrial Boiler Real-time Monitoring",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "11px",
                                    "lineHeight": "1.2",
                                },
                            ),
                        ],
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "锅炉选择",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "11px",
                                    "marginBottom": "4px",
                                },
                            ),
                            dcc.Dropdown(
                                id="dashboard-boiler-select",
                                options=BOILER_OPTIONS,
                                value="Boiler-1",
                                clearable=False,
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "width": "140px",
                                },
                            ),
                        ],
                        style={"marginRight": "24px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "系统时间",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "11px",
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                id="dashboard-current-time",
                                children="--:--:--",
                                style={
                                    "color": ACCENT_CYAN,
                                    "fontSize": "22px",
                                    "fontWeight": "700",
                                    "fontFamily": "Consolas, monospace",
                                    "backgroundColor": DARK_BG_INPUT,
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "borderRadius": "4px",
                                    "padding": "4px 14px",
                                },
                            ),
                        ],
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-end"},
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "backgroundColor": DARK_BG_CARD,
            "border": f"1px solid {BORDER_COLOR}",
            "borderRadius": "8px",
            "padding": "14px 24px",
            "marginBottom": "16px",
        },
    )


POLLUTANT_NAMES = {
    "nox": "氮氧化物 NOx",
    "so2": "二氧化硫 SO₂",
    "co": "一氧化碳 CO",
    "dust": "粉尘",
}

POLLUTANT_UNITS = {
    "nox": "mg/m³",
    "so2": "mg/m³",
    "co": "ppm",
    "dust": "mg/m³",
}


def build_alert_toast_card(alert_data, index=0, is_new=True, is_exiting=False):
    alert_id = alert_data.get("id", 0)
    pollutant = alert_data.get("pollutant", "")
    pollutant_name = POLLUTANT_NAMES.get(pollutant, pollutant)
    unit = POLLUTANT_UNITS.get(pollutant, "")
    current_val = alert_data.get("value", 0)
    limit_val = alert_data.get("limit_val", 1)
    exceed_pct = max(0, ((current_val - limit_val) / max(1, limit_val)) * 100)
    timestamp = alert_data.get("timestamp", "")
    try:
        from datetime import datetime
        ts = datetime.fromisoformat(timestamp)
        time_str = ts.strftime("%H:%M:%S")
    except Exception:
        time_str = timestamp[11:19] if len(timestamp) > 19 else timestamp

    if is_exiting:
        anim_class = "alert-toast-exit"
    elif is_new:
        anim_class = "alert-toast-enter"
    else:
        anim_class = "alert-toast-stay"

    return html.Div(
        id={"type": "alert-toast", "index": alert_id},
        className=anim_class,
        children=[
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "⚠",
                                style={
                                    "color": "#fff",
                                    "fontSize": "18px",
                                    "marginRight": "8px",
                                },
                            ),
                            html.Span(
                                "排放超标告警",
                                style={
                                    "color": "#fff",
                                    "fontSize": "14px",
                                    "fontWeight": "700",
                                },
                            ),
                            html.Span(
                                time_str,
                                style={
                                    "color": "rgba(255,255,255,0.75)",
                                    "fontSize": "12px",
                                    "marginLeft": "auto",
                                    "fontFamily": "Consolas, monospace",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginBottom": "8px",
                        },
                    ),
                    html.Div(
                        [
                            html.Span(
                                pollutant_name,
                                style={
                                    "color": "#fff",
                                    "fontSize": "13px",
                                    "fontWeight": "600",
                                },
                            ),
                            html.Span(
                                f"  当前值: {current_val:.1f}{unit}",
                                style={
                                    "color": "#fff",
                                    "fontSize": "12px",
                                    "fontFamily": "Consolas, monospace",
                                },
                            ),
                            html.Span(
                                f"  限值: {limit_val:.1f}{unit}",
                                style={
                                    "color": "rgba(255,255,255,0.8)",
                                    "fontSize": "12px",
                                    "fontFamily": "Consolas, monospace",
                                },
                            ),
                        ],
                        style={"marginBottom": "6px"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                "超标幅度: ",
                                style={
                                    "color": "rgba(255,255,255,0.8)",
                                    "fontSize": "12px",
                                },
                            ),
                            html.Span(
                                f"+{exceed_pct:.1f}%",
                                style={
                                    "color": "#fff",
                                    "fontSize": "14px",
                                    "fontWeight": "700",
                                    "fontFamily": "Consolas, monospace",
                                },
                            ),
                        ],
                    ),
                ],
                style={
                    "padding": "12px 16px",
                    "backgroundColor": "rgba(255, 77, 109, 0.95)",
                    "border": "1px solid #FF4D6D",
                    "borderLeft": "4px solid #fff",
                    "borderRadius": "6px",
                    "boxShadow": "0 4px 16px rgba(255, 77, 109, 0.4)",
                    "width": "320px",
                    "color": "#fff",
                },
            ),
        ],
        style={},
    )


def build_alerts_container():
    return html.Div(
        id="alerts-toast-container",
        children=[],
        style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "zIndex": 9999,
            "display": "flex",
            "flexDirection": "column",
            "gap": "10px",
            "pointerEvents": "none",
            "width": "340px",
        },
    )


def build_alert_history_row(alert_data):
    pollutant = alert_data.get("pollutant", "")
    pollutant_name = POLLUTANT_NAMES.get(pollutant, pollutant)
    unit = POLLUTANT_UNITS.get(pollutant, "")
    peak_val = alert_data.get("peak_value", alert_data.get("value", 0))
    duration_sec = alert_data.get("duration", 0) or 0
    if duration_sec >= 3600:
        duration_str = f"{int(duration_sec // 3600)}h {int((duration_sec % 3600) // 60)}m"
    elif duration_sec >= 60:
        duration_str = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s"
    else:
        duration_str = f"{int(duration_sec)}s"

    timestamp = alert_data.get("timestamp", "")
    try:
        from datetime import datetime
        ts = datetime.fromisoformat(timestamp)
        time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        time_str = timestamp[:19]

    status = alert_data.get("status", "active")
    status_color = ACCENT_RED if status == "active" else ACCENT_GREEN
    status_text = "持续中" if status == "active" else "已结束"

    return html.Tr(
        [
            html.Td(time_str, style={"color": TEXT_SECONDARY, "padding": "8px 12px", "borderBottom": f"1px solid {BORDER_COLOR}", "fontFamily": "Consolas, monospace", "fontSize": "12px"}),
            html.Td(pollutant_name, style={"color": TEXT_PRIMARY, "padding": "8px 12px", "borderBottom": f"1px solid {BORDER_COLOR}", "fontSize": "12px"}),
            html.Td(duration_str, style={"color": TEXT_PRIMARY, "padding": "8px 12px", "borderBottom": f"1px solid {BORDER_COLOR}", "fontSize": "12px", "fontFamily": "Consolas, monospace"}),
            html.Td(
                [
                    html.Span(f"{peak_val:.1f}", style={"color": ACCENT_RED, "fontFamily": "Consolas, monospace", "fontSize": "12px", "fontWeight": "600"}),
                    html.Span(f" {unit}", style={"color": TEXT_SECONDARY, "fontSize": "11px"}),
                ],
                style={"padding": "8px 12px", "borderBottom": f"1px solid {BORDER_COLOR}"},
            ),
            html.Td(
                html.Span(
                    status_text,
                    style={
                        "color": status_color,
                        "fontSize": "11px",
                        "padding": "2px 8px",
                        "borderRadius": "3px",
                        "backgroundColor": f"rgba({int(status_color[1:3],16)}, {int(status_color[3:5],16)}, {int(status_color[5:7],16)}, 0.15)",
                    },
                ),
                style={"padding": "8px 12px", "borderBottom": f"1px solid {BORDER_COLOR}"},
            ),
        ]
    )


def build_alert_history_panel():
    return html.Div(
        [
            html.Div(
                id="alert-history-header",
                children=[
                    html.Div(
                        [
                            html.Span(
                                "📋",
                                style={"fontSize": "16px", "marginRight": "8px"},
                            ),
                            html.Span(
                                "告警记录",
                                style={
                                    "color": TEXT_PRIMARY,
                                    "fontSize": "14px",
                                    "fontWeight": "600",
                                },
                            ),
                            html.Span(
                                id="alert-history-count",
                                children="(0条)",
                                style={
                                    "color": ACCENT_RED,
                                    "fontSize": "13px",
                                    "fontWeight": "600",
                                    "marginLeft": "6px",
                                },
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    html.Span(
                        id="alert-history-chevron",
                        children="▼",
                        style={
                            "color": TEXT_SECONDARY,
                            "fontSize": "12px",
                            "transition": "transform 0.3s",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "10px 20px",
                    "cursor": "pointer",
                    "backgroundColor": DARK_BG_CARD,
                    "border": f"1px solid {BORDER_COLOR}",
                    "borderRadius": "8px 8px 0 0",
                    "userSelect": "none",
                },
            ),
            html.Div(
                id="alert-history-body",
                children=[
                    html.Div(
                        [
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("时间", style={"color": TEXT_PRIMARY, "padding": "10px 12px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "left", "fontSize": "12px", "fontWeight": "600"}),
                                                html.Th("超标指标", style={"color": TEXT_PRIMARY, "padding": "10px 12px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "left", "fontSize": "12px", "fontWeight": "600"}),
                                                html.Th("持续时长", style={"color": TEXT_PRIMARY, "padding": "10px 12px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "left", "fontSize": "12px", "fontWeight": "600"}),
                                                html.Th("峰值", style={"color": TEXT_PRIMARY, "padding": "10px 12px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "left", "fontSize": "12px", "fontWeight": "600"}),
                                                html.Th("状态", style={"color": TEXT_PRIMARY, "padding": "10px 12px", "borderBottom": f"2px solid {ACCENT_CYAN}", "textAlign": "left", "fontSize": "12px", "fontWeight": "600"}),
                                            ]
                                        )
                                    ),
                                    html.Tbody(
                                        id="alert-history-tbody",
                                        children=[
                                            html.Tr(
                                                html.Td(
                                                    "暂无告警记录",
                                                    colSpan=5,
                                                    style={
                                                        "color": TEXT_SECONDARY,
                                                        "padding": "20px",
                                                        "textAlign": "center",
                                                        "fontSize": "13px",
                                                    },
                                                )
                                            )
                                        ],
                                    ),
                                ],
                                style={"width": "100%", "borderCollapse": "collapse"},
                            ),
                        ],
                        style={
                            "maxHeight": "320px",
                            "overflowY": "auto",
                        },
                    ),
                ],
                style={
                    "backgroundColor": DARK_BG_CARD,
                    "border": f"1px solid {BORDER_COLOR}",
                    "borderTop": "none",
                    "borderRadius": "0 0 8px 8px",
                    "padding": "0",
                    "display": "none",
                },
            ),
        ],
        style={
            "position": "fixed",
            "bottom": "0",
            "left": "0",
            "right": "0",
            "zIndex": 9997,
            "padding": "0 20px",
        },
    )


def build_dashboard_layout():
    return html.Div(
        [
            build_alerts_container(),
            build_top_navbar(),
            build_key_params_section(),
            build_efficiency_section(),
            dbc.Row(
                [
                    dbc.Col(
                        build_emission_section(),
                        width=12,
                        lg=7,
                        style={"padding": "0 8px 0 0"},
                    ),
                    dbc.Col(
                        build_suggestions_section(),
                        width=12,
                        lg=5,
                        style={"padding": "0 0 0 8px"},
                    ),
                ],
                style={"margin": "0"},
            ),
            html.Div(style={"height": "80px"}),
            build_alert_history_panel(),
            dcc.Interval(
                id="dashboard-interval",
                interval=3000,
                n_intervals=0,
            ),
            dcc.Store(id="dashboard-latest-data", data=None),
            dcc.Store(id="dashboard-history-data", data=None),
            dcc.Store(id="dashboard-suggestions", data=None),
            dcc.Store(id="alert-master-store", data=None),
            dcc.Store(id="active-alert-ids-store", data=[]),
            dcc.Store(id="alert-display-times-store", data={}),
            dcc.Store(id="alert-history-collapsed", data=True),
        ],
        style={
            "backgroundColor": DARK_BG,
            "minHeight": "100vh",
            "padding": "20px 24px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
    )


layout = build_dashboard_layout()
