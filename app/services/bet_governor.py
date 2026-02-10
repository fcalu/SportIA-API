def get_official_picks(props):
    
    official = []

    for p in props:

        # ❌ Sin línea real
        if p.get("line") is None:
            continue

        # ❌ Sin edge
        if p.get("bet_tier") in ["NO BET", "LEAN"]:
            continue

        # ❌ Edge negativo
        if p.get("edge", 0) <= 0:
            continue

        official.append(p)

    return official
