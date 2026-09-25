"""Phase 1d — Assemble games.csv."""
import json, pandas as pd

with open("data/bga_raw.json") as f:
    games = json.load(f)

df = pd.DataFrame(games)
numeric = ["bgg_avg_rating","bgg_num_ratings","bgg_weight",
           "bgg_min_players","bgg_max_players","bgg_min_playtime",
           "bgg_max_playtime","bgg_year"]
for col in numeric:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.sort_values("bgg_avg_rating", ascending=False, na_position="last")
df.to_csv("data/games.csv", index=False)

print(f"Total games: {len(df)}")
print(f"With BGG match: {df.bgg_id.notna().sum()}")
print(f"Manual review needed: {(df.match_confidence == 'manual').sum()}")
if "bgg_avg_rating" in df.columns:
    print(f"Rating range: {df.bgg_avg_rating.min():.2f} – {df.bgg_avg_rating.max():.2f}")
print(df[["bga_name","bgg_avg_rating","bgg_weight","bgg_rank"]].head(20).to_string())
