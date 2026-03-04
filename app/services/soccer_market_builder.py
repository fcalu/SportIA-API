def safe_float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def build_soccer_markets(odds, script):
    
    total_line = safe_float(odds.get("over_under"), 2.5)

    home_ml = odds.get("home_moneyline")
    away_ml = odds.get("away_moneyline")
    draw_ml = odds.get("draw_moneyline")

    return [

        # ==============================
        # TOTAL GOALS
        # ==============================

        {
            "name": "Match Total Goals",
            "role": "team",
            "type": "total_goals",
            "line": total_line,
            "over_odds": odds.get("over_odds"),
            "under_odds": odds.get("under_odds"),
            "season_avg": 2.6
        },

        # ==============================
        # BOTH TEAMS TO SCORE
        # ==============================

        {
            "name": "Both Teams To Score",
            "role": "team",
            "type": "btts",
            "line": 0.5,
            "season_avg": 0.55
        },

        # ==============================
        # 1X2 MARKET
        # ==============================

        {
            "name": "Full Time Result - Home",
            "role": "team",
            "type": "moneyline_home",
            "odds": home_ml
        },

        {
            "name": "Full Time Result - Draw",
            "role": "team",
            "type": "moneyline_draw",
            "odds": draw_ml
        },

        {
            "name": "Full Time Result - Away",
            "role": "team",
            "type": "moneyline_away",
            "odds": away_ml
        },

        # ==============================
        # CORNERS
        # ==============================

        {
            "name": "Corners Market",
            "role": "team",
            "type": "corners",
            "line": 9.5,
            "season_avg": 9.2
        }
    ]
