import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import dcc, html

from database import DEFAULT_POINT_LIMITS


DARK_BG = "#0B1A2B"
DARK_BG_CARD = "#112240"
DARK_BG_INPUT = "#1A2E4D"
ACCENT_CYAN = "#00D4FF"
ACCENT_GREEN = "#00FF88"
ACCENT_ORANGE = "#FFB800"
ACCENT_RED = "#FF4D6D"
TEXT_PRIMARY = "#E6F1FF"
TEXT_SECONDARY = "#88A0C0"
BORDER_COLOR = "#1E3A5F"


POINT_OPTIONS = [
    {"label": f"{v['name']} ({v['unit']})", "value": k}
    for k, v in DEFAULT_POINT_LIMITS.items()
]


BOILER_OPTIONS = [
    {"label": "Boiler-1", "value": "Boiler-1"},
    {"label": "Boiler-2", "value": "Boiler-2"},
    {"label": "Boiler-3", "value": "Boiler-3"},
]


TIME_RANGE_OPTIONS = [
    {"label": "最近1小时", "value": "1h"},
    {"label": "最近6小时", "value": "6h"},
    {"label": "最近24小时", "value": "24h"},
    {"label": "最近7天", "value": "7d"},
    {"label": "自定义", "value": "custom"},
]


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


def _make_stat_card(card_id, title, value, subtitle="", color=ACCENT_CYAN, extra=None):
    children = [
        html.Div(
            title,
            style={
                "color": TEXT_SECONDARY,
                "fontSize": "12px",
                "marginBottom": "8px",
            },
        ),
        html.Div(
            value,
            id=f"stat-value-{card_id}",
            style={
                "color": color,
                "fontSize": "28px",
                "fontWeight": "700",
                "fontFamily": "Consolas, monospace",
            },
        ),
    ]
    if subtitle:
        children.append(
            html.Div(
                subtitle,
                id=f"stat-sub-{card_id}",
                style={
                    "color": TEXT_SECONDARY,
                    "fontSize": "12px",
                    "marginTop": "6px",
                },
            )
        )
    if extra:
        children.append(extra)
    return dbc.Col(
        html.Div(children, style=DEFAULT_CARD_STYLE),
        width=2,
        style={"padding": "6px"},
    )


def build_top_bar():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "锅炉选择",
                        style={
                            "color": TEXT_SECONDARY,
                            "fontSize": "12px",
                            "marginBottom": "6px",
                        },
                    ),
                    dcc.Dropdown(
                        id="history-boiler-select",
                        options=BOILER_OPTIONS,
                        value=BOILER_OPTIONS[0]["value"],
                        clearable=False,
                        style={
                            "backgroundColor": DARK_BG_INPUT,
                            "color": TEXT_PRIMARY,
                            "width": "160px",
                        },
                    ),
                ],
                style={"marginRight": "24px"},
            ),
            html.Div(
                [
                    html.Div(
                        "时间范围",
                        style={
                            "color": TEXT_SECONDARY,
                            "fontSize": "12px",
                            "marginBottom": "6px",
                        },
                    ),
                    dcc.Dropdown(
                        id="history-time-range",
                        options=TIME_RANGE_OPTIONS,
                        value=TIME_RANGE_OPTIONS[1]["value"],
                        clearable=False,
                        style={
                            "backgroundColor": DARK_BG_INPUT,
                            "color": TEXT_PRIMARY,
                            "width": "160px",
                        },
                    ),
                ],
                style={"marginRight": "24px"},
            ),
            html.Div(
                id="history-custom-time-container",
                style={"display": "none"},
                children=[
                    html.Div(
                        [
                            html.Div(
                                "开始时间",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.DatePickerSingle(
                                id="history-start-date",
                                date=(datetime.now() - timedelta(days=1)).date(),
                                display_format="YYYY-MM-DD",
                                style={"backgroundColor": DARK_BG_INPUT},
                            ),
                            dcc.Input(
                                id="history-start-time",
                                type="text",
                                placeholder="HH:MM",
                                value="00:00",
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "borderRadius": "4px",
                                    "padding": "4px 8px",
                                    "marginLeft": "4px",
                                    "width": "70px",
                                },
                            ),
                        ],
                        style={"marginRight": "16px", "display": "inline-block"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "结束时间",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.DatePickerSingle(
                                id="history-end-date",
                                date=datetime.now().date(),
                                display_format="YYYY-MM-DD",
                                style={"backgroundColor": DARK_BG_INPUT},
                            ),
                            dcc.Input(
                                id="history-end-time",
                                type="text",
                                placeholder="HH:MM",
                                value="23:59",
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "borderRadius": "4px",
                                    "padding": "4px 8px",
                                    "marginLeft": "4px",
                                    "width": "70px",
                                },
                            ),
                        ],
                        style={"display": "inline-block"},
                    ),
                ],
            ),
            html.Div(
                dbc.Button(
                    "查询",
                    id="history-query-btn",
                    color="primary",
                    size="sm",
                    style={
                        "backgroundColor": ACCENT_CYAN,
                        "border": "none",
                        "color": DARK_BG,
                        "fontWeight": "600",
                        "padding": "6px 24px",
                    },
                ),
                style={"marginLeft": "auto", "alignSelf": "flex-end"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "flex-end",
            "backgroundColor": DARK_BG_CARD,
            "border": f"1px solid {BORDER_COLOR}",
            "borderRadius": "8px",
            "padding": "16px 20px",
            "marginBottom": "16px",
        },
    )


