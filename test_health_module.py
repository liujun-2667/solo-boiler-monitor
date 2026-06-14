import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import database as db
from health_engine import run_health_assessment, predict_trends, TREND_PARAMS
from efficiency import compute_all_metrics

db.init_db()

boiler_id = "Boiler-1"

print("=" * 60)
print("健康模块功能测试")
print("=" * 60)

print("\n1. 检查数据库表是否存在...")
try:
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        print(f"   现有表: {tables}")
        has_health = "health_scores" in tables
        has_pred = "predictive_alerts" in tables
        print(f"   health_scores表: {'✓' if has_health else '✗'}")
        print(f"   predictive_alerts表: {'✓' if has_pred else '✗'}")
except Exception as e:
    print(f"   错误: {e}")

print("\n2. 生成模拟数据并测试健康评估...")
test_data = {
    "main_steam_temp": 540.0,
    "main_steam_press": 16.7,
    "main_steam_flow": 720.0,
    "feedwater_temp": 255.0,
    "feedwater_flow": 735.0,
    "exhaust_temp": 135.0,
    "furnace_press": -60.0,
    "o2": 4.0,
    "co": 80.0,
    "nox": 70.0,
    "so2": 30.0,
    "dust": 8.0,
    "coal_feed": 85.0,
    "primary_air": 450.0,
    "induced_air": 520.0,
    "sh1_out_temp": 410.0,
    "sh2_out_temp": 460.0,
    "sh3_out_temp": 510.0,
    "sh4_out_temp": 538.0,
    "rh1_out_temp": 360.0,
    "rh2_out_temp": 440.0,
    "rh3_out_temp": 500.0,
    "rh4_out_temp": 530.0,
    "drum_level": 0.0,
    "fly_ash_carbon": 2.8,
}

test_metrics = compute_all_metrics(test_data)
print(f"   燃烧效率: {test_metrics.get('efficiency', 'N/A'):.2f}%")

scores, details, trends = run_health_assessment(boiler_id, test_data, test_metrics)

print(f"\n3. 健康度评分结果:")
print(f"   燃烧系统: {scores.get('combustion', 0):.1f} 分")
print(f"   汽水系统: {scores.get('steam_water', 0):.1f} 分")
print(f"   排放系统: {scores.get('emission', 0):.1f} 分")
print(f"   整体效率: {scores.get('efficiency', 0):.1f} 分")
print(f"   总健康度: {scores.get('overall', 0):.1f} 分")

print(f"\n4. 各子系统维度明细:")
for sys_name, sys_details in details.items():
    print(f"   {sys_name}:")
    for dim, val in sys_details.items():
        print(f"      {dim}: {val}")

print(f"\n5. 趋势预测参数: {list(TREND_PARAMS.keys())}")
for pk, pr in trends.items():
    if pr:
        print(f"   {pk}:")
        print(f"      趋势方向: {pr.get('trend_direction', 'N/A')}")
        print(f"      斜率: {pr.get('slope', 'N/A')}")
        print(f"      预测点数: {len(pr.get('predicted_values', []))}")
        print(f"      置信区间上界数: {len(pr.get('confidence_upper', []))}")
        print(f"      预计超标时间: {pr.get('minutes_to_exceed', 'N/A')} 分钟")
    else:
        print(f"   {pk}: 数据不足")

print(f"\n6. 检查数据库中的健康评分记录...")
latest = db.get_latest_health_score(boiler_id)
if latest:
    print(f"   最新记录ID: {latest['id']}")
    print(f"   时间: {latest['timestamp']}")
    print(f"   总评分: {latest['overall_score']}")
else:
    print("   无记录")

print(f"\n7. 检查预测性告警...")
alerts = db.get_active_predictive_alerts(boiler_id)
print(f"   活跃预测告警数: {len(alerts)}")
for a in alerts:
    print(f"   - {a['param_name']}: 预计{a['minutes_to_exceed']:.0f}分钟后超标")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
