"""Phase 1a — Fetch BGA game list."""
import requests, json, os, re, sys
from bs4 import BeautifulSoup

os.makedirs("data", exist_ok=True)
OUT = "data/bga_raw.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://boardgamearena.com",
}

GAME_LINK_RE = re.compile(r'/gamepanel\?game=([a-z0-9_]+)', re.IGNORECASE)


def extract_from_anchors(soup):
    games, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "gamepanel?game=" in href or "/gamepanel/" in href:
            slug = href.split("game=")[-1].split("&")[0].strip("/").split("/")[-1]
            if slug and slug not in seen:
                seen.add(slug)
                name = a.get_text(strip=True) or slug
                games.append({"bga_slug": slug, "bga_name": name})
    return games


def extract_from_regex(html):
    """Fallback in case the links are present in the raw markup but BeautifulSoup's
    parser doesn't expose them as clean <a> tags (e.g. malformed HTML, attributes
    split across a client-side template)."""
    games, seen = [], set()
    for slug in GAME_LINK_RE.findall(html):
        if slug not in seen:
            seen.add(slug)
            games.append({"bga_slug": slug, "bga_name": slug})
    return games


def extract_from_embedded_json(html):
    """SPA-style pages often ship their initial data as a JSON blob inside a
    <script> tag rather than as server-rendered links. Scan script bodies for
    JSON objects/arrays that look like game entries."""
    games, seen = [], set()
    for script_text in re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
        if "game" not in script_text.lower():
            continue
        for m in re.finditer(r'(\{[^{}]{0,400}\}|\[[^\[\]]{0,4000}\])', script_text, re.DOTALL):
            snippet = m.group(1)
            if len(snippet) < 40 or '"' not in snippet:
                continue
            try:
                data = json.loads(snippet)
            except Exception:
                continue
            candidates = data if isinstance(data, list) else [data]
            for item in candidates:
                if isinstance(item, dict) and any(k in item for k in ("slug", "name", "id")):
                    slug = item.get("slug") or item.get("name") or item.get("id")
                    if isinstance(slug, str) and slug and slug not in seen:
                        seen.add(slug)
                        games.append({"bga_slug": slug, "bga_name": item.get("display_name", slug)})
    return games


def print_diagnostics(html):
    print("=== DIAGNOSTIC: no games found by any strategy ===")
    print(f"Response length: {len(html)} chars")
    print(f"'gamepanel' occurrences: {html.lower().count('gamepanel')}")
    print(f"'<script' tag count: {html.lower().count('<script')}")
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    print(f"<title>: {title_match.group(1).strip() if title_match else '(none found)'}")
    print("First 3000 characters of response body:")
    print(html[:3000])
    print("=== END DIAGNOSTIC ===")


def fetch_game_list():
    r = requests.get("https://boardgamearena.com/gamelist", headers=HEADERS, timeout=20)
    print(f"GET /gamelist -> status={r.status_code} content-type={r.headers.get('content-type')} "
          f"length={len(r.text)} final_url={r.url}")
    r.raise_for_status()
    html = r.text

    soup = BeautifulSoup(html, "lxml")
    games = extract_from_anchors(soup)
    print(f"Strategy 'anchors': found {len(games)} games")
    if games:
        return games, html

    games = extract_from_regex(html)
    print(f"Strategy 'regex': found {len(games)} games")
    if games:
        return games, html

    games = extract_from_embedded_json(html)
    print(f"Strategy 'embedded_json': found {len(games)} games")
    if games:
        return games, html

    return [], html


games, html = fetch_game_list()

for g in games:
    g.setdefault("bga_rules_url", f"https://boardgamearena.com/gamepanel?game={g['bga_slug']}")

with open(OUT, "w") as f:
    json.dump(games, f, indent=2)

print(f"Found {len(games)} games on BGA → {OUT}")

if not games:
    print_diagnostics(html)
    sys.exit(1)
