# Baltimore Triage

**Where is Baltimore bad, and the city not responding?** A marimo notebook that doubles as a web app. It scores
all 55 Community Statistical Areas on need vs service across 10 topics, then zooms from the whole city down to the
street address of every still-open request.

![The map explorer zoomed into one area](docs/app.png)

## Run it

You need [uv](https://docs.astral.sh/uv/). Every dependency is pinned inside `script.py`, so this is all:

```bash
# The web app (code hidden)
uvx marimo run --sandbox script.py

# The notebook (code visible, editable)
uvx marimo edit --sandbox script.py
```

It works offline: the analysis uses the saved snapshot in `data/`. With internet, a banner also shows live counts.
Delete `data/` to download a fresh snapshot from Open Baltimore (about 2 minutes).

**Share a view:** add `?area=` to the app URL, for example `http://localhost:2718/?area=Cherry%20Hill`.

## Deploy to GitHub Pages

The Pages build runs the app entirely in the browser with marimo WebAssembly. It serves the saved snapshot and
audio from `public/`, disables live API calls, and loads the expensive fix-clock/model outputs from the checked-in
`data/precomputed/` cache.

Test the same build locally:

```bash
python scripts/build_pages_assets.py
python -m marimo export html-wasm script.py -o dist --mode run --execute --no-sandbox
python -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`. To publish, set **Settings → Pages → Source** to **GitHub Actions** and push
`main` or `feature/github-pages-deployment`. The workflow in `.github/workflows/pages.yml` builds and deploys the
site. `public/data/` and `dist/` are generated artifacts and are intentionally ignored by git.

## What's inside

| File | What it is |
| --- | --- |
| `script.py` | The notebook and app: story, map explorer (a custom anywidget), scoring, checks |
| `app.css` | App styling (hero header, section headings, sidebar links) |
| `data/` | Snapshot of 9 Open Baltimore and BNIA datasets (2026-09-18) |
| `data/precomputed/` | Cached model outputs used by local and browser builds |
| `scripts/build_pages_assets.py` | Copies and simplifies browser-served data into `public/` |
| `.github/workflows/pages.yml` | Builds and deploys the interactive WASM app |
| `Bmore_plan.md` | Project plan and method |
| `agent_log.md` | Notes on using an AI coding agent: what helped, what went wrong |
| `marimo_feedback.md` | Our notes on marimo features, bugs and requests |

## The method in one paragraph

**Need** is how bad things are (resident 311 reports per 1,000 residents; open vacancy notices per 1,000 parcels).
**Service** is how well the city responds *as a share of that need*: for 311, how long a typical request stays
open (the share of the first 7 days already closed, read off the same time-to-fix clock as a single resident
call); for vacancy, the share of vacant buildings rehabbed or torn down since 2023; plus proactive city tickets
per resident report. Measuring service as a share, not a count, stops the worst areas from looking well served
just because they have the most problems. **Neglect** is not the difference between the two: service is regressed
on need within each
topic, and the score is how far *below* that fitted line an area sits, so it cannot just restate the need map.
Subtracting instead ranked areas at Spearman +0.88 with need alone. 2,000 random weightings show which areas stay
in the top 10 no matter what you care about.

## Organization response scores

Selecting a CSA on the map also updates an organization response section. For each organization and issue
component, it compares the local share of resident requests closed within the current **Fix days** setting with
that organization's citywide rate for the same component. The local-minus-citywide result is percentile-ranked
against comparable CSA/component cells; those component scores are then weighted by eligible request count into a
0–100 organization score. A score near 50 is typical after controlling for the organization and component, while
a higher score means the organization is resolving that area's requests faster than its usual citywide pace.

Only requests old enough to have received the full fix window count, and organization/component cells with fewer
than 10 eligible requests are not scored. Proactive tickets and known bulk administrative closes are excluded.
The responsibility table is derived from the `Agency` assigned on Baltimore's 311 records. It describes observed
routing—not legal responsibility—and a component can be split among multiple organizations.
