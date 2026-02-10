import math

# ==========================================================
# 📊 NORMAL CDF SIN SCIPY
# ==========================================================
def normal_cdf(x, mean, std):
    if std <= 0:
        return 0.5
    z = (x - mean) / (std * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))


def prob_over(line: float, mean: float, std: float) -> float:
    return round(1 - normal_cdf(line, mean, std), 4)


def prob_under(line: float, mean: float, std: float) -> float:
    return round(normal_cdf(line, mean, std), 4)
