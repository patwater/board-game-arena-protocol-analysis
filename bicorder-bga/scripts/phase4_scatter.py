"""Phase 4b — Build scatter.html."""
import pandas as pd, json, os

df = pd.read_csv("data/analysis/merged.csv")
df = df[df["bgg_avg_rating"].notna() & df["surprise_factor"].notna()].copy()

# Prepare data payload
cols = ["bga_slug","bga_name","bgg_avg_rating","surprise_factor","bgg_weight",
        "bgg_num_ratings","bgg_categories","legibility_type","corpus_quality"]
records = df[cols].fillna("").to_dict("records")

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>BGG Rating × Surprise Factor</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;1,9..144,400&family=DM+Sans:wght@400;500;600&display=swap">
<style>
:root {{
  --bg:#f5f0e8; --surface:#fffcf6; --surface-2:#ece7db;
  --text:#1e1b2e; --muted:#6b6380; --accent:#b8710d; --border:#d9d3c4;
  --grid:rgba(100,90,80,.12);
  --c1:#1a7a8a; --c2:#c4560e; --c3:#5e3f9e; --c4:#2a7a3b;
}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{
  --bg:#0d1120;--surface:#141829;--surface-2:#1c2236;
  --text:#e8e2d5;--muted:#8b84a0;--accent:#f0a820;--border:#2c3050;
  --grid:rgba(200,190,180,.08);
  --c1:#3ecfba;--c2:#f0a820;--c3:#b090f8;--c4:#5cba70;
  color-scheme:dark;
}}}}
:root[data-theme=dark]{{
  --bg:#0d1120;--surface:#141829;--surface-2:#1c2236;
  --text:#e8e2d5;--muted:#8b84a0;--accent:#f0a820;--border:#2c3050;
  --grid:rgba(200,190,180,.08);
  --c1:#3ecfba;--c2:#f0a820;--c3:#b090f8;--c4:#5cba70;
  color-scheme:dark;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'DM Sans',system-ui,sans-serif;background:var(--bg);color:var(--text);
  padding-inline:16px;padding-block:24px;}}
h1{{font-family:'Fraunces',Georgia,serif;font-size:clamp(1.4rem,3vw,2rem);
  font-weight:600;margin-bottom:6px;}}
.sub{{font-size:.9rem;color:var(--muted);margin-bottom:20px;max-width:600px;}}
.controls{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px;align-items:center;}}
.controls label{{font-size:12px;color:var(--muted);font-weight:600;letter-spacing:.06em;text-transform:uppercase;}}
.controls input,.controls select{{
  background:var(--surface);border:1px solid var(--border);border-radius:6px;
  color:var(--text);padding:5px 10px;font-size:13px;font-family:inherit;}}
.chart-wrap{{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:16px;position:relative;margin-bottom:20px;overflow:visible;}}
svg#sc{{width:100%;height:auto;display:block;overflow:visible;}}
.tt{{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--border);
  border-radius:8px;padding:10px 14px;font-size:12.5px;line-height:1.5;max-width:220px;
  box-shadow:0 4px 20px rgba(0,0,0,.12);opacity:0;transition:opacity .12s;z-index:10;}}
.tt.v{{opacity:1;}}
.tt-n{{font-weight:600;margin-bottom:5px;}}
.tt-s{{display:flex;gap:14px;margin-bottom:5px;}}
.tt-s span{{font-size:11px;color:var(--muted);}}
.tt-s strong{{display:block;color:var(--text);font-size:13px;}}
.tt-cat{{font-size:11px;color:var(--muted);font-style:italic;}}
.note{{font-size:11px;color:var(--muted);font-style:italic;padding-top:10px;
  border-top:1px solid var(--border);margin-top:10px;}}
</style>
</head>
<body>
<h1>BGG Rating × Surprise Factor</h1>
<p class="sub">Protocol Bicorder divergence (community − rules score across 6 axes) vs. BoardGameGeek average rating. {len(records)} games.</p>
<div class="controls">
  <label>Min ratings</label>
  <input type="range" id="minRatings" min="0" max="5000" step="100" value="20">
  <span id="minRatingsVal" style="font-size:12px;color:var(--muted)">20</span>
  <label style="margin-left:12px">Search</label>
  <input type="text" id="search" placeholder="game name..." style="width:160px">
