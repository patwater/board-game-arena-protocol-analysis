"""Phase 4d — Build top-divergence.html."""
import pandas as pd

df = pd.read_csv("data/analysis/merged.csv")
df = df[df["surprise_factor"].notna()].copy()
top = df.nlargest(50,"surprise_factor")[["bga_name","surprise_factor","bgg_avg_rating","bgg_weight","bgg_categories"]]
bot = df.nsmallest(50,"surprise_factor")[["bga_name","surprise_factor","bgg_avg_rating","bgg_weight","bgg_categories"]]

def table_rows(sub):
    rows = ""
    for i,(_, r) in enumerate(sub.iterrows(),1):
        sf = r.surprise_factor
        col = "#1a8c7e" if sf > 0 else "#c4560e"
        rating_str = f"{r.bgg_avg_rating:.2f}" if pd.notna(r.bgg_avg_rating) else "—"
        rows += f"""<tr>
          <td style="color:var(--muted);font-variant-numeric:tabular-nums">{i}</td>
          <td style="font-weight:500">{r.bga_name}</td>
          <td style="color:{col};font-weight:600;font-variant-numeric:tabular-nums;text-align:right">{sf:+.1f}</td>
          <td style="font-variant-numeric:tabular-nums;text-align:right">{rating_str}</td>
          <td style="font-size:11px;color:var(--muted)">{str(r.bgg_categories or "").split(",")[0].strip()}</td>
        </tr>"""
    return rows

HTML = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Top Divergence Games</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=DM+Sans:wght@400;500&display=swap">
<style>
:root{{--bg:#f5f0e8;--surface:#fffcf6;--text:#1e1b2e;--muted:#6b6380;--border:#d9d3c4;--accent:#b8710d;}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{
  --bg:#0d1120;--surface:#141829;--text:#e8e2d5;--muted:#8b84a0;--border:#2c3050;--accent:#f0a820;color-scheme:dark;}}}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);padding:24px 16px;}}
h1{{font-family:'Fraunces',serif;font-size:1.6rem;margin-bottom:8px;}}
.sub{{font-size:.9rem;color:var(--muted);margin-bottom:20px;}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px;}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr;}}}}
h2{{font-family:'Fraunces',serif;font-size:1.1rem;margin-bottom:12px;color:var(--accent);}}
table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:10px;overflow:hidden;border:1px solid var(--border);font-size:12.5px;}}
th{{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:8px 10px;text-align:left;border-bottom:1px solid var(--border);}}
td{{padding:6px 10px;border-bottom:1px solid var(--border);}}
tr:last-child td{{border-bottom:none;}}
</style></head><body>
<h1>Highest & Lowest Surprise Factor</h1>
<p class="sub">Top and bottom 50 games by total Protocol Bicorder divergence across all scored BGA titles.</p>
<div class="grid">
  <div>
    <h2>Most emergent (highest divergence)</h2>
    <table><thead><tr><th>#</th><th>Game</th><th style="text-align:right">SF</th><th style="text-align:right">BGG</th><th>Category</th></tr></thead>
    <tbody>{table_rows(top)}</tbody></table>
  </div>
  <div>
    <h2>Most legible (lowest / negative divergence)</h2>
    <table><thead><tr><th>#</th><th>Game</th><th style="text-align:right">SF</th><th style="text-align:right">BGG</th><th>Category</th></tr></thead>
    <tbody>{table_rows(bot)}</tbody></table>
  </div>
</div>
</body></html>"""

with open("data/analysis/top-divergence.html","w") as f:
    f.write(HTML)
print("top-divergence.html written")
