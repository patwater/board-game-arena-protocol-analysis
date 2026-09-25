"""Phase 3b — Post-process scores."""
import pandas as pd

df = pd.read_csv("data/scores.csv")

# Deduplicate (keep last score per game in case of re-runs)
df = df.drop_duplicates(subset="bga_slug", keep="last").reset_index(drop=True)

# Drop rows with no divergence data at all
div_cols = [c for c in df.columns if c.startswith("div_")]
df = df[df[div_cols].notna().any(axis=1)].copy()

# Derived columns
df["surprise_abs"] = df[div_cols].abs().sum(axis=1, skipna=True)

def bucket(sf):
    if pd.isna(sf): return None
    if abs(sf) < 6: return "low"
    if abs(sf) <= 18: return "moderate"
    return "high"

df["surprise_bucket"] = df["surprise_factor"].apply(bucket)

def leg_type(row):
    sf = row.get("surprise_factor")
    rating = row.get("bgg_avg_rating")
    if pd.isna(sf) or pd.isna(rating): return None
    if sf > 6 and rating >= 7.5: return "transcendent"
    if sf <= 6 and rating >= 7.5: return "legible"
    if sf > 6 and rating < 7.5: return "hidden"
    return "workmanlike"

df["legibility_type"] = df.apply(leg_type, axis=1)

df.to_csv("data/scores_clean.csv", index=False)
print(f"Clean scores: {len(df)} games")
print(df["surprise_bucket"].value_counts())
print(df["legibility_type"].value_counts())
print(f"\nTop 10 by Surprise Factor:")
print(df.nlargest(10,"surprise_factor")[["bga_name","surprise_factor","bgg_avg_rating"]].to_string())
