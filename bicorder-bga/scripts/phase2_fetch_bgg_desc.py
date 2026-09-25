"""Phase 2b — Extract BGG descriptions from Phase 1 cache."""
import json, os, pandas as pd
from tqdm import tqdm

os.makedirs("data/corpus_raw", exist_ok=True)
df = pd.read_csv("data/games.csv")

for _, row in tqdm(df.iterrows(), total=len(df), desc="BGG descriptions"):
    slug = row["bga_slug"]
    out = f"data/corpus_raw/{slug}_bgg_desc.txt"
    if os.path.exists(out):
        continue
    cache = f"data/bgg_cache/{slug}_thing.json"
    if os.path.exists(cache):
        with open(cache) as f:
            data = json.load(f)
        desc = data.get("bgg_description", "")
    else:
        desc = str(row.get("bgg_description", "") or "")
    with open(out, "w") as f:
        f.write(desc)

print("BGG descriptions extracted.")
