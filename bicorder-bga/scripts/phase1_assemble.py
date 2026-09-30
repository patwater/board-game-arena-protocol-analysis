"""Phase 1d — Assemble games.csv."""
import json, sys, pandas as pd

with open("data/bga_raw.json") as f:
    games = json.load(f)

if not games:
    print("No games in data/bga_raw.json — phase1_fetch_bga.py found zero games. Aborting.")
    sys.exit(1)

df = pd.DataFrame(games)
numeric = ["bgg_avg_rating","bgg_num_ratings","bgg_weight",
           "bgg_min_players","bgg_max_players","bgg_min_playtime",
           "bgg_max_playtime","bgg_year"]
for col in numeric:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

sort_col = "bgg_avg_rating" if "bgg_avg_rating" in df.columns else "bga_name"
df = df.sort_values(sort_col, ascending=False, na_position="last")
df.to_csv("data/games.csv", index=False)

print(f"Total games: {len(df)}")
if "bgg_id" in df.columns:
    print(f"With BGG match: {df.bgg_id.notna().sum()}")
if "match_confidence" in df.columns:
    print(f"Manual review needed: {(df.match_confidence == 'manual').sum()}")
if "bgg_avg_rating" in df.columns:
    print(f"Rating range: {df.bgg_avg_rating.min():.2f} – {df.bgg_avg_rating.max():.2f}")
cols = [c for c in ["bga_name","bgg_avg_rating","bgg_weight","bgg_rank"] if c in df.columns]
print(df[cols].head(20).to_string())
