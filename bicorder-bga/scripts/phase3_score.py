"""Phase 3a — Bicorder scoring via Claude API."""
import anthropic, json, os, time, re, pandas as pd
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

client = anthropic.Anthropic()
AXES = ["trust", "alive", "emergent", "social", "flocking", "inclusion"]
MODEL = "claude-haiku-4-5-20251001"

os.makedirs("data/logs", exist_ok=True)

EXTRACT_SYSTEM = """You are a protocol analyst working with the Protocol Bicorder framework.
Extract short passages (1-3 sentences each) from the provided text that are most relevant
to these six dimensions:
1. trust-inducing: does the game foster trust or adversarial dynamics?
2. alive: does the game feel dynamic and living, or scripted and static?
3. emergent: does coordination arise from rules, or emerge through play?
4. social: is it a solitary or deeply social experience?
5. flocking: do players optimize individually or coordinate collectively?
6. inclusion: who can play, and who is left out?

Return ONLY a JSON object:
{"trust": "...", "alive": "...", "emergent": "...", "social": "...", "flocking": "...", "inclusion": "..."}
If a dimension is not addressed, use an empty string. No other text."""

SCORE_SYSTEM = """You are scoring board game texts using the Protocol Bicorder framework.
Rate each dimension 1-9 based ONLY on what the text explicitly conveys.

Scale anchors (1→9):
- trust: adversarial → cooperative/trust-building
- alive: scripted/static → dynamic/living/unpredictable
- emergent: fully rule-prescribed → fully emergent through play
- social: solitary/isolated → deeply social/relational
- flocking: individual optimization → collective coordination
- inclusion: exclusionary/specialist → inclusive/accessible

Return ONLY a JSON object with float scores:
{"trust": N, "alive": N, "emergent": N, "social": N, "flocking": N, "inclusion": N}
No other text."""

def parse_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=30))
def call_claude(system, user_msg, max_tokens=400):
    msg = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user_msg}]
    )
    return msg.content[0].text

def extract_passages(text, name):
    if not text or len(text.strip()) < 50:
        return {ax: "" for ax in AXES}
    prompt = f"Extract passages from this text about {name}:\n\n{text[:3000]}"
    raw = call_claude(EXTRACT_SYSTEM, prompt, max_tokens=500)
    result = parse_json(raw)
    return {ax: result.get(ax, "") for ax in AXES}

def score_passages(passages, name, perspective):
    text = "\n".join(f"{k}: {v}" for k, v in passages.items() if v)
    if not text.strip():
        return {ax: None for ax in AXES}
    prompt = f"Rate this {perspective} text about {name}:\n\n{text}"
    raw = call_claude(SCORE_SYSTEM, prompt, max_tokens=200)
    result = parse_json(raw)
    return {ax: float(result[ax]) if ax in result else None for ax in AXES}

# Load existing scores for resumability
SCORES_PATH = "data/scores.csv"
if os.path.exists(SCORES_PATH):
    done = set(pd.read_csv(SCORES_PATH, usecols=["bga_slug"]).bga_slug)
else:
    done = set()

games_df = pd.read_csv("data/games.csv")
meta_cols = ["bga_slug","bgg_id","bgg_avg_rating","bgg_weight",
             "bgg_num_ratings","bgg_rank","bgg_categories","bgg_mechanics"]

rows = []
corpus_files = sorted(f for f in os.listdir("data/corpus") if f.endswith(".json"))

for fname in tqdm(corpus_files, desc="Scoring"):
    slug = fname.replace(".json","")
    if slug in done:
        continue
    with open(f"data/corpus/{fname}") as f:
        corpus = json.load(f)
    if corpus.get("corpus_quality") == "empty":
        continue

    name = corpus["bga_name"]
    try:
        rule_pass = extract_passages(corpus.get("rules_text",""), name)
        time.sleep(0.3)
        comm_pass = extract_passages(corpus.get("community_text",""), name)
        time.sleep(0.3)
        rule_scores = score_passages(rule_pass, name, "RULES")
        time.sleep(0.3)
        comm_scores = score_passages(comm_pass, name, "COMMUNITY")
        time.sleep(0.5)
    except Exception as e:
        with open("data/logs/phase3_errors.log","a") as log:
            log.write(f"{slug}: {e}\n")
        continue

    row = {"bga_slug": slug, "bga_name": name,
           "corpus_quality": corpus.get("corpus_quality"),
           "low_confidence": corpus.get("community_review_count", 0) < 3}
    for ax in AXES:
        r, c = rule_scores.get(ax), comm_scores.get(ax)
        row[f"rule_{ax}"] = r
        row[f"comm_{ax}"] = c
        row[f"div_{ax}"] = round(c - r, 2) if (r is not None and c is not None) else None

    valid = [row[f"div_{ax}"] for ax in AXES if row[f"div_{ax}"] is not None]
    row["surprise_factor"] = round(sum(valid), 2) if valid else None

    meta = games_df[games_df.bga_slug == slug][meta_cols].to_dict("records")
    if meta:
        row.update(meta[0])
    row["scored_at"] = pd.Timestamp.now().isoformat()
    rows.append(row)

    if len(rows) % 20 == 0:
        pd.DataFrame(rows).to_csv(
            SCORES_PATH, mode="a",
            header=not os.path.exists(SCORES_PATH) or os.path.getsize(SCORES_PATH) == 0,
            index=False)
        rows = []

if rows:
    pd.DataFrame(rows).to_csv(
        SCORES_PATH, mode="a",
        header=not os.path.exists(SCORES_PATH) or os.path.getsize(SCORES_PATH) == 0,
        index=False)

print(f"Scoring complete → {SCORES_PATH}")
