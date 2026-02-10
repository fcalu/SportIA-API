def safe_float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def build_soccer_markets(odds, script):

    total_line = safe_float(odds.get("over_under"), 2.5)

    return [
        {
            "name": "Match Market",
            "role": "team",
            "type": "over_2_5",
            "line": total_line,
            "season_avg": 2.6
        },
        {
            "name": "Both Teams To Score",
            "role": "team",
            "type": "btts",
            "line": 0.5,
            "season_avg": 0.55
        },
        {
            "name": "Corners Market",
            "role": "team",
            "type": "corners",
            "line": 9.5,
            "season_avg": 9.2
        }
    ]
