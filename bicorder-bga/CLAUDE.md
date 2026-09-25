# Protocol Bicorder × Board Game Arena

Applies the Protocol Bicorder framework (Nathan Schneider / CU Boulder) to all
~1,400 games on Board Game Arena. Measures divergence between what each game's
rulebook signals and what the player community actually experiences, across six axes:

**trust-inducing · alive · emergent · social · flocking · exclusion/inclusion**

Divergence = community score − rule score per axis (1–9 scale each).
Surprise Factor = sum of six divergence values.

## Run order

Trigger each workflow manually in GitHub Actions (Actions tab → select workflow → Run workflow):

1. Phase 1 — game list + BGG metadata → `data/games.csv`
2. Phase 2 — text corpus → `data/corpus/*.json`
3. Phase 3 — bicorder scoring → `data/scores_clean.csv`
4. Phase 4 — analysis + visualizations → `data/analysis/`

Each workflow commits its output back to the repo. Phases are resumable:
scripts skip already-processed games by checking for cached output files.

## Secrets required

- `ANTHROPIC_API_KEY` — used in Phase 3 only (Claude Haiku for scoring)

## Data layout

data/
  games.csv              ← Phase 1 output (master game index)
  bgg_cache/             ← BGG API response cache (gitignored)
  corpus_raw/            ← Raw scraped text (gitignored)
  corpus/                ← Assembled corpus JSON per game (committed)
  scores.csv             ← Raw scoring output
  scores_clean.csv       ← Cleaned + derived columns
  analysis/
    scatter.html         ← Interactive BGG rating × Surprise Factor
    heatmap.html         ← Divergence by game category
    top-divergence.html  ← Ranked lists
    report.md            ← Narrative findings
