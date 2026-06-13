import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import dcc, html

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

DEFAULT_CARD_STYLE = {
    "backgroundColor": DARK_BG_CARD,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "16px",
}


def build_report_layout():
    now = datetime.now()
    return html.Div(
        [
            html.Div(
                "工业锅炉 · 排放合规报告",
                style={
                    "color": TEXT_PRIMARY,
                    "fontSize": "20px",
                    "fontWeight": "700",
                    "marginBottom": "16px",
                    "paddingLeft": "4px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("锅炉选择", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                            dcc.Dropdown(
                                id="report-boiler-select",
                                options=[
                                    {"label": "Boiler-1", "value": "Boiler-1"},
                                    {"label": "Boiler-2", "value": "Boiler-2"},
                                    {"label": "Boiler-3", "value": "Boiler-3"},
                                ],
                                value="Boiler-1",
                                clearable=False,
                                style={"backgroundColor": DARK_BG_INPUT, "color": TEXT_PRIMARY, "width": "160px"},
                            ),
                        ],
                        style={"marginRight": "24px"},
                    ),
                    html.Div(
                        [
                            html.Div("报告年份", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                            dcc.Dropdown(
                                id="report-year",
                                options=[{"label": str(y), "value": y} for y in range(now.year - 2, now.year + 1)],
                                value=now.year,
                                clearable=False,
                                style={"backgroundColor": DARK_BG_INPUT, "color": TEXT_PRIMARY, "width": "120px"},
                            ),
                        ],
                        style={"marginRight": "24px"},
                    ),
                    html.Div(
                        [
                            html.Div("报告月份", style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginBottom": "6px"}),
                            dcc.Dropdown(
                                id="report-month",
                                options=[{"label": f"{m}月", "value": m} for m in range(1, 13)],
                                value=now.month,
                                clearable=False,
                                style={"backgroundColor": DARK_BG_INPUT, "color": TEXT_PRIMARY, "width": "120px"},
                            ),
                        ],
                        style={"marginRight": "24px"},
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                "生成报告",
                                id="report-generate-btn",
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
                            html.Span(
                                id="report-status",
                                style={"color": ACCENT_GREEN, "fontSize": "13px", "marginLeft": "12px"},
                            ),
                        ],
                        style={"marginRight": "16px", "alignSelf": "flex-end"},
                    ),
                    html.Div(
                        [
                            html.A(
                                dbc.Button(
                                    "导出PDF",
                                    id="report-pdf-btn",
                                    color="success",
                                    size="sm",
                                    style={
                                        "backgroundColor": ACCENT_GREEN,
                                        "border": "none",
                                        "color": DARK_BG,
                                        "fontWeight": "600",
                                        "padding": "6px 24px",
                                    },
                                ),
                                id="report-pdf-link",
                                href="/api/report/pdf?boiler_id=Boiler-1&year={}&month={}".format(now.year, now.month),
                                target="_blank",
                                style={"textDecoration": "none"},
                            ),
                        ],
                        style={"alignSelf": "flex-end"},
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
            ),
            html.Div(id="report-content", style={"marginBottom": "16px"}),
        ],
        style={
            "backgroundColor": DARK_BG,
            "minHeight": "100vh",
            "padding": "20px 24px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
    )
