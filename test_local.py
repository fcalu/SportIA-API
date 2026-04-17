import sys
import os
import asyncio
import json

# 🔧 Fix imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from types import SimpleNamespace
from app.services.predictor import ai_predict


async def test():

    req = SimpleNamespace(
        sport="soccer",
        league="soccer/KSA.1",
        event_id="756161",
        home_team="Al Qadsiah",
        away_team="Al Shabab"
    )

    print("\n🚀 Running local test...\n")

    result = await ai_predict(req)

    # ======================================================
    # 🔥 DEBUG CLAVE (BTTS)
    # ======================================================
    try:
        btts_prop = next(
            p for p in result.get("player_props", [])
            if p.get("type") == "btts"
        )

        print("\n⚽ BTTS DEBUG:")
        print("Model Prob Over:", btts_prop.get("model_prob_over"))
        print("Model Prob Under:", btts_prop.get("model_prob_under"))
        print("Over Odds:", btts_prop.get("over_odds"))
        print("Edge Over:", btts_prop.get("edge_over"))
        print("Bet Tier:", btts_prop.get("bet_tier"))

        # 🚨 Validación crítica
        assert btts_prop.get("model_prob_over") is not None, "❌ BTTS sigue en NULL"

    except StopIteration:
        print("❌ No se encontró prop BTTS")

    except AssertionError as e:
        print(e)

    # ======================================================
    # 📊 OUTPUT COMPLETO
    # ======================================================
    print("\n🔥 FULL RESULT:\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(test())