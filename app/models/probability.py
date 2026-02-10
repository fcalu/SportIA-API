def over25_prob(home_avg, away_avg):
    total = home_avg + away_avg
    base = 0.45 if total < 2.4 else 0.55 if total < 3 else 0.62
    return {"low": round(base-0.07,2),"base":round(base,2),"high":round(base+0.07,2)}
