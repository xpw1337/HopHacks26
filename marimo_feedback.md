# marimo feedback

Raw notes for the "marimo feedback" section (strongly recommended by the rubric under Interactivity). Write things down as they happen. Real, specific notes beat general praise.

All notes below are from marimo 0.24.2, 2026-09-19.

## What worked well

- One scoring function feeds the map, scatter, Gap Card, robust top 10 and CSV. Moving a slider re-runs only what depends on it, so every panel always agrees.
- Same file, two products: `marimo edit` = notebook, `marimo run` = web app with code hidden. `mo.sidebar` (controls stay on screen), `App(css_file=...)` (hero styling) and `mo.query_params` (`?area=` share links) made it feel like a real app with no second codebase.
- `mo.ui.anywidget`: our map explorer (clickable SVG map + Gap Card + zoom to street-level dots) is plain JS, no map library. `selected` and `focus` come back to Python via `explorer.value`.
- A cell can push new data into a live widget (`widget.data = ...`); the browser redraws without re-creating it, so the selection survives slider moves. Verified in a throwaway test notebook first.
- `app.run()` returns `(outputs, defs)`, so we could test the whole notebook from a plain Python script.
- `marimo check` (lint) and `marimo export html` gave a quick "does it run clean" test.
- `mo.accordion` keeps the data checks one click away.

## What was hard or confusing

- `mo.ui.altair_chart` turns off selection on geoshape (map) charts. Prints "Geoshapes + chart selection is not yet supported". We ended up writing our own SVG map widget to get click-to-select.
- `mo.nav_menu` with `#section` links navigates to `/#section`. If the URL has a query (`?area=...`), that drops it and reloads the whole app. Plain `<a href="#section">` in `mo.Html` works.
- Not documented: does setting a widget trait from Python re-run cells that read `.value`? Source reading says no (only frontend changes do). Worth one line in the docs.
- `marimo run` uses marimo's own theme setting, not the browser's dark preference, so testing dark mode needed `[tool.marimo.display] theme = "dark"` in a pyproject.toml.
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
4. `mo.nav_menu` in-page links that keep the current query string.