</div>
<div class="chart-wrap" id="cw">
  <svg id="sc" viewBox="0 0 700 440" aria-label="Scatter plot of BGG rating vs Surprise Factor"></svg>
  <div class="tt" id="tt"></div>
</div>
<p class="note">BGG ratings and bicorder scores are approximate. Divergence = community score − rules score per axis. Surprise Factor = sum across 6 axes.</p>
<script>
const DATA = {json.dumps(records)};
const VW=700,VH=440,ML=64,MR=22,MT=40,MB=54,PW=VW-ML-MR,PH=VH-MT-MB;
const XMIN=5.5,XMAX=9.5,YMIN=-52,YMAX=52;
const sx=b=>ML+(b-XMIN)/(XMAX-XMIN)*PW;
const sy=d=>MT+(1-(d-YMIN)/(YMAX-YMIN))*PH;
const QX=sx(7.5),QY=sy(6);
const typeColor={{"transcendent":"var(--c2)","legible":"var(--c1)","hidden":"var(--c3)","workmanlike":"var(--c4)"}};

let minR=20, searchTerm="";
document.getElementById("minRatings").addEventListener("input",e=>{{
  minR=+e.target.value;
  document.getElementById("minRatingsVal").textContent=e.target.value;
  render();
}});
document.getElementById("search").addEventListener("input",e=>{{
  searchTerm=e.target.value.toLowerCase(); render();
}});

