"""Phase 1b — Match BGA games to BGG IDs."""
import requests, json, os, time, xml.etree.ElementTree as ET
from thefuzz import fuzz
from tqdm import tqdm

os.makedirs("data/bgg_cache", exist_ok=True)

with open("data/bga_raw.json") as f:
    games = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)"}
SLEEP = 1.2

def search_bgg(name, exact=True):
    params = {"query": name, "type": "boardgame"}
    if exact:
        params["exact"] = 1
    r = requests.get("https://boardgamegeek.com/xmlapi2/search",
                     params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    results = []
    for item in root.findall("item"):
        bgg_id = item.get("id")
        name_el = item.find("name[@type='primary']")
        bgg_name = name_el.get("value") if name_el is not None else ""
        year_el = item.find("yearpublished")
        year = int(year_el.get("value", 0)) if year_el is not None else 0
        results.append({"bgg_id": bgg_id, "bgg_name": bgg_name, "year": year})
    return results

for g in tqdm(games, desc="Matching BGG"):
    slug = g["bga_slug"]
    cache = f"data/bgg_cache/{slug}_search.json"
    if os.path.exists(cache):
        with open(cache) as f:
            g.update(json.load(f))
        continue

    name = g["bga_name"]
    match = {"bgg_id": None, "bgg_name": None, "match_confidence": "none"}

    try:
        results = search_bgg(name, exact=True)
        time.sleep(SLEEP)
        if not results:
            results = search_bgg(name, exact=False)
            time.sleep(SLEEP)

        if results:
            # Pick best fuzzy match
            best = max(results, key=lambda x: fuzz.token_sort_ratio(name.lower(), x["bgg_name"].lower()))
            score = fuzz.token_sort_ratio(name.lower(), best["bgg_name"].lower())
            if score >= 70:
                match = {"bgg_id": best["bgg_id"], "bgg_name": best["bgg_name"],
                         "match_confidence": "high" if score >= 90 else "fuzzy"}
            else:
                match = {"bgg_id": None, "bgg_name": None, "match_confidence": "manual"}
    except Exception as e:
        match["error"] = str(e)

    g.update(match)
    with open(cache, "w") as f:
        json.dump(match, f)

with open("data/bga_raw.json", "w") as f:
    json.dump(games, f, indent=2)

matched = sum(1 for g in games if g.get("bgg_id"))
print(f"Matched {matched}/{len(games)} games to BGG IDs")
manual = sum(1 for g in games if g.get("match_confidence") == "manual")
print(f"Needs manual review: {manual}")
