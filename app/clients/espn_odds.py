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

    # ======================================================
    # 🔎 EXTRAER DRAW MONEYLINE (SOCCER)
    # ======================================================

    draw_moneyline = None

    if sport == "soccer":

        links = book.get("links", [])

        for link in links:
            rel = link.get("rel", [])
            href = link.get("href", "")

            # ESPN usa "draw" en rel
            if "draw" in rel:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        draw_resp = await client.get(href)
                        if draw_resp.status_code == 200:
                            draw_data = draw_resp.json()
                            draw_moneyline = draw_data.get("moneyLine")
                except Exception:
                    draw_moneyline = None

    # ======================================================
    # RETURN STRUCTURE
    # ======================================================

    return {
        "provider": book.get("provider", {}).get("name", "Unknown"),
        "raw_details": book.get("details"),

        # 🔥 MERCADOS PRINCIPALES
        "spread": book.get("spread"),
        "over_under": book.get("overUnder"),

        # 💰 MONEYLINE
        "home_moneyline": book.get("homeTeamOdds", {}).get("moneyLine"),
        "away_moneyline": book.get("awayTeamOdds", {}).get("moneyLine"),
        "draw_moneyline": draw_moneyline,  # ← NUEVO

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

        # ⚖️ ODDS
        "over_odds": book.get("overOdds"),
        "under_odds": book.get("underOdds"),
        "home_spread_odds": book.get("homeTeamOdds", {}).get("spreadOdds"),
        "away_spread_odds": book.get("awayTeamOdds", {}).get("spreadOdds"),
    }