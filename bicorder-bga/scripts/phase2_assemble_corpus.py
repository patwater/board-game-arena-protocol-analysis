"""Phase 2d — Assemble corpus JSON per game."""
import json, os, pandas as pd
from tqdm import tqdm
from datetime import datetime

os.makedirs("data/corpus", exist_ok=True)
df = pd.read_csv("data/games.csv")

def word_count(text):
    return len(text.split()) if text else 0

def load_text(path):
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return ""

def load_reviews(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

summary_rows = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Assembling corpus"):
    slug = row["bga_slug"]
    name = row["bga_name"]
    out = f"data/corpus/{slug}.json"
    if os.path.exists(out):
        continue

    bga_rules = load_text(f"data/corpus_raw/{slug}_bga_rules.txt")
    bgg_desc  = load_text(f"data/corpus_raw/{slug}_bgg_desc.txt")
    reviews   = load_reviews(f"data/corpus_raw/{slug}_bgg_reviews.json")

    # Rules text: BGA rules page + BGG description
    rules_parts = [p for p in [bga_rules, bgg_desc] if p]
    rules_text = "\n\n---\n\n".join(rules_parts)
    # Trim to ~3000 words
    words = rules_text.split()
    if len(words) > 3000:
        rules_text = " ".join(words[:3000])
    rules_sources = (["bga_rules"] if bga_rules else []) + (["bgg_description"] if bgg_desc else [])

    # Community text: concatenate reviews
    comm_parts = [f"[Rating: {r['rating']}/10] {r['text']}" for r in reviews]
    community_text = "\n\n".join(comm_parts)
    words_c = community_text.split()
    if len(words_c) > 4000:
        community_text = " ".join(words_c[:4000])

    rw = word_count(rules_text)
    cw = word_count(community_text)
    if rw > 200 and cw > 200:
        quality = "good"
    elif rw > 0 and cw == 0:
        quality = "rules_only"
    elif rw == 0 and cw > 0:
        quality = "community_only"
    elif rw > 0 or cw > 0:
        quality = "thin"
    else:
        quality = "empty"

    corpus = {
        "bga_slug": slug, "bga_name": name,
        "bgg_id": str(row.get("bgg_id", "")),
        "rules_text": rules_text, "rules_sources": rules_sources,
        "community_text": community_text,
        "community_sources": ["bgg_reviews"] if reviews else [],
        "community_review_count": len(reviews),
        "rules_word_count": rw, "community_word_count": cw,
        "corpus_quality": quality,
        "fetched_at": datetime.utcnow().isoformat(),
    }
    with open(out, "w") as f:
        json.dump(corpus, f, indent=2)

    summary_rows.append({"bga_slug": slug, "bga_name": name,
                          "corpus_quality": quality, "rules_word_count": rw,
                          "community_review_count": len(reviews),
                          "community_word_count": cw,
                          "low_confidence": len(reviews) < 3})

pd.DataFrame(summary_rows).to_csv("data/corpus_summary.csv", index=False)
summary = pd.DataFrame(summary_rows)
print(summary.corpus_quality.value_counts().to_string())
print(f"Low confidence: {summary.low_confidence.sum()}")
