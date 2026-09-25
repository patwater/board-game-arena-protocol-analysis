"""Phase 1a — Fetch BGA game list."""
import requests, json, os, time
from bs4 import BeautifulSoup

os.makedirs("data", exist_ok=True)
OUT = "data/bga_raw.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)",
    "Referer": "https://boardgamearena.com",
}

def fetch_game_list():
    # Try XHR endpoint first
    try:
        r = requests.get(
            "https://boardgamearena.com/gamelist",
            params={"query": "", "status": ""},
            headers=HEADERS, timeout=15
        )
        r.raise_for_status()
        # If JSON returned directly
        if r.headers.get("content-type","").startswith("application/json"):
            data = r.json()
            games = []
            for item in data.get("data", {}).get("games", []):
                slug = item.get("name") or item.get("id")
                name = item.get("display_name") or item.get("name", slug)
                games.append({"bga_slug": slug, "bga_name": name,
                               "bga_rules_url": f"https://boardgamearena.com/gamepanel?game={slug}"})
            if games:
                return games
    except Exception:
        pass

    # Fall back to HTML parsing
    r = requests.get("https://boardgamearena.com/gamelist", headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    games = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "gamepanel?game=" in href or "/gamepanel/" in href:
            slug = href.split("game=")[-1].split("&")[0].strip("/").split("/")[-1]
            if slug and slug not in seen:
                seen.add(slug)
                name = a.get_text(strip=True) or slug
                games.append({"bga_slug": slug, "bga_name": name,
                               "bga_rules_url": f"https://boardgamearena.com/gamepanel?game={slug}"})
    return games

games = fetch_game_list()
with open(OUT, "w") as f:
    json.dump(games, f, indent=2)
print(f"Found {len(games)} games on BGA → {OUT}")
