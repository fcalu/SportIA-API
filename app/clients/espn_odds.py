import httpx


async def get_event_odds(sport: str, league: str, event_id: str):
    """
    Obtiene odds principales (spread, total, moneyline) desde ESPN Core API
    Compatible con NBA, NFL, Soccer
    """

    url = (
        f"https://sports.core.api.espn.com/v2/"
        f"sports/{sport}/leagues/{league}"
        f"/events/{event_id}/competitions/{event_id}/odds"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)

        if r.status_code != 200:
            return {}

        data = r.json()

    if not data.get("items"):
        return {}

    book = data["items"][0]  # Normalmente DraftKings

    return {
        "provider": book.get("provider", {}).get("name", "Unknown"),
        "raw_details": book.get("details"),

        # 🔥 MERCADOS PRINCIPALES
        "spread": book.get("spread"),
        "over_under": book.get("overUnder"),

        # 💰 MONEYLINE
        "home_moneyline": book.get("homeTeamOdds", {}).get("moneyLine"),
        "away_moneyline": book.get("awayTeamOdds", {}).get("moneyLine"),

        # 📉 SPREAD VISUAL
        "home_spread": book.get("homeTeamOdds", {})
                          .get("current", {})
                          .get("pointSpread", {})
                          .get("alternateDisplayValue"),

        "away_spread": book.get("awayTeamOdds", {})
                          .get("current", {})
                          .get("pointSpread", {})
                          .get("alternateDisplayValue"),

        # 🎯 TOTAL VISUAL
        "total": book.get("current", {})
                     .get("total", {})
                     .get("alternateDisplayValue"),

        # ⚖️ ODDS (por si quieres edge por precio luego)
        "over_odds": book.get("overOdds"),
        "under_odds": book.get("underOdds"),
        "home_spread_odds": book.get("homeTeamOdds", {}).get("spreadOdds"),
        "away_spread_odds": book.get("awayTeamOdds", {}).get("spreadOdds"),
    }
