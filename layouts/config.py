import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dash import dcc, html, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import database as db
import json
from datetime import datetime


DARK_BG = "#0B1A2B"
DARK_CARD = "#112240"
DARK_BG_INPUT = "#1A2E4D"
DARK_BORDER = "#1E3A5F"
DARK_TEXT = "#E6F1FF"
DARK_MUTED = "#88A0C0"
ACCENT_COLOR = "#00FF88"
ACCENT_CYAN = "#00D4FF"
DANGER_COLOR = "#FF4D6D"
WARNING_COLOR = "#FFB800"


def _card_style():
    return {
        "backgroundColor": DARK_CARD,
        "border": f"1px solid {DARK_BORDER}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "16px",
    }


def _section_title(text):
    return html.Div(
        [
            html.Span(
                style={
                    "display": "inline-block",
                    "width": "3px",
                    "height": "16px",
                    "backgroundColor": ACCENT_CYAN,
                    "marginRight": "8px",
                    "verticalAlign": "middle",
                }
            ),
            html.Span(
                text,
                style={
                    "color": DARK_TEXT,
                    "fontWeight": "bold",
                    "verticalAlign": "middle",
                    "fontSize": "16px",
                },
            ),
        ],
        style={
            "marginBottom": "16px",
            "borderBottom": f"1px solid {DARK_BORDER}",
            "paddingBottom": "8px",
        },
    )


def _save_button(btn_id):
    return dbc.Button(
        "确认保存",
        id=btn_id,
        color="success",
        size="lg",
        style={
            "backgroundColor": ACCENT_COLOR,
            "border": f"1px solid {ACCENT_COLOR}",
            "minWidth": "160px",
            "fontWeight": "bold",
            "color": "#0B1A2B",
        },
    )


def _success_alert(alert_id):
    return dbc.Alert(
        id=alert_id,
        color="success",
        is_open=False,
        duration=3000,
        style={"marginTop": "12px"},
    )


def _build_point_limits_data():
    limits = db.get_point_limits()
    data = []
    for key, val in limits.items():
        data.append({
            "point_key": key,
            "point_name": val.get("name", ""),
            "unit": val.get("unit", ""),
            "min_val": val.get("min", 0),
            "max_val": val.get("max", 0),
        })
    return data


def _build_o2_curve_data():
    curve = db.get_o2_curve()
    return [{"load_ratio": str(r), "o2_value": v} for r, v in curve]


def _build_config_history_data():
    history = db.get_config_history(50)
    data = []
    for record in history:
        try:
            old_v = json.loads(record["old_value"]) if record["old_value"] else "-"
            new_v = json.loads(record["new_value"]) if record["new_value"] else "-"
            if isinstance(old_v, dict):
                old_v = json.dumps(old_v, ensure_ascii=False)
            if isinstance(new_v, dict):
                new_v = json.dumps(new_v, ensure_ascii=False)
        except Exception:
            old_v = record["old_value"] or "-"
            new_v = record["new_value"] or "-"
        data.append({
            "id": record["id"],
            "config_type": record["config_type"],
            "old_value": str(old_v),
            "new_value": str(new_v),
            "changed_at": record["changed_at"],
        })
    return data


def _datatable_style():
    return {
        "style_header": {
            "backgroundColor": DARK_BG_INPUT,
            "color": DARK_TEXT,
            "fontWeight": "bold",
            "border": f"1px solid {DARK_BORDER}",
            "textAlign": "center",
        },
        "style_cell": {
            "backgroundColor": DARK_CARD,
            "color": DARK_TEXT,
            "border": f"1px solid {DARK_BORDER}",
            "textAlign": "left",
            "padding": "8px 12px",
            "fontSize": "13px",
        },
        "style_data_conditional": [
            {
                "if": {"state": "active"},
                "backgroundColor": DARK_BG_INPUT,
                "border": f"1px solid {ACCENT_CYAN}",
            }
        ],
        "style_table": {
            "overflowX": "auto",
            "borderRadius": "6px",
        },
    }


