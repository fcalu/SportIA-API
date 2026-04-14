import sys
import os
import asyncio

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

    result = await ai_predict(req)

    print("\n🔥 RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(test())