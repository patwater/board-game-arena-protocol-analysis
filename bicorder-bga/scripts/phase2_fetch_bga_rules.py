"""Phase 2a — Fetch BGA rules pages."""
import requests, pandas as pd, os, time, re
from bs4 import BeautifulSoup
from tqdm import tqdm

os.makedirs("data/corpus_raw", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

df = pd.read_csv("data/games.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BicorderBot/1.0)",
           "Referer": "https://boardgamearena.com"}
SLEEP = 1.0

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_rules(slug):
    urls = [
        f"https://boardgamearena.com/gamepanel?game={slug}",
        f"https://boardgamearena.com/learn-to-play/{slug}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            # Remove nav/footer
            for tag in soup(["nav","header","footer","script","style"]):
                tag.decompose()
            # Try targeted selectors first
            for sel in ["#help_section", ".help-content", "#rules", ".game-rules",
                        "[data-section='rules']", ".gamepanel-rules"]:
                el = soup.select_one(sel)
                if el:
                    text = clean_text(el.get_text(separator=" ", strip=True))
                    if len(text.split()) > 80:
                        return text
            # Fall back to main content
            main = soup.find("main") or soup.find("article") or soup.body
            if main:
                text = clean_text(main.get_text(separator=" ", strip=True))
                if len(text.split()) > 80:
                    return text[:5000]
        except Exception:
            continue
    return ""

errors = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="BGA rules"):
    slug = row["bga_slug"]
    out = f"data/corpus_raw/{slug}_bga_rules.txt"
    if os.path.exists(out):
        continue
    text = fetch_rules(slug)
    with open(out, "w") as f:
        f.write(text)
    if not text:
        errors.append(slug)
    time.sleep(SLEEP)

print(f"Done. Missing rules text: {len(errors)}")
if errors:
    with open("data/logs/phase2_missing_rules.txt","w") as f:
        f.write("\n".join(errors))