def tab1_point_limits():
    return dbc.Card(
        [
            _section_title("Tab1 - 测点上下限配置"),
            html.P(
                "配置各监测测点的正常运行范围，超出范围将触发预警。表格支持直接编辑。",
                style={"color": DARK_MUTED, "marginBottom": "12px"},
            ),
            dash_table.DataTable(
                id="point-limits-table",
                columns=[
                    {"name": "测点Key", "id": "point_key", "editable": False},
                    {"name": "测点名称", "id": "point_name", "editable": True},
                    {"name": "单位", "id": "unit", "editable": True},
                    {"name": "最小值", "id": "min_val", "editable": True, "type": "numeric"},
                    {"name": "最大值", "id": "max_val", "editable": True, "type": "numeric"},
                ],
                data=_build_point_limits_data(),
                editable=True,
                row_deletable=False,
                sort_action="native",
                filter_action="native",
                page_size=15,
                **_datatable_style(),
            ),
            html.Div(
                [
                    html.Div(
                        id="point-limits-trace",
                        style={
                            "color": WARNING_COLOR,
                            "fontSize": "12px",
                            "marginTop": "12px",
                            "minHeight": "20px",
                        },
                    ),
                    html.Div(
                        [_save_button("save-point-limits-btn")],
                        style={"marginTop": "16px", "textAlign": "right"},
                    ),
                    _success_alert("point-limits-save-alert"),
                ],
                style={"marginTop": "16px"},
            ),
        ],
        style=_card_style(),
    )


def tab2_emission_limits():
    limits = db.get_emission_limits()

    def _pollutant_row(key, label, color):
        data = limits.get(key, {})
        return dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.Strong(label, style={"color": color, "fontSize": "16px"}),
                            html.Span(
                                f" ({data.get('unit', '')})",
                                style={"color": DARK_MUTED, "marginLeft": "6px"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "height": "100%"},
                    ),
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Label("小时均值限值", style={"color": DARK_MUTED, "fontSize": "12px"}),
                        dbc.Input(
                            id=f"emission-{key}-hourly",
                            type="number",
                            value=data.get("hourly", 0),
                            min=0,
                            step=1,
                            style={
                                "backgroundColor": DARK_BG_INPUT,
                                "color": DARK_TEXT,
                                "border": f"1px solid {DARK_BORDER}",
                            },
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Label("瞬时峰值限值", style={"color": DARK_MUTED, "fontSize": "12px"}),
                        dbc.Input(
                            id=f"emission-{key}-peak",
                            type="number",
                            value=data.get("peak", 0),
                            min=0,
                            step=1,
                            style={
                                "backgroundColor": DARK_BG_INPUT,
                                "color": DARK_TEXT,
                                "border": f"1px solid {DARK_BORDER}",
                            },
                        ),
                    ],
                    md=4,
                ),
            ],
            style={
                "padding": "16px",
                "marginBottom": "12px",
                "backgroundColor": DARK_BG_INPUT,
                "borderRadius": "6px",
                "border": f"1px solid {DARK_BORDER}",
            },
            align="center",
        )

    return dbc.Card(
        [
            _section_title("Tab2 - 排放限值配置"),
            html.P(
                "配置大气污染物排放限值，系统将自动监测并触发超标预警。",
                style={"color": DARK_MUTED, "marginBottom": "16px"},
            ),
            _pollutant_row("nox", "氮氧化物 (NOx)", "#e06c75"),
            _pollutant_row("so2", "二氧化硫 (SO2)", "#e5c07b"),
            _pollutant_row("co", "一氧化碳 (CO)", "#61afef"),
            _pollutant_row("dust", "粉尘 (烟尘)", "#98c379"),
            html.Div(
                [_save_button("save-emission-limits-btn")],
                style={"marginTop": "20px", "textAlign": "right"},
            ),
            _success_alert("emission-limits-save-alert"),
        ],
        style=_card_style(),
    )


def tab3_o2_curve():
    return dbc.Card(
        [
            _section_title("Tab3 - 最佳O2曲线配置"),
            html.P(
                "配置不同负荷率下的最佳氧量设定值，用于燃烧优化诊断。支持新增和删除行。",
                style={"color": DARK_MUTED, "marginBottom": "12px"},
            ),
            dash_table.DataTable(
                id="o2-curve-table",
                columns=[
                    {"name": "负荷率 (0~1)", "id": "load_ratio", "editable": True, "type": "numeric"},
                    {"name": "最佳O2值 (%)", "id": "o2_value", "editable": True, "type": "numeric"},
                ],
                data=_build_o2_curve_data(),
                editable=True,
                row_deletable=True,
                sort_action="native",
                page_size=12,
                **_datatable_style(),
            ),
            html.Div(
                [
                    dbc.Button(
                        "+ 新增一行",
                        id="add-o2-row-btn",
                        color="secondary",
                        size="sm",
                        style={
                            "backgroundColor": DARK_BORDER,
                            "border": "none",
                            "color": DARK_TEXT,
                            "marginRight": "12px",
                        },
                    ),
                ],
                style={"marginTop": "12px"},
            ),
            html.Div(
                [_save_button("save-o2-curve-btn")],
                style={"marginTop": "16px", "textAlign": "right"},
            ),
            _success_alert("o2-curve-save-alert"),
        ],
        style=_card_style(),
    )


def tab4_diag_thresholds():
    thresholds = db.get_diag_thresholds()

    def _threshold_row(label, input_id, default_val, unit, description):
        return dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.Strong(label, style={"color": DARK_TEXT, "display": "block"}),
                            html.Small(description, style={"color": DARK_MUTED}),
                        ]
                    ),
                    md=6,
                ),
                dbc.Col(
                    [
                        dbc.InputGroup(
                            [
                                dbc.Input(
                                    id=input_id,
                                    type="number",
                                    value=thresholds.get(input_id, default_val),
                                    min=0,
                                    step=0.1,
                                    style={
                                        "backgroundColor": DARK_BG_INPUT,
                                        "color": DARK_TEXT,
                                        "border": f"1px solid {DARK_BORDER}",
                                    },
                                ),
                                dbc.InputGroupText(
                                    unit,
                                    style={
                                        "backgroundColor": DARK_BORDER,
                                        "color": DARK_TEXT,
                                        "border": f"1px solid {DARK_BORDER}",
                                    },
                                ),
                            ]
                        ),
                    ],
                    md=4,
                ),
            ],
            style={
                "padding": "14px 0",
                "borderBottom": f"1px solid {DARK_BORDER}",
            },
            align="center",
        )

    return dbc.Card(
        [
            _section_title("Tab4 - 诊断规则阈值"),
            html.P(
                "调整智能诊断规则的触发阈值，阈值越严格预警越频繁。",
                style={"color": DARK_MUTED, "marginBottom": "16px"},
            ),
            _threshold_row(
                "排烟温度高阈值",
                "exhaust_temp_high",
                145,
                "℃",
                "排烟温度超过此值且氧量偏高时触发诊断",
            ),
            _threshold_row(
                "CO突升阈值",
                "co_spike",
                200,
                "ppm",
                "CO浓度超过此值且氧量偏低时触发诊断",
            ),
            _threshold_row(
                "飞灰含碳量阈值",
                "fly_ash_carbon_high",
                5,
                "%",
                "飞灰含碳量超过此值时触发诊断",
            ),
            _threshold_row(
                "过热器温差阈值",
                "sh_temp_diff",
                15,
                "℃",
                "过热器各段最大温差超过此值时触发诊断",
            ),
            _threshold_row(
                "氧量偏差阈值",
                "o2_deviation",
                0.8,
                "%",
                "实际氧量与最佳氧量偏差超过此值时触发诊断",
            ),
            html.Div(
                [_save_button("save-diag-thresholds-btn")],
                style={"marginTop": "20px", "textAlign": "right"},
            ),
            _success_alert("diag-thresholds-save-alert"),
        ],
        style=_card_style(),
    )


def tab5_config_history():
    return dbc.Card(
        [
            _section_title("Tab5 - 配置修改历史"),
            html.P(
                "最近50条配置变更记录（只读），展示修改前后的对比。",
                style={"color": DARK_MUTED, "marginBottom": "12px"},
            ),
            dash_table.DataTable(
                id="config-history-table",
                columns=[
                    {"name": "ID", "id": "id"},
                    {"name": "配置项类型", "id": "config_type"},
                    {"name": "修改前", "id": "old_value"},
                    {"name": "修改后", "id": "new_value"},
                    {"name": "修改时间", "id": "changed_at"},
                ],
                data=_build_config_history_data(),
                editable=False,
                row_deletable=False,
                sort_action="native",
                filter_action="native",
                page_size=15,
                **_datatable_style(),
            ),
            html.Div(
                dbc.Button(
                    "刷新记录",
                    id="refresh-history-btn",
                    color="secondary",
                    size="sm",
                    style={
                        "backgroundColor": DARK_BORDER,
                        "border": "none",
                        "color": DARK_TEXT,
                        "marginTop": "12px",
                    },
                ),
                style={"textAlign": "right"},
            ),
        ],
        style=_card_style(),
    )


