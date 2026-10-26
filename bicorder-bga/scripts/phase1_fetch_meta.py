"""Phase 1c — Fetch BGG metadata for matched games."""
import requests, json, os, sys, time, xml.etree.ElementTree as ET, html
from tqdm import tqdm

os.makedirs("data/bgg_cache", exist_ok=True)

with open("data/bga_raw.json") as f:
    games = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)"}
SLEEP = 1.2

# BGG's XML API has required a registered application + Bearer token since
# 2025-07-02 (https://boardgamegeek.com/using_the_xml_api). Register an
# application at https://boardgamegeek.com/applications, create a token for
# it, and set BGG_API_TOKEN (as a repo secret in CI, or in your shell locally).
BGG_API_TOKEN = os.environ.get("BGG_API_TOKEN")
if BGG_API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {BGG_API_TOKEN}"

def fetch_thing(bgg_id):
    r = requests.get(f"https://boardgamegeek.com/xmlapi2/thing",
                     params={"id": bgg_id, "stats": 1}, headers=HEADERS, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    item = root.find("item")
    if item is None:
        return {}

    def val(path, attr="value"):
        el = item.find(path)
        return el.get(attr) if el is not None else None

    def vals(tag, attr="value"):
        return ",".join(l.get(attr, "") for l in item.findall(f"link[@type='{tag}']"))

    desc_el = item.find("description")
    desc = html.unescape(desc_el.text or "") if desc_el is not None else ""

    rank_el = item.find("statistics/ratings/ranks/rank[@type='subtype'][@name='boardgame']")
    rank = rank_el.get("value") if rank_el is not None else None

    return {
        "bgg_name_official": val("name[@type='primary']"),
        "bgg_avg_rating":    val("statistics/ratings/average"),
        "bgg_num_ratings":   val("statistics/ratings/usersrated"),
        "bgg_weight":        val("statistics/ratings/averageweight"),
        "bgg_min_players":   val("minplayers"),
        "bgg_max_players":   val("maxplayers"),
        "bgg_min_playtime":  val("minplaytime"),
        "bgg_max_playtime":  val("maxplaytime"),
        "bgg_year":          val("yearpublished"),
        "bgg_rank":          rank,
        "bgg_categories":    vals("boardgamecategory"),
        "bgg_mechanics":     vals("boardgamemechanic"),
        "bgg_description":   desc[:3000],
    }

def preflight():
    """Fail fast (or skip cleanly) instead of repeating the same failure
    across every game. Returns True if metadata fetching should proceed."""
    candidates = [g for g in games if g.get("bgg_id")]
    if not candidates:
        return False

    if not BGG_API_TOKEN:
        print("BGG_API_TOKEN is not set — skipping BGG metadata fetch entirely.")
        print("Register an application at https://boardgamegeek.com/applications, "
              "create a token, and set it as BGG_API_TOKEN to enable this step.")
        return False

    probe_id = candidates[0]["bgg_id"]
    r = requests.get("https://boardgamegeek.com/xmlapi2/thing",
                      params={"id": probe_id, "stats": 1}, headers=HEADERS, timeout=20)
    if r.status_code == 401:
        print("=== DIAGNOSTIC: BGG XML API returned 401 Unauthorized on preflight check ===")
        print(f"Probed id={probe_id}, status={r.status_code}")
        print(f"Response body: {r.text[:500]}")
        print("BGG_API_TOKEN is set but was rejected — check it's a valid, unexpired token")
        print("for an approved application at https://boardgamegeek.com/applications.")
        print("=== END DIAGNOSTIC ===")
        sys.exit(1)
    r.raise_for_status()
    return True


if not preflight():
    with open("data/bga_raw.json", "w") as f:
        json.dump(games, f, indent=2)
    sys.exit(0)

for g in tqdm(games, desc="BGG metadata"):
    if not g.get("bgg_id"):
        continue
    slug = g["bga_slug"]
    cache = f"data/bgg_cache/{slug}_thing.json"
    if os.path.exists(cache):
        with open(cache) as f:
            g.update(json.load(f))
        continue
    try:
        meta = fetch_thing(g["bgg_id"])
        g.update(meta)
        with open(cache, "w") as f:
            json.dump(meta, f)
        time.sleep(SLEEP)
    except Exception as e:
        print(f"Error on {slug}: {e}")

with open("data/bga_raw.json", "w") as f:
    json.dump(games, f, indent=2)
print("BGG metadata fetch complete.")