def build_trend_section():
    return html.Div(
        [
            _make_section_title("多参数趋势分析"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "左Y轴参数",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.Dropdown(
                                id="trend-y1-params",
                                options=POINT_OPTIONS,
                                value=["main_steam_temp", "exhaust_temp"],
                                multi=True,
                                placeholder="选择参数...",
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "width": "340px",
                                },
                            ),
                        ],
                        style={"marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "右Y轴参数",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.Dropdown(
                                id="trend-y2-params",
                                options=POINT_OPTIONS,
                                value=["main_steam_flow"],
                                multi=True,
                                placeholder="选择参数...",
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "width": "340px",
                                },
                            ),
                        ],
                    ),
                ],
                style={"display": "flex", "marginBottom": "12px"},
            ),
            dcc.Graph(
                id="trend-chart",
                style={"height": "380px"},
                config={"displayModeBar": True, "displaylogo": False},
            ),
        ],
        style={
            **DEFAULT_CARD_STYLE,
            "marginBottom": "16px",
        },
    )


def build_efficiency_cards():
    return html.Div(
        [
            _make_section_title("燃烧效率统计", ACCENT_GREEN),
            dbc.Row(
                [
                    _make_stat_card(
                        "avg-eff",
                        "平均燃烧效率",
                        "-- %",
                        "时间段内均值",
                        ACCENT_GREEN,
                    ),
                    _make_stat_card(
                        "max-eff",
                        "最高效率",
                        "-- %",
                        "--:--:--",
                        ACCENT_CYAN,
                    ),
                    _make_stat_card(
                        "min-eff",
                        "最低效率",
                        "-- %",
                        "--:--:--",
                        ACCENT_ORANGE,
                    ),
                    _make_stat_card(
                        "std-eff",
                        "效率标准差",
                        "--",
                        "波动性指标",
                        ACCENT_RED,
                    ),
                    _make_stat_card(
                        "avg-q2",
                        "排烟热损失 q2",
                        "-- %",
                        "均值",
                        TEXT_PRIMARY,
                    ),
                    _make_stat_card(
                        "avg-q3",
                        "气体不完全燃烧 q3",
                        "-- %",
                        "均值",
                        TEXT_PRIMARY,
                    ),
                ],
                style={"margin": "-6px"},
            ),
            dbc.Row(
                [
                    _make_stat_card(
                        "avg-q4",
                        "固体不完全燃烧 q4",
                        "-- %",
                        "均值",
                        TEXT_PRIMARY,
                    ),
                    _make_stat_card(
                        "avg-q5",
                        "散热损失 q5",
                        "-- %",
                        "均值",
                        TEXT_PRIMARY,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    "效率分布",
                                    style={
                                        "color": TEXT_SECONDARY,
                                        "fontSize": "12px",
                                        "marginBottom": "8px",
                                    },
                                ),
                                dcc.Graph(
                                    id="efficiency-histogram",
                                    style={"height": "100px"},
                                    config={"displayModeBar": False},
                                ),
                            ],
                            style=DEFAULT_CARD_STYLE,
                        ),
                        width=8,
                        style={"padding": "6px"},
                    ),
                ],
                style={"margin": "-6px", "marginTop": "0px"},
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


