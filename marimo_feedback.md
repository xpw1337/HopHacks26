# marimo feedback

Raw notes for the "marimo feedback" section (strongly recommended by the rubric under Interactivity). Write things down as they happen. Real, specific notes beat general praise.

All notes below are from marimo 0.24.2, 2026-09-19.

## What worked well

- One scoring function feeds the map, scatter, Gap Card, robust top 10 and CSV. Moving a slider re-runs only what depends on it, so every panel always agrees.
- `mo.ui.anywidget`: the Gap Card is ~70 lines of plain JS. Its `focus` trait comes back to Python as `gap_card.value["focus"]` and drives the map with no extra wiring.
- `app.run()` returns `(outputs, defs)`, so we could test the whole notebook from a plain Python script.
- `marimo check` (lint) and `marimo export html` gave a quick "does it run clean" test.
- `mo.accordion` keeps the data checks one click away.

## What was hard or confusing

- `mo.ui.altair_chart` turns off selection on geoshape (map) charts. Prints "Geoshapes + chart selection is not yet supported". We pick areas through the scatter plot + a dropdown instead.
- Layered Altair charts: `.value` is not available; you need `.apply_selection(df)`. Found by reading the source.
- `mo.ui.radio` has no `.selected_key` (but `mo.ui.dropdown` does).
- `mo.ui.dictionary` of sliders renders labels hard to read in dark mode. Rendering each slider in our own `hstack` fixed it.

## Bugs or surprises

- Full-detail boundaries (1.7 MB GeoJSON) made the map cell show an `output_max_bytes` error. Simplifying to ~10 m (65 KB) fixed it.
- `marimo run` / `marimo export` on a notebook with PEP 723 deps asks "Run in a sandboxed venv?" and aborts with no terminal. Pass `--sandbox` or `--no-sandbox`.
- In dark mode, the dropdown shows light text on a white box.

## What we'd ask the marimo team for

1. Click selection on Altair geoshape maps.
2. A clearer hint when a chart hits the output size limit ("your data is large, try simplifying it").
3. `.selected_key` on `mo.ui.radio`, to match `mo.ui.dropdown`.
