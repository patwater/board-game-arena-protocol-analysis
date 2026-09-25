"""Phase 4a — Merge data for analysis."""
import pandas as pd, os
os.makedirs("data/analysis", exist_ok=True)

scores = pd.read_csv("data/scores_clean.csv")
games  = pd.read_csv("data/games.csv")[["bga_slug","bgg_categories","bgg_mechanics",
                                         "bgg_min_players","bgg_max_players","bgg_weight"]]
df = scores.merge(games, on="bga_slug", how="left", suffixes=("","_g"))

# Explode categories
df_cats = df.assign(category=df.bgg_categories.str.split(",")).explode("category")
df_cats["category"] = df_cats["category"].str.strip()
df_cats = df_cats[df_cats["category"].str.len() > 1]

df.to_csv("data/analysis/merged.csv", index=False)
df_cats.to_csv("data/analysis/merged_cats.csv", index=False)
print(f"Merged: {len(df)} games, {len(df_cats)} category rows")
print(f"Unique categories: {df_cats.category.nunique()}")
