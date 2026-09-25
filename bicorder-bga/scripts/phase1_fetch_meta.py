"""Phase 1c — Fetch BGG metadata for matched games."""
import requests, json, os, time, xml.etree.ElementTree as ET, html
from tqdm import tqdm

os.makedirs("data/bgg_cache", exist_ok=True)

with open("data/bga_raw.json") as f:
    games = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)"}
SLEEP = 1.2

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
