"""Phase 1a — Fetch BGA game list."""
import requests, json, os, sys

os.makedirs("data", exist_ok=True)
OUT = "data/bga_raw.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)",
    "Referer": "https://boardgamearena.com",
}


def extract_balanced_array(text, start_idx):
    """text[start_idx] must be the opening '[' of a JSON array. Scan forward,
    tracking bracket depth while respecting string escaping, and return the
    substring up to (and including) the matching ']'."""
    depth = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
    raise ValueError("unbalanced JSON array")


def fetch_game_list():
    # boardgamearena.com redirects to en.boardgamearena.com; requests follows
    # redirects by default. The page embeds the full game catalog as a
    # "game_list" JSON array inside the initial app-state <script> block
    # (confirmed live: 1388 entries, matching BGA's ~1,400-game catalog).
    r = requests.get("https://boardgamearena.com/gamelist", headers=HEADERS, timeout=20)
    print(f"GET /gamelist -> status={r.status_code} final_url={r.url} length={len(r.text)}")
    r.raise_for_status()
    html = r.text

    key = '"game_list":['
    idx = html.find(key)
    if idx == -1:
        print("=== DIAGNOSTIC: 'game_list' key not found in response ===")
        print(f"Response length: {len(html)} chars")
        print("First 3000 characters of response body:")
        print(html[:3000])
        return []

    array_str = extract_balanced_array(html, idx + len(key) - 1)
    raw_games = json.loads(array_str)

    games = []
    for g in raw_games:
        slug = g.get("name")
        if not slug:
            continue
        games.append({
            "bga_slug": slug,
            "bga_name": g.get("display_name_en") or slug,
            "bga_rules_url": f"https://boardgamearena.com/gamepanel?game={slug}",
            "bga_status": g.get("status"),
            # BGA tags most games with the authoritative BGG id directly;
            # phase1_match_bgg.py only needs to search for the remainder.
            "bgg_id": str(g["bgg_id"]) if g.get("bgg_id") else None,
        })
    return games


games = fetch_game_list()

with open(OUT, "w") as f:
    json.dump(games, f, indent=2)

print(f"Found {len(games)} games on BGA → {OUT}")
have_bgg = sum(1 for g in games if g.get("bgg_id"))
print(f"Already BGG-tagged by BGA: {have_bgg}/{len(games)}")

if not games:
    sys.exit(1)
