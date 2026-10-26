"""Phase 2c — Fetch BGG reviews."""
import requests, json, os, time, xml.etree.ElementTree as ET, html, re
import pandas as pd
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

os.makedirs("data/corpus_raw", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

df = pd.read_csv("data/games.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)"}
SLEEP = 1.2

# See phase1_fetch_meta.py for background: BGG's XML API has required a
# registered application + Bearer token since 2025-07-02.
BGG_API_TOKEN = os.environ.get("BGG_API_TOKEN")
if BGG_API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {BGG_API_TOKEN}"

def is_english(text):
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return len(text) > 0 and ascii_chars / len(text) > 0.75

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
def fetch_reviews(bgg_id, page=1):
    r = requests.get(
        "https://boardgamegeek.com/xmlapi2/thing",
        params={"id": bgg_id, "ratingcomments": 1, "pagesize": 50, "page": page},
        headers=HEADERS, timeout=20
    )
    r.raise_for_status()
    root = ET.fromstring(r.text)
    reviews = []
    for c in root.findall(".//comment"):
        rating = c.get("rating", "")
        text = html.unescape(c.get("value", "")).strip()
        if len(text) > 80 and is_english(text):
            reviews.append({"rating": rating, "text": text[:600]})
    return reviews

if not BGG_API_TOKEN:
    print("BGG_API_TOKEN is not set — skipping BGG review fetch entirely.")
    print("Register an application at https://boardgamegeek.com/applications, "
          "create a token, and set it as BGG_API_TOKEN to enable this step. "
          "Downstream corpus assembly treats missing reviews as community_review_count=0.")

errors = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="BGG reviews"):
    slug = row["bga_slug"]
    bgg_id = row.get("bgg_id")
    out = f"data/corpus_raw/{slug}_bgg_reviews.json"
    if os.path.exists(out) or not bgg_id or str(bgg_id) == "nan":
        continue
    if not BGG_API_TOKEN:
        with open(out, "w") as f:
            json.dump([], f)
        continue
    try:
        reviews = fetch_reviews(str(int(float(bgg_id))))
        # Try page 2 if mostly non-English on page 1
        if len(reviews) < 5:
            time.sleep(SLEEP)
            reviews += fetch_reviews(str(int(float(bgg_id))), page=2)
        reviews = reviews[:25]
        with open(out, "w") as f:
            json.dump(reviews, f)
        time.sleep(SLEEP)
    except Exception as e:
        errors.append(f"{slug}: {e}")
        with open(out, "w") as f:
            json.dump([], f)

print(f"Done. Errors: {len(errors)}")
if errors:
    with open("data/logs/phase2_review_errors.txt","w") as f:
        f.write("\n".join(errors))
