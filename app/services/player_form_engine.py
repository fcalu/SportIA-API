import statistics


def analyze_player_form(game_log, stat_key, line, projected_minutes):

    values = [
        g.get(stat_key)
        for g in game_log
        if g.get(stat_key) is not None
    ]

    minutes = [
        g.get("minutes")
        for g in game_log
        if g.get("minutes") is not None
    ]

    if not values:
        return {}

    avg = sum(values) / len(values)
    high = max(values)
    low = min(values)

    std_dev = statistics.stdev(values) if len(values) > 1 else 0

    hit_rate = sum(1 for v in values if v >= line) / len(values)

    avg_minutes = sum(minutes) / len(minutes) if minutes else 0

    minutes_delta = round(projected_minutes - avg_minutes, 2)

    hot = avg > (line * 1.1)
    cold = avg < (line * 0.9)

    return {
        "avg_last_n": round(avg, 2),
        "high_last_n": high,
        "low_last_n": low,
        "std_last_n": round(std_dev, 2),
        "hit_rate_vs_line": round(hit_rate, 2),
        "avg_minutes_last_n": round(avg_minutes, 2),
        "minutes_projection_delta": minutes_delta,
        "trend": "HOT" if hot else "COLD" if cold else "NEUTRAL"
    }
