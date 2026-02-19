import json
import os
from datetime import datetime, timedelta, timezone

FILE_PATH = "model_history.json"


# ==========================================================
# 📁 LOAD HISTORY
# ==========================================================
def load_history():
    if not os.path.exists(FILE_PATH):
        return []
    with open(FILE_PATH, "r") as f:
        return json.load(f)


# ==========================================================
# 💾 SAVE HISTORY
# ==========================================================
def save_history(history):
    with open(FILE_PATH, "w") as f:
        json.dump(history, f, indent=2)


# ==========================================================
# 📌 SAVE NEW PREDICTION
# ==========================================================
def save_prediction(event_id, market_type, bet_tier, odds, result=None):

    history = load_history()

    history.append({
        "event_id": event_id,
        "market_type": market_type,
        "bet_tier": bet_tier,
        "odds": odds,
        "result": result,  # WIN / LOSS / PUSH / None
        "stake": 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    save_history(history)


# ==========================================================
# 💰 CALCULATE PROFIT
# ==========================================================
def calculate_profit(odds, stake, result):

    if result != "WIN":
        return -stake if result == "LOSS" else 0

    if odds > 0:
        return stake * (odds / 100)
    else:
        return stake * (100 / abs(odds))


# ==========================================================
# 📊 PERFORMANCE METRICS
# ==========================================================
def calculate_performance_metrics():

    history = load_history()

    now = datetime.now(timezone.utc)
    last_30d = now - timedelta(days=30)
    last_7d = now - timedelta(days=7)

    total_30 = wins_30 = 0
    total_value = wins_value = 0

    stake_7 = profit_7 = 0

    for h in history:

        if not h.get("result"):
            continue  # Skip unresolved bets

        created = datetime.fromisoformat(h["created_at"])

        # 30 DAY ACCURACY
        if created >= last_30d:
            total_30 += 1
            if h["result"] == "WIN":
                wins_30 += 1

        # VALUE BET HIT RATE
        if h["bet_tier"] in ["VALUE_BET", "STRONG_VALUE", "ELITE_VALUE"]:
            total_value += 1
            if h["result"] == "WIN":
                wins_value += 1

        # 7 DAY ROI
        if created >= last_7d:
            stake_7 += h["stake"]
            profit_7 += calculate_profit(h["odds"], h["stake"], h["result"])

    accuracy_30 = (wins_30 / total_30 * 100) if total_30 else 0
    roi_7 = (profit_7 / stake_7 * 100) if stake_7 else 0
    value_hit = (wins_value / total_value * 100) if total_value else 0

    return {
        "model_accuracy_30d": round(accuracy_30, 2),
        "roi_7days": f"{round(roi_7, 2)}%",
        "hit_rate_valuebets": round(value_hit, 2)
    }