function render(){{
  const svg=document.getElementById("sc");
  const filtered=DATA.filter(g=>(!minR||+g.bgg_num_ratings>=minR)&&+g.bgg_avg_rating>0&&g.surprise_factor!=="");
  let h="";
  // Quadrant fills
  h+=`<rect x="${{ML}}" y="${{MT}}" width="${{QX-ML}}" height="${{QY-MT}}" style="fill:rgba(94,63,158,.05)"/>`;
  h+=`<rect x="${{QX}}" y="${{MT}}" width="${{ML+PW-QX}}" height="${{QY-MT}}" style="fill:rgba(196,86,14,.07)"/>`;
  h+=`<rect x="${{ML}}" y="${{QY}}" width="${{QX-ML}}" height="${{MT+PH-QY}}" style="fill:rgba(150,140,130,.03)"/>`;
  h+=`<rect x="${{QX}}" y="${{QY}}" width="${{ML+PW-QX}}" height="${{MT+PH-QY}}" style="fill:rgba(26,122,138,.06)"/>`;
  // Grid
  [5.5,6,6.5,7,7.5,8,8.5,9,9.5].forEach(v=>{{
    const x=sx(v);
    h+=`<line x1="${{x}}" y1="${{MT}}" x2="${{x}}" y2="${{MT+PH}}" stroke="var(--grid)" stroke-width="1"/>`;
    h+=`<text x="${{x}}" y="${{MT+PH+16}}" text-anchor="middle" fill="var(--muted)" font-size="10" font-family="DM Sans,sans-serif">${{v}}</text>`;
  }});
  [-48,-36,-24,-12,0,12,24,36,48].forEach(v=>{{
    const y=sy(v);
    if(y<MT-2||y>MT+PH+2)return;
    h+=`<line x1="${{ML}}" y1="${{y}}" x2="${{ML+PW}}" y2="${{y}}" stroke="var(--grid)" stroke-width="1"/>`;
    h+=`<text x="${{ML-7}}" y="${{y+4}}" text-anchor="end" fill="var(--muted)" font-size="10" font-family="DM Sans,sans-serif">${{v>0?"+":""}}${{v}}</text>`;
  }});
  // Dividers
  h+=`<line x1="${{QX}}" y1="${{MT}}" x2="${{QX}}" y2="${{MT+PH}}" stroke="var(--border)" stroke-width="1.5" stroke-dasharray="4 3"/>`;
  h+=`<line x1="${{ML}}" y1="${{QY}}" x2="${{ML+PW}}" y2="${{QY}}" stroke="var(--border)" stroke-width="1.5" stroke-dasharray="4 3"/>`;
  // Quadrant labels
  const ql=(ML+QX)/2,qr=(QX+ML+PW)/2;
  const ql_style=`fill:var(--muted);font-size:8.5px;font-family:DM Sans,sans-serif;font-weight:600;letter-spacing:.09em;opacity:.6`;
  h+=`<text x="${{ql}}" y="${{MT+14}}" text-anchor="middle" style="${{ql_style}}">HIDDEN EMERGENCE</text>`;
  h+=`<text x="${{qr}}" y="${{MT+14}}" text-anchor="middle" style="${{ql_style}}">TRANSCENDENT</text>`;
  h+=`<text x="${{ql}}" y="${{MT+PH-7}}" text-anchor="middle" style="${{ql_style}}">WORKMANLIKE</text>`;
  h+=`<text x="${{qr}}" y="${{MT+PH-7}}" text-anchor="middle" style="${{ql_style}}">LEGIBLE EXCELLENCE</text>`;
  // Axis labels
  h+=`<text x="${{ML+PW/2}}" y="${{VH-4}}" text-anchor="middle" fill="var(--muted)" font-size="11" font-family="DM Sans,sans-serif" font-weight="500">BGG Average Rating →</text>`;
  h+=`<text x="16" y="${{MT+PH/2}}" text-anchor="middle" fill="var(--muted)" font-size="11" font-family="DM Sans,sans-serif" font-weight="500" transform="rotate(-90,16,${{MT+PH/2}})">← Surprise Factor</text>`;
  // Points
  filtered.forEach((g,i)=>{{
    const x=sx(+g.bgg_avg_rating),y=sy(+g.surprise_factor);
    if(x<ML||x>ML+PW||y<MT||y>MT+PH)return;
    const col=typeColor[g.legibility_type]||"var(--muted)";
    const hl=searchTerm&&g.bga_name.toLowerCase().includes(searchTerm);
    const r=hl?9:5, op=searchTerm&&!hl?0.2:0.75;
    h+=`<circle cx="${{x}}" cy="${{y}}" r="${{r}}" style="fill:${{col}};stroke:var(--surface);stroke-width:1.5;opacity:${{op}};cursor:pointer" data-i="${{i}}" class="gp"/>`;
  }});
  svg.innerHTML=h;
  // Tooltip
  const tt=document.getElementById("tt"),cw=document.getElementById("cw");
  svg.querySelectorAll(".gp").forEach(el=>{{
    el.addEventListener("mouseenter",()=>{{
      const g=filtered[+el.dataset.i];
      tt.innerHTML=`<div class="tt-n">${{g.bga_name}}</div>
        <div class="tt-s">
          <span><strong>${{(+g.bgg_avg_rating).toFixed(2)}}</strong>BGG Rating</span>
          <span><strong>${{+g.surprise_factor>0?"+":""}}${{(+g.surprise_factor).toFixed(1)}}</strong>Surprise Factor</span>
          <span><strong>${{(+g.bgg_weight||0).toFixed(1)}}</strong>Weight</span>
        </div>
        <div class="tt-cat">${{g.bgg_categories?.split(",").slice(0,3).join(", ")||""}}</div>`;
      tt.classList.add("v");
    }});
    el.addEventListener("mousemove",e=>{{
      const r=cw.getBoundingClientRect();
      let tx=e.clientX-r.left+12,ty=e.clientY-r.top-30;
      if(tx+230>cw.offsetWidth)tx-=245;
      if(ty<0)ty=4;
      tt.style.left=tx+"px";tt.style.top=ty+"px";
    }});
    el.addEventListener("mouseleave",()=>tt.classList.remove("v"));
  }});
}}
render();
</script>
</body>
</html>"""

with open("data/analysis/scatter.html","w") as f:
    f.write(HTML)
print(f"scatter.html written ({len(records)} games)")
