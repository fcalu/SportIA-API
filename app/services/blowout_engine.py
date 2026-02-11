# ==========================================
# 🧨 NBA BLOWOUT RISK ENGINE
# ==========================================

def apply_blowout_adjustment(prop, odds):

    spread = abs(float(odds.get("spread", 0)))

    # Si no hay riesgo real, no tocar nada
    if spread < 15:
        return prop

    role = prop.get("role")
    minutes = prop.get("projected_minutes", 0)
    mean = prop["projection_model"]["mean"]
    std = prop["projection_model"]["std_dev"]

    # ===============================
    # NIVEL 1: Spread 15–19
    # ===============================
    if 15 <= spread < 20:
        primary_cut = 0.15
        bench_boost = 0.08
        variance_boost = 0.15

    # ===============================
    # NIVEL 2: Spread 20+
    # ===============================
    else:
        primary_cut = 0.22
        bench_boost = 0.12
        variance_boost = 0.22

    # Ajuste por rol
    if role == "Primary":
        minutes *= (1 - primary_cut)
        mean *= (1 - primary_cut)
    else:
        minutes *= (1 + bench_boost)
        mean *= (1 + bench_boost)

    # Aumentar varianza
    std *= (1 + variance_boost)

    prop["projected_minutes"] = round(minutes, 2)
    prop["projection_model"]["mean"] = round(mean, 2)
    prop["projection_model"]["std_dev"] = round(std, 2)

    # Marcador interno
    prop["blowout_adjusted"] = True

    return prop
