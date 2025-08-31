# src/strategy.py
import random

def gen_strategy(symbol: str, spot: float, max_pain: float, support: float, resistance: float):
    lines = []
    diff = (spot - max_pain)
    # 🧲 Max Pain 提醒
    strength = "🟢 弱磁吸"
    if abs(diff) < 5:
        strength = "🔴 極強磁吸"
    elif abs(diff) < 15:
        strength = "🟡 中等磁吸"
    lines.append(f"🧲 重點 Max Pain 提醒\n🧲 美股 {symbol}: ${spot:.2f} {strength} (距離: {diff:+.2f})")

    # 💡 策略建議（範例規則，可再引入 AI LLM 做更智能生成）
    short = "觀察突破阻力可短線追多" if spot > resistance*0.98 else "支撐附近可短線低接"
    mid = "若站穩 Max Pain 上方，偏多操作" if spot > max_pain else "盤整格局，中線觀望"
    long = "產業基本面仍具前景，長期看多"  # 可接財報/產業AI評估

    lines.append("💡 交易策略建議")
    lines.append(f"‧ 短線: {short}")
    lines.append(f"‧ 中線: {mid}")
    lines.append(f"‧ 長線: {long}")

    # 💡 策略提醒（隨機模板 + 可接 AI 分析）
    reminders = [
        "🚀 強勢追蹤: 關注 GOOG 的延續性",
        "🛒 逢低布局: 考慮 TSLA 的反彈機會",
        "⚖️ 平衡配置: 七巨頭分散風險，長期看漲"
    ]
    lines.append("\n💡 交易策略提醒")
    lines.extend(random.sample(reminders, 3))

    return "\n".join(lines)