def build_correlation_section():
    return html.Div(
        [
            _make_section_title("参数相关性分析", ACCENT_ORANGE),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "X轴参数",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.Dropdown(
                                id="corr-x-param",
                                options=POINT_OPTIONS,
                                value="o2",
                                clearable=False,
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "width": "260px",
                                },
                            ),
                        ],
                        style={"marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Y轴参数",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.Dropdown(
                                id="corr-y-param",
                                options=POINT_OPTIONS,
                                value="exhaust_temp",
                                clearable=False,
                                style={
                                    "backgroundColor": DARK_BG_INPUT,
                                    "color": TEXT_PRIMARY,
                                    "width": "260px",
                                },
                            ),
                        ],
                        style={"marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Pearson 相关系数",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            html.Div(
                                id="corr-pearson-value",
                                children="--",
                                style={
                                    "color": ACCENT_ORANGE,
                                    "fontSize": "24px",
                                    "fontWeight": "700",
                                    "fontFamily": "Consolas, monospace",
                                    "backgroundColor": DARK_BG_INPUT,
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "borderRadius": "6px",
                                    "padding": "4px 16px",
                                    "minWidth": "120px",
                                    "textAlign": "center",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        [
                            html.Div(
                                "相关性强度",
                                style={
                                    "color": TEXT_SECONDARY,
                                    "fontSize": "12px",
                                    "marginBottom": "6px",
                                },
                            ),
                            html.Div(
                                id="corr-strength-label",
                                children="--",
                                style={
                                    "color": TEXT_PRIMARY,
                                    "fontSize": "14px",
                                    "fontWeight": "600",
                                    "backgroundColor": DARK_BG_INPUT,
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "borderRadius": "6px",
                                    "padding": "8px 16px",
                                    "minWidth": "120px",
                                    "textAlign": "center",
                                },
                            ),
                        ],
                        style={"marginLeft": "16px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-end", "marginBottom": "12px"},
            ),
            dcc.Graph(
                id="corr-scatter-chart",
                style={"height": "360px"},
                config={"displayModeBar": True, "displaylogo": False},
            ),
        ],
        style={
            "backgroundColor": DARK_BG_CARD,
            "border": f"1px solid {BORDER_COLOR}",
            "borderRadius": "8px",
            "padding": "16px",
        },
    )


def build_history_layout():
    return html.Div(
        [
            dcc.Store(id="history-query-store"),
            html.Div(
                "工业锅炉 · 历史数据分析",
                style={
                    "color": TEXT_PRIMARY,
                    "fontSize": "20px",
                    "fontWeight": "700",
                    "marginBottom": "16px",
                    "paddingLeft": "4px",
                },
            ),
            build_top_bar(),
            build_trend_section(),
            build_efficiency_cards(),
            build_correlation_section(),
        ],
        style={
            "backgroundColor": DARK_BG,
            "minHeight": "100vh",
            "padding": "20px 24px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
    )


layout = build_history_layout()
