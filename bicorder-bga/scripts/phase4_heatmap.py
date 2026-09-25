"""Phase 4c — Build heatmap.html (divergence by category)."""
import pandas as pd

df = pd.read_csv("data/analysis/merged_cats.csv")
df = df[df["surprise_factor"].notna() & (df["category"].str.len() > 1)]

stats = (df.groupby("category")
           .agg(count=("bga_slug","count"),
                median_sf=("surprise_factor","median"),
                median_rating=("bgg_avg_rating","median"))
           .reset_index()
           .query("count >= 5")
           .sort_values("median_sf", ascending=False))

def sf_color(v):
    if pd.isna(v): return "var(--muted)"
    if v > 12:  return "#1a8c7e"
    if v > 6:   return "#5bb5ac"
    if v > 0:   return "#a8cbc8"
    if v > -6:  return "#c8b89a"
    return "#c4560e"

rows_html = ""
for _, r in stats.iterrows():
    col = sf_color(r.median_sf)
    rating_str = f"{r.median_rating:.2f}" if pd.notna(r.median_rating) else "—"
    rows_html += f"""<tr>
      <td>{r.category}</td>
      <td style="font-variant-numeric:tabular-nums;text-align:right">{int(r["count"])}</td>
      <td style="font-variant-numeric:tabular-nums;text-align:right">
        <span style="display:inline-block;background:{col};color:#fff;border-radius:4px;padding:2px 8px;font-weight:600">
          {r.median_sf:+.1f}
        </span>
      </td>
      <td style="font-variant-numeric:tabular-nums;text-align:right">
        {rating_str}
      </td>
    </tr>"""

HTML = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Divergence by Category</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=DM+Sans:wght@400;500&display=swap">
<style>
:root{{--bg:#f5f0e8;--surface:#fffcf6;--text:#1e1b2e;--muted:#6b6380;--border:#d9d3c4;}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{
  --bg:#0d1120;--surface:#141829;--text:#e8e2d5;--muted:#8b84a0;--border:#2c3050;color-scheme:dark;}}}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);padding:24px 16px;}}
h1{{font-family:'Fraunces',serif;font-size:1.6rem;margin-bottom:8px;}}
.sub{{font-size:.9rem;color:var(--muted);margin-bottom:20px;}}
table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:10px;overflow:hidden;border:1px solid var(--border);}}
th{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:10px 14px;text-align:left;border-bottom:1px solid var(--border);}}
td{{padding:8px 14px;font-size:13px;border-bottom:1px solid var(--border);}}
tr:last-child td{{border-bottom:none;}}
tr:hover td{{background:rgba(128,120,100,.05);}}
</style></head><body>
<h1>Surprise Factor by Category</h1>
<p class="sub">Median Protocol Bicorder Surprise Factor for BGG categories with ≥ 5 games on BGA. Sorted by median divergence.</p>
<table>
<thead><tr><th>Category</th><th style="text-align:right">Games</th><th style="text-align:right">Median SF</th><th style="text-align:right">Median BGG</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""

with open("data/analysis/heatmap.html","w") as f:
    f.write(HTML)
print(f"heatmap.html written ({len(stats)} categories)")