def register_callbacks(app):
    @app.callback(
        Output("point-limits-trace", "children"),
        Input("point-limits-table", "data"),
        State("point-limits-table", "data_previous"),
        prevent_initial_call=True,
    )
    def trace_point_limits_changes(current, previous):
        if not previous:
            return ""
        changes = []
        prev_map = {r["point_key"]: r for r in previous}
        for r in current:
            key = r["point_key"]
            p = prev_map.get(key, {})
            for field in ["point_name", "unit", "min_val", "max_val"]:
                if r.get(field) != p.get(field):
                    changes.append(
                        f"[{key}] {field}: {p.get(field)} → {r.get(field)}"
                    )
        if changes:
            return "修改留痕: " + "  |  ".join(changes)
        return ""

    @app.callback(
        Output("point-limits-save-alert", "children"),
        Output("point-limits-save-alert", "is_open"),
        Input("save-point-limits-btn", "n_clicks"),
        State("point-limits-table", "data"),
        prevent_initial_call=True,
    )
    def save_point_limits(n_clicks, rows):
        limits_dict = {}
        for r in rows:
            limits_dict[r["point_key"]] = {
                "name": r["point_name"],
                "unit": r["unit"],
                "min": float(r["min_val"]),
                "max": float(r["max_val"]),
            }
        db.update_point_limits(limits_dict)
        return f"测点上下限配置已保存 ({datetime.now().strftime('%H:%M:%S')})", True

    @app.callback(
        Output("emission-limits-save-alert", "children"),
        Output("emission-limits-save-alert", "is_open"),
        Input("save-emission-limits-btn", "n_clicks"),
        State("emission-nox-hourly", "value"),
        State("emission-nox-peak", "value"),
        State("emission-so2-hourly", "value"),
        State("emission-so2-peak", "value"),
        State("emission-co-hourly", "value"),
        State("emission-co-peak", "value"),
        State("emission-dust-hourly", "value"),
        State("emission-dust-peak", "value"),
        prevent_initial_call=True,
    )
    def save_emission_limits(
        n_clicks, nox_h, nox_p, so2_h, so2_p, co_h, co_p, dust_h, dust_p
    ):
        emission_limits = db.get_emission_limits()
        limits_dict = {
            "nox": {
                "name": emission_limits.get("nox", {}).get("name", "氮氧化物"),
                "unit": emission_limits.get("nox", {}).get("unit", "mg/m³"),
                "hourly": float(nox_h),
                "peak": float(nox_p),
            },
            "so2": {
                "name": emission_limits.get("so2", {}).get("name", "二氧化硫"),
                "unit": emission_limits.get("so2", {}).get("unit", "mg/m³"),
                "hourly": float(so2_h),
                "peak": float(so2_p),
            },
            "co": {
                "name": emission_limits.get("co", {}).get("name", "一氧化碳"),
                "unit": emission_limits.get("co", {}).get("unit", "ppm"),
                "hourly": float(co_h),
                "peak": float(co_p),
            },
            "dust": {
                "name": emission_limits.get("dust", {}).get("name", "粉尘"),
                "unit": emission_limits.get("dust", {}).get("unit", "mg/m³"),
                "hourly": float(dust_h),
                "peak": float(dust_p),
            },
        }
        db.update_emission_limits(limits_dict)
        return f"排放限值配置已保存 ({datetime.now().strftime('%H:%M:%S')})", True

    @app.callback(
        Output("o2-curve-table", "data"),
        Input("add-o2-row-btn", "n_clicks"),
        State("o2-curve-table", "data"),
        State("o2-curve-table", "columns"),
        prevent_initial_call=True,
    )
    def add_o2_row(n_clicks, rows, columns):
        rows.append({c["id"]: "" for c in columns})
        return rows

    @app.callback(
        Output("o2-curve-save-alert", "children"),
        Output("o2-curve-save-alert", "is_open"),
        Input("save-o2-curve-btn", "n_clicks"),
        State("o2-curve-table", "data"),
        prevent_initial_call=True,
    )
    def save_o2_curve(n_clicks, rows):
        with db.get_db() as conn:
            conn.execute("DELETE FROM o2_curve")
            for r in rows:
                if r.get("load_ratio") and r.get("o2_value"):
                    conn.execute(
                        "INSERT INTO o2_curve (load_ratio, o2_value) VALUES (?,?)",
                        (str(r["load_ratio"]), float(r["o2_value"])),
                    )
            conn.execute(
                "INSERT INTO config_history (config_type, old_value, new_value, changed_at) VALUES (?,?,?,?)",
                (
                    "o2_curve",
                    "",
                    json.dumps(rows, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        return f"最佳O2曲线配置已保存 ({datetime.now().strftime('%H:%M:%S')})", True

    @app.callback(
        Output("diag-thresholds-save-alert", "children"),
        Output("diag-thresholds-save-alert", "is_open"),
        Input("save-diag-thresholds-btn", "n_clicks"),
        State("exhaust_temp_high", "value"),
        State("co_spike", "value"),
        State("fly_ash_carbon_high", "value"),
        State("sh_temp_diff", "value"),
        State("o2_deviation", "value"),
        prevent_initial_call=True,
    )
    def save_diag_thresholds(n_clicks, exh, co, fly, sh, o2):
        thresholds = {
            "exhaust_temp_high": float(exh),
            "co_spike": float(co),
            "fly_ash_carbon_high": float(fly),
            "sh_temp_diff": float(sh),
            "o2_deviation": float(o2),
        }
        old = db.get_diag_thresholds()
        with db.get_db() as conn:
            for k, v in thresholds.items():
                conn.execute(
                    "INSERT OR REPLACE INTO diag_thresholds (rule_key, value) VALUES (?,?)",
                    (k, v),
                )
                conn.execute(
                    "INSERT INTO config_history (config_type, old_value, new_value, changed_at) VALUES (?,?,?,?)",
                    (
                        "diag_thresholds:" + k,
                        json.dumps(old.get(k), ensure_ascii=False),
                        json.dumps(v, ensure_ascii=False),
                        datetime.now().isoformat(),
                    ),
                )
            conn.commit()
        return f"诊断规则阈值已保存 ({datetime.now().strftime('%H:%M:%S')})", True

    @app.callback(
        Output("config-history-table", "data"),
        Input("refresh-history-btn", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_history(n_clicks):
        return _build_config_history_data()


def build_config_layout():
    return html.Div(
        [
            html.H3(
                "工业锅炉系统 - 配置管理",
                style={
                    "color": DARK_TEXT,
                    "marginBottom": "24px",
                    "textAlign": "center",
                    "paddingTop": "20px",
                },
            ),
            dcc.Tabs(
                id="config-tabs",
                value="tab1",
                children=[
                    dcc.Tab(
                        label="测点上下限配置",
                        value="tab1",
                        style={
                            "backgroundColor": DARK_CARD,
                            "color": DARK_MUTED,
                            "border": f"1px solid {DARK_BORDER}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        selected_style={
                            "backgroundColor": ACCENT_CYAN,
                            "color": "#0B1A2B",
                            "border": f"1px solid {ACCENT_CYAN}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        children=[tab1_point_limits()],
                    ),
                    dcc.Tab(
                        label="排放限值配置",
                        value="tab2",
                        style={
                            "backgroundColor": DARK_CARD,
                            "color": DARK_MUTED,
                            "border": f"1px solid {DARK_BORDER}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        selected_style={
                            "backgroundColor": ACCENT_CYAN,
                            "color": "#0B1A2B",
                            "border": f"1px solid {ACCENT_CYAN}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        children=[tab2_emission_limits()],
                    ),
                    dcc.Tab(
                        label="最佳O2曲线配置",
                        value="tab3",
                        style={
                            "backgroundColor": DARK_CARD,
                            "color": DARK_MUTED,
                            "border": f"1px solid {DARK_BORDER}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        selected_style={
                            "backgroundColor": ACCENT_CYAN,
                            "color": "#0B1A2B",
                            "border": f"1px solid {ACCENT_CYAN}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        children=[tab3_o2_curve()],
                    ),
                    dcc.Tab(
                        label="诊断规则阈值",
                        value="tab4",
                        style={
                            "backgroundColor": DARK_CARD,
                            "color": DARK_MUTED,
                            "border": f"1px solid {DARK_BORDER}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        selected_style={
                            "backgroundColor": ACCENT_CYAN,
                            "color": "#0B1A2B",
                            "border": f"1px solid {ACCENT_CYAN}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        children=[tab4_diag_thresholds()],
                    ),
                    dcc.Tab(
                        label="配置修改历史",
                        value="tab5",
                        style={
                            "backgroundColor": DARK_CARD,
                            "color": DARK_MUTED,
                            "border": f"1px solid {DARK_BORDER}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        selected_style={
                            "backgroundColor": ACCENT_CYAN,
                            "color": "#0B1A2B",
                            "border": f"1px solid {ACCENT_CYAN}",
                            "borderBottom": "none",
                            "padding": "12px 20px",
                            "fontWeight": "bold",
                        },
                        children=[tab5_config_history()],
                    ),
                ],
                style={"marginBottom": "0"},
                parent_style={
                    "borderBottom": f"2px solid {ACCENT_CYAN}",
                    "marginBottom": "0",
                },
            ),
        ],
        style={
            "backgroundColor": DARK_BG,
            "minHeight": "100vh",
            "padding": "0 40px 60px 40px",
        },
    )
