import httpx
from app.clients.espn_player_stats import get_player_stats

BASE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2026/teams"


# ==========================================================
# TEAM ROSTER LOADER
# ==========================================================
async def get_team_roster(team_id: str):

    url = f"{BASE}/{team_id}/athletes?lang=en&region=us"

    print(f"\n📡 FETCH ROSTER → TEAM {team_id}")
    print(f"🌐 URL → {url}")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

        players = []

        items = data.get("items", [])
        print(f"👥 PLAYERS FOUND → {len(items)}")

        for item in items:
            ref = item["$ref"]

            pr = await client.get(ref)
            pr.raise_for_status()
            p = pr.json()

            raw_player = {
                "id": p.get("id"),
                "fullName": p.get("displayName"),
                "position": {
                    "abbreviation": p.get("position", {}).get("abbreviation", "SF")
                },
                "teamId": team_id
            }

            norm = await normalize_player(raw_player)
            players.append(norm)

    print(f"✅ NORMALIZED PLAYERS → {len(players)}")
    return players


# ==========================================================
# PLAYER NORMALIZER — PRODUCTION SAFE + DEBUG
# ==========================================================
async def normalize_player(raw):

    player_id = raw["id"]
    pos = raw.get("position", {}).get("abbreviation", "SF")

    print(f"\n🧪 NORMALIZING PLAYER → {raw.get('fullName')} ({player_id})")

    stats = await get_player_stats(player_id)

    print("📊 RAW STATS →", stats)

    # ===============================
    # FALLBACK SAFE EXTRACTION
    # ===============================
    if not stats:
        print("⚠️ NO STATS → USING DEFAULTS")
        minutes, pts, reb, ast = 18, 6, 3, 2
    else:
        minutes = (
            stats.get("minutes")
            or stats.get("avgMinutes")
            or stats.get("minutesPerGame")
            or 18
        )

        pts = (
            stats.get("points")
            or stats.get("avgPoints")
            or stats.get("pointsPerGame")
            or 6
        )

        reb = (
            stats.get("rebounds")
            or stats.get("avgRebounds")
            or stats.get("reboundsPerGame")
            or 3
        )

        ast = (
            stats.get("assists")
            or stats.get("avgAssists")
            or stats.get("assistsPerGame")
            or 2
        )

    # ===============================
    # HARD PROTECTION AGAINST ZERO
    # ===============================
    if not minutes or minutes == 0:
        print("⚠️ MINUTES = 0 → FORCING 18")
        minutes = 18

    # ===============================
    # RATE CALCULATIONS
    # ===============================
    ppm = pts / minutes if minutes else 0
    rpm = reb / minutes if minutes else 0
    apm = ast / minutes if minutes else 0

    usage = min(0.32, max(0.14, ppm * 1.45))

    normalized = {
        "id": player_id,
        "name": raw["fullName"],
        "position": pos,
        "role": "Primary" if usage > 0.25 else "Secondary",
        "base_minutes": round(minutes, 2),
        "usage_rate": round(usage, 3),
        "points_per_min": round(ppm, 3),
        "reb_per_min": round(rpm, 3),
        "ast_per_min": round(apm, 3)
    }

    print("✅ NORMALIZED →", normalized)

    return normalized
   