# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.24.2",
#     "polars==1.44.2",
#     "pyarrow",
#     "altair==6.3.0",
#     "numpy==2.5.3",
#     "shapely==2.1.2",
#     "httpx==0.28.1",
#     "anywidget==0.11.0",
#     "scikit-learn==1.7.2",
# ]
# ///

import marimo

__generated_with = "0.24.2"
# Full width so the maps can break the reading column. app.css puts prose back into a measure;
# without that, body text would run the width of the screen and be unreadable.
app = marimo.App(width="full", app_title="Baltimore Triage", css_file="app.css")


@app.cell
def _():
    import base64
    import json
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timedelta
    from pathlib import Path

    import altair as alt
    import anywidget
    import httpx
    import marimo as mo
    import numpy as np
    import polars as pl
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.isotonic import IsotonicRegression
    import shapely
    import traitlets

    @alt.theme.register("triage", enable=True)
    def _triage_theme():
        """One chart look for all fourteen of them, sharing the page's rules.

        Greyscale furniture, colour only where it carries data, and the same red-to-green ramp the
        maps use so a reader never has to learn two schemes. Gridlines sit well below the marks;
        the skill guidance is explicit that they should not compete with the data.
        """
        _sans = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
        _ink, _muted, _rule = "#0b1116", "#7d8fa0", "#e3e8ed"
        return {
            "config": {
                "background": "transparent",
                "font": _sans,
                "view": {"stroke": None, "continuousWidth": 380, "continuousHeight": 260},
                "title": {
                    "font": "Newsreader, Georgia, serif",
                    "fontSize": 15,
                    "fontWeight": 500,
                    "color": _ink,
                    "anchor": "start",
                    "offset": 12,
                    "subtitleFont": _sans,
                    "subtitleColor": _muted,
                    "subtitleFontSize": 11,
                },
                "axis": {
                    "labelFont": _sans,
                    "labelFontSize": 11,
                    "labelColor": _muted,
                    "titleFont": _sans,
                    "titleFontSize": 11,
                    "titleFontWeight": 500,
                    "titleColor": _muted,
                    "titlePadding": 8,
                    "domain": False,
                    "ticks": False,
                    "labelPadding": 6,
                    "gridColor": _rule,
                    "gridWidth": 1,
                },
                "legend": {
                    "labelFont": _sans,
                    "labelFontSize": 11,
                    "labelColor": _muted,
                    "titleFont": _sans,
                    "titleFontSize": 11,
                    "titleColor": _muted,
                    "symbolType": "square",
                    "symbolSize": 90,
                    "orient": "top",
                    "direction": "horizontal",
                    "offset": 4,
                },
                "range": {
                    "category": ["#1a844e", "#c8912f", "#b83227", "#44586a", "#7d8fa0"],
                    "diverging": ["#1a844e", "#c8912f", "#b83227"],
                    "ramp": ["#1a844e", "#c8912f", "#b83227"],
                },
                "point": {"size": 70, "filled": True, "opacity": 0.85},
                "circle": {"size": 70, "opacity": 0.85},
                "bar": {"cornerRadius": 0},
                "rule": {"color": _muted},
                "text": {"font": _sans, "fontSize": 11, "color": _ink},
            }
        }

    return (
        Path,
        ThreadPoolExecutor,
        alt,
        anywidget,
        base64,
        datetime,
        httpx,
        json,
        HistGradientBoostingClassifier,
        IsotonicRegression,
        mo,
        np,
        pl,
        shapely,
        timedelta,
        traitlets,
    )


@app.cell
def _(datetime, mo, pl, requests_311, snapshot_meta):
    # The opening is not a claim about Baltimore, it is one of Baltimore's own records. The worst
    # still-open streetlight report in the file, printed the way the city filed it.
    _end = datetime.fromisoformat(snapshot_meta["snapshot_ts"])
    _worst = (
        requests_311.filter(
            ~pl.col("proactive") & pl.col("closed").is_null() & (pl.col("domain") == "Streetlights")
        )
        .with_columns(
            ((_end - pl.col("created")).dt.total_seconds() / 86400).round(0).cast(pl.Int64).alias("days"),
            ((pl.col("due") - pl.col("created")).dt.total_seconds() / 86400).round(0).cast(pl.Int64).alias("sla"),
        )
        .sort("days", descending=True)
        .row(0, named=True)
    )
    _street = _worst["address"].split(",")[0].title()

    mo.Html(
        f"""
        <div class="slip">
          <p class="slip-kicker">Baltimore City 311 &nbsp;&nbsp; service request &nbsp;&nbsp; still open</p>
          <h1>A streetlight on {_street} has been out for {_worst["days"]} days.</h1>
          <p class="slip-lede">The city gave itself {_worst["sla"]} days to fix it. Nobody has closed
          the ticket, and nothing about that is unusual. This is what happens to a request after it is
          filed, for all {requests_311.filter(~pl.col("proactive")).height:,} of them, and what the
          waiting depends on.</p>
          <dl class="slip-record">
            <div class="slip-field"><dt>request type</dt><dd>{_worst["sr_type"]}</dd></div>
            <div class="slip-field"><dt>neighborhood</dt><dd>{_worst["csa"].split("/")[0]}</dd></div>
            <div class="slip-field"><dt>filed</dt><dd>{_worst["created"].strftime("%d %b %Y")}</dd></div>
            <div class="slip-field is-promise"><dt>city&rsquo;s deadline</dt><dd>{_worst["sla"]} days</dd></div>
            <div class="slip-field is-late"><dt>open for</dt><dd>{_worst["days"]} days</dd></div>
            <div class="slip-field"><dt>status</dt><dd>{_worst["status"]}</dd></div>
          </dl>
        </div>
        """
    )
    return


@app.cell
def _(live_banner):
    live_banner
    return


@app.cell
def _(mo, snapshot_meta):
    mo.md(f"""
    ## Executive summary

    Each public welfare agency in Baltimore works its own queue, so the bigger picture is missed:
    nobody sees the area that is failing on many fronts at once, or the area that has stopped
    calling 311.

    We score all 55 Community Statistical Areas on **need** (how bad conditions are) and
    **service** (how long those problems stay open — the same clock as a single resident call).
    The priority is the **neglect gap**: how far an area falls below the service its level of
    need predicts.

    *(Data snapshot: {snapshot_meta["snapshot_date"]}.)*
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Problem statement

    Baltimore has a **neglect gap**: areas that get less service than other areas carrying the same
    amount of need. Need on its own is not the story &mdash; every dashboard in the city already
    shows that East and West Baltimore are struggling. The gap shows where that struggle is going
    unanswered.

    Nothing in the city's systems measures it, for three reasons:

    1. **Complaints.** 311 is reactive. Areas that call get served, so service follows who calls, not just what is broken.
    2. **Silos.** Housing, Transportation, BGE and Sanitation each rank only their own work. No one adds them up.
    3. **Politics.** Money split evenly by council district ignores where conditions are worst.

    **One block, three tickets.** A block that is 30% vacant, has a streetlight dark for four months, and has
    trash piling up shows up as three small tickets in three departments. It never shows up as one urgent
    problem, even though that combination is exactly what abandonment looks like.

    **Silence looks like satisfaction.** An area with few 311 calls looks healthy on every dashboard. It may
    instead be an area that stopped believing the city will come.

    **What this notebook gives an official:** the gap, measured for all 55 areas, sorted into the three
    answers that decide a budget &mdash; the areas to **concentrate on**, served least for the need they
    carry; the areas **already being worked**, where the response matches the problem; and the areas
    getting **more attention than their conditions call for**.
    """)
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(r"""
        **What others found (and what we build on)**

        - **311 reporting is uneven.** Kontokosta & Hong (2021, *Sustainable Cities and Society*) show that
          311 complaint rates differ by neighborhood for reasons beyond actual conditions. So we never treat
          complaint counts alone as need, and we flag quiet areas with bad observed conditions.
        - **Streetlights matter for safety.** Chalfin et al. (2022, *Journal of Quantitative Criminology*),
          a randomized trial in New York City public housing, found clearly fewer nighttime outdoor crimes
          where lighting was added.
        - **Fixing vacant property matters.** Branas et al. (2018, *PNAS*), a citywide randomized trial in
          Philadelphia, found that cleaning up vacant lots cut gun violence nearby, most of all in the poorest areas.
        - **Baltimore's own indicators.** BNIA Vital Signs publishes population, crime and vacancy by
          Community Statistical Area. We use it for our denominators and as a cross-check.

        What is new here: we score **service against need in the same topic**, and we use the city's own
        `Proactive` 311 tickets as a signal of whether the city is *looking* in an area, not just answering.
        """),
        kind="info",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Data overview
    """)
    return


@app.cell
def _(mo, snapshot_meta):
    _c = snapshot_meta["counts"]
    _rows = [
        ("311 Customer Service Requests (2026)", f'{_c["requests_311"]:,}', "Need (reports) and service (time still open, proactive tickets)"),
        ("Vacant Building Notices (open)", f'{_c["open_notices"]:,}', "Vacancy need (written by inspectors)"),
        ("Rehabs of Vacant Buildings", f'{_c["rehabs"]:,}', "Vacancy service"),
        ("Completed City Demolitions", f'{_c["demolitions"]:,}', "Vacancy service"),
        ("Real Property parcels", f'{_c["parcels"]:,}', "Denominator (per 1,000 parcels)"),
        ("Community Statistical Areas", f'{_c["areas"]}', "The 55 areas we rank"),
        ("BNIA Total Population (2020)", f'{_c["population"]:,}', "Denominator (per 1,000 residents)"),
        ("BNIA Violent Crime Rate (2023)", "55 areas", "Context only (no service measure exists)"),
        ("BNIA Vacant & Abandoned % (2023)", "55 areas", "Cross-check of our vacancy numbers"),
    ]
    _table = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in _rows)
    mo.md(f"""
    We join **9 Open Baltimore datasets**, by parcel number and by location. Every 311 request and every
    housing record is placed inside one of the 55 areas by its map point. We keep each point and street
    address, so the map can zoom from the whole city down to a single block.

    | Dataset | Records used | What it gives us |
    | --- | --- | --- |
    {_table}

    **Topics we score** (need and service for each): streetlights, potholes, roads, illegal dumping,
    dirty streets and alleys, rats, graffiti, trees, flooding, and vacant buildings.

    We removed **{snapshot_meta["dropped"]["duplicate_or_transferred"]:,}** 311 requests marked duplicate or
    transferred, so the same pothole is not counted twice.
    """)
    return


@app.cell
def _(mo, method_check, clock_vs_cutoff):
    mo.accordion(
        {
            "Why service is a share of need, not a count (click to open)": method_check,
            "Clock vs old 7-day cutoff (click to open)": clock_vs_cutoff,
        }
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Core visualization

    **Click an area to zoom in to its streets.** Each dot is a real request or vacant building: orange
    dots are still open, and bigger means older. **Click a topic in the Gap Card** to color the map by that
    topic alone. **Move the sliders in the sidebar** to change what matters. The weights are yours; the
    notebook does not decide which problem matters most.
    """)
    return


@app.cell
def _(explorer, mo, skyline_view):
    _skyline = mo.vstack(
        [
            mo.md(r"""
            Tower height is the **positive weighted neglect gap**, using the same topic weights as
            the 2D map. Drag to rotate, scroll to zoom, and click an area to pin it.
            """),
            # Keep the two large map widgets below marimo's output-size ceiling by
            # sending the skyline only when its tab is opened.
            mo.lazy(skyline_view),
        ]
    )
    mo.vstack(
        [
            mo.md(r"""
            Switch between the operational **neglect gap** map and the 3D **neglect skyline**.
            """),
            mo.ui.tabs(
                {
                    "Neglect gap — streets and work list": explorer,
                    "Neglect skyline — gap towers": _skyline,
                }
            ),
        ]
    )
    return


@app.cell
def _(FIX_HORIZON, fix_topics, mo, pl):
    # The slowest topic carries the point, so let the data pick it rather than hard-coding a name.
    _no_median = fix_topics.filter(pl.col("median_days").is_null()).sort("n", descending=True)
    _w = _no_median.row(0, named=True) if _no_median.height else None
    _punchline = (
        f"**{_w['domain']}** is the case in point. The requests that did close took a median of "
        f"{_w['naive_median_days']:.0f} days, which sounds survivable. But "
        f"{100 * _w['still_open_at_horizon']:.0f}% are predicted to still be open at {FIX_HORIZON} days, so the "
        f"half-way mark never arrives and the honest answer is that it has no median at all."
        if _w else
        "Every topic here reaches its half-way mark inside the window."
    )
    mo.md(
        rf"""
    ### The fix clock

    The map above ranks areas by the area under this same curve: how much of the first week a
    typical request is already closed. This view asks the blunter question: **if you report it
    today, when does it get fixed?**

    Press play. Every area starts fully shaded, and the color drains as its requests close. Whatever is
    still standing at the end never got fixed at all.

    Averaging how long finished repairs took would answer the wrong question, because a request that is
    never closed never enters the average. {_punchline}
    """
    )
    return


@app.cell
def _(DATA_DIR, json, mo):
    # Pre-recorded, replayed from disk. The notebook makes no API call here and none anywhere else:
    # a live voice service is one more thing that can fail in front of a reader, and it would make the
    # run non-reproducible. `scripts/make_call_demo.py` regenerates these assets by hand.
    _f = DATA_DIR / "demo_call" / "transcript.json"
    demo_calls = json.loads(_f.read_text()) if _f.exists() else []
    call_pick = mo.ui.dropdown(
        options={f'"{_c["text"][:52]}..."': _c["id"] for _c in demo_calls},
        value=f'"{demo_calls[0]["text"][:52]}..."' if demo_calls else None,
        label="**A resident calls it in**",
    ) if demo_calls else None
    return call_pick, demo_calls


@app.cell
def _(DATA_DIR, call_pick, demo_calls, domain_scores, fix_days, fix_summary, mo, overall, pl):
    def call_panel(calls, picked, summary):
        """Show a reported complaint next to the clock and that area's gap rank."""
        _c = next((_x for _x in calls if _x["id"] == picked), None)
        if _c is None:
            return mo.md("")
        _audio = DATA_DIR / "demo_call" / (_c["audio"] or "")
        _row = summary.filter((pl.col("domain") == _c["domain"]) & (pl.col("csa") == _c["csa"]))
        if _row.height:
            _r = _row.row(0, named=True)
            _med = "never reaches half" if _r["median_days"] is None else f"half gone by day {_r['median_days']}"
            _verdict = (
                f"Logged as **{_c['domain']}** in **{_c['csa']}**. Going on the "
                f"{_r['n']:,} requests like it since January: **{100 * _r['fixed_by_7']:.0f}%** are fixed "
                f"inside a week, **{100 * _r['fixed_by_30']:.0f}%** inside a month, and "
                f"**{100 * _r['still_open_at_horizon']:.0f}%** are predicted to still be open at the end &mdash; {_med}."
            )
        else:
            _verdict = f"Logged as **{_c['domain']}** in **{_c['csa']}**, which has too few requests like it to score."
        _gap = overall.filter(pl.col("csa") == _c["csa"])
        _topic = domain_scores.filter((pl.col("csa") == _c["csa"]) & (pl.col("domain") == _c["domain"]))
        if _gap.height and _topic.height:
            _g, _t = _gap.row(0, named=True), _topic.row(0, named=True)
            _svc = (
                "not enough requests to score"
                if _t["service_rate"] is None
                else f"**{100 * _t['service_rate']:.0f}%** of the first {fix_days.value} days already closed"
            )
            _verdict += (
                f" That same clock is what the map ranks: **{_c['csa']}** is gap rank "
                f"**{_g['rank']}** of {overall.height}, and {_c['domain']} service is {_svc}."
            )
        return mo.vstack(
            [
                mo.audio(str(_audio)) if _c["audio"] and _audio.exists() else mo.md(""),
                mo.md(f"> {_c['text']}"),
                mo.md(f"{_verdict}  \n<small>{_c['address']}</small>"),
            ]
        )

    mo.md("") if call_pick is None else mo.vstack(
        [call_pick, call_panel(demo_calls, call_pick.value, fix_summary)]
    )
    return


@app.cell
def _(clock_topic, fix_clock_view, mo):
    mo.vstack([clock_topic, fix_clock_view])
    return


@app.cell
def _(
    ALLEY_MIN_ARM,
    RATS,
    alley,
    alley_compare,
    alley_growth_chart,
    alley_ring_chart,
    mo,
):
    _s = alley["stats"]
    _pivot = alley["rings"].pivot(on="ring", index="outcome", values="density")
    _ring_cols = [_c for _c in _pivot.columns if _c != "outcome"]
    _ring_rows = "\n".join(
        f"| {'**' + _r['outcome'] + '**' if _r['outcome'] == RATS else _r['outcome']} | "
        + " | ".join(f"{_r[_c]:+.4f}" for _c in _ring_cols)
        + f" | {alley['decay'][_r['outcome']]:.1f}× |"
        for _r in _pivot.iter_rows(named=True)
    )
    _method = mo.md(
        f"""
    Two things had to be dealt with before this number meant anything.

    **The alleys are not alike.** Rat reports near the alleys the city leaves open were already
    **{_s["baseline_fast"] / _s["baseline_left"]:.1f}x rarer** than near the ones it clears
    quickly, and already climbing before the alley was reported at all. A plain before-and-after
    difference reads that head start as an effect and returns +0.16. So the comparison keeps only
    the **{_s["clean_share"]:.0%}** of alleys with no rat report nearby in the previous
    {_s["window"]} days. Both arms then start at zero, and the answer drops to +{_s["diff"]:.2f}.

    **Reports of everything cluster.** A pair can look local for reasons that have nothing to do
    with rubbish, so we ran the identical test on outcomes an alley *cannot* cause. Rats fall away
    {_s["decay"]:.1f}x from the inner ring to the outer; those outcomes average
    {_s["placebo_decay"]:.1f}x. Rats is the only pair of the 36 we tested that beats its own
    placebos on this.

    | Outcome | {" | ".join(_ring_cols)} | decay |
    | --- | {" | ".join("---:" for _ in _ring_cols)} | ---: |
    {_ring_rows}

    Still observational: these alleys were not assigned at random, and a month is a short window.
    The full matrix of 36 pairs is in `pair_review.md`.
    """
    )

    if min(_s["n_left"], _s["n_fast"]) < ALLEY_MIN_ARM:
        alley_section = mo.md(
            "### While the alley waits\n"
            "Not enough alleys in this snapshot were left open long enough to compare against the "
            "ones cleared quickly, so this section has nothing to show."
        )
    else:
        alley_section = mo.vstack(
            [
                mo.md(
                    f"""
    ### While the alley waits

    The clock above says how long a dirty alley waits. This asks what happens meanwhile.

    Among alleys with no rat problem nearby to begin with, the ones the city left unfixed for a
    month drew **{_s["lift"]:.0%} more rat reports within {_s["radius"]} m** over the next month
    than the ones it cleared inside a week &mdash; **{_s["left_any"]:.0%}** of them got one,
    against **{_s["fast_any"]:.0%}**. The extra reports sit right beside the alley and fade with
    distance.
    """
                ),
                # Control above the chart it changes, as with the sidebar and the map.
                alley_compare,
                mo.hstack([alley_growth_chart, alley_ring_chart], widths=[1, 1], gap=1.5, align="start"),
                mo.accordion({"How we checked this (click to open)": _method}),
            ]
        )
    alley_section
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### The unison call

    How long it takes for each neighborhood to respond to a complaint &mdash; visualized
    """
    )
    return


@app.cell
def _(storm_view):
    storm_view
    return


@app.cell
def _(STORM_ORIGIN, STORM_TOPIC, fix_summary, mo, pl):
    _scored = fix_summary.filter(pl.col("n") >= 30)
    ask_topic = mo.ui.dropdown(
        options=sorted(_scored["domain"].unique().to_list()), value=STORM_TOPIC, label="**I want to report**"
    )
    ask_area = mo.ui.dropdown(
        options=sorted(_scored.filter(pl.col("domain") == STORM_TOPIC)["csa"].unique().to_list()),
        value=STORM_ORIGIN,
        label="**on my block in**",
    )
    return ask_area, ask_topic


@app.cell
def _(FIX_HORIZON, ask_area, ask_topic, fix_inputs, fix_summary, mo, pl):
    def ask_answer(topic, area, summary, inputs):
        """The same question the sequence dramatises, asked one request at a time."""
        _row = summary.filter((pl.col("domain") == topic) & (pl.col("csa") == area))
        if not _row.height or _row.row(0, named=True)["n"] < 30:
            return mo.md(
                f"Too few **{topic.lower()}** reports in **{area}** to say anything honest. "
                "Pick another pairing."
            )
        _r = _row.row(0, named=True)
        _peers = summary.filter((pl.col("domain") == topic) & (pl.col("n") >= 30)).sort("still_open_at_horizon")
        _best, _worst = _peers.row(0, named=True), _peers.row(_peers.height - 1, named=True)
        _rank = _peers.with_row_index("i").filter(pl.col("csa") == area).row(0, named=True)["i"] + 1
        _sla = inputs.filter((pl.col("domain") == topic) & (pl.col("csa") == area))
        _promise = _sla.row(0, named=True)["sla_days"] if _sla.height else None

        return mo.vstack(
            [
                mo.md(
                    f"""
    ## {100 * _r["still_open_at_horizon"]:.0f}% chance it is never dealt with

    Report **{topic.lower()}** on a block in **{area}** today and, going on the {_r["n"]:,} reports
    like it since January, **{100 * _r["fixed_by_7"]:.0f}%** are closed inside a week,
    **{100 * _r["fixed_by_30"]:.0f}%** inside a month, and
    **{100 * _r["still_open_at_horizon"]:.0f}%** are still open {FIX_HORIZON} days later.
    {"The city gives itself **" + f"{_promise:.0f}" + " days** for this." if _promise else ""}
    """
                ),
                mo.md(
                    f"""
    That puts it **{_rank} of {_peers.height}** neighborhoods for this problem. The same report gets
    left open **{100 * _best["still_open_at_horizon"]:.0f}%** of the time in
    **{_best["csa"]}** and **{100 * _worst["still_open_at_horizon"]:.0f}%** of the time in
    **{_worst["csa"]}**. Nothing about the request changes &mdash; only the address.
    """
                ),
            ]
        )

    mo.vstack(
        [
            mo.md(
                """
    ### Try it on your own block

    The sequence above runs one request everywhere at once. This runs it wherever you like.
    """
            ),
            mo.hstack([ask_topic, ask_area], justify="start", gap=2),
            ask_answer(ask_topic.value, ask_area.value, fix_summary, fix_inputs),
        ]
    )
    return


@app.cell
def _(fix_calibration, fix_model, mo, pl):
    _c = {_r["horizon"]: _r for _r in fix_calibration.iter_rows(named=True)}
    _best = min(_c.values(), key=lambda _r: _r["gap"])
    _wins = sum(1 for _r in _c.values() if _r["gap"] <= _r["gap_simple"])
    _rank = max(_c.values(), key=lambda _r: _r["ranking"])
    mo.accordion(
        {
            "How far can you trust these numbers?": mo.vstack(
                [
                    mo.md(
                        f"""
    The model is a gradient-boosted hazard model: for each request it answers, interval by interval,
    *given this is still open, does it close now?*, and the answers multiply back into the curve
    above. It trained on {fix_model["n_train"]:,} request-intervals over {fix_model["rounds"]} rounds,
    then had its confidence calibrated against {fix_model["n_calib"]:,} more that it had not seen.

    To check it, the whole thing was rebuilt on the early part of the year and scored on the
    {_best["n"]:,} requests that came later. Across ten bands of predicted risk, the gap between what
    it said and what happened is **{_best["gap"]:.3f} at {_best["horizon"]} days**, and it beats a
    plain counting estimate at **{_wins} of {len(_c)}** horizons. Asked instead to rank which
    requests will still be open, it gets **{_rank["ranking"]:.2f}** at {_rank["horizon"]} days, where
    0.5 is a coin toss.

    Two honest limits. The city's response *shape* changed partway through the year, becoming slower
    to acknowledge and then quicker to catch up, and no model can predict a shift it has never seen;
    the first week is the least reliable stretch because of it. And most of the answer comes from
    what kind of problem it is, not where it is &mdash; the map sharpens a topic's story rather than
    telling a separate one.
    """
                    ),
                    mo.ui.table(
                        fix_calibration.select(
                            pl.col("horizon").alias("day"), "n",
                            pl.col("observed").round(3),
                            pl.col("gap").round(4).alias("gap (model)"),
                            pl.col("gap_simple").round(4).alias("gap (counting)"),
                            pl.col("ranking").round(3).alias("ranking within topic"),
                        ),
                        selection=None,
                    ),
                ]
            )
        }
    )
    return


@app.cell
def _(BULK_CLOSED, areas, np, pl, requests_311, spearman):
    def reporting_bias(requests_311, areas):
        """Does calling 311 more often buy an area faster service?

        The tempting comparison, reporting rate against the share of requests ever closed, is
        confounded twice over. Topics close at wildly different rates, so an area's topic mix alone
        moves the number; and "ever closed" counts a request still sitting open as a failure, which
        is a statement about censoring as much as about service. So we also standardize: predict each
        area's close rate from its topic mix and citywide topic rates, and correlate the leftover.
        """
        _r = requests_311.filter(~pl.col("proactive") & ~pl.col("sr_type").is_in(BULK_CLOSED))
        _a = (
            _r.group_by("csa").agg(
                pl.len().alias("n"),
                pl.col("closed").is_not_null().mean().alias("close_rate"),
                (pl.col("closed").is_not_null()
                 & ((pl.col("closed") - pl.col("created")) <= pl.duration(days=7))).mean().alias("fast_share"),
            )
            .join(areas.select("csa", "pop"), on="csa")
            .with_columns((pl.col("n") / pl.col("pop") * 1000).alias("rate"))
        )
        # Indirect standardization: the close rate an area's topic mix alone would predict.
        _city = _r.group_by("domain").agg(pl.col("closed").is_not_null().mean().alias("_d_rate"))
        _mix = (
            _r.group_by("csa", "domain").agg(pl.len().alias("_k"))
            .with_columns((pl.col("_k") / pl.col("_k").sum().over("csa")).alias("_share"))
            .join(_city, on="domain")
            .group_by("csa").agg((pl.col("_share") * pl.col("_d_rate")).sum().alias("expected"))
        )
        _a = _a.join(_mix, on="csa").with_columns((pl.col("close_rate") - pl.col("expected")).alias("residual"))
        return {
            "naive": spearman(_a["rate"], _a["close_rate"]),
            "from_mix": spearman(_a["rate"], _a["expected"]),
            "residual": spearman(_a["rate"], _a["residual"]),
            "fast": spearman(_a["rate"], _a["fast_share"]),
            "vacancy": spearman(_a["rate"], areas.join(_a.select("csa"), on="csa")["bnia_vacant_pct"]),
            "n_areas": _a.height,
        }

    bias_stats = reporting_bias(requests_311, areas)
    return (bias_stats,)


@app.cell
def _(bias_stats, mo):
    mo.callout(
        mo.md(
            f"""
    **Does complaining more get you served faster? No.**

    Areas that report more do have more of their requests closed (rank correlation
    {bias_stats["naive"]:+.2f}), which looks like a reward for being loud. It is not. Topic mix alone
    predicts {bias_stats["from_mix"]:+.2f} of it, because the areas that report most report
    overwhelmingly about street cleaning, which closes almost every time. Take the topic mix out and
    the advantage is {bias_stats["residual"]:+.2f} &mdash; nothing. On speed rather than eventual
    closure it points the other way ({bias_stats["fast"]:+.2f} against the share fixed inside a week).

    For the topics this notebook leads with &mdash; vacancy, streetlights, dumping &mdash; volume tracks
    conditions rather than civic energy: reporting rate moves with vacancy at
    {bias_stats["vacancy"]:+.2f}. We would not push that further. Published work using independent
    ground truth (street surveys in Kansas City, pothole counts in Houston) finds the opposite for
    *nuisance* categories, where poorer neighborhoods report **less** than their conditions warrant.
    Both can hold at once, and it is why the clock above is fitted one topic at a time: comparing
    areas on a blend of topics compares their problems, not their service.
    """
        ),
        kind="info",
    )
    return


@app.cell
def _(fix_summary, mo, pl):
    clock_topic = mo.ui.dropdown(
        options=sorted(fix_summary["domain"].unique().to_list()),
        value="Streetlights",
        label="**Topic**",
    )
    return (clock_topic,)


@app.cell
def _(DEFAULT_FIX_DAYS, DOMAIN_ORDER, mo):
    weight_sliders = mo.ui.dictionary(
        {d: mo.ui.slider(0, 3, step=0.5, value=1, show_value=True, full_width=True) for d in DOMAIN_ORDER}
    )
    fix_days = mo.ui.slider(
        1, 60, step=1, value=DEFAULT_FIX_DAYS, show_value=True, label="Rank time still open over the first (days)"
    )
    window = mo.ui.dropdown(
        options={"All of 2026 so far": 0, "Last 180 days": 180, "Last 90 days": 90},
        value="All of 2026 so far",
        label="Time window for 311",
    )
    per = mo.ui.radio(
        options={"per 1,000 residents": "pop", "per 1,000 parcels": "parcels"},
        value="per 1,000 residents",
        label="Count 311 need",
    )
    return fix_days, per, weight_sliders, window


@app.cell
def _(DOMAIN_ORDER, fix_days, mo, per, weight_sliders, window):
    # The sidebar stays on screen while you scroll, so every chart below can be re-weighted in place.
    _weight_rows = [
        mo.hstack([mo.md(f"<small>{d}</small>"), weight_sliders[d]], widths=[1, 1], align="center") for d in DOMAIN_ORDER
    ]
    mo.sidebar(
        [
            mo.md("### Baltimore Triage"),
            # Plain "#section" links, not mo.nav_menu: nav_menu links to "/#section", which drops the
            # "?area=" query and reloads the whole app.
            mo.Html(
                '<nav class="side-nav">'
                + "".join(
                    f'<a href="#{anchor}">{label}</a>'
                    for anchor, label in [
                        ("executive-summary", "Summary"),
                        ("problem-statement", "Problem"),
                        ("data-overview", "Data"),
                        ("core-visualization", "Explore the map"),
                        ("the-fix-clock", "The fix clock"),
                        ("the-unison-call", "The unison call"),
                        ("insight-synthesis", "Insights"),
                        ("discussion-future-work", "Discussion"),
                        ("marimo-feedback", "marimo feedback"),
                        ("agentic-tool-usage-what-we-learned", "AI tool notes"),
                    ]
                )
                + "</nav>"
            ),
            mo.md("---\n**What counts**"),
            fix_days,
            window,
            per,
            mo.md("**Topic weights** <small>(0 = ignore)</small>"),
            *_weight_rows,
            mo.md("<small>Vacant buildings always use parcels, and count rehabs and demolitions since Jan 2023.</small>"),
        ],
        width="330px",
    )
    return


@app.cell
def _(area_reqs, area_vac, focus_topic, mo, picked_area, pl, selected_area, snapshot_meta, VACANCY):
    # No area picked (the city view), so there is no crew list to hand anyone. Show nothing.
    mo.stop(not picked_area)
    if focus_topic == VACANCY:
        _list = (
            area_vac.filter(~pl.col("handled"))
            .sort("notice_date")
            .select(
                pl.col("address").alias("Address"),
                pl.col("notice_date").dt.strftime("%b %Y").alias("Vacant notice since"),
            )
        )
        _what = "vacant buildings with no rehab permit or demolition since 2023, oldest notice first"
    else:
        _list = (
            area_reqs.filter(pl.col("status") == "open")
            .sort("days", descending=True)
            .select(
                pl.col("domain").alias("Topic"),
                pl.col("address").alias("Address"),
                pl.col("created").dt.strftime("%Y-%m-%d").alias("Reported"),
                pl.col("days").alias("Days open"),
                pl.col("sr_type").alias("311 type"),
            )
        )
        _what = f"still-open {focus_topic.lower() + ' ' if focus_topic else ''}311 requests, oldest first"
    mo.vstack(
        [
            mo.md(
                f"### Work list: {selected_area}\n"
                f"{_list.height:,} {_what} (as of {snapshot_meta['snapshot_date']}). "
                "This is what a crew would get. Pick another area or topic on the map to change it."
            ),
            mo.ui.table(_list, selection=None, page_size=8, show_column_summaries=False),
            mo.download(
                data=_list.write_csv().encode("utf-8"),
                filename=f"work_list_{selected_area.replace('/', '-')}.csv",
                mimetype="text/csv",
                label="Download this work list (CSV)",
            ),
        ]
    )
    return


@app.cell
def _(mo, quadrant):
    mo.hstack(
        [
            quadrant,
            mo.md(
                "### Need vs service, all 55 areas\n"
                "Each dot is an area. **Bottom right** is the priority corner: high need, low service. "
                "**Top left** gets more service than its need suggests. The pink ring is the area picked on the map.\n\n"
                "Need and service are percentiles *within each topic*, averaged with your weights. The score is "
                "not the distance between the two: it is how far **below the fitted service-on-need line** an area "
                "sits, so a high score means it is served less than areas with the same amount of need."
            ),
        ],
        widths=[3, 2],
        align="center",
        gap=2,
    )
    return


@app.cell
def _(ROBUST_SHARE, mo, robust_chart, robust_table):
    mo.vstack(
        [
            mo.md(
                "### The robust top 10\n"
                "We tried **2,000 random sets of topic weights** and ranked the areas each time. "
                f"**Robust** areas are in the top 10 under at least {ROBUST_SHARE:.0%} of them. "
                "**Weight sensitive** areas depend on what you care about, so treat them with care."
            ),
            robust_chart,
            robust_table,
        ]
    )
    return


@app.cell
def _(mo, undercount_chart, undercount_note):
    mo.vstack(
        [
            mo.md(
                "### These may be worse than they look\n"
                "Areas where vacancy (written down by city inspectors, not residents) is high but residents file "
                "few 311 requests. A complaint-driven system under-serves these places and never notices."
            ),
            undercount_chart,
            undercount_note,
        ]
    )
    return


@app.cell
def _(insights, mo):
    mo.md(f"""
    ## Insight synthesis

    {insights}
    """)
    return


@app.cell
def _(TRIAGE_AHEAD, TRIAGE_FROM, TRIAGE_TO, fix_queue, fix_stranded, fix_triage, mo, pl):
    _t = fix_triage
    mo.vstack(
        [
            mo.Html(
                f"""
                <div class="board">
                  <div class="board-line">
                    <span>queue <b>{fix_queue.height:,}</b></span>
                    <span>aged <b>{TRIAGE_FROM}&ndash;{TRIAGE_TO}d</b></span>
                    <span>horizon <b>+{TRIAGE_AHEAD}d</b></span>
                    <span>tested on <b>{fix_triage["n"]:,}</b> unseen</span>
                    <span>ranking <b>{fix_triage["auc"]:.3f}</b></span>
                  </div>
                  <h3>Monday morning</h3>
                  <p>Everything above describes Baltimore. This is the one thing here a city could
                  act on. Two requests, both about {TRIAGE_TO} days old: one will be closed by the end
                  of the month, the other has effectively already been lost, and nobody at the city
                  knows which is which.</p>
                  <p>Below are the <strong>{fix_queue.height:,}</strong> requests currently between
                  {TRIAGE_FROM} and {TRIAGE_TO} days old, ranked by the chance they are still open
                  {TRIAGE_AHEAD} days from now. Sorting by age cannot do this &mdash; every request
                  here is roughly the same age. Flag the worst tenth and
                  <strong>{fix_triage["precision"]:.0%}</strong> of those flags are right against
                  <strong>{fix_triage["base"]:.0%}</strong> at random, catching
                  <strong>{fix_triage["recall"]:.0%}</strong> of everything that really did stay open.</p>
                  <p>The model stops discriminating past about a month, once the curve flattens and
                  almost nothing moves. <strong>{fix_stranded:,}</strong> open requests are already
                  past that point.</p>
                </div>
                """
            ),
            mo.ui.table(
                fix_queue.head(150).select(
                    (pl.col("risk") * 100).round(0).cast(pl.Int64)
                    .map_elements(lambda v: f"{v}%", return_dtype=pl.String)
                    .alias(f"still open in {TRIAGE_AHEAD} days"),
                    pl.col("waiting").map_elements(lambda v: f"{v} days", return_dtype=pl.String)
                    .alias("waiting so far"),
                    pl.col("sla_days").round(0).cast(pl.Int64)
                    .map_elements(lambda v: f"{v} days", return_dtype=pl.String)
                    .alias("city promised"),
                    pl.col("domain").alias("problem"),
                    pl.col("csa").alias("neighborhood"),
                    "address",
                ),
                selection=None,
                page_size=8,
            ),
            mo.md(
                f"<small>Worst 150 of {fix_queue.height:,}. Scroll to the bottom of the list and the "
                f"same-aged requests read 0% &mdash; those are about to be closed without anyone "
                f"doing anything. The promise column is the city's own target for that request "
                f"type.</small>"
            ),
        ]
    )
    return


@app.cell
def _(dispatch_download, mo):
    mo.vstack(
        [
            mo.md(
                "### Take it to the meeting\n"
                "The ranked list for your current settings, with each area's three widest topic gaps."
            ),
            dispatch_download,
        ]
    )
    return


@app.cell
def _(MIN_REQUESTS, mo):
    mo.md(f"""
    ## Discussion / Future work

    ### What this tool cannot claim

    - **It measures recorded need, not all need.** Problems nobody wrote down are invisible to it.
    - **It shows association, not cause.** A wide gap does not prove neglect caused the conditions,
      or that closing the gap will fix them.
    - **Percentiles hide size.** The area at the 99th percentile may be far worse than the one at the
      95th. Look at the raw rates in the Gap Card before acting.
    - **Small numbers swing a lot.** We hide an area's service score for a topic when it has fewer
      than {MIN_REQUESTS} requests there.
    - **Homeless outreach is left out on purpose.** Those 311 records count requests for outreach,
      not people. Scoring them as "need" would be misleading.
    - **Crime has no service number** (911 data has no response times), so it is context, not part of the gap.
      Violent crime *per resident* also looks extreme where few people live but many visit (Downtown, Harbor East),
      so we keep it out of the "worse than they look" test.
    - **Heavy reporting can lift well-off areas.** Some areas rank high on potholes and roads partly because
      residents there report a lot. Try the "per 1,000 parcels" option, and read the Gap Card's raw numbers.
    - **Parcels on an area's edge** are counted only if they sit fully inside it, so a few are missed.

    ### How it could be misused

    A priority list can be read backwards, as a reason to cut service where areas look "fine."
    This tool is for placing the **next** dollar, never for taking one away.

    ### Future work

    - **Vacancy duration.** 311 ranking now uses the fix clock; vacant buildings still use share
      handled since 2023, not how long a notice has sat.
    - **A block-level compound score** so “one block, three tickets” is a number, not only a story.
    - **A tipping-point model** for vacancy spreading from one house to its neighbors.
    - **Owner matching** across property records to find the biggest holders of neglected property.
    - **A real test.** Save today's ranking and check in six months whether high-gap areas got more service.
      A priority tool nobody ever checks is just an opinion with a map.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## marimo feedback

    **What worked well**

    - **Reactivity made the method honest.** Sliders, the time window and the clock horizon all feed
      one scoring function. marimo re-runs only what depends on them, so the map, scatter, Gap Card,
      robust top 10 and CSV always agree.
    - **One file, two products.** `marimo edit` shows this notebook with its code; `marimo run` serves the
      same file as a web app with the code hidden. `mo.sidebar` keeps the controls on screen,
      `App(css_file=...)` styles the hero, and `mo.query_params` gives every area a shareable link.
    - **`mo.ui.anywidget` let us build what marimo lacks.** Our map explorer is plain SVG and JavaScript
      (no map library, so it works offline). Its `selected` and `focus` come back to Python like any control.
    - **Updating a live widget.** A cell can push new data into a widget (`widget.data = ...`) and the browser
      redraws without re-creating it, so the picked area survives every slider move.
    - **PEP 723 + `--sandbox`** means one command sets up everything from the notebook file itself.
    - **`mo.accordion`** kept the data checks one click away without slowing the 5-minute read.

    **What was hard**

    - **You can't click a map shape yet.** In marimo 0.24.2, `mo.ui.altair_chart` turns off selection on
      geoshape charts ("Geoshapes + chart selection is not yet supported"). We wrote our own map widget to get
      around it, but most people won't, so this is still our top feature request.
    - **`mo.nav_menu` reloads the app when the URL has a query.** Its `#section` links go to `/#section`, which
      drops `?area=...` and reloads the whole page. Plain `<a href="#section">` links in `mo.Html` work.
    - **Would pushing data into a widget re-run the cells that read it?** The docs don't say. Reading the source
      showed only browser-side changes trigger re-runs, so there is no loop, but a one-line note would help.
    - **Layered charts don't return `.value`.** You must call `.apply_selection(df)` instead. It works, but
      it took reading the source to find out.
    - **Big maps hit the output size limit.** Our full-detail area boundaries (1.7 MB) made the map cell show an
      `output_max_bytes` error instead of a chart. Simplifying the shapes to ~10 m (65 KB) fixed it. A friendlier
      hint ("your chart data is large, try simplifying it") would help.
    - **`--sandbox` prompts can block scripts.** `marimo export` and `marimo run` ask "Run in a sandboxed venv?"
      and abort when there is no terminal to answer. Pass `--sandbox` or `--no-sandbox` explicitly.
    - **One name, one cell.** Every global name can be defined only once, which is great for correctness
      but means temporary names need a leading underscore.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Agentic tool usage: what we learned

    We used Claude Code (an AI coding agent) for planning, data discovery and writing this notebook.

    **Where it helped**

    - **It checked the real data before writing code.** It queried the live Open Baltimore APIs and found
      that our plan had missed `TRM-Potholes` (12,286 requests), which is far bigger than the one pothole
      type we had listed (`TRM-Pickup Pothole`, 4,715). It also found four request types with a
      `Proactive` twin, not just one.
    - **It found hidden duplicates.** About 1 in 5 requests in our topics are marked duplicate or transferred.
      Counting them would have inflated need.
    - **It reviewed our old starter script** and found it was cut off mid-file, used made-up request type
      names, and had a text search that would crash on a bracket in one name.
    - **It tested risky ideas small first.** Before turning the notebook into an app, it built a 60-line throwaway
      notebook to check that live widget updates, sidebar sliders and jump links work in `marimo run`. Then it
      clicked through the real app in a headless browser, in light and dark themes.

    **Where it was wrong, or we had to push**

    - **The biggest method flaw was caught by a person, not the tool.** Our first design counted
      demolitions per parcel as "service," which made the worst vacancy areas look well served. A human
      review caught it. The agent then agreed and rewrote service as a share of need.
    - **Starter code can look polished and still be broken.** The earlier AI-written script looked complete
      but could not run.
    - **"It runs" is not "it works."** The notebook passed a headless run and an HTML export, but opening it in
      a real browser showed the map was too big to display. Later, the sidebar links passed the small test but
      reloaded the whole app once shareable `?area=` links existed. Only clicking through the real app caught it.
    - **First results needed a sanity check.** The first "quiet but bad" list flagged Downtown and Harbor East,
      because violent crime *per resident* is extreme where few people live. We switched to vacancy only.

    **Lessons**

    1. Make the agent check names and counts against the live data, not its memory.
    2. Ask it to *attack* the method, not just build it.
    3. Keep a running log (`agent_log.md`). Specific examples are easy to lose by the end of a hackathon.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Appendix: how it works

    Everything below is the machinery: data loading, scoring and chart building. You do not need to read
    it to use the notebook.
    """)
    return


@app.cell
def _():
    # Request types verified against the live 311 layer (2026) on 2026-09-19.
    # "reported" = opened by residents (need); "proactive" = opened by city staff (service signal).
    DOMAINS_311 = {
        "Streetlights": {
            "reported": [
                "BGE-StLight(s) Out",
                "BGE-StLight(s) Out Rear",
                "BGE-StLighting Cable Faults",
                "TRM-Street Light Out",
                "TRM-StLight Damaged/Knocked Down/Rusted",
                "RP-Street Lighting Repairs",
            ],
            "proactive": [],
        },
        "Potholes": {"reported": ["TRM-Potholes", "TRM-Pickup Pothole"], "proactive": []},
        "Roads": {
            "reported": [
                "TRM-Street Repairs",
                "TEC-Street Repair (Misc)",
                "TR-Street Cut Issues",
                "TRT-Street and Crosswalk Markings",
            ],
            "proactive": [],
        },
        "Illegal dumping": {"reported": ["HCD-Illegal Dumping"], "proactive": []},
        "Dirty streets & alleys": {
            "reported": ["SW-Dirty Street", "SW-Dirty Alley", "SW-Mixed Refuse"],
            "proactive": ["SW-Dirty Street Proactive", "SW-Dirty Alley Proactive"],
        },
        "Rats": {"reported": ["SW-Rat Rubout"], "proactive": ["SW-Rat Rubout Proactive"]},
        "Graffiti": {"reported": ["SW-Graffiti Removal"], "proactive": ["SW-Graffiti Removal Proactive"]},
        "Trees": {
            "reported": [
                "FOR-Tree Maintenance",
                "FOR-Down Tree",
                "FOR-Broken Branch in Tree",
                "FOR-Fallen Limb",
                "HCD-Trees and Shrubs",
            ],
            "proactive": [],
        },
        "Flooding": {"reported": ["WW-Storm Flooded Street"], "proactive": []},
    }
    VACANCY = "Vacant buildings"
    DOMAIN_ORDER = [VACANCY, *DOMAINS_311]
    MIN_REQUESTS = 10  # below this, an area's service score for a topic is hidden
    VACANCY_SINCE = "2023-01-01"  # rehabs and demolitions counted from this date
    DEFAULT_FIX_DAYS = 7  # clock horizon; binary 30-day close rates saturate for sanitation
    ROBUST_SHARE = 0.8  # "robust" = in the top 10 under at least this share of random weightings

    FIX_HORIZON = 180  # days a reported request is followed for before we stop counting
    FIX_KAPPA = 20.0  # pseudo-count pulling a thin (topic, area) cell toward its topic-wide curve
    FIX_HALF_LIFE = 60  # days; older requests count for less, because the city's pace drifts
    # Interval edges for the hazard model. Tight early, where most requests close and a day matters,
    # widening later, where the question is only whether a thing is still open at all.
    FIX_EDGES = [0, 1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180]
    FIX_CALIB_FROM = "2026-05-01T00:00:00"  # trained before this date, calibrated on what came after
    FIX_HOLDOUT_FROM = "2026-07-01T00:00:00"  # and scored against requests later than both
    FIX_CATS = ["domain", "csa", "agency", "method"]
    FIX_NUMS = ["k", "log_start", "dow", "sla_days", "reports_per_1k", "vacancy", "crime",
                "parcels_pc", "base_logit"]
    # Every one of these 4,700 rows closes the instant it opens: a bulk administrative close, not a
    # same-day repair. Left in, it would make potholes look instant.
    BULK_CLOSED = ["TRM-Pickup Pothole"]

    # The sequence. Westport is the slowest area for streetlights, so the call we open on is the one
    # still glowing at the end: the story closes on the person it started with.
    STORM_ORIGIN = "Westport/Mount Winans/Lakeland"
    STORM_TOPIC = "Streetlights"
    # Kept identical to scripts/make_call_demo.py, because these are the captions for those clips.
    STORM_PREMISE = (
        "Hi... yeah, hi. My name's Denise. I'm over in Westport, just off Annapolis Road. "
        "I've called about this before, honestly."
    )
    STORM_ISSUE = "The streetlights on my block have been out. Three weeks now."
    # An area counts as answered when three in four of its reports are closed. Half is too generous
    # to mean anything here -- every area passes it inside three weeks -- and no area in this topic
    # ever reaches zero, so demanding all of them would paint the whole city as failing forever.
    STORM_ANSWERED = 0.25
    # The work list. For a request already open this long, how likely is it to still be open this
    # much later? Three weeks is far enough that the answer is not obvious and near enough to act on.
    # Before a week it is too early to call. After a month the model has nothing left to say: by then
    # the curve has flattened and every request scores the same, which is its own finding rather than
    # a work list. In between is the only window where knowing changes what you would do.
    TRIAGE_FROM, TRIAGE_TO, TRIAGE_AHEAD = 7, 30, 21

    # Colors: blue = over-served, orange = under-served (colorblind-safe pair).
    OVER, MID, UNDER = "#2b6cb0", "#f1f1f1", "#dd6b20"
    return (
        BULK_CLOSED,
        DEFAULT_FIX_DAYS,
        DOMAINS_311,
        DOMAIN_ORDER,
        FIX_HORIZON,
        FIX_CALIB_FROM,
        FIX_CATS,
        FIX_EDGES,
        FIX_HOLDOUT_FROM,
        FIX_HALF_LIFE,
        FIX_KAPPA,
        FIX_NUMS,
        MID,
        MIN_REQUESTS,
        OVER,
        ROBUST_SHARE,
        STORM_ANSWERED,
        STORM_ISSUE,
        STORM_ORIGIN,
        STORM_PREMISE,
        STORM_TOPIC,
        TRIAGE_AHEAD,
        TRIAGE_FROM,
        TRIAGE_TO,
        UNDER,
        VACANCY,
        VACANCY_SINCE,
    )


@app.cell
def _():
    _BNIA = "https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services"
    _DHCD = "https://egisdata.baltimorecity.gov/egis/rest/services/Housing/DHCD_Open_Baltimore_Datasets/FeatureServer"
    LAYERS = {
        "sr311": "https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_current/FeatureServer/0",
        "areas": f"{_BNIA}/Community_Statistical_Areas_(CSAs)__Reference_Boundaries/FeatureServer/0",
        "population": f"{_BNIA}/Tpop/FeatureServer/0",
        "crime": f"{_BNIA}/Viol/FeatureServer/0",
        "bnia_vacant": f"{_BNIA}/Vacant/FeatureServer/0",
        "demolitions": f"{_DHCD}/0",
        "open_notices": f"{_DHCD}/1",
        "rehabs": f"{_DHCD}/2",
        "parcels": "https://baltegis.baltimorecity.gov/mapping/rest/services/CityView/RealProperty_OB/FeatureServer/0",
    }
    return (LAYERS,)


@app.cell
def _(ThreadPoolExecutor, httpx, json, np, shapely):
    def arcgis_query(client, layer_url, **params):
        """POST one query to an ArcGIS layer and return the JSON, raising on API errors."""
        _resp = client.post(f"{layer_url}/query", data={"f": "json", **params}, timeout=120)
        _resp.raise_for_status()
        _data = _resp.json()
        if "error" in _data:
            raise RuntimeError(f"ArcGIS error from {layer_url}: {_data['error']}")
        return _data

    def fetch_rows(client, layer_url, where, fields, with_xy=False):
        """Fetch every matching row (all pages, in parallel), optionally with lon/lat as x, y."""
        _info = client.get(layer_url, params={"f": "json"}, timeout=60).json()
        _page = min(int(_info.get("maxRecordCount", 1000)), 2000)
        _oid = _info.get("objectIdField", "OBJECTID")
        _total = arcgis_query(client, layer_url, where=where, returnCountOnly="true")["count"]

        def _one(offset):
            _data = arcgis_query(
                client, layer_url, where=where, outFields=fields, orderByFields=_oid,
                returnGeometry=str(with_xy).lower(), outSR=4326,
                resultOffset=offset, resultRecordCount=_page,
            )
            _out = []
            for _f in _data["features"]:
                _row = dict(_f["attributes"])
                if with_xy:
                    _g = _f.get("geometry") or {}
                    _row["x"], _row["y"] = _g.get("x"), _g.get("y")
                _out.append(_row)
            return _out

        with ThreadPoolExecutor(max_workers=6) as _pool:
            _rows = [r for chunk in _pool.map(_one, range(0, _total, _page)) for r in chunk]
        if len(_rows) != _total:
            raise RuntimeError(f"Expected {_total} rows from {layer_url}, got {len(_rows)}")
        return _rows

    def assign_area(x, y, area_shapes):
        """Return the area name containing each (x, y) point, or None if outside all areas."""
        _x = np.asarray(x, dtype=float)
        _y = np.asarray(y, dtype=float)
        _out = np.full(len(_x), None, dtype=object)
        for _name, _geom in area_shapes:
            _hit = shapely.contains_xy(_geom, _x, _y) & (_out == None)  # noqa: E711
            _out[_hit] = _name
        return _out

    def count_parcels(client, parcels_url, esri_geometry):
        """Count parcels fully inside one area polygon, using a server-side spatial query."""
        return arcgis_query(
            client, parcels_url, where="1=1", returnCountOnly="true",
            geometry=json.dumps(esri_geometry), geometryType="esriGeometryPolygon",
            inSR=4326, spatialRel="esriSpatialRelContains",
        )["count"]

    def live_count(layer_url, where):
        """Quick count for the live banner. Returns None instead of failing."""
        try:
            with httpx.Client() as _c:
                return arcgis_query(_c, layer_url, where=where, returnCountOnly="true")["count"]
        except Exception:
            return None
    return arcgis_query, assign_area, count_parcels, fetch_rows, live_count


@app.cell
def _(
    DOMAINS_311,
    LAYERS,
    arcgis_query,
    assign_area,
    count_parcels,
    datetime,
    fetch_rows,
    httpx,
    json,
    pl,
    shapely,
):
    def build_snapshot(data_dir):
        """Download every source once, place records in areas, and save a parquet snapshot."""
        data_dir.mkdir(parents=True, exist_ok=True)
        with httpx.Client() as _c:
            # --- Areas: boundaries, population, crime, BNIA vacancy, parcel counts
            _geo = _c.post(
                f"{LAYERS['areas']}/query",
                data={"where": "1=1", "outFields": "Community", "outSR": 4326, "f": "geojson"},
                timeout=120,
            ).json()
            _geo["features"] = [f for f in _geo["features"] if f["properties"]["Community"] != "Unassigned -- Jail"]
            _esri = {
                f["attributes"]["Community"]: f["geometry"]
                for f in arcgis_query(_c, LAYERS["areas"], where="1=1", outFields="Community", outSR=4326)["features"]
            }

            def _bnia(layer, field):
                _rows = arcgis_query(_c, LAYERS[layer], where="1=1", outFields=f"CSA2010,{field}", returnGeometry="false")
                return {r["attributes"]["CSA2010"]: r["attributes"][field] for r in _rows["features"]}

            _pop, _crime, _vac = _bnia("population", "tpop20"), _bnia("crime", "viol23"), _bnia("bnia_vacant", "vacant23")
            for _f in _geo["features"]:
                _name = _f["properties"]["Community"]
                _f["properties"] = {
                    "csa": _name,
                    "pop": _pop[_name],
                    "parcels": count_parcels(_c, LAYERS["parcels"], _esri[_name]),
                    "violent_crime_rate": _crime[_name],
                    "bnia_vacant_pct": _vac[_name],
                }
            _shapes = [(f["properties"]["csa"], shapely.geometry.shape(f["geometry"])) for f in _geo["features"]]
            for _, _g in _shapes:
                shapely.prepare(_g)

            # --- 311 requests in our topics
            _type_domain = {
                t: (d, kind == "proactive")
                for d, spec in DOMAINS_311.items()
                for kind in ("reported", "proactive")
                for t in spec[kind]
            }
            _types = ",".join("'" + t.replace("'", "''") + "'" for t in _type_domain)
            _raw = pl.DataFrame(
                fetch_rows(
                    _c, LAYERS["sr311"], f"SRType IN ({_types})",
                    # DueDate is the city's own SLA target, so "late" can be judged against its own
                    # promise rather than against a cutoff we picked. SRStatus is kept rather than
                    # only used as a filter: without it a missing CloseDate cannot tell a request
                    # that is genuinely still open from one that was quietly cancelled.
                    "SRType,SRStatus,CreatedDate,CloseDate,DueDate,Agency,MethodReceived,"
                    "Neighborhood,Latitude,Longitude,Address",
                ),
                infer_schema_length=None,
            )
            _bad = pl.col("SRStatus").str.contains("(?i)duplicate|transferred")
            _sr = _raw.filter(~_bad).with_columns(
                pl.col("Longitude").cast(pl.Float64, strict=False).alias("x"),
                pl.col("Latitude").cast(pl.Float64, strict=False).alias("y"),
            )
            _sr = _sr.with_columns(
                pl.Series("csa", assign_area(_sr["x"], _sr["y"], _shapes), dtype=pl.String),
                pl.col("SRType").replace_strict({t: v[0] for t, v in _type_domain.items()}).alias("domain"),
                pl.col("SRType").replace_strict({t: v[1] for t, v in _type_domain.items()}).alias("proactive"),
                pl.from_epoch("CreatedDate", time_unit="ms").alias("created"),
                pl.from_epoch("CloseDate", time_unit="ms").alias("closed"),
                pl.from_epoch(pl.col("DueDate").cast(pl.Int64, strict=False), time_unit="ms").alias("due"),
            )
            _sr_in = _sr.filter(pl.col("csa").is_not_null()).select(
                "csa", "domain", "proactive", pl.col("SRType").alias("sr_type"), "created", "closed", "due",
                pl.col("SRStatus").alias("status"),
                pl.col("Agency").str.strip_chars().alias("agency"),  # the layer pads these to fixed width
                pl.col("MethodReceived").str.strip_chars().alias("method"),
                pl.col("Neighborhood").str.strip_chars().alias("neighborhood"),
                pl.col("x", "y").round(5), pl.col("Address").str.strip_chars().alias("address"),
            )

            # --- Housing: open vacancy notices, rehab permits, demolitions
            _housing_specs = {
                "open_notice": ("open_notices", "BLOCKLOT,DateNotice,Address", "DateNotice"),
                "rehab": ("rehabs", "BLOCKLOT,DateIssue,VBN,Address", "DateIssue"),
                "demolition": ("demolitions", "BLOCKLOT,DateDemoFinished,Address", "DateDemoFinished"),
            }
            _frames, _housing_counts = [], {}
            for _kind, (_layer, _fields, _date) in _housing_specs.items():
                _h = pl.DataFrame(fetch_rows(_c, LAYERS[_layer], "1=1", _fields, with_xy=True), infer_schema_length=None)
                _housing_counts[_kind] = _h.height
                _frames.append(
                    _h.select(
                        pl.lit(_kind).alias("kind"),
                        pl.col("BLOCKLOT").str.strip_chars().alias("blocklot"),
                        pl.from_epoch(pl.col(_date).cast(pl.Int64), time_unit="ms").alias("date"),
                        pl.Series("csa", assign_area(_h["x"], _h["y"], _shapes), dtype=pl.String),
                        pl.col("x").cast(pl.Float64).round(5),
                        pl.col("y").cast(pl.Float64).round(5),
                        pl.col("Address").cast(pl.String).str.strip_chars().alias("address"),
                    )
                )
            _housing = pl.concat(_frames)
            _housing_in = _housing.filter(pl.col("csa").is_not_null())

        # --- Save
        _sr_in.write_parquet(data_dir / "requests_311.parquet")
        _housing_in.write_parquet(data_dir / "housing.parquet")
        (data_dir / "areas.geojson").write_text(json.dumps(_geo))
        _meta = {
            "snapshot_date": _sr_in["created"].max().strftime("%Y-%m-%d"),
            "snapshot_ts": _sr_in["created"].max().isoformat(),
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "counts": {
                "requests_311": _sr_in.height,
                "open_notices": _housing_counts["open_notice"],
                "rehabs": _housing_counts["rehab"],
                "demolitions": _housing_counts["demolition"],
                "parcels": sum(f["properties"]["parcels"] for f in _geo["features"]),
                "areas": len(_geo["features"]),
                "population": sum(f["properties"]["pop"] for f in _geo["features"]),
            },
            "dropped": {
                "requests_fetched": _raw.height,
                "duplicate_or_transferred": _raw.height - _sr.height,
                "requests_outside_areas": _sr.height - _sr_in.height,
                "housing_outside_areas": _housing.height - _housing_in.height,
            },
        }
        (data_dir / "snapshot_meta.json").write_text(json.dumps(_meta, indent=2))
        return _meta
    return (build_snapshot,)


@app.cell
def _(Path, build_snapshot, json, mo, pl, shapely):
    DATA_DIR = (mo.notebook_dir() or Path.cwd()) / "data"
    _files = ["requests_311.parquet", "housing.parquet", "areas.geojson", "snapshot_meta.json"]
    if not all((DATA_DIR / f).exists() for f in _files):
        with mo.status.spinner("No saved snapshot found. Downloading from Open Baltimore (a few minutes, once)..."):
            build_snapshot(DATA_DIR)

    snapshot_meta = json.loads((DATA_DIR / "snapshot_meta.json").read_text())
    areas_geo = json.loads((DATA_DIR / "areas.geojson").read_text())
    # Display copy only: simplify boundaries to ~10 m (1.7 MB -> ~65 KB) so the map fits marimo's output limit.
    # Placing points in areas used the full-detail shapes when the snapshot was built.
    for _f in areas_geo["features"]:
        _shape = shapely.set_precision(shapely.geometry.shape(_f["geometry"]).simplify(1e-4, preserve_topology=True), 1e-5)
        _f["geometry"] = shapely.geometry.mapping(_shape)
    requests_311 = pl.read_parquet(DATA_DIR / "requests_311.parquet")
    housing = pl.read_parquet(DATA_DIR / "housing.parquet")
    areas = pl.DataFrame([f["properties"] for f in areas_geo["features"]])
    return DATA_DIR, areas, areas_geo, housing, requests_311, snapshot_meta


@app.cell
def _(DOMAINS_311, LAYERS, ThreadPoolExecutor, live_count, mo, snapshot_meta):
    def _open_count(item):
        _topic, _types = item
        _values = ",".join(f"'{t.replace(chr(39), chr(39) * 2)}'" for t in _types["reported"])
        return _topic, live_count(
            LAYERS["sr311"],
            f"SRType IN ({_values}) AND SRStatus IN ('Open','New')",
        )

    with ThreadPoolExecutor(max_workers=6) as _pool:
        _topic_counts = dict(_pool.map(_open_count, DOMAINS_311.items()))
        _vbn = _pool.submit(live_count, LAYERS["open_notices"], "1=1").result()

    _available = {topic: count for topic, count in _topic_counts.items() if count is not None}
    if not _available and _vbn is None:
        live_banner = mo.callout(
            mo.md(
                f"**Live data unavailable right now.** Everything below uses the saved snapshot "
                f"from {snapshot_meta['snapshot_date']}, so the notebook works offline."
            ),
            kind="warn",
        )
    else:
        _request_summary = (
            f"{sum(_available.values()):,} open resident requests across all "
            f"{len(DOMAINS_311)} tracked 311 topics"
            if len(_available) == len(DOMAINS_311)
            else f"live request counts for {len(_available)} of {len(DOMAINS_311)} tracked 311 topics"
        )
        _vacancy_summary = (
            f"{_vbn:,} open vacancy notices"
            if _vbn is not None
            else "vacancy count temporarily unavailable"
        )
        _breakdown = "\n".join(
            f"- **{topic}:** {count:,}" if count is not None else f"- **{topic}:** unavailable"
            for topic, count in _topic_counts.items()
        )
        live_banner = mo.callout(
            mo.md(
                f"**Live city workload:** {_request_summary} · {_vacancy_summary}.\n\n"
                f"{_breakdown}\n\n"
                f"The analysis below uses the fixed snapshot from {snapshot_meta['snapshot_date']}, "
                f"so its text and charts stay consistent."
            ),
            kind="info",
        )
    return (live_banner,)


@app.cell
def _(DOMAINS_311, MIN_REQUESTS, VACANCY, VACANCY_SINCE, datetime, np, pl, timedelta):
    def pct_rank(col):
        """Percentile rank (0 = lowest, 1 = highest) within each topic, ignoring missing values."""
        _c = pl.col(col)
        return ((_c.rank("average") - 1) / (_c.count() - 1)).over("domain")

    def neglect_residual(service_col="service_pct", need_col="need_pct"):
        """How far *below* the service its need predicts an area sits, within a topic.

        Least-squares fit of service on need across the areas scored for that topic, then the
        negated residual. Orthogonal to need by construction, so the ranking cannot be the need
        map wearing a different name; a plain need - service difference is not (see `metric`).
        """
        _x = pl.when(pl.col(service_col).is_not_null()).then(pl.col(need_col))  # only pairs the fit can use
        _y = pl.col(service_col)
        _xm, _ym = _x.mean().over("domain"), _y.mean().over("domain")
        _sxx = ((_x - _xm) ** 2).sum().over("domain")
        _slope = pl.when(_sxx > 0).then(((_x - _xm) * (_y - _ym)).sum().over("domain") / _sxx).otherwise(0.0)
        return -(_y - (_ym + _slope * (pl.col(need_col) - _xm)))

    def duration_service(fix_clock, t):
        """Share of the first t days a typical request is already closed: 1 - mean(S[0:t]).

        S(u) is the share still open on day u, the same curve the Fix Clock draws. The mean of
        S from day 0 through day t is RMST(t) / (t + 1): the fraction of that window spent
        unfixed. Subtracting from 1 makes a service share. Cells with a median of "never"
        still get a finite number.
        """
        _S = np.asarray(fix_clock["S"], dtype=float)
        _t = int(min(max(int(t), 0), _S.shape[1] - 1))
        return fix_clock["cells"].with_columns(
            pl.Series("duration_share", 1.0 - _S[:, : _t + 1].mean(axis=1)),
            # UInt32 matches the vacancy n_service column so diagonal concat stays aligned.
            pl.Series("n_clock", np.rint(np.asarray(fix_clock["n"])).astype(np.uint32)),
        )

    def score_areas(
        requests_311, housing, areas, *, snapshot_ts, window_days, fix_days, per,
        metric="residual", service="duration", fix_clock=None,
    ):
        """Need and service per area and topic, as raw rates and percentiles, plus the gap.

        Service is always a share of need in the same topic (never a count per resident or parcel),
        so an area does not look well served just because it has a lot of problems.

        `service="duration"` (default) is 1 − mean(S[0:t]) from the precomputed Fix Clock,
        sliced at `fix_days`. Need still follows `window_days` and `per`. Vacancy is unchanged
        (share handled since 2023). `service="fast_share"` is the old binary close-within-t rule.

        `metric="residual"` scores the gap as how far below the fitted service-on-need line an area
        sits. `metric="difference"` is the original need_pct - service_pct, kept for comparison: it
        ranks areas at Spearman +0.88 with need alone, so it is close to a relabelled need map.
        """
        _end = datetime.fromisoformat(snapshot_ts)
        _start = _end - timedelta(days=window_days) if window_days else datetime(1900, 1, 1)
        _sr = requests_311.filter(pl.col("created") >= _start)
        _grid = areas.select("csa", "pop", "parcels").join(
            pl.DataFrame({"domain": list(DOMAINS_311)}), how="cross"
        )

        # Need: resident reports per 1,000 residents (or parcels)
        _reported = _sr.filter(~pl.col("proactive"))
        _need = _reported.group_by("csa", "domain").agg(pl.len().alias("n_reports"))

        # Service 1: how long requests stay open (default), or the old closed-within-t share.
        if service == "duration":
            if fix_clock is None:
                raise ValueError("fix_clock is required when service='duration'")
            _dur = duration_service(fix_clock, fix_days)
            _fast = _dur.select(
                "csa", "domain",
                pl.col("n_clock").alias("n_service"),
                pl.col("duration_share").alias("closed_fast_share"),
            )
        elif service == "fast_share":
            _fast = (
                _reported.filter(pl.col("created") <= _end - timedelta(days=fix_days))
                .with_columns(
                    ((pl.col("closed") - pl.col("created")) <= pl.duration(days=fix_days)).fill_null(False).alias("fast")
                )
                .group_by("csa", "domain")
                .agg(pl.len().alias("n_service"), pl.col("fast").mean().alias("closed_fast_share"))
            )
        else:
            raise ValueError(f"unknown service={service!r}")

        # Service 2: proactive tickets per resident report (only topics that have proactive twins)
        _pro = _sr.filter(pl.col("proactive")).group_by("csa", "domain").agg(pl.len().alias("n_proactive"))
        _has_pro = [d for d, s in DOMAINS_311.items() if s["proactive"]]

        _s311 = (
            _grid.join(_need, on=["csa", "domain"], how="left")
            .join(_fast, on=["csa", "domain"], how="left")
            .join(_pro, on=["csa", "domain"], how="left")
            .with_columns(pl.col("n_reports", "n_service", "n_proactive").fill_null(0))
            .with_columns(
                (pl.col("n_reports") / pl.col(per) * 1000).alias("need_rate"),
                pl.when(pl.col("n_service") >= MIN_REQUESTS).then(pl.col("closed_fast_share")).alias("closed_fast_share"),
                pl.when(pl.col("domain").is_in(_has_pro) & (pl.col("n_proactive") + pl.col("n_reports") >= MIN_REQUESTS))
                .then(pl.col("n_proactive") / (pl.col("n_proactive") + pl.col("n_reports")))
                .alias("proactive_share"),
            )
            .with_columns(pct_rank("closed_fast_share").alias("_p1"), pct_rank("proactive_share").alias("_p2"))
            .with_columns(pl.mean_horizontal("_p1", "_p2").alias("_service_mix"))
            .with_columns(pl.when(pl.col("closed_fast_share").is_null()).then(None).otherwise(pl.col("_service_mix")).alias("_service_mix"))
            .select(
                "csa", "domain", "need_rate", "n_reports", "n_service",
                pl.col("closed_fast_share").alias("service_rate"), "proactive_share", "_service_mix",
            )
        )

        # Vacancy: need = open notices per 1,000 parcels;
        # service = share of vacant buildings that got a rehab permit or demolition since VACANCY_SINCE.
        _h = housing.filter(
            (pl.col("kind") == "open_notice") | (pl.col("date") >= datetime.fromisoformat(VACANCY_SINCE))
        ).filter(pl.col("blocklot").is_not_null())
        _vac = (
            _h.group_by("csa")
            .agg(
                (pl.col("kind") == "open_notice").sum().alias("n_reports"),
                pl.col("blocklot").n_unique().alias("n_service"),
                pl.col("blocklot").filter(pl.col("kind") != "open_notice").n_unique().alias("n_handled"),
            )
        )
        _svac = (
            areas.select("csa", "parcels")
            .join(_vac, on="csa", how="left")
            .with_columns(pl.col("n_reports", "n_service", "n_handled").fill_null(0))
            .with_columns(
                pl.lit(VACANCY).alias("domain"),
                (pl.col("n_reports") / pl.col("parcels") * 1000).alias("need_rate"),
                pl.when(pl.col("n_service") >= MIN_REQUESTS)
                .then(pl.col("n_handled") / pl.col("n_service"))
                .alias("service_rate"),
                (pl.col("n_handled") / pl.col("parcels") * 1000).alias("old_service_per_parcel"),
                pl.lit(None, dtype=pl.Float64).alias("proactive_share"),
            )
            .with_columns(pl.col("service_rate").alias("_service_mix"))
            .select(
                "csa", "domain", "need_rate", "n_reports", "n_service", "service_rate",
                "proactive_share", "_service_mix", "old_service_per_parcel",
            )
        )

        _gap = neglect_residual() if metric == "residual" else pl.col("need_pct") - pl.col("service_pct")
        return (
            pl.concat([_s311, _svac], how="diagonal")
            .with_columns(pct_rank("need_rate").alias("need_pct"), pct_rank("_service_mix").alias("service_pct"))
            .with_columns(_gap.alias("gap"))
            .drop("_service_mix")
        )

    def summarize(domain_scores, weights):
        """Weighted need, service and gap per area, using only topics that have a gap score."""
        _w = pl.DataFrame({"domain": list(weights), "w": [float(v) for v in weights.values()]})
        _ds = domain_scores.join(_w, on="domain").filter(pl.col("gap").is_not_null() & (pl.col("w") > 0))
        _top = (
            _ds.sort("gap", descending=True)
            .with_columns(
                (pl.col("domain") + " (" + (pl.col("gap") * 100).round(0).cast(pl.Int64).map_elements(lambda g: f"{g:+d}", return_dtype=pl.String) + ")").alias("_label")
            )
            .group_by("csa", maintain_order=True)
            .agg(pl.col("_label").head(3).str.join("; ").alias("widest_gaps"))
        )
        return (
            _ds.group_by("csa")
            .agg(
                ((pl.col("need_pct") * pl.col("w")).sum() / pl.col("w").sum()).alias("need"),
                ((pl.col("service_pct") * pl.col("w")).sum() / pl.col("w").sum()).alias("service"),
                ((pl.col("gap") * pl.col("w")).sum() / pl.col("w").sum()).alias("gap"),
                pl.len().alias("topics_scored"),
            )
            .join(_top, on="csa", how="left")
            .sort("gap", descending=True)
            .with_row_index("rank", offset=1)
        )
    return duration_service, neglect_residual, score_areas, summarize


@app.cell
def _(BULK_CLOSED, FIX_HALF_LIFE, FIX_HORIZON, FIX_KAPPA, datetime, np, pl):
    def fit_fix_clock(requests_311, *, snapshot_ts, horizon=FIX_HORIZON, kappa=FIX_KAPPA,
                      half_life=FIX_HALF_LIFE):
        """How long a reported problem stays open, as a curve rather than an average.

        For each topic and area we estimate S(t), the share of requests still open on day t, with a
        discrete-time hazard on a daily grid:

            h_topic(t) = closed(t) / at_risk(t)                           topic-wide, all 55 areas
            h_cell(t)  = (closed(t) + kappa * h_topic(t)) / (at_risk(t) + kappa)
            S_cell(t)  = prod over u <= t of (1 - h_cell(u))

        Averaging how long finished repairs took answers the wrong question, because a request that
        is never closed never enters the average. Here it stays in the risk set instead, which is why
        Roads can have no median at all: most road requests are still open when the data ends.

        `kappa` is a pseudo-count, the dial between a per-topic model and a per-area one. At 0 each
        cell gets its own Kaplan-Meier curve; raised, thin cells fall back on the topic's own history
        rather than on noise. 141 of the 487 cells hold fewer than 30 requests, so some pooling is
        not optional. Once a cell's risk set empties, only the kappa terms remain and its curve
        carries on at the topic's rate.

        Requests are weighted `0.5 ** (age / half_life)` rather than counted once each, because the
        city's pace drifts: a request from January says less about today than one from August. Held
        out on the second half of the year, a 60-day half-life cut the day-14 error from 0.070 to
        0.041 and improved both the Brier score and the between-area signal. See the calibration note
        under the clock for what it does not fix.
        """
        _end = datetime.fromisoformat(snapshot_ts)
        _r = (
            requests_311.filter(~pl.col("proactive") & ~pl.col("sr_type").is_in(BULK_CLOSED))
            .with_columns(
                ((pl.coalesce("closed", pl.lit(_end)) - pl.col("created")).dt.total_seconds() / 86400)
                .clip(0.0, None).alias("_dur"),
                pl.col("closed").is_not_null().alias("_event"),
            )
            .with_columns(
                pl.col("_dur").floor().clip(0, horizon).cast(pl.Int32).alias("_exit"),
                (pl.col("_event") & (pl.col("_dur") <= horizon)).alias("_event"),
            )
        )
        _cells = _r.select("domain", "csa").unique().sort("domain", "csa")
        _at = {_k: _i for _i, _k in enumerate(_cells.iter_rows())}
        _n, _T = len(_at), horizon + 1

        # One flat bincount per grid: exits of any kind, and the subset that were actually closed.
        _ci = np.array([_at[_k] for _k in _r.select("domain", "csa").iter_rows()])
        _flat = _ci * _T + _r["_exit"].to_numpy()
        _w = (
            0.5 ** ((_end - _r["created"]).dt.total_seconds().to_numpy() / 86400.0 / half_life)
            if half_life else np.ones(len(_flat))
        )
        _ev = _r["_event"].to_numpy()
        _exits = np.bincount(_flat, weights=_w, minlength=_n * _T).reshape(_n, _T)
        _events = np.bincount(_flat[_ev], weights=_w[_ev], minlength=_n * _T).reshape(_n, _T)
        # Weighted counts drive the fit, but a reader is owed the real number of requests.
        _raw = np.bincount(_ci, minlength=_n).astype(float)
        _raw_open = _raw - np.bincount(_ci[_ev], minlength=_n)
        _totals = _exits.sum(axis=1, keepdims=True)
        _at_risk = _totals - np.concatenate([np.zeros((_n, 1)), np.cumsum(_exits, axis=1)[:, :-1]], axis=1)

        _domains = sorted(set(_cells["domain"].to_list()))
        _dom_of = np.array([_domains.index(_d) for _d in _cells["domain"]])
        _dev, _dar = np.zeros((len(_domains), _T)), np.zeros((len(_domains), _T))
        np.add.at(_dev, _dom_of, _events)
        np.add.at(_dar, _dom_of, _at_risk)
        _h_dom = np.divide(_dev, _dar, out=np.zeros_like(_dev), where=_dar > 0)

        _num, _den = _events + kappa * _h_dom[_dom_of], _at_risk + kappa
        _h = np.divide(_num, _den, out=np.zeros_like(_num), where=_den > 0)
        return {
            "days": np.arange(_T),
            "cells": _cells,
            "domains": _domains,
            "dom_of": _dom_of,
            "S": np.cumprod(1.0 - _h, axis=1),
            "S_domain": np.cumprod(1.0 - _h_dom, axis=1),
            "at_risk": _at_risk,
            "events": _events,
            "n": _raw,
            "n_open": _raw_open,
            "n_effective": _totals.ravel(),
            "kappa": kappa,
        }

    def median_days(curves):
        """First day each curve drops to half still open, or None where it never does."""
        _hit = np.asarray(curves) <= 0.5
        return [int(np.argmax(_r)) if _r.any() else None for _r in np.atleast_2d(_hit)]

    return fit_fix_clock, median_days


@app.cell
def _(
    BULK_CLOSED,
    FIX_CATS,
    FIX_EDGES,
    FIX_HORIZON,
    FIX_NUMS,
    HistGradientBoostingClassifier,
    IsotonicRegression,
    datetime,
    fit_fix_clock,
    np,
    pl,
):
    def fix_features(requests_311, areas, *, snapshot_ts):
        """One row per resident-reported request, with everything known the moment it was filed."""
        _end = datetime.fromisoformat(snapshot_ts)
        _a = areas.with_columns((pl.col("parcels") / pl.col("pop")).alias("parcels_pc"))
        _r = (
            requests_311.filter(~pl.col("proactive") & ~pl.col("sr_type").is_in(BULK_CLOSED))
            .with_columns(
                ((pl.coalesce("closed", pl.lit(_end)) - pl.col("created")).dt.total_seconds() / 86400)
                .clip(0.0, None).floor().alias("exit"),
                pl.col("closed").is_not_null().alias("event"),
                pl.col("created").dt.weekday().alias("dow"),
                # The city's own promised turnaround, set when the request is filed. Not an outcome.
                ((pl.col("due") - pl.col("created")).dt.total_seconds() / 86400).alias("sla_days"),
            )
        )
        _vol = (
            _r.group_by("csa").agg(pl.len().alias("_n"))
            .join(_a.select("csa", "pop"), on="csa")
            .with_columns((pl.col("_n") / pl.col("pop") * 1000).alias("reports_per_1k"))
        )
        return _r.join(_vol.select("csa", "reports_per_1k"), on="csa").join(
            _a.select("csa", vacancy="bnia_vacant_pct", crime="violent_crime_rate", parcels_pc="parcels_pc"),
            on="csa",
        )

    def _baseline(train_raw, snapshot_ts):
        """Counting-model hazard per (topic, area, interval), handed to the model as a starting point."""
        _f = fit_fix_clock(train_raw, snapshot_ts=snapshot_ts)
        _S = _f["S"]
        _edge = np.column_stack([_S[:, min(_e, _S.shape[1] - 1)] for _e in FIX_EDGES])
        _h = 1 - np.divide(_edge[:, 1:], np.maximum(_edge[:, :-1], 1e-9))
        return {_k: _i for _i, _k in enumerate(_f["cells"].iter_rows())}, np.clip(_h, 1e-6, 1 - 1e-6)

    def _grid(r, idx, H, *, with_label):
        """Explode requests into one row per interval they were still open for.

        This is what makes censoring a non-issue: a request that is still open simply stops
        producing rows, rather than being dropped from the data or counted as fixed.
        """
        _K = len(FIX_EDGES) - 1
        _g = (
            r.with_columns(k=pl.lit(list(range(_K)), dtype=pl.List(pl.Int32))).explode("k")
            .with_columns(
                pl.col("k").replace_strict({_i: float(FIX_EDGES[_i]) for _i in range(_K)}).alias("start"),
                pl.col("k").replace_strict({_i: float(FIX_EDGES[_i + 1]) for _i in range(_K)}).alias("stop"),
            )
        )
        if with_label:
            _g = _g.filter(pl.col("exit") >= pl.col("start")).with_columns(
                (pl.col("event") & (pl.col("exit") < pl.col("stop"))).cast(pl.Int8).alias("y")
            )
        _g = _g.with_columns((pl.col("start") + 1).log().alias("log_start"))
        _keys = list(_g.select("domain", "csa").iter_rows())
        _hb = np.array([H[idx[_q]][_k] if _q in idx else 0.2 for _q, _k in zip(_keys, _g["k"].to_numpy())])
        return _g.with_columns(pl.Series("base_logit", np.log(_hb / (1 - _hb))))

    def _matrix(g, codes):
        """Categoricals as integer codes; anything unseen becomes a missing value the model handles."""
        _cols = [np.array([codes[_c].get(_v, np.nan) for _v in g[_c]], dtype=float) for _c in FIX_CATS]
        _cols += [g[_c].cast(pl.Float64).fill_null(np.nan).to_numpy() for _c in FIX_NUMS]
        return np.column_stack(_cols)

    def train_fix_model(requests_311, areas, *, snapshot_ts, calib_from, seed=2026):
        """Gradient-boosted hazard, then isotonic calibration on a slice it was not trained on.

        The classifier answers one question per interval: given this request is still open, does it
        close now? Multiplying the answers back together gives the survival curve. Boosting is what
        lets it use per-request facts a per-area average cannot. Permutation importance says almost all
        of that comes from one of them: shuffling the SLA date the city itself set costs 0.11 Brier at
        seven days, against 0.06 for the topic, 0.002 for the owning agency and nothing at all for the
        reporting channel. Shuffling the neighbourhood and every area statistic costs nothing
        measurable. The strongest thing we know about how long you will wait is the deadline the city
        wrote on your ticket when you filed it.

        Calibrating on later requests than it trained on matters because sharpness and honesty are
        different things: the raw scores rank requests well but overstate their confidence.
        """
        _cal = datetime.fromisoformat(calib_from)
        _early = requests_311.filter(pl.col("created") < _cal).with_columns(
            pl.when(pl.col("closed") >= _cal).then(None).otherwise(pl.col("closed")).alias("closed")
        )
        _idx, _H = _baseline(_early, calib_from)
        _rf = fix_features(_early, areas, snapshot_ts=calib_from)
        _train = _grid(_rf, _idx, _H, with_label=True)
        _codes = {_c: {_v: _i for _i, _v in enumerate(sorted(_train[_c].unique().to_list()))} for _c in FIX_CATS}

        _model = HistGradientBoostingClassifier(
            max_iter=400, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=30,
            l2_regularization=1.0, categorical_features=list(range(len(FIX_CATS))),
            random_state=seed, early_stopping=True, validation_fraction=0.15,
        ).fit(_matrix(_train, _codes), _train["y"].to_numpy())

        _rc = fix_features(requests_311.filter(pl.col("created") >= _cal), areas, snapshot_ts=snapshot_ts)
        _cg = _grid(_rc, _idx, _H, with_label=True)
        _iso = IsotonicRegression(out_of_bounds="clip", y_min=1e-6, y_max=1 - 1e-6).fit(
            _model.predict_proba(_matrix(_cg, _codes))[:, 1], _cg["y"].to_numpy()
        )
        return {"model": _model, "iso": _iso, "codes": _codes, "idx": _idx, "H": _H,
                "n_train": _train.height, "n_calib": _cg.height, "rounds": int(_model.n_iter_)}

    def predict_fix_curves(bundle, r, *, horizon=FIX_HORIZON):
        """S(t) per request: the chance it is still open on day t."""
        _K = len(FIX_EDGES) - 1
        _g = _grid(r, bundle["idx"], bundle["H"], with_label=False)
        _h = bundle["iso"].predict(
            bundle["model"].predict_proba(_matrix(_g, bundle["codes"]))[:, 1]
        ).reshape(r.height, _K)
        _days = np.arange(horizon + 1)
        _S = np.ones((r.height, horizon + 1))
        _prev = np.ones(r.height)
        for _i in range(_K):
            _lo, _hi = FIX_EDGES[_i], FIX_EDGES[_i + 1]
            _sel = (_days > _lo) & (_days <= _hi)
            # Spread each interval's survival across its days so the curve reads smoothly.
            _S[:, _sel] = _prev[:, None] * (1 - _h[:, [_i]]) ** ((_days[_sel] - _lo) / (_hi - _lo))
            _prev = _prev * (1 - _h[:, _i])
        return _S

    return fix_features, predict_fix_curves, train_fix_model


@app.cell
def _(
    FIX_CALIB_FROM,
    datetime,
    fit_fix_clock,
    fix_features,
    np,
    pl,
    predict_fix_curves,
    train_fix_model,
):
    def calibration_check(requests_311, areas, *, snapshot_ts, cutoff, horizons=(3, 7, 14, 30), bins=10):
        """Score the model against requests filed after it was built, and against a simpler rival.

        Splitting by date rather than at random matters: a random split would let the model see how
        the very requests it is tested on turned out. Anything closed after the cutoff is hidden too,
        so a request that closed in August enters training as still open, the way it looked on the
        day. `gap` is the average distance between predicted and observed across ten bands of
        predicted risk. `gap_simple` is the same for a plain counting estimate, which is the thing
        the trained model has to beat to earn its place.
        """
        _cut, _end = datetime.fromisoformat(cutoff), datetime.fromisoformat(snapshot_ts)
        _past = requests_311.filter(pl.col("created") < _cut).with_columns(
            pl.when(pl.col("closed") >= _cut).then(None).otherwise(pl.col("closed")).alias("closed")
        )
        _bundle = train_fix_model(_past, areas, snapshot_ts=cutoff, calib_from=FIX_CALIB_FROM)
        _later = requests_311.filter(pl.col("created") >= _cut)
        _te = fix_features(_later, areas, snapshot_ts=snapshot_ts).with_columns(
            ((_end - pl.col("created")).dt.total_seconds() / 86400).alias("room")
        )
        _ml = predict_fix_curves(_bundle, _te)

        _simple = fit_fix_clock(_past, snapshot_ts=cutoff)
        _at = {_k: _i for _i, _k in enumerate(_simple["cells"].iter_rows())}
        _keys = list(_te.select("domain", "csa").iter_rows())
        _sv = np.array([_simple["S"][_at[_k]] if _k in _at else np.full(_ml.shape[1], np.nan) for _k in _keys])
        _room, _exit = _te["room"].to_numpy(), _te["exit"].to_numpy()

        def _gap(_p, _o):
            _ok = ~np.isnan(_p)
            _p, _o = _p[_ok], _o[_ok]
            _order = np.argsort(_p)
            return sum(len(_b) * abs(_p[_b].mean() - _o[_b].mean())
                       for _b in np.array_split(_order, bins) if len(_b)) / max(len(_p), 1)

        def _auc(_o, _p):
            _ok = ~np.isnan(_p)
            _o, _p = _o[_ok], _p[_ok]
            if _o.min() == _o.max():
                return float("nan")
            _r = _p.argsort().argsort() + 1.0
            _n1 = _o.sum()
            return float((_r[_o == 1].sum() - _n1 * (_n1 + 1) / 2) / (_n1 * (len(_o) - _n1)))

        _dom = np.array([_k[0] for _k in _keys])

        # Does ranking the queue actually work? Take the requests still open at TRIAGE_FROM that we
        # can still see TRIAGE_AHEAD days past, rank them by the model's conditional risk, and check
        # how many of the ones it puts at the top really do stay open.
        _span = TRIAGE_FROM + TRIAGE_AHEAD
        _q = (_room >= _span) & (_exit > TRIAGE_FROM)
        _score = np.divide(_ml[_q, min(_span, FIX_HORIZON)],
                           np.maximum(_ml[_q, TRIAGE_FROM], 1e-9))
        _truth = (_exit[_q] > _span).astype(float)
        _order = np.argsort(-_score)
        _top = _order[: max(1, len(_order) // 10)]
        _base = _truth.mean() if len(_truth) else 0.0
        _triage = {
            "n": int(_q.sum()),
            "base": float(_base),
            "auc": _auc(_truth, _score),
            "precision": float(_truth[_top].mean()) if len(_top) else 0.0,
            "recall": float(_truth[_top].sum() / max(_truth.sum(), 1)),
            "flagged": int(len(_top)),
        }
        _triage["lift"] = _triage["precision"] / _base if _base else 0.0

        _rows = []
        for _t in horizons:
            _sel = _room >= _t
            _o = (_exit[_sel] > _t).astype(float)
            # Ranking is judged inside a topic, where the topic curve is a constant and only the
            # request's own circumstances can tell one case from another.
            _a, _w = [], []
            for _d in np.unique(_dom):
                _s2 = _sel & (_dom == _d)
                _o2 = (_exit[_s2] > _t).astype(float)
                if len(_o2) < 50 or _o2.min() == _o2.max():
                    continue
                _v = _auc(_o2, _ml[_s2, _t])
                if not np.isnan(_v):
                    _a.append(_v)
                    _w.append(len(_o2))
            _rows.append({
                "horizon": _t, "n": int(_sel.sum()), "observed": float(_o.mean()),
                "gap": _gap(_ml[_sel, _t], _o), "gap_simple": _gap(_sv[_sel, _t], _o),
                "ranking": float(np.average(_a, weights=_w)) if _a else float("nan"),
            })
        return pl.DataFrame(_rows), _triage

    return (calibration_check,)


@app.cell
def _(ROBUST_SHARE, np, pl):
    def rank_stability(domain_scores, n_samples=2000, top_k=10, seed=2026):
        """Rank areas under many random topic weightings; report how often each lands in the top k."""
        _wide = domain_scores.pivot(on="domain", index="csa", values="gap").sort("csa")
        _names = _wide["csa"].to_list()
        _g = _wide.drop("csa").to_numpy().astype(float)
        _mask = ~np.isnan(_g)
        _weights = np.random.default_rng(seed).dirichlet(np.ones(_g.shape[1]), size=n_samples).T
        _scores = (np.nan_to_num(_g) @ _weights) / np.maximum(_mask @ _weights, 1e-12)
        _ranks = (-_scores).argsort(axis=0).argsort(axis=0) + 1
        return (
            pl.DataFrame(
                {
                    "csa": _names,
                    "top10_share": (_ranks <= top_k).mean(axis=1),
                    "median_rank": np.median(_ranks, axis=1),
                    "best_rank": np.percentile(_ranks, 5, axis=1),
                    "worst_rank": np.percentile(_ranks, 95, axis=1),
                }
            )
            .with_columns(
                pl.when(pl.col("top10_share") >= ROBUST_SHARE).then(pl.lit("Robust"))
                .when(pl.col("top10_share") >= 0.1).then(pl.lit("Weight sensitive"))
                .otherwise(pl.lit("Rarely top 10"))
                .alias("verdict")
            )
            .sort(["top10_share", "median_rank"], descending=[True, False])
        )

    def spearman(a, b):
        """Rank correlation between two equal-length arrays (ignores pairs with missing values)."""
        _a, _b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        _ok = ~(np.isnan(_a) | np.isnan(_b))
        _ra = _a[_ok].argsort().argsort()
        _rb = _b[_ok].argsort().argsort()
        return float(np.corrcoef(_ra, _rb)[0, 1])
    return rank_stability, spearman


@app.cell
def _(
    DEFAULT_FIX_DAYS,
    DOMAIN_ORDER,
    areas,
    fix_clock,
    housing,
    rank_stability,
    requests_311,
    score_areas,
    snapshot_meta,
    summarize,
):
    # Fixed default settings: these back every number written in the text, so prose never drifts from charts.
    # 311 service is the Fix Clock sliced at DEFAULT_FIX_DAYS (same S the map and demo calls use).
    default_scores = score_areas(
        requests_311, housing, areas,
        snapshot_ts=snapshot_meta["snapshot_ts"], window_days=0, fix_days=DEFAULT_FIX_DAYS, per="pop",
        service="duration", fix_clock=fix_clock,
    )
    default_overall = summarize(default_scores, {d: 1 for d in DOMAIN_ORDER})
    default_robust = rank_stability(default_scores)
    return default_overall, default_robust, default_scores


@app.cell
def _(
    DEFAULT_FIX_DAYS,
    DOMAIN_ORDER,
    areas,
    default_overall,
    default_scores,
    fix_clock,
    housing,
    mo,
    pl,
    requests_311,
    score_areas,
    snapshot_meta,
    spearman,
    summarize,
):
    _kw = dict(
        snapshot_ts=snapshot_meta["snapshot_ts"], window_days=0, per="pop",
    )
    _eq = {d: 1 for d in DOMAIN_ORDER}
    _cut7 = score_areas(
        requests_311, housing, areas, **_kw, fix_days=DEFAULT_FIX_DAYS, service="fast_share",
    )
    _cut30 = score_areas(requests_311, housing, areas, **_kw, fix_days=30, service="fast_share")
    _dur30 = score_areas(
        requests_311, housing, areas, **_kw, fix_days=30, service="duration", fix_clock=fix_clock,
    )
    _diff = score_areas(
        requests_311, housing, areas, **_kw, fix_days=DEFAULT_FIX_DAYS,
        service="duration", fix_clock=fix_clock, metric="difference",
    )
    _o_cut = summarize(_cut7, _eq)
    _o_diff = summarize(_diff, _eq)
    _cmp = default_overall.select("csa", pl.col("rank").alias("rank_duration")).join(
        _o_cut.select("csa", pl.col("rank").alias("rank_cutoff")), on="csa",
    )
    _r_rank = spearman(_cmp["rank_duration"], _cmp["rank_cutoff"])
    _r_need_gap = spearman(default_overall["need"], default_overall["gap"])
    _r_need_gap_diff = spearman(_o_diff["need"], _o_diff["gap"])
    _r_need_svc = spearman(default_overall["need"], default_overall["service"])
    _san = ["Illegal dumping", "Dirty streets & alleys", "Rats", "Graffiti"]

    def _sat(scores, label):
        _s = scores.filter(pl.col("domain").is_in(_san) & pl.col("service_rate").is_not_null())
        _n = _s.height
        return {
            "label": label,
            "mean": float(_s["service_rate"].mean()) if _n else float("nan"),
            "std": float(_s["service_rate"].std()) if _n else float("nan"),
            "share_ge_95": float(_s.filter(pl.col("service_rate") >= 0.95).height / _n) if _n else float("nan"),
        }

    _rows = [
        _sat(_cut7, "cutoff, 7 days"),
        _sat(_cut30, "cutoff, 30 days"),
        _sat(default_scores, "clock, 7 days"),
        _sat(_dur30, "clock, 30 days"),
    ]
    clock_vs_cutoff_stats = {
        "rank_spearman": _r_rank,
        "need_gap_residual": _r_need_gap,
        "need_gap_difference": _r_need_gap_diff,
        "need_service": _r_need_svc,
        "sanitation": _rows,
    }
    _table = "\n".join(
        f"| {r['label']} | {r['mean']:.0%} | {r['std']:.2f} | {100 * r['share_ge_95']:.0f}% |" for r in _rows
    )
    clock_vs_cutoff = mo.md(f"""
    The map ranks the **same clock** the resident call uses (share of the first {DEFAULT_FIX_DAYS}
    days already closed), not a binary “closed within {DEFAULT_FIX_DAYS} days” cutoff. The old
    cutoff is kept as `service="fast_share"` so we can check the two rankings against each other.

    - Gap rank, clock vs cutoff (equal weights): Spearman **{_r_rank:+.2f}**.
    - Need vs gap, residual (what the map uses): **{_r_need_gap:+.2f}**. Need vs gap, raw
      need − service: **{_r_need_gap_diff:+.2f}**. The residual keeps the ranking from becoming
      a need map.
    - Need vs service percentiles: **{_r_need_svc:+.2f}**.

    Sanitation (dumping, dirty streets, rats, graffiti). At 30 days the old cutoff saturates.
    The clock still notices *when* inside the window a ticket closed, so we keep the default
    horizon at {DEFAULT_FIX_DAYS} days.

    | Measure | Mean service | Std | Share ≥ 95% |
    | --- | --- | --- | --- |
    {_table}
    """)
    return clock_vs_cutoff, clock_vs_cutoff_stats


@app.cell
def _(
    FIX_CALIB_FROM,
    FIX_HORIZON,
    TRIAGE_AHEAD,
    TRIAGE_FROM,
    TRIAGE_TO,
    areas,
    datetime,
    fix_features,
    median_days,
    np,
    pl,
    predict_fix_curves,
    requests_311,
    snapshot_meta,
    train_fix_model,
):
    # Trained once against the snapshot, never on the slider path: the sliders re-slice these curves,
    # they never retrain. Takes a few seconds.
    fix_model = train_fix_model(
        requests_311, areas, snapshot_ts=snapshot_meta["snapshot_ts"], calib_from=FIX_CALIB_FROM
    )
    _r = fix_features(requests_311, areas, snapshot_ts=snapshot_meta["snapshot_ts"])
    _per_request = predict_fix_curves(fix_model, _r)

    # The map needs one curve per area, so average the requests that actually landed there.
    _cells = _r.select("domain", "csa").unique().sort("domain", "csa")
    _at = {_k: _i for _i, _k in enumerate(_cells.iter_rows())}
    _ci = np.array([_at[_k] for _k in _r.select("domain", "csa").iter_rows()])
    _counts = np.bincount(_ci, minlength=_cells.height).astype(float)
    _S = np.zeros((_cells.height, _per_request.shape[1]))
    np.add.at(_S, _ci, _per_request)
    _S = _S / np.maximum(_counts[:, None], 1)
    _open = np.bincount(_ci[~_r["event"].to_numpy()], minlength=_cells.height)

    fix_clock = {"cells": _cells, "S": _S, "n": _counts, "n_open": _open.astype(float),
                 "per_request": _per_request}
    fix_summary = _cells.with_columns(
        pl.Series("n", fix_clock["n"]).cast(pl.Int64),
        pl.Series("n_open", fix_clock["n_open"]).cast(pl.Int64),
        pl.Series("median_days", median_days(_S), dtype=pl.Int64),
        pl.Series("fixed_by_7", 1 - _S[:, 7]),
        pl.Series("fixed_by_30", 1 - _S[:, 30]),
        pl.Series("fixed_by_90", 1 - _S[:, 90]),
        pl.Series("still_open_at_horizon", _S[:, -1]),
    )

    # Topic-wide curves, each area weighted by how many requests it contributed.
    _domains = sorted(_cells["domain"].unique().to_list())
    _SD = np.array([
        np.average(_S[(_cells["domain"] == _d).to_numpy()], axis=0,
                   weights=np.maximum(_counts[(_cells["domain"] == _d).to_numpy()], 1e-9))
        for _d in _domains
    ])
    fix_topics = pl.DataFrame({"domain": _domains}).with_columns(
        pl.Series("median_days", median_days(_SD), dtype=pl.Int64),
        pl.Series("fixed_by_7", 1 - _SD[:, 7]),
        pl.Series("fixed_by_30", 1 - _SD[:, 30]),
        pl.Series("still_open_at_horizon", _SD[:, -1]),
        pl.Series("n", [float(_counts[(_cells["domain"] == _d).to_numpy()].sum()) for _d in _domains]).cast(pl.Int64),
    ).sort("still_open_at_horizon", descending=True)

    # Naive comparison: the median of only those requests that did close, which is what an average
    # over finished repairs would report.
    _naive = (
        requests_311.filter(~pl.col("proactive") & pl.col("closed").is_not_null())
        .filter(~pl.col("sr_type").is_in(["TRM-Pickup Pothole"]))
        .with_columns(((pl.col("closed") - pl.col("created")).dt.total_seconds() / 86400).clip(0.0, None).alias("d"))
        .group_by("domain").agg(pl.col("d").median().alias("naive_median_days"))
    )
    fix_topics = fix_topics.join(_naive, on="domain", how="left")

    # Every request still open at the snapshot, ranked by how likely it is to still be open three
    # weeks from now. This is the part of the model a city could actually use: sorting a work list
    # this way beats sorting it by age, because plenty of old requests are about to close anyway.
    _idx_r = np.arange(_per_request.shape[0])
    _clock = np.minimum(_r["exit"].to_numpy().astype(int), FIX_HORIZON)   # where to read the curve
    _later = np.minimum(_clock + TRIAGE_AHEAD, FIX_HORIZON)
    _now = _per_request[_idx_r, _clock]
    _open = (
        _r.with_columns(
            # The real age, not the clipped one. `exit` tops out at the horizon, and printing 180 for
            # a request that has been waiting 260 days would put a modelling detail on screen.
            ((datetime.fromisoformat(snapshot_meta["snapshot_ts"]) - pl.col("created"))
             .dt.total_seconds() / 86400).round(0).cast(pl.Int64).alias("waiting"),
            pl.Series("risk", np.divide(_per_request[_idx_r, _later], np.maximum(_now, 1e-9))),
        )
        .filter(~pl.col("event"))
    )
    fix_stranded = _open.filter(pl.col("waiting") > 120).height
    fix_queue = (
        _open.filter(pl.col("waiting").is_between(TRIAGE_FROM, TRIAGE_TO))
        .select("csa", "domain", "address", "waiting", "risk", "sla_days")
        .sort("risk", descending=True)
    )

    # The typical request of each kind in each area, so the sequence can show what the model was
    # handed before it answers.
    fix_inputs = _r.group_by("domain", "csa").agg(
        pl.col("agency").mode().first().alias("agency"),
        pl.col("method").mode().first().alias("method"),
        pl.col("sla_days").median().alias("sla_days"),
        pl.col("reports_per_1k").first().alias("reports_per_1k"),
        pl.col("vacancy").first().alias("vacancy"),
        pl.len().alias("n"),
    )
    return fix_clock, fix_inputs, fix_model, fix_queue, fix_stranded, fix_summary, fix_topics


@app.cell
def _(FIX_HOLDOUT_FROM, areas, calibration_check, requests_311, snapshot_meta):
    # Rebuilt on the early part of the year and scored on the rest, so the clock is judged on
    # requests it never saw.
    fix_calibration, fix_triage = calibration_check(
        requests_311, areas, snapshot_ts=snapshot_meta["snapshot_ts"], cutoff=FIX_HOLDOUT_FROM
    )
    return fix_calibration, fix_triage


@app.cell
def _(
    areas,
    fix_clock,
    fix_days,
    housing,
    mo,
    per,
    rank_stability,
    requests_311,
    score_areas,
    snapshot_meta,
    summarize,
    weight_sliders,
    window,
):
    mo.stop(
        sum(weight_sliders.value.values()) == 0,
        mo.callout(mo.md("All topic weights are 0. Turn at least one slider up."), kind="warn"),
    )
    # Re-slice the trained clock at the slider horizon. Need follows the window / per controls.
    domain_scores = score_areas(
        requests_311, housing, areas,
        snapshot_ts=snapshot_meta["snapshot_ts"],
        window_days=window.value, fix_days=fix_days.value, per=per.value,
        service="duration", fix_clock=fix_clock,
    )
    overall = summarize(domain_scores, weight_sliders.value)
    robust = rank_stability(domain_scores)
    return domain_scores, overall, robust


@app.cell
def _():
    # The one pair out of 36 we tested that behaves like a local mechanism: rubbish left out breeds
    # rats beside it. The full matrix, and why the other 35 do not survive, is in pair_review.md.
    ALLEY, RATS = "Dirty streets & alleys", "Rats"
    ALLEY_WINDOW = 28  # days watched before the alley was reported, and after
    ALLEY_FAST = 7  # closed this fast = the comparison arm
    ALLEY_RINGS = [0, 50, 150, 400]  # metres; 150 is the headline radius
    ALLEY_MIN_ARM = 100  # below this there is no comparison worth drawing
    # Outcomes a dirty alley cannot cause. They measure how much of any "local" effect is really
    # just reports of everything piling into the same few blocks.
    ALLEY_PLACEBOS = ["Potholes", "Roads", "Streetlights", "Trees"]
    return (
        ALLEY,
        ALLEY_FAST,
        ALLEY_MIN_ARM,
        ALLEY_PLACEBOS,
        ALLEY_RINGS,
        ALLEY_WINDOW,
        RATS,
    )


@app.cell
def _(
    ALLEY,
    ALLEY_FAST,
    ALLEY_PLACEBOS,
    ALLEY_RINGS,
    ALLEY_WINDOW,
    RATS,
    datetime,
    np,
    pl,
    requests_311,
    shapely,
    snapshot_meta,
    timedelta,
):
    def alley_effect(requests, *, snapshot_ts):
        """What grows next to a dirty alley the city has not come back to.

        Two arms: alleys still open `ALLEY_WINDOW` days after they were reported, against alleys
        closed inside `ALLEY_FAST` days. Around each one we count reports of another topic within
        a radius, in the window before it was filed and the window after.

        The arms are not alike to begin with. Rat reports near the alleys the city leaves open were
        already 2.3x rarer, and already climbing before the alley was reported at all. A plain
        before-and-after difference reads that head start as an effect, which is how this analysis
        goes wrong. So the comparison keeps only alleys with **no** reports of the outcome nearby
        in the preceding window. Both arms then start at exactly zero and the next month is a fair
        comparison, at the cost of two thirds of the estimate: +0.16 becomes +0.07.
        """
        _end = datetime.fromisoformat(snapshot_ts)
        _usable = requests.filter(~pl.col("proactive") & pl.col("x").is_not_null())
        # An alley needs a full window on each side, so the first and last weeks are not eligible.
        _opens = _usable["created"].min() + timedelta(days=ALLEY_WINDOW)
        _cause = (
            _usable.filter(
                (pl.col("domain") == ALLEY)
                & (pl.col("created") >= _opens)
                & (pl.col("created") <= _end - timedelta(days=ALLEY_WINDOW))
            )
            .with_columns(
                ((pl.coalesce("closed", pl.lit(_end)) - pl.col("created")).dt.total_seconds() / 86400)
                .alias("open_days")
            )
            .with_columns(
                pl.when(pl.col("open_days") <= ALLEY_FAST).then(pl.lit("Fixed within a week"))
                .when(pl.col("open_days") >= ALLEY_WINDOW).then(pl.lit("Left open a month"))
                .otherwise(pl.lit(None, dtype=pl.String))
                .alias("arm")
            )
            .filter(pl.col("arm").is_not_null())
        )

        # Metres per degree at Baltimore's latitude. Accurate to centimetres across one city, and
        # it needs no projection library, so this still works offline.
        _lon_m, _lat_m = 111_320.0 * np.cos(np.radians(39.30)), 111_132.0

        def _metres(frame):
            return np.column_stack(
                [frame["x"].to_numpy() * _lon_m, frame["y"].to_numpy() * _lat_m]
            )

        _cause_pts = shapely.points(_metres(_cause))
        _filed = _cause["created"].to_numpy().astype("datetime64[s]").astype("int64")

        def _nearby(outcome, radius):
            """Days between each nearby report of `outcome` and the alley report it sits beside."""
            _sub = _usable.filter(pl.col("domain") == outcome)
            _ci, _oi = shapely.STRtree(shapely.points(_metres(_sub))).query(
                _cause_pts, predicate="dwithin", distance=radius
            )
            _when = _sub["created"].to_numpy().astype("datetime64[s]").astype("int64")
            return _ci, (_when[_oi] - _filed[_ci]) / 86400.0

        def _windows(outcome, radius):
            """Reports before and after each alley report, within `radius`."""
            _ci, _off = _nearby(outcome, radius)
            _before = np.bincount(_ci[(_off >= -ALLEY_WINDOW) & (_off < 0)], minlength=_cause.height)
            _after = np.bincount(_ci[(_off > 0) & (_off < ALLEY_WINDOW)], minlength=_cause.height)
            return _before, _after

        _arm = _cause["arm"].to_numpy()
        _is_left, _is_fast = _arm == "Left open a month", _arm == "Fixed within a week"
        _radius = ALLEY_RINGS[2]
        _before, _after = _windows(RATS, _radius)
        _clean = _before == 0  # nothing nearby to begin with, so the arms start level
        _left, _fast = _is_left & _clean, _is_fast & _clean

        # How the gap opens day by day, which is the thing a single number cannot show.
        _ci, _off = _nearby(RATS, _radius)
        _sel = (_off > 0) & (_off < ALLEY_WINDOW)
        _day, _idx = np.ceil(_off[_sel]).astype(int), _ci[_sel]
        _growth = [{"day": 0, "arm": _a, "reports": 0.0} for _a in ("Left open a month", "Fixed within a week")]
        for _d in range(1, ALLEY_WINDOW + 1):
            _so_far = np.bincount(_idx[_day <= _d], minlength=_cause.height)
            _growth += [
                {"day": _d, "arm": "Left open a month", "reports": float(_so_far[_left].mean())},
                {"day": _d, "arm": "Fixed within a week", "reports": float(_so_far[_fast].mean())},
            ]

        # Where the extra reports sit. A mechanism is local, so its inner ring should be much
        # denser than its outer one; a whole block drifting upward looks flat.
        _ring_ha = [
            np.pi * (ALLEY_RINGS[_i + 1] ** 2 - ALLEY_RINGS[_i] ** 2) / 10_000
            for _i in range(len(ALLEY_RINGS) - 1)
        ]
        _rings, _decay = [], {}
        for _outcome in [RATS, *ALLEY_PLACEBOS]:
            _cumulative = []
            for _r in ALLEY_RINGS[1:]:
                _, _out_after = _windows(_outcome, _r)
                _cumulative.append(float(_out_after[_left].mean() - _out_after[_fast].mean()))
            _by_ring = [_cumulative[0]] + [
                _cumulative[_i] - _cumulative[_i - 1] for _i in range(1, len(_cumulative))
            ]
            _density = [_v / _ha for _v, _ha in zip(_by_ring, _ring_ha)]
            _rings += [
                {
                    "outcome": _outcome,
                    "ring": f"{ALLEY_RINGS[_i]}–{ALLEY_RINGS[_i + 1]} m",
                    "order": _i,
                    "density": _v,
                }
                for _i, _v in enumerate(_density)
            ]
            _decay[_outcome] = abs(_density[0]) / abs(_density[-1]) if _density[-1] else float("inf")

        _a, _b = _after[_left], _after[_fast]
        _diff = float(_a.mean() - _b.mean())
        _se = float(np.sqrt(_a.var(ddof=1) / len(_a) + _b.var(ddof=1) / len(_b)))
        return {
            "growth": pl.DataFrame(_growth),
            "rings": pl.DataFrame(_rings),
            "decay": _decay,
            "stats": {
                "n_left": int(_left.sum()),
                "n_fast": int(_fast.sum()),
                "clean_share": float(_clean.mean()),
                "left_rate": float(_a.mean()),
                "fast_rate": float(_b.mean()),
                "left_any": float((_a > 0).mean()),
                "fast_any": float((_b > 0).mean()),
                "diff": _diff,
                "se": _se,
                "sigma": _diff / _se if _se else 0.0,
                "lift": _diff / _b.mean() if _b.mean() else 0.0,
                # The imbalance that forced the clean-start restriction, kept so the method note
                # can quote it rather than assert it.
                "baseline_left": float(_before[_is_left].mean()),
                "baseline_fast": float(_before[_is_fast].mean()),
                "decay": _decay[RATS],
                "placebo_decay": float(np.median([_decay[_o] for _o in ALLEY_PLACEBOS])),
                "radius": _radius,
                "window": ALLEY_WINDOW,
            },
        }

    alley = alley_effect(requests_311, snapshot_ts=snapshot_meta["snapshot_ts"])
    return (alley,)


@app.cell
def _(ALLEY_PLACEBOS, mo):
    alley_compare = mo.ui.dropdown(
        options=ALLEY_PLACEBOS, value="Potholes", label="**Compare rats against**"
    )
    return (alley_compare,)


@app.cell
def _(OVER, RATS, UNDER, alley, alley_compare, alt, pl):
    _arms = ["Fixed within a week", "Left open a month"]
    _s = alley["stats"]
    alley_growth_chart = (
        alt.Chart(alley["growth"])
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X(
                "day:Q",
                title="Days after the alley was reported →",
                scale=alt.Scale(domain=[0, _s["window"]], nice=False),
            ),
            y=alt.Y("reports:Q", title="Rat reports per alley"),
            color=alt.Color(
                "arm:N",
                scale=alt.Scale(domain=_arms, range=[OVER, UNDER]),
                sort=_arms,
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("arm:N", title="Alley"),
                alt.Tooltip("day:Q", title="Days after"),
                alt.Tooltip("reports:Q", title="Rat reports per alley", format=".3f"),
            ],
        )
        .properties(
            width=300,
            height=260,
            # Titles are kept short and the numbers pushed into the subtitle, because Altair widens
            # a chart to fit its title and two long ones overflow the column at laptop width.
            title=alt.TitleParams(
                "Both start clean, then the gap opens",
                subtitle=[
                    f"Running total within {_s['radius']} m, from the day the alley",
                    "was reported. Neither arm had a rat report before it.",
                ],
                anchor="start",
                subtitleColor="#777",
            ),
        )
    )

    _picked = alley_compare.value
    _rats_decay, _other_decay = alley["decay"][RATS], alley["decay"][_picked]
    _title = alt.TitleParams(
        "Only rats fade with distance"
        if _rats_decay > _other_decay
        else f"Rats fade with distance, and so does {_picked.lower()}",
        subtitle=[
            f"Rats drop {_rats_decay:.1f}× from the inner ring to the outer;",
            f"{_picked.lower()}, which an alley cannot cause, {_other_decay:.1f}×.",
        ],
        anchor="start",
        subtitleColor="#777",
    )
    _shown = alley["rings"].filter(pl.col("outcome").is_in([RATS, _picked]))
    _zero = alt.Chart(alt.Data(values=[{"z": 0}])).mark_rule(strokeDash=[4, 4], color="#888").encode(y="z:Q")
    _lines = (
        alt.Chart(_shown)
        .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=70, filled=True))
        .encode(
            x=alt.X(
                "ring:N",
                sort=alt.EncodingSortField("order"),
                title="Distance from the alley →",
                axis=alt.Axis(labelAngle=0),  # three short labels fit flat; Vega rotates by default
            ),
            y=alt.Y("density:Q", title="Extra reports per hectare", axis=alt.Axis(format=".2f")),
            color=alt.Color(
                "outcome:N",
                scale=alt.Scale(domain=[RATS, _picked], range=[UNDER, "#9aa0a6"]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("outcome:N", title="Outcome"),
                alt.Tooltip("ring:N", title="Ring"),
                alt.Tooltip("density:Q", title="Extra reports per hectare", format="+.4f"),
            ],
        )
    )
    alley_ring_chart = (_zero + _lines).properties(width=300, height=260, title=_title)
    return alley_growth_chart, alley_ring_chart


@app.cell
def _(MID, OVER, UNDER, alt, overall, pl, selected_area):
    _dots = (
        alt.Chart(overall)
        .mark_circle(size=110, stroke="#333", strokeWidth=0.4)
        .encode(
            x=alt.X("need:Q", title="Need (percentile) →", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            y=alt.Y("service:Q", title="Service (percentile) →", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            color=alt.Color(
                "gap:Q",
                scale=alt.Scale(range=[OVER, MID, UNDER], domainMid=0, domain=[-0.6, 0.6], clamp=True),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("csa:N", title="Area"),
                alt.Tooltip("rank:Q", title="Gap rank"),
                alt.Tooltip("need:Q", format=".0%"),
                alt.Tooltip("service:Q", format=".0%"),
                alt.Tooltip("gap:Q", format="+.2f"),
            ],
        )
    )
    _picked = overall.filter(pl.col("csa") == selected_area)
    # Pink marks the picked area: outside the blue/orange gap scale, and readable in light and dark themes.
    _ring = alt.Chart(_picked).mark_circle(size=420, fill=None, stroke="#d53f8c", strokeWidth=3).encode(x="need:Q", y="service:Q")
    _name = alt.Chart(_picked).mark_text(dy=-20, fontWeight="bold", fontSize=12, color="#d53f8c").encode(
        x="need:Q", y="service:Q", text="csa:N"
    )
    _mid = alt.Chart(alt.Data(values=[{"m": 0.5}]))
    _rules = _mid.mark_rule(strokeDash=[4, 4], color="#888").encode(x="m:Q") + _mid.mark_rule(
        strokeDash=[4, 4], color="#888"
    ).encode(y="m:Q")

    def _corner(x, y, text, align):
        return (
            alt.Chart(alt.Data(values=[{"x": x, "y": y, "t": text}]))
            .mark_text(fontSize=11, fontWeight="bold", color="#777", align=align)
            .encode(x="x:Q", y="y:Q", text="t:N")
        )

    _labels = (
        _corner(0.98, 0.03, "PRIORITY: high need, low service", "right")
        + _corner(0.98, 0.97, "Being worked", "right")
        + _corner(0.02, 0.97, "Over-served", "left")
        + _corner(0.02, 0.03, "Fine", "left")
    )
    quadrant = (_rules + _labels + _dots + _ring + _name).properties(
        width=420, height=400, title="Orange dots, bottom right: high need, low service"
    )
    return (quadrant,)


@app.cell
def _(areas_geo, np, shapely):
    # Flat projection for our own SVG map: fine at city scale, and needs no JS map library (works offline).
    _b = np.array([shapely.geometry.shape(f["geometry"]).bounds for f in areas_geo["features"]])
    _lon0, _lat0, _lon1, _lat1 = _b[:, 0].min(), _b[:, 1].min(), _b[:, 2].max(), _b[:, 3].max()
    _kx = np.cos(np.radians((_lat0 + _lat1) / 2))
    _scale = 1000 / (_lat1 - _lat0)
    MAP_SIZE = [round(float((_lon1 - _lon0) * _kx * _scale), 1), 1000.0]

    def project(lon, lat):
        """Longitude/latitude to map units (1 unit is about 20 m)."""
        return (np.asarray(lon) - _lon0) * _kx * _scale, (_lat1 - np.asarray(lat)) * _scale

    def svg_path(geom):
        """SVG path data for a (multi)polygon, holes included."""
        _parts = []
        for _poly in getattr(geom, "geoms", [geom]):
            for _ring in [_poly.exterior, *_poly.interiors]:
                _x, _y = project(*np.asarray(_ring.coords)[:, :2].T)
                _parts.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in zip(_x, _y)) + "Z")
        return "".join(_parts)

    map_shapes = []
    for _f in areas_geo["features"]:
        _g = shapely.geometry.shape(_f["geometry"])
        _x, _y = project([_g.bounds[0], _g.bounds[2]], [_g.bounds[3], _g.bounds[1]])
        map_shapes.append(
            {
                "csa": _f["properties"]["csa"],
                "d": svg_path(_g),
                "box": [round(float(_x[0]), 1), round(float(_y[0]), 1), round(float(_x[1] - _x[0]), 1), round(float(_y[1] - _y[0]), 1)],
            }
        )
    return MAP_SIZE, map_shapes, project


@app.cell
def _(areas_geo, np, project, shapely):
    # Anchor points for the call cards. A bounding-box centre drifts into the harbour for the
    # waterfront areas; representative_point is guaranteed to land inside the shape itself.
    map_centroids = {}
    for _f in areas_geo["features"]:
        _p = shapely.geometry.shape(_f["geometry"]).representative_point()
        _x, _y = project(_p.x, _p.y)
        map_centroids[_f["properties"]["csa"]] = [round(float(_x), 1), round(float(_y), 1)]

    def bloom_order(origin, centroids):
        """Areas sorted by distance from the origin, with each one's share of the ripple's width."""
        _o = centroids[origin]
        _d = {_c: float(np.hypot(_p[0] - _o[0], _p[1] - _o[1])) for _c, _p in centroids.items()}
        _far = max(_d.values()) or 1.0
        return {_c: round(_v / _far, 4) for _c, _v in _d.items()}

    return bloom_order, map_centroids


@app.cell
def _(anywidget, traitlets):
    class TriageExplorer(anywidget.AnyWidget):
        """Clickable gap map + Gap Card in one widget.

        Click an area to select it and zoom to its streets (dots = real requests and vacant buildings).
        Click a Gap Card row to recolor the map by that topic. Python reads `selected` and `focus`,
        and pushes new scores (`data`) and dots (`points`) without re-creating the widget.
        """

        _esm = r"""
        const OVER = [43, 108, 176], MID = [241, 241, 241], UNDER = [221, 107, 32];
        const DOT = { open: "#dd6b20", slow: "#f6ad55", fast: "#a0aec0", vacant: "#2d3748", handled: "#2b6cb0" };
        const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
        const gapColor = (g) => {
          if (g === null || g === undefined) return "url(#tx-na)";
          const t = Math.max(-1, Math.min(1, g / 0.6));
          return `rgb(${t < 0 ? mix(MID, OVER, -t) : mix(MID, UNDER, t)})`;
        };
        const signed = (g) => (g > 0 ? "+" : "") + Math.round(g * 100);
        const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
        const NS = "http://www.w3.org/2000/svg";

        function render({ model, el }) {
          const [W, H] = model.get("size");
          const full = [0, 0, W, H];
          let view = full.slice(), zoomed = false, anim = null;

          el.innerHTML = `
            <div class="tx">
              <div class="tx-map">
                <div class="tx-bar">
                  <button class="tx-back" hidden>← Back to city</button>
                  <b class="tx-title"></b>
                  <input class="tx-search" list="tx-names" placeholder="Find an area…">
                  <datalist id="tx-names"></datalist>
                </div>
                <svg class="tx-svg" viewBox="${full.join(" ")}">
                  <defs><pattern id="tx-na" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                    <rect width="8" height="8" fill="#e2e2e2"/><line x1="0" y1="0" x2="0" y2="8" stroke="#c4c4c4" stroke-width="3"/></pattern></defs>
                  <g class="tx-areas"></g><g class="tx-dots"></g>
                </svg>
                <div class="tx-legend"></div>
                <div class="tx-tip" hidden></div>
              </div>
              <div class="tx-card"></div>
            </div>`;
          const $ = (s) => el.querySelector(s);
          const svg = $(".tx-svg"), gAreas = $(".tx-areas"), gDots = $(".tx-dots"), tip = $(".tx-tip");

          // --- Areas: built once
          const paths = {};
          for (const s of model.get("shapes")) {
            const p = document.createElementNS(NS, "path");
            p.setAttribute("d", s.d);
            p.dataset.csa = s.csa;
            gAreas.appendChild(p);
            paths[s.csa] = { el: p, box: s.box };
            $("#tx-names").insertAdjacentHTML("beforeend", `<option value="${esc(s.csa)}">`);
          }
          const boxOf = (csa) => paths[csa] && paths[csa].box;

          const select = (csa, zoom) => {
            if (!paths[csa]) return;
            if (model.get("selected") !== csa) {
              model.set("selected", csa);
              model.save_changes();
            }
            if (zoom) zoomTo(csa);
          };

          // --- Zoom: animate the viewBox to the area's box (kept at the map's shape)
          const zoomTo = (csa) => {
            let target = full;
            zoomed = !!csa;
            if (csa) {
              const [x, y, w, h] = boxOf(csa);
              let tw = w * 1.3, th = h * 1.3;
              if (tw / th > W / H) th = (tw * H) / W; else tw = (th * W) / H;
              target = [x + w / 2 - tw / 2, y + h / 2 - th / 2, tw, th];
            }
            gDots.style.display = "none";
            const from = view.slice(), t0 = performance.now();
            cancelAnimationFrame(anim);
            const step = (now) => {
              const t = Math.min(1, (now - t0) / 550), e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
              view = from.map((v, i) => v + (target[i] - v) * e);
              svg.setAttribute("viewBox", view.join(" "));
              if (t < 1) anim = requestAnimationFrame(step);
              else { drawDots(); paint(); }
            };
            anim = requestAnimationFrame(step);
            paint();
          };

          // --- Colors, outline, titles, legend
          const paint = () => {
            const data = model.get("data"), focus = model.get("focus"), sel = model.get("selected");
            if (!data.overall) return;
            const values = focus ? data.topics[focus] || {} : Object.fromEntries(Object.entries(data.overall).map(([k, v]) => [k, v.gap]));
            for (const [csa, p] of Object.entries(paths)) {
              // Zoomed: plain background for the picked area so the dots stand out (its gap is in the card).
              p.el.setAttribute("fill", zoomed && csa === sel ? "#f5f2ec" : gapColor(values[csa]));
              p.el.classList.toggle("tx-sel", csa === sel);
              p.el.classList.toggle("tx-dim", zoomed && csa !== sel);
            }
            if (paths[sel]) gAreas.appendChild(paths[sel].el); // draw the outline on top
            $(".tx-back").hidden = !zoomed;
            const pts = model.get("points");
            $(".tx-title").textContent = zoomed
              ? `${sel}${pts.area === sel && pts.note ? ": " + pts.note : ""}`
              : focus ? `${focus} only: orange areas get less than their need predicts` : "Neglect: orange = served less than this much need predicts";
            $(".tx-legend").innerHTML = zoomed
              ? (focus === "Vacant buildings" ? "" :
                  `<span><i style="background:${DOT.open}"></i>still open (bigger = older)</span>` +
                  (focus ? `<span><i style="background:${DOT.slow}"></i>closed late</span><span><i style="background:${DOT.fast}"></i>closed within ${data.fix_days} days</span>` : "")) +
                (!focus || focus === "Vacant buildings"
                  ? `<span><i class="sq" style="background:${DOT.vacant}"></i>vacant, no rehab or demolition</span><span><i class="sq" style="background:${DOT.handled}"></i>vacant, handled</span>` : "")
              : `<span class="tx-grad-l">over-served</span><span class="tx-grad"></span><span>under-served</span><span class="tx-na-key"><i></i>not enough data</span>`;
          };

          // --- Dots for the zoomed area (sizes stay constant on screen)
          const drawDots = () => {
            const pts = model.get("points");
            gDots.innerHTML = "";
            if (!zoomed || pts.area !== model.get("selected")) return;
            const k = view[2] / (svg.clientWidth || 560);
            const frag = [];
            pts.items.forEach((p, i) => {
              const r = (p.r || 3) * k;
              frag.push(p.k === "vacant" || p.k === "handled"
                ? `<rect x="${p.x - r * 0.8}" y="${p.y - r * 0.8}" width="${r * 1.6}" height="${r * 1.6}" fill="${DOT[p.k]}" data-i="${i}"/>`
                : `<circle cx="${p.x}" cy="${p.y}" r="${r}" fill="${DOT[p.k]}" data-i="${i}"/>`);
            });
            gDots.innerHTML = frag.join("");
            gDots.style.display = "";
          };

          // --- Gap Card for the selected area
          const drawCard = () => {
            const data = model.get("data"), sel = model.get("selected"), focus = model.get("focus");
            const card = (data.cards || {})[sel];
            if (!card) {
              // Nothing picked (the city view). Say so, rather than leaving an empty column.
              $(".tx-card").innerHTML = sel ? "" :
                `<div class="gc-empty">Click an area on the map, or search for one, to see which
                 topics it is under-served on.</div>`;
              return;
            }
            const CW = 230, PAD = 10, x = (p) => PAD + p * (CW - 2 * PAD);
            let html = `<div class="gc-head"><b>${esc(sel)}</b><span>${esc(card.subtitle)}</span></div>
              <div class="gc-row gc-scale"><span></span><svg width="${CW}" height="14"><text x="${PAD}" y="11">0%</text>
              <text x="${CW / 2}" y="11" text-anchor="middle">50%</text><text x="${CW - PAD}" y="11" text-anchor="end">100%</text></svg><span>gap</span></div>`;
            for (const r of card.rows) {
              const color = r.gap === null ? "#999" : r.gap > 0 ? "#dd6b20" : "#2b6cb0";
              let s = `<line x1="${PAD}" x2="${CW - PAD}" y1="12" y2="12" class="gc-track"/>`;
              if (r.gap !== null) {
                s += `<line x1="${x(r.need)}" x2="${x(r.service)}" y1="12" y2="12" stroke="${color}" stroke-width="4"/>`;
                s += `<circle cx="${x(r.service)}" cy="12" r="6" fill="white" stroke="${color}" stroke-width="2.5"/>`;
              }
              s += `<circle cx="${x(r.need)}" cy="12" r="6" fill="${color}"/>`;
              html += `<div class="gc-row${focus === r.domain ? " gc-focus" : ""}${r.gap === null ? " gc-na" : ""}" data-domain="${esc(r.domain)}" title="${esc(r.detail)}">
                <span class="gc-name">${esc(r.domain)}</span><svg width="${CW}" height="24">${s}</svg>
                <span class="gc-gap" style="color:${color}">${r.gap === null ? "n/a" : signed(r.gap)}</span></div>`;
            }
            html += `<div class="gc-foot"><span class="gc-dot" style="background:#555"></span> need
              <span class="gc-dot gc-hollow"></span> service · <span style="color:#dd6b20">orange = under-served</span> ·
              <span style="color:#2b6cb0">blue = over-served</span><br>Click a row to color the map by that topic.
              Hover for raw numbers.</div>`;
            $(".tx-card").innerHTML = html;
          };

          // --- Events
          gAreas.addEventListener("click", (e) => e.target.dataset.csa && select(e.target.dataset.csa, true));
          // Back to the city view also clears the pick: the map shows no outline, so leaving
          // `selected` set would keep the Gap Card and the work list on an area nothing points at.
          $(".tx-back").addEventListener("click", () => {
            model.set("selected", "");
            model.save_changes();
            zoomTo(null);
          });
          $(".tx-search").addEventListener("change", (e) => {
            if (paths[e.target.value]) { select(e.target.value, true); e.target.value = ""; e.target.blur(); }
          });
          $(".tx-card").addEventListener("click", (e) => {
            const row = e.target.closest("[data-domain]");
            if (!row) return;
            model.set("focus", model.get("focus") === row.dataset.domain ? "" : row.dataset.domain);
            model.save_changes();
          });
          const showTip = (e, html) => {
            const box = $(".tx-map").getBoundingClientRect();
            tip.innerHTML = html;
            tip.hidden = false;
            tip.style.left = `${Math.min(e.clientX - box.left + 14, box.width - 240)}px`;
            tip.style.top = `${e.clientY - box.top + 14}px`;
          };
          svg.addEventListener("mousemove", (e) => {
            const data = model.get("data"), focus = model.get("focus");
            if (e.target.dataset.i !== undefined) {
              return showTip(e, esc(model.get("points").items[+e.target.dataset.i].t));
            }
            const csa = e.target.dataset.csa;
            if (!csa || !data.overall) return (tip.hidden = true);
            const o = data.overall[csa] || {}, g = focus ? (data.topics[focus] || {})[csa] : o.gap;
            showTip(e, `<b>${esc(csa)}</b><br>${focus ? esc(focus) + " gap" : "Gap"}: ${g === null || g === undefined ? "n/a" : signed(g)}` +
              (o.rank ? ` · overall rank ${o.rank} of ${data.n}` : "") + (zoomed ? "" : "<br><i>click to zoom in</i>"));
          });
          svg.addEventListener("mouseleave", () => (tip.hidden = true));

          model.on("change:data", () => { paint(); drawCard(); });
          model.on("change:focus", () => { paint(); drawCard(); });
          model.on("change:selected", () => { paint(); drawCard(); });
          model.on("change:points", () => { drawDots(); paint(); });
          paint();
          drawCard();
          return () => cancelAnimationFrame(anim);
        }
        export default { render };
        """
        _css = r"""
        .tx { display: flex; flex-wrap: wrap; gap: 20px; font: 13px/1.35 system-ui, sans-serif; align-items: flex-start; }
        .tx-map { flex: 1 1 480px; min-width: 300px; position: relative; }
        .tx-card { flex: 0 1 440px; min-width: 300px; }
        .tx-bar { display: flex; align-items: center; gap: 8px; min-height: 32px; margin-bottom: 4px; flex-wrap: wrap; }
        .tx-title { flex: 1 1 100%; order: 3; font-size: 14px; }
        .tx-search, .tx-back { font: inherit; padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(127,127,127,0.45); background: transparent; color: inherit; }
        .tx-search { width: 170px; margin-left: auto; }
        .tx-back { cursor: pointer; font-weight: 600; }
        .tx-back:hover { background: rgba(127,127,127,0.15); }
        .tx-svg { width: 100%; height: auto; display: block; max-height: 640px; }
        .tx-areas path { stroke: #fff; stroke-width: 0.8; vector-effect: non-scaling-stroke; cursor: pointer; transition: opacity 0.3s; }
        .tx-areas path:hover { stroke: #444; stroke-width: 1.5; }
        .tx-areas path.tx-sel { stroke: #111; stroke-width: 2.8; }
        .tx-areas path.tx-dim { opacity: 0.25; }
        .tx-dots circle, .tx-dots rect { stroke: #fff; stroke-width: 0.6; vector-effect: non-scaling-stroke; opacity: 0.9; }
        .tx-dots circle:hover, .tx-dots rect:hover { stroke: #000; stroke-width: 1.5; }
        .tx-legend { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 14px; font-size: 11px; color: #777; margin-top: 4px; }
        .tx-legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: -1px; }
        .tx-legend i.sq { border-radius: 2px; }
        .tx-grad { width: 160px; height: 10px; border-radius: 3px; background: linear-gradient(90deg, #2b6cb0, #f1f1f1, #dd6b20); }
        .tx-grad-l { margin-right: -8px; }
        .tx-na-key i { background: repeating-linear-gradient(45deg, #e2e2e2 0 3px, #c4c4c4 3px 5px); border-radius: 2px; }
        .tx-tip { position: absolute; pointer-events: none; background: rgba(20,20,20,0.92); color: #fff; padding: 6px 9px;
                  border-radius: 6px; font-size: 12px; max-width: 240px; z-index: 5; }
        .gc-head { display: flex; justify-content: space-between; align-items: baseline; margin: 6px 0; gap: 12px; }
        .gc-head b { font-size: 15px; }
        .gc-head span { color: #777; font-size: 12px; text-align: right; }
        .gc-row { display: grid; grid-template-columns: 150px 230px 40px; align-items: center; cursor: pointer; border-radius: 4px; }
        .gc-row:hover { background: rgba(127,127,127,0.12); }
        .gc-focus { background: rgba(221,107,32,0.15); outline: 1px solid #dd6b20; }
        .gc-na .gc-name { color: #999; }
        .gc-scale { cursor: default; color: #999; font-size: 10px; }
        .gc-scale:hover { background: none; }
        .gc-scale text { fill: #999; font-size: 10px; }
        .gc-track { stroke: rgba(127,127,127,0.3); stroke-width: 1; }
        .gc-gap { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
        .gc-foot { margin-top: 8px; color: #777; font-size: 11px; }
        .gc-empty { color: #777; font-size: 12px; padding: 14px 10px; max-width: 230px; }
        .gc-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; vertical-align: middle; }
        .gc-hollow { border: 2px solid #555; width: 5px; height: 5px; }
        """
        shapes = traitlets.List([]).tag(sync=True)
        size = traitlets.List([1000, 1000]).tag(sync=True)
        data = traitlets.Dict({}).tag(sync=True)
        points = traitlets.Dict({"area": "", "note": "", "items": []}).tag(sync=True)
        selected = traitlets.Unicode("").tag(sync=True)
        focus = traitlets.Unicode("").tag(sync=True)
    return (TriageExplorer,)


@app.cell
def _(anywidget, traitlets):
    class FixClock(anywidget.AnyWidget):
        """A countdown map: every area shaded by the share of its requests still open on day t.

        Deliberately a second widget rather than an extension of TriageExplorer, whose click-and-zoom
        contract round-trips through marimo's graph. Nothing here writes back to Python: the playhead
        lives in JavaScript, so a playing animation cannot trigger a re-execution on every frame.
        """

        _esm = r"""
        const RAMP = [[26, 132, 78], [226, 168, 62], [196, 52, 42]];
        const mixc = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
        const BAR = 0.25;                      // green means three in four reports closed
        const shade = (s) => {
          const t = Math.max(0, Math.min(1, s));
          if (t <= BAR) return `rgb(${mixc(RAMP[0], RAMP[1], t / BAR).join(",")})`;
          return `rgb(${mixc(RAMP[1], RAMP[2], (t - BAR) / (1 - BAR)).join(",")})`;
        };

        function render({ model, el }) {
          const [W, H] = model.get("size");
          el.innerHTML = `
            <div class="fc-wrap">
              <div class="fc-head">
                <div>
                  <div class="fc-day">Day <b class="fc-t">0</b></div>
                  <div class="fc-topic"></div>
                </div>
                <div class="fc-readout"></div>
              </div>
              <svg class="fc-map" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
                <g class="fc-areas"></g>
              </svg>
              <div class="fc-ctrl">
                <button class="fc-play" title="Play or pause">&#9654;</button>
                <input class="fc-scrub" type="range" min="0" value="0" step="1">
                <select class="fc-speed">
                  <option value="60">1 day / sec</option>
                  <option value="12" selected>5 days / sec</option>
                  <option value="4">15 days / sec</option>
                </select>
              </div>
              <div class="fc-legend">
                <span>3 in 4 closed</span><span class="fc-grad"></span><span>none closed</span>
                <span class="fc-hint">hover an area</span>
              </div>
            </div>`;

          const svg = el.querySelector(".fc-map"), gAreas = el.querySelector(".fc-areas");
          const elT = el.querySelector(".fc-t"), elTopic = el.querySelector(".fc-topic");
          const elRead = el.querySelector(".fc-readout"), elHint = el.querySelector(".fc-hint");
          const btn = el.querySelector(".fc-play"), scrub = el.querySelector(".fc-scrub");
          const speed = el.querySelector(".fc-speed");

          let t = 0, playing = false, anim = null, last = 0, hovered = null;
          const paths = {};
          for (const sh of model.get("shapes")) {
            const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
            p.setAttribute("d", sh.d);
            p.setAttribute("class", "fc-area");
            p.addEventListener("mouseenter", () => { hovered = sh.csa; paint(); });
            p.addEventListener("mouseleave", () => { hovered = null; paint(); });
            gAreas.appendChild(p);
            paths[sh.csa] = p;
          }

          const horizon = () => model.get("horizon");
          const curveOf = (csa) => (model.get("curves") || {})[csa];
          // Stored as 0-100 integers to keep the payload small; back to a share here.
          const sAt = (csa, day) => {
            const c = curveOf(csa);
            return c ? c[Math.min(day, c.length - 1)] / 100 : null;
          };

          const paint = () => {
            elT.textContent = t;
            scrub.value = t;
            let num = 0, den = 0;
            for (const [csa, p] of Object.entries(paths)) {
              const s = sAt(csa, t);
              if (s === null) { p.setAttribute("fill", "rgba(150,150,150,0.12)"); continue; }
              p.setAttribute("fill", shade(s));
              const n = (model.get("labels")[csa] || {}).n || 0;
              num += s * n; den += n;
            }
            for (const [csa, p] of Object.entries(paths)) p.classList.toggle("fc-hov", csa === hovered);
            elRead.innerHTML = den
              ? `<b>${Math.round(100 * num / den)}%</b> still open citywide`
              : "";
            if (hovered) {
              const lab = model.get("labels")[hovered] || {};
              const s = sAt(hovered, t);
              const med = lab.median === null || lab.median === undefined ? "never reaches half" : `half gone by day ${lab.median}`;
              elHint.innerHTML = `<b>${hovered}</b> &mdash; ${s === null ? "not enough requests" : Math.round(100 * s) + "% still open"} &middot; ${med} &middot; n=${lab.n || 0}`;
            } else {
              elHint.textContent = "hover an area";
            }
          };

          const step = (now) => {
            if (!playing) return;
            const perDay = Number(speed.value);
            if (now - last >= perDay) {
              const adv = Math.max(1, Math.floor((now - last) / perDay));
              last = now;
              t = t + adv;
              if (t >= horizon()) { t = horizon(); setPlaying(false); paint(); return; }
              paint();
            }
            anim = requestAnimationFrame(step);
          };

          const setPlaying = (v) => {
            playing = v;
            btn.innerHTML = v ? "&#10073;&#10073;" : "&#9654;";
            cancelAnimationFrame(anim);
            if (v) { last = performance.now(); anim = requestAnimationFrame(step); }
          };

          btn.addEventListener("click", () => {
            if (!playing && t >= horizon()) t = 0;   // replay from the top
            setPlaying(!playing);
          });
          scrub.addEventListener("input", () => { setPlaying(false); t = Number(scrub.value); paint(); });
          speed.addEventListener("change", () => { last = performance.now(); });

          const reset = () => {
            scrub.max = horizon();
            elTopic.textContent = model.get("topic");
            t = 0; setPlaying(false); paint();
          };
          model.on("change:curves", reset);
          model.on("change:topic", reset);
          reset();
          return () => cancelAnimationFrame(anim);
        }
        export default { render };
        """

        _css = r"""
        .fc-wrap { font: 13px system-ui, -apple-system, sans-serif; }
        .fc-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 4px; }
        .fc-day { font-size: 15px; color: #666; }
        .fc-day b { font-family: "IBM Plex Mono", monospace; font-size: 26px; color: #dd6b20; font-variant-numeric: tabular-nums; }
        .fc-topic { color: #888; font-size: 12px; }
        .fc-readout { font-size: 13px; color: #666; }
        .fc-readout b { font-size: 18px; color: #dd6b20; font-variant-numeric: tabular-nums; }
        .fc-map { width: 100%; height: auto; display: block; }
        .fc-area { stroke: rgba(127,127,127,0.45); stroke-width: 0.6; }
        .fc-area.fc-hov { stroke: #2d3748; stroke-width: 2.5; }
        .fc-ctrl { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
        .fc-play { width: 32px; height: 28px; cursor: pointer; border: 1px solid rgba(127,127,127,0.4);
                   border-radius: 4px; background: transparent; color: inherit; font-size: 12px; }
        .fc-play:hover { border-color: #dd6b20; color: #dd6b20; }
        .fc-scrub { flex: 1; accent-color: #dd6b20; }
        .fc-speed { border: 1px solid rgba(127,127,127,0.4); border-radius: 4px; padding: 3px;
                    background: transparent; color: inherit; font-size: 12px; }
        .fc-legend { display: flex; align-items: center; gap: 6px; margin-top: 6px; color: #888; font-size: 11px; }
        .fc-grad { width: 90px; height: 9px; border-radius: 2px;
                   background: linear-gradient(90deg, rgb(45,158,96), rgb(226,168,62), rgb(200,56,44)); }
        .fc-hint { margin-left: auto; }
        """

        shapes = traitlets.List([]).tag(sync=True)
        size = traitlets.List([1000, 1000]).tag(sync=True)
        curves = traitlets.Dict({}).tag(sync=True)
        labels = traitlets.Dict({}).tag(sync=True)
        topic = traitlets.Unicode("").tag(sync=True)
        horizon = traitlets.Int(180).tag(sync=True)
    return (FixClock,)


@app.cell
def _(anywidget, traitlets):
    class NeglectSkyline(anywidget.AnyWidget):
        """Rotatable 3D columns: unresolved report burden over the Baltimore map."""

        _esm = r"""
        const OVER = [43, 108, 176], MID = [241, 241, 241], UNDER = [221, 107, 32];
        const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
        const color = (gap, alpha=1) => {
          if (gap === null || gap === undefined) return `rgba(140,140,140,${alpha})`;
          const t = Math.max(-1, Math.min(1, gap / 0.6));
          const c = t < 0 ? mix(MID, OVER, -t) : mix(MID, UNDER, t);
          return `rgba(${c.join(",")},${alpha})`;
        };
        const shade = (css, amount) => {
          const m = css.match(/rgba?\((\d+),(\d+),(\d+)/);
          if (!m) return css;
          return `rgb(${[1,2,3].map(i => Math.max(0, Math.min(255, +m[i] + amount))).join(",")})`;
        };
        const signed = (gap) => (gap > 0 ? "+" : "") + Math.round(gap * 100);
        const esc = (s) => String(s).replace(/[&<>"]/g, c => (
          { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]
        ));

        function render({ model, el }) {
          el.innerHTML = `
            <div class="ns-wrap">
              <div class="ns-head">
                <div><b class="ns-title"></b><span class="ns-sub">tower height = positive neglect gap</span></div>
                <div class="ns-city"></div>
              </div>
              <div class="ns-main">
                <div class="ns-stage">
                  <canvas></canvas><div class="ns-tip" hidden></div><div class="ns-picked" hidden></div>
                </div>
                <div class="ns-card"></div>
              </div>
              <div class="ns-controls">
                <label>Rotate<input class="ns-angle" type="range" min="-65" max="65" value="-24" step="1"></label>
                <button class="ns-reset" title="Reset rotation and zoom">Reset view</button>
              </div>
              <div class="ns-legend">
                <span>over-served</span><i class="ns-grad"></i><span>under-served</span>
                <span class="ns-key">drag to rotate · scroll to zoom · click to pin</span>
              </div>
            </div>`;

          const canvas = el.querySelector("canvas"), stage = el.querySelector(".ns-stage");
          const tip = el.querySelector(".ns-tip"), angle = el.querySelector(".ns-angle");
          const title = el.querySelector(".ns-title");
          const city = el.querySelector(".ns-city"), picked = el.querySelector(".ns-picked");
          const cardEl = el.querySelector(".ns-card");
          const resetView = el.querySelector(".ns-reset");
          let columns = [], ground = [];
          let hovered = null, selected = model.get("selected") || null, zoom = 1.08, projection = null;
          let dragging = false, dragX = 0, dragAngle = 0, moved = false;

          const datum = (csa) => ((model.get("data") || {}).areas || {})[csa];
          const drawCard = () => {
            const data = model.get("data") || {}, focus = model.get("focus") || "";
            const card = data.card;
            if (!selected) {
              cardEl.innerHTML = `<div class="ngc-empty"><b>Gap Card</b><span>Click a tower or map area to compare its need and service by topic.</span></div>`;
              return;
            }
            if (!card || card.csa !== selected) {
              cardEl.innerHTML = `<div class="ngc-empty"><b>${esc(selected)}</b><span>Loading its Gap Card…</span></div>`;
              return;
            }
            const CW = 230, PAD = 10, x = p => PAD + p * (CW - 2 * PAD);
            let html = `<div class="ngc-head"><b>${esc(card.csa)}</b><span>${esc(card.subtitle)}</span></div>
              <div class="ngc-row ngc-scale"><span></span><svg width="${CW}" height="14"><text x="${PAD}" y="11">0%</text>
              <text x="${CW / 2}" y="11" text-anchor="middle">50%</text><text x="${CW - PAD}" y="11" text-anchor="end">100%</text></svg><span>gap</span></div>`;
            for (const row of card.rows) {
              const rowColor = row.gap === null ? "#999" : row.gap > 0 ? "#dd6b20" : "#2b6cb0";
              let marks = `<line x1="${PAD}" x2="${CW - PAD}" y1="12" y2="12" class="ngc-track"/>`;
              if (row.gap !== null) {
                marks += `<line x1="${x(row.need)}" x2="${x(row.service)}" y1="12" y2="12" stroke="${rowColor}" stroke-width="4"/>`;
                marks += `<circle cx="${x(row.service)}" cy="12" r="6" fill="white" stroke="${rowColor}" stroke-width="2.5"/>`;
              }
              marks += `<circle cx="${x(row.need)}" cy="12" r="6" fill="${rowColor}"/>`;
              html += `<div class="ngc-row${focus === row.domain ? " ngc-focus" : ""}${row.gap === null ? " ngc-na" : ""}"
                data-domain="${esc(row.domain)}" title="${esc(row.detail)}"><span class="ngc-name">${esc(row.domain)}</span>
                <svg width="${CW}" height="24">${marks}</svg><span class="ngc-gap" style="color:${rowColor}">
                ${row.gap === null ? "n/a" : signed(row.gap)}</span></div>`;
            }
            html += `<div class="ngc-foot"><span class="ngc-dot" style="background:#555"></span> need
              <span class="ngc-dot ngc-hollow"></span> service · <span style="color:#dd6b20">orange = under-served</span> ·
              <span style="color:#2b6cb0">blue = over-served</span><br>Click a row to color the skyline by that topic.
              Click it again for all topics. Hover for raw numbers.</div>`;
            cardEl.innerHTML = html;
          };

          const resize = () => {
            const dpr = window.devicePixelRatio || 1;
            const w = Math.max(320, stage.clientWidth), h = Math.max(360, Math.min(600, w * 0.66));
            canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
            canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
            draw();
          };

          const drawPrism = (ctx, c, h, fill, picked) => {
            const w = picked ? 8 : 5.5, d = w * 0.55, x = c.x, y = c.y, top = y - h;
            ctx.beginPath();
            ctx.moveTo(x, top - d); ctx.lineTo(x + w, top); ctx.lineTo(x, top + d); ctx.lineTo(x - w, top);
            ctx.closePath(); ctx.fillStyle = shade(fill, 24); ctx.fill();
            ctx.beginPath();
            ctx.moveTo(x - w, top); ctx.lineTo(x, top + d); ctx.lineTo(x, y + d); ctx.lineTo(x - w, y);
            ctx.closePath(); ctx.fillStyle = shade(fill, -28); ctx.fill();
            ctx.beginPath();
            ctx.moveTo(x, top + d); ctx.lineTo(x + w, top); ctx.lineTo(x + w, y); ctx.lineTo(x, y + d);
            ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
            if (picked) {
              ctx.strokeStyle = "#111"; ctx.lineWidth = 2;
              ctx.strokeRect(x - w - 2, top - d - 2, 2 * w + 4, h + 2 * d + 4);
            }
            return { x, y, top: top - d, w: Math.max(7, w + 2) };
          };

          const draw = () => {
            const dpr = window.devicePixelRatio || 1, cw = canvas.width / dpr, ch = canvas.height / dpr;
            const ctx = canvas.getContext("2d");
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, cw, ch);
            const [W, H] = model.get("size"), theta = Number(angle.value) * Math.PI / 180;
            const tilt = 0.58, scale = Math.min(cw / (W * 1.30), ch / (H * 0.96)) * zoom;
            const baseY = ch * 0.75, cs = Math.cos(theta), sn = Math.sin(theta);
            projection = { cw, ch, W, H, theta, tilt, scale, baseY, cs, sn };
            const screen = ([x, y]) => {
              const dx = x - W / 2, dy = y - H / 2;
              return [cw / 2 + (dx * cs - dy * sn) * scale, baseY + (dx * sn + dy * cs) * scale * tilt];
            };

            // Ground plane: the same 55 CSA shapes as the 2D decision map.
            ctx.save();
            ctx.translate(cw / 2, baseY); ctx.scale(scale, scale * tilt); ctx.rotate(theta); ctx.translate(-W / 2, -H / 2);
            ground = [];
            for (const sh of model.get("shapes")) {
              const row = datum(sh.csa), p = new Path2D(sh.d);
              ctx.fillStyle = row ? color(row.gap, 0.42) : "rgba(140,140,140,0.20)";
              ctx.fill(p);
              ctx.strokeStyle = sh.csa === selected ? "#111" :
                sh.csa === hovered ? "#2d3748" : "rgba(60,70,80,0.62)";
              ctx.lineWidth = (sh.csa === selected ? 3.2 : sh.csa === hovered ? 2.4 : 1.15) / scale;
              ctx.stroke(p);
              ground.push({ csa: sh.csa, path: p, row });
            }
            ctx.restore();

            let raw = [];
            for (const [csa, point] of Object.entries(model.get("centroids"))) {
              const row = datum(csa);
              if (!row || row.gap === null || row.gap === undefined) continue;
              const value = Math.max(0, row.gap);
              const [x, y] = screen(point);
              raw.push({ csa, row, value, x, y });
            }
            const max = Math.max(...raw.map(d => d.value), 1e-9);
            raw.sort((a, b) => a.y - b.y);
            columns = [];
            for (const c of raw.filter(d => d.value > 0)) {
              const h = 6 + Math.sqrt(Math.max(0, c.value) / max) * Math.min(160, ch * 0.31);
              const hit = drawPrism(ctx, c, h, color(c.row.gap), c.csa === selected || c.csa === hovered);
              columns.push({ ...c, ...hit, h });
            }
            const underserved = raw.filter(d => d.row.gap > 0);
            const widest = underserved.length ? Math.max(...underserved.map(d => d.row.gap)) : 0;
            city.innerHTML = raw.length
              ? `<b>${underserved.length}</b> areas below expected service · widest gap +${widest.toFixed(2)}`
              : "No scored areas at these weights";
            if (selected && datum(selected)) {
              const row = datum(selected), sign = row.gap > 0 ? "+" : "";
              picked.innerHTML = `<b>${selected}</b><span>neglect gap ${row.gap == null ? "n/a" : sign + row.gap.toFixed(2)} · rank ${row.rank || "n/a"} · click empty map to clear</span>`;
              picked.hidden = false;
            } else {
              picked.hidden = true;
            }
            drawCard();
          };

          const showTip = (event, c) => {
            const box = stage.getBoundingClientRect(), sign = c.row.gap > 0 ? "+" : "";
            const verdict = c.row.gap > 0 ? "below expected service" : "at or above expected service";
            tip.innerHTML = `<b>${c.csa}</b><br>neglect gap ${c.row.gap == null ? "n/a" : sign + c.row.gap.toFixed(2)}` +
              `<br>${verdict} · rank ${c.row.rank || "n/a"}`;
            tip.hidden = false;
            tip.style.left = `${Math.min(event.clientX - box.left + 12, box.width - 245)}px`;
            tip.style.top = `${Math.max(6, event.clientY - box.top - 64)}px`;
          };
          const mapPoint = (x, y) => {
            if (!projection) return null;
            const { cw, W, H, tilt, scale, baseY, cs, sn } = projection;
            const rx = (x - cw / 2) / scale, ry = (y - baseY) / (scale * tilt);
            return [W / 2 + rx * cs + ry * sn, H / 2 - rx * sn + ry * cs];
          };
          const hitAt = (x, y) => {
            const column = [...columns].reverse().find(c => x >= c.x-c.w && x <= c.x+c.w && y >= c.top && y <= c.y+8);
            if (column) return column;
            const point = mapPoint(x, y);
            if (!point) return null;
            const ctx = canvas.getContext("2d");
            const area = [...ground].reverse().find(g => ctx.isPointInPath(g.path, point[0], point[1]));
            if (!area || !area.row) return null;
            return { ...area, value: Math.max(0, area.row.gap || 0) };
          };
          canvas.addEventListener("mousemove", (event) => {
            const box = canvas.getBoundingClientRect(), x = event.clientX - box.left, y = event.clientY - box.top;
            if (dragging) {
              const delta = event.clientX - dragX;
              if (Math.abs(delta) > 2) moved = true;
              angle.value = Math.max(-65, Math.min(65, dragAngle + delta * 0.24));
              tip.hidden = true; draw(); return;
            }
            const hit = hitAt(x, y);
            const next = hit ? hit.csa : null;
            if (next !== hovered) { hovered = next; draw(); }
            if (hit) showTip(event, hit); else tip.hidden = true;
          });
          canvas.addEventListener("mouseleave", () => { hovered = null; tip.hidden = true; draw(); });
          canvas.addEventListener("mousedown", (event) => {
            dragging = true; moved = false; dragX = event.clientX; dragAngle = Number(angle.value);
            canvas.classList.add("ns-dragging");
          });
          window.addEventListener("mouseup", (event) => {
            if (!dragging) return;
            dragging = false; canvas.classList.remove("ns-dragging");
            if (!moved) {
              const box = canvas.getBoundingClientRect();
              const hit = hitAt(event.clientX - box.left, event.clientY - box.top);
              selected = hit ? hit.csa : null;
              model.set("selected", selected || "");
              model.save_changes();
              draw();
            }
          });
          canvas.addEventListener("wheel", (event) => {
            event.preventDefault();
            zoom = Math.max(0.72, Math.min(1.75, zoom * (event.deltaY > 0 ? 0.92 : 1.08)));
            draw();
          }, { passive: false });
          canvas.addEventListener("dblclick", () => {
            zoom = 1.08; angle.value = -24; selected = null;
            model.set("selected", ""); model.save_changes(); draw();
          });

          angle.addEventListener("input", draw);
          cardEl.addEventListener("click", (event) => {
            const row = event.target.closest("[data-domain]");
            if (!row) return;
            model.set("focus", model.get("focus") === row.dataset.domain ? "" : row.dataset.domain);
            model.save_changes();
          });
          resetView.addEventListener("click", () => {
            zoom = 1.08; angle.value = -24; selected = null; hovered = null;
            model.set("selected", ""); model.save_changes(); draw();
          });

          const reset = () => {
            const focus = model.get("focus") || "";
            title.textContent = (focus || "Weighted") + " neglect gap";
            draw();
          };
          model.on("change:data", reset);
          model.on("change:focus", reset);
          model.on("change:selected", () => {
            selected = model.get("selected") || null;
            draw();
          });
          model.on("change:shapes", draw);
          new ResizeObserver(resize).observe(stage);
          requestAnimationFrame(resize);
          return () => {};
        }
        export default { render };
        """

        _css = r"""
        .ns-wrap { font: 13px system-ui, -apple-system, sans-serif; }
        .ns-head { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin-bottom: 4px; }
        .ns-title { font-size: 17px; }
        .ns-sub { display: block; color: #888; font-size: 11px; }
        .ns-city { color: #777; font-size: 11px; text-align: right; }
        .ns-city b { color: #dd6b20; font-size: 17px; }
        .ns-main { display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; }
        .ns-stage { flex: 1 1 560px; min-width: 300px; position: relative; border-radius: 12px; overflow: hidden;
                    border: 1px solid rgba(90,100,110,.18);
                    background: radial-gradient(ellipse at 50% 72%, rgba(43,108,176,.16), transparent 62%),
                                linear-gradient(180deg, rgba(127,127,127,.035), rgba(127,127,127,.14)); }
        .ns-card { flex: 0 1 440px; min-width: 300px; overflow-x: auto; }
        .ns-stage canvas { display: block; width: 100%; cursor: grab; }
        .ns-stage canvas.ns-dragging { cursor: grabbing; }
        .ns-tip { position: absolute; pointer-events: none; background: rgba(20,20,20,.93); color: white;
                  border-radius: 6px; padding: 7px 9px; max-width: 245px; font-size: 11px; z-index: 2; }
        .ns-picked { position: absolute; left: 10px; top: 10px; padding: 6px 8px; border-radius: 6px;
                     background: rgba(20,20,20,.86); color: white; pointer-events: none; font-size: 11px; }
        .ns-picked b, .ns-picked span { display: block; }
        .ns-picked span { color: #d9dee5; }
        .ngc-empty { display: grid; gap: 5px; min-height: 120px; place-content: center; text-align: center;
                     padding: 18px; border: 1px dashed rgba(127,127,127,.4); border-radius: 8px; color: #777; }
        .ngc-empty b { color: inherit; font-size: 15px; }
        .ngc-head { display: flex; justify-content: space-between; align-items: baseline; margin: 6px 0; gap: 12px; }
        .ngc-head b { font-size: 15px; }
        .ngc-head span { color: #777; font-size: 12px; text-align: right; }
        .ngc-row { display: grid; grid-template-columns: 150px 230px 40px; align-items: center;
                   cursor: pointer; border-radius: 4px; }
        .ngc-row:hover { background: rgba(127,127,127,.12); }
        .ngc-row.ngc-focus { background: rgba(221,107,32,.15); outline: 1px solid #dd6b20; }
        .ngc-na .ngc-name { color: #999; }
        .ngc-scale { cursor: default; color: #999; font-size: 10px; }
        .ngc-scale:hover { background: none; }
        .ngc-scale text { fill: #999; font-size: 10px; }
        .ngc-track { stroke: rgba(127,127,127,.3); stroke-width: 1; }
        .ngc-gap { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
        .ngc-foot { margin-top: 8px; color: #777; font-size: 11px; }
        .ngc-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; vertical-align: middle; }
        .ngc-hollow { border: 2px solid #555; width: 5px; height: 5px; }
        .ns-controls { display: flex; justify-content: flex-end;
                       align-items: center; gap: 12px; margin-top: 8px; }
        .ns-controls label { display: grid; grid-template-columns: auto 1fr; gap: 7px; align-items: center;
                             color: #777; font-size: 11px; min-width: 230px; }
        .ns-controls input { width: 100%; accent-color: #dd6b20; }
        .ns-reset { cursor: pointer; border: 1px solid rgba(127,127,127,.45); border-radius: 4px;
                    background: transparent; color: inherit; padding: 5px 9px; font-size: 11px; }
        .ns-legend { display: flex; align-items: center; gap: 6px; color: #888; font-size: 11px; margin-top: 7px; }
        .ns-grad { width: 130px; height: 9px; border-radius: 2px;
                   background: linear-gradient(90deg,#2b6cb0,#f1f1f1,#dd6b20); }
        .ns-key { margin-left: auto; }
        @media (max-width: 600px) {
          .ns-controls { justify-content: stretch; }
          .ns-controls label { flex: 1; min-width: 0; }
          .ns-city { display: none; }
        }
        """

        shapes = traitlets.List([]).tag(sync=True)
        size = traitlets.List([1000, 1000]).tag(sync=True)
        centroids = traitlets.Dict({}).tag(sync=True)
        data = traitlets.Dict({}).tag(sync=True)
        focus = traitlets.Unicode("").tag(sync=True)
        selected = traitlets.Unicode("").tag(sync=True)
    return (NeglectSkyline,)


@app.cell
def _(anywidget, traitlets):
    class CallStorm(anywidget.AnyWidget):
        """One call, then the same call from everywhere, then the wait.

        A scripted sequence rather than a chart: a resident reports a problem, the identical report
        is imagined from all 55 neighborhoods at once, and the map drains at the rate the model
        predicts for each one. The counterfactual is the point -- those 55 calls did not happen, and
        the sequence says so on screen before it runs.

        Visual-first by construction. Audio clips are fired at cue times but never drive the clock,
        so the whole thing plays correctly with no audio present at all.
        """

        _esm = r"""
        // One AudioContext for the page. Chrome allows six per process and marimo re-renders
        // widgets, so this is deliberately module-level rather than per-render.
        let AC = null;
        const BUF = {};

        const audio = {
          ctx() {
            if (!AC) { const C = window.AudioContext || window.webkitAudioContext; AC = C ? new C() : null; }
            return AC;
          },
          async unlock(clips) {
            const c = this.ctx(); if (!c) return;
            if (c.state === "suspended") { try { await c.resume(); } catch (e) {} }
            for (const [k, uri] of Object.entries(clips || {})) {
              if (BUF[k] !== undefined) continue;
              BUF[k] = null;                       // claim the slot so we decode once
              try {
                const r = await fetch(uri);
                BUF[k] = await c.decodeAudioData(await r.arrayBuffer());
              } catch (e) { BUF[k] = null; }       // a missing clip must never break the sequence
            }
          },
          play(name, when, gain) {
            const c = this.ctx(), b = BUF[name]; if (!c || !b) return;
            const s = c.createBufferSource(), g = c.createGain();
            s.buffer = b; g.gain.value = gain === undefined ? 1 : gain;
            s.connect(g); g.connect(c.destination); s.start(c.currentTime + (when || 0));
          },
          tone(freq, when, dur, gain, type) {
            const c = this.ctx(); if (!c) return;
            const t = c.currentTime + (when || 0), o = c.createOscillator(), g = c.createGain();
            o.type = type || "sine"; o.frequency.value = freq;
            g.gain.setValueAtTime(0.0001, t);
            g.gain.exponentialRampToValueAtTime(gain, t + 0.012);
            g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
            o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + dur + 0.02);
          },
          ring(when) { this.tone(440, when, 1.1, 0.04); this.tone(480, when, 1.1, 0.04); },
        };

        // Green is not "some progress", it is "this area cleared the bar": three in four reports
        // closed. Below the bar the greens deepen; above it the ramp runs amber to red by how far
        // short it fell. The step at the bar is deliberate -- crossing it is the event worth seeing,
        // and a smooth ramp let areas sitting on a sixth of their reports still look answered.
        const DEEP = [26, 132, 78], MINT = [138, 196, 116];
        const AMBER = [226, 168, 62], RED = [196, 52, 42];
        const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
        const shade = (s, bar) => {
          const t = Math.max(0, Math.min(1, s));
          if (t <= bar) return `rgb(${mix(DEEP, MINT, bar ? t / bar : 0).join(",")})`;
          return `rgb(${mix(AMBER, RED, Math.min(1, (t - bar) / (1 - bar))).join(",")})`;
        };

        function render({ model, el }) {
          const [W, H] = model.get("size");
          const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

          el.innerHTML = `
            <div class="cs-wrap">
              <div class="cs-stage">
                <svg class="cs-map" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
                  <g class="cs-areas"></g><g class="cs-rings"></g>
                  <g class="cs-cards"></g><g class="cs-stamps"></g>
                </svg>
                <div class="cs-hud">
                  <div class="cs-phase"></div>
                  <div class="cs-clock"><span class="cs-dayw">Predicted day <b class="cs-day">0</b></span>
                    <span class="cs-speed"></span></div>
                  <div class="cs-count"></div>
                <div class="cs-mark"></div>
                <div class="cs-me"></div>
                </div>
                <div class="cs-board"></div>
                <div class="cs-bar"><i class="cs-bar-done"></i></div>
                <div class="cs-ev"></div>
                <div class="cs-end"></div>
                <div class="cs-cap"></div>
              </div>
              <div class="cs-ctrl">
                <button class="cs-play">Play the call</button>
                <button class="cs-skip" title="Jump to the final state">Skip to the end</button>
                <span class="cs-note"></span>
              </div>
            </div>`;

          const $ = (c) => el.querySelector(c);
          const gA = $(".cs-areas"), gR = $(".cs-rings"), gC = $(".cs-cards"), gS = $(".cs-stamps");
          const elPhase = $(".cs-phase"), elDay = $(".cs-day"), elDayW = $(".cs-dayw");
          const elSpeed = $(".cs-speed"), elCount = $(".cs-count"), elCap = $(".cs-cap");
          const elBoard = $(".cs-board"), btn = $(".cs-play"), skip = $(".cs-skip"), note = $(".cs-note");
          const elBar = $(".cs-bar"), elBarDone = $(".cs-bar-done"), elEnd = $(".cs-end");
          const elEv = $(".cs-ev"), elMark = $(".cs-mark"), elMe = $(".cs-me");

          const cur = () => model.get("curves") || {};
          const lab = () => model.get("labels") || {};
          const cen = () => model.get("centroids") || {};
          const hz = () => model.get("horizon") || 180;
          const barOf = () => model.get("answered") || 0.25;
          const sAt = (csa, d) => { const c = cur()[csa]; return c ? c[Math.min(Math.round(d), c.length - 1)] / 100 : null; };

          // --- build the map once -------------------------------------------------
          const paths = {}, cards = {}, stamps = {};
          for (const sh of model.get("shapes")) {
            const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
            p.setAttribute("d", sh.d); p.setAttribute("class", "cs-area");
            gA.appendChild(p); paths[sh.csa] = p;
          }

          // Cards are drawn in map units, so they must be counter-scaled as the camera moves or they
          // balloon when it pushes in. place() is the single place that owns a card's transform.
          let camScale = 1;
          const place = (csa, g, grown) => {
            const c = cen()[csa]; if (!c) return;
            const k = (grown ? 1 : 0.01) * camScale;
            g.setAttribute("transform", `translate(${c[0]},${c[1]}) scale(${k})`);
          };
          const rescale = () => {
            for (const [csa, g] of Object.entries(cards)) {
              place(csa === "__origin" ? model.get("origin") : csa, g, g.classList.contains("cs-in"));
            }
          };

          const mkCard = (csa, big) => {
            const c = cen()[csa]; if (!c) return null;
            const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
            g.setAttribute("class", "cs-card" + (big ? " cs-big" : ""));
            g.setAttribute("transform", `translate(${c[0]},${c[1]}) scale(${0.01 * camScale})`);
            const w = big ? 150 : 46, h = big ? 54 : 26;
            g.innerHTML =
              `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${big ? 8 : 6}"></rect>` +
              [0, 1, 2, 3].map((i) =>
                `<rect class="cs-bar" x="${-w / 2 + (big ? 14 : 9) + i * (big ? 9 : 7)}" y="-5"
                       width="${big ? 4 : 3}" height="10" rx="1.5" style="animation-delay:${i * 0.12}s"></rect>`
              ).join("") +
              (big ? `<text class="cs-name" x="${-w / 2 + 52}" y="-4">${csa.split("/")[0]}</text>
                      <text class="cs-sub" x="${-w / 2 + 52}" y="10">calling 311</text>` : "");
            gC.appendChild(g); return g;
          };

          // --- state --------------------------------------------------------------
          let raf = null, t0 = 0, fired = new Set(), phase = "idle", cdAt = null, running = false;
          let markSet = new Set();
          let cleared = [], stampSet = new Set(), timers = [];
          const CD_A = 12000, CD_DAY_A = 30, CD_B = 9000;   // warped: slow to day 30, then run
          const dayAt = (e) => e <= CD_A
            ? (CD_DAY_A * e) / CD_A
            : CD_DAY_A + (hz() - CD_DAY_A) * Math.min(1, (e - CD_A) / CD_B);
          const speedAt = (e) => e <= CD_A ? (CD_DAY_A * 1000) / CD_A : ((hz() - CD_DAY_A) * 1000) / CD_B;

          const clearDay = (csa) => { const l = lab()[csa] || {}; return l.clear === undefined ? null : l.clear; };

          // Day zero means nothing has been answered yet, so the city starts wholly red. Anything
          // without a curve stays a neutral grey rather than claiming to be either.
          const fillsAt = (d) => {
            for (const [csa, p] of Object.entries(paths)) {
              const s = sAt(csa, d);
              p.setAttribute("fill", s === null ? "rgba(255,255,255,0.10)" : shade(s, barOf()));
            }
          };

          const paintDay = (d) => {
            elDay.textContent = Math.round(d);
            let open = 0, tot = 0;
            for (const [csa, p] of Object.entries(paths)) {
              const s = sAt(csa, d);
              if (s === null) { p.setAttribute("fill", "rgba(255,255,255,0.10)"); continue; }
              p.setAttribute("fill", shade(s, barOf()));
              // The longer an area sits unanswered while its neighbours resolve, the angrier its
              // outline gets. The fill still carries the number; this only draws the eye to it.
              const rot = s > 0.5 ? Math.min(1, (d / hz()) * 1.6 * s) : 0;
              if (rot > 0.04) {
                p.style.stroke = `rgba(255,86,70,${(0.3 + 0.7 * rot).toFixed(2)})`;
                p.style.strokeWidth = (0.7 + 2.3 * rot).toFixed(2);
              } else if (p.style.stroke) {
                p.style.stroke = ""; p.style.strokeWidth = "";
              }
              const n = (lab()[csa] || {}).n || 0; open += s * n; tot += n;
              const cd = clearDay(csa);
              if (cd !== null && d >= cd && !stampSet.has(csa)) {
                stampSet.add(csa); cleared.push(csa);
                const _cc = cen()[csa];
                if (_cc) ring(_cc[0], _cc[1], 70, 700, "cs-done");
                // pitched by finish order: the city plays a falling melody as neglect deepens
                audio.tone(880 * Math.pow(0.945, cleared.length), 0, 0.42, 0.06, "triangle");
                p.classList.add("cs-pop"); setTimeout(() => p.classList.remove("cs-pop"), 420);
              }
            }
            // Days are abstract. "Three months" is not.
            const MARKS = [[7, "one week"], [30, "one month"], [90, "three months"], [180, "six months"]];
            for (const [dd, text] of MARKS) {
              if (d >= dd && !markSet.has(dd)) {
                markSet.add(dd);
                elMark.textContent = text;
                elMark.classList.remove("cs-flash");
                void elMark.offsetWidth;
                elMark.classList.add("cs-flash");
              }
            }
            const og = model.get("origin"), os = sAt(og, d);
            if (os !== null) {
              elMe.innerHTML = `${og.split("/")[0]} &mdash; <b>${Math.round(100 * os)}%</b> still open`;
            }
            const tot2 = Object.keys(cur()).length;
            elCount.innerHTML = `<b>${cleared.length}</b> of ${tot2} past three in four`;
            elBar.classList.add("cs-on");
            elBarDone.style.width = `${(100 * cleared.length) / Math.max(tot2, 1)}%`;
            elSpeed.textContent = `${Math.round(speedAt(cdAt === null ? 0 : performance.now() - cdAt))} days/sec`;
            drawBoard(d);
          };

          const drawBoard = (d) => {
            const rows = Object.keys(cur()).map((csa) => ({ csa, s: sAt(csa, d), cd: clearDay(csa) }));
            rows.sort((a, b) => b.s - a.s);
            const top = rows.slice(0, 6);
            elBoard.innerHTML = `<div class="cs-bh">longest still waiting</div>` + top.map((r) =>
              `<div class="cs-br"><span>${r.csa.split("/")[0]}</span><b>${Math.round(100 * r.s)}%</b></div>`
            ).join("");
          };

          // --- cue handlers -------------------------------------------------------
          const say = (text, type) => {
            if (!type || reduce) { elCap.textContent = text; return; }
            elCap.textContent = ""; let i = 0;
            const id = setInterval(() => {
              elCap.textContent = text.slice(0, ++i);
              if (i >= text.length) clearInterval(id);
            }, 22);
            timers.push(id);
          };

          const issueClips = () =>
            Object.keys(model.get("clips") || {}).filter((k) => k.startsWith("issue_")).sort();

          const ring = (x, y, r1, ms, cls) => {
            const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            c.setAttribute("class", "cs-ring " + (cls || ""));
            c.setAttribute("cx", x); c.setAttribute("cy", y); c.setAttribute("r", 1);
            gR.appendChild(c);
            requestAnimationFrame(() => {
              c.style.transition = `r ${ms}ms linear, opacity ${ms}ms ease-out`;
              c.setAttribute("r", r1); c.style.opacity = "0";
            });
            const id = setTimeout(() => c.remove(), ms + 120);
            timers.push(id);
          };

          const mapSpan = () => Math.hypot(W, H);

          const svg = $(".cs-map");
          const FULL = [0, 0, W, H];
          let view = FULL.slice(), camAnim = null;

          const applyView = () => {
            svg.setAttribute("viewBox", view.map((v) => v.toFixed(1)).join(" "));
            camScale = view[2] / W;
            rescale();
          };

          const camera = (target, ms) => {
            const from = view.slice(), t0 = performance.now();
            cancelAnimationFrame(camAnim);
            const step = (now) => {
              const t = Math.min(1, (now - t0) / ms);
              const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;   // easeInOutQuad
              view = from.map((v, i) => v + (target[i] - v) * e);
              applyView();
              if (t < 1) camAnim = requestAnimationFrame(step);
            };
            camAnim = requestAnimationFrame(step);
          };

          const boxOf = (csa) => (model.get("shapes").find((x) => x.csa === csa) || {}).box;

          const camTo = (csa, pad, ms) => {
            const b = boxOf(csa); if (!b) { camera(FULL, ms); return; }
            const [x, y, w, h] = b;
            let tw = w * pad, th = h * pad;
            if (tw / th > W / H) th = (tw * H) / W; else tw = (th * W) / H;
            camera([x + w / 2 - tw / 2, y + h / 2 - th / 2, tw, th], ms);
          };

          // The ripple only has to read as "it is spreading". Voicing all 52 at once was a smear,
          // so a handful speak here and the whole city speaks together on the unison beat.
          const RIPPLE = 1250;

          const bloom = () => {
            const order = Object.entries(model.get("bloom") || {})
              .filter(([csa]) => csa !== model.get("origin"))
              .sort((a, b) => a[1] - b[1]);
            const clips = issueClips();
            const voiceEvery = Math.max(1, Math.floor(order.length / 6));
            const o = cen()[model.get("origin")];
            // One wave leaving her block. Each area answers as the front reaches it, so the spread
            // is something you watch travel rather than a diagram of lines.
            if (o) ring(o[0], o[1], mapSpan(), RIPPLE, "cs-front");
            order.forEach(([csa, frac], n) => {
              const delay = 40 + frac * RIPPLE;
              const g = mkCard(csa, false); if (!g) return;
              cards[csa] = g;
              const id = setTimeout(() => {
                g.classList.add("cs-in"); place(csa, g, true);
                const c = cen()[csa];
                if (c) ring(c[0], c[1], 55, 620, "cs-echo");
                if (paths[csa]) {
                  paths[csa].classList.add("cs-hit");
                  setTimeout(() => paths[csa].classList.remove("cs-hit"), 520);
                }
                if (clips.length && n % voiceEvery === 0) {
                  audio.play(clips[(n / voiceEvery) % clips.length | 0], 0, 0.22);
                }
              }, delay);
              timers.push(id);
            });
          };

          // Every voice at once, a few milliseconds apart so it thickens instead of phasing.
          // Show the inputs before the answer. Without this the countdown reads as a recording of
          // what already happened rather than a forecast for a request nobody has filed yet.
          const evidence = () => {
            const e = model.get("evidence") || {};
            const rows = e.rows || [];
            elEv.innerHTML =
              `<div class="cs-ev-h">what the model is given</div>`
              + rows.map(([k, v], i) =>
                  `<div class="cs-ev-r" style="animation-delay:${i * 130}ms">
                     <span>${k}</span><b>${v}</b></div>`).join("")
              + `<div class="cs-ev-f">gradient-boosted hazard model &middot; trained on
                   ${e.trained || "?"} request-intervals &middot; tested on ${e.tested || "?"}
                   it never saw</div>`;
            elEv.classList.add("cs-on");
            const id = setTimeout(() => elEv.classList.remove("cs-on"), 3600);
            timers.push(id);
          };

          const unison = () => {
            const clips = issueClips();
            audio.play("sfx_burst", 0, 0.7);
            clips.forEach((k, i) => audio.play(k, i * 0.012, 0.95));
            // A ring out of every neighborhood on the same frame. Simultaneity is the whole point,
            // so nothing here is staggered.
            for (const [csa, c] of Object.entries(cen())) {
              if (!paths[csa]) continue;
              ring(c[0], c[1], 130, 900, "cs-burst");
            }
            for (const g of Object.values(cards)) g.classList.add("cs-shout");
            for (const p of Object.values(paths)) p.classList.add("cs-shout-a");
            setTimeout(() => {
              for (const g of Object.values(cards)) g.classList.remove("cs-shout");
              for (const p of Object.values(paths)) p.classList.remove("cs-shout-a");
            }, 900);
          };

          const collapse = () => {
            for (const [csa, g] of Object.entries(cards)) {
              g.classList.add("cs-out");
              place(csa === "__origin" ? model.get("origin") : csa, g, false);
            }
            gR.innerHTML = "";
            for (const p of Object.values(paths)) p.classList.add("cs-lit");
            fillsAt(0);
            elDayW.classList.add("cs-on");
          };

          const apply = (c) => {
            if (c.kind === "phase") elPhase.textContent = c.text;
            else if (c.kind === "caption") say(c.text, c.type);
            else if (c.kind === "ring") {
              const p = paths[model.get("origin")];
              if (p) { p.classList.add("cs-origin"); }
              const _o = cen()[model.get("origin")];
              if (_o) ring(_o[0], _o[1], 110, 1200, "cs-echo");
              if (BUF["sfx_ring"]) audio.play("sfx_ring", 0, 0.85); else audio.ring(0);
            } else if (c.kind === "origin_card") {
              const g = mkCard(model.get("origin"), true);
              if (g) {
                cards.__origin = g;
                requestAnimationFrame(() => { g.classList.add("cs-in"); place(model.get("origin"), g, true); });
              }
            } else if (c.kind === "audio") audio.play(c.clip, 0, c.gain === undefined ? 1 : c.gain);
            else if (c.kind === "camera") {
              if (c.to === "full") camera(FULL, c.ms || 1600);
              else camTo(model.get("origin"), c.pad || 4.2, c.ms || 1400);
            }
            else if (c.kind === "bloom") bloom();
            else if (c.kind === "evidence") evidence();
            else if (c.kind === "unison") unison();
            else if (c.kind === "collapse") collapse();
            else if (c.kind === "countdown") {
              phase = "countdown"; cdAt = performance.now();
              audio.play("sfx_bed", 0, 0.5);   // 22s of underscore over a ~21s countdown
            }
            else if (c.kind === "end") finish();
          };

          const finish = () => {
            phase = "end";
            cancelAnimationFrame(raf); raf = null; running = false;
            paintDay(hz());
            btn.textContent = "Replay"; btn.disabled = false;

            const rows = Object.keys(cur()).map((csa) => ({ csa, s: sAt(csa, hz()) }));
            const stuck = rows.filter((r) => clearDay(r.csa) === null).sort((a, b) => b.s - a.s);
            const origin = model.get("origin");
            const me = rows.find((r) => r.csa === origin);

            // Name the ones left waiting, on the map, where the red is. A day number told you when
            // something finished; this tells you what never did.
            gS.innerHTML = "";
            for (const r of stuck.slice(0, 5)) {
              const c = cen()[r.csa]; if (!c) continue;
              const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
              t.setAttribute("class", "cs-tag"); t.setAttribute("x", c[0]); t.setAttribute("y", c[1]);
              t.innerHTML = `${r.csa.split("/")[0]}<tspan x="${c[0]}" dy="15">`
                + `${Math.round(100 * r.s)}% never answered</tspan>`;
              gS.appendChild(t);
              if (paths[r.csa]) paths[r.csa].classList.add("cs-stuck");
            }

            elPhase.textContent = "Six months later";
            elCap.textContent = "";
            elEnd.innerHTML = stuck.length
              ? `<div class="cs-end-n"><b>${rows.length - stuck.length}</b> of ${rows.length} got
                   three in four reports closed</div>
                 <div class="cs-end-s"><b>${stuck.length}</b> never did, in ${hz()} days</div>
                 <div class="cs-end-o">Denise called from ${origin.split("/")[0]}. Six months on,
                   <b>${Math.round(100 * (me ? me.s : 0))}%</b> of its streetlight reports are
                   still open &mdash; the worst in the city.</div>`
              : `<div class="cs-end-n"><b>all ${rows.length}</b> got three in four closed</div>
                 <div class="cs-end-s">inside ${hz()} days</div>`;
            elEnd.classList.add("cs-on");
          };

          const tick = (now) => {
            const e = now - t0, cues = model.get("cues") || [];
            for (let i = 0; i < cues.length; i++) {
              if (!fired.has(i) && e >= cues[i].t) { fired.add(i); apply(cues[i]); }
            }
            if (phase === "countdown") {
              const ce = now - cdAt;
              paintDay(dayAt(ce));
              if (ce >= CD_A + CD_B) { finish(); return; }
            }
            if (running) raf = requestAnimationFrame(tick);
          };

          const reset = () => {
            cancelAnimationFrame(raf); raf = null; running = false; phase = "idle";
            fired = new Set(); cleared = []; stampSet = new Set(); markSet = new Set();
            elEv.innerHTML = ""; elEv.classList.remove("cs-on");
            elMark.textContent = ""; elMe.textContent = "";
            for (const id of timers) clearTimeout(id), clearInterval(id);
            timers = [];
            gC.innerHTML = ""; gR.innerHTML = ""; gS.innerHTML = "";
            cancelAnimationFrame(camAnim); view = FULL.slice(); applyView();
            for (const k of Object.keys(cards)) delete cards[k];
            for (const p of Object.values(paths)) p.className.baseVal = "cs-area";
            elPhase.textContent = ""; elCap.textContent = ""; elCount.textContent = "";
            elSpeed.textContent = ""; elBoard.innerHTML = ""; elDay.textContent = "0";
            elEnd.innerHTML = ""; elEnd.classList.remove("cs-on");
            elBar.classList.remove("cs-on"); elBarDone.style.width = "0%";
            elDayW.classList.remove("cs-on");
            for (const p of Object.values(paths)) { p.style.stroke = ""; p.style.strokeWidth = ""; }
            fillsAt(0);
            note.textContent = Object.keys(model.get("clips") || {}).length
              ? "" : "no audio assets found — playing silent";
          };

          const start = async () => {
            reset();
            btn.disabled = true; btn.textContent = "Playing…";
            await audio.unlock(model.get("clips"));
            if (reduce) { phase = "countdown"; finish(); return; }
            running = true; t0 = performance.now(); raf = requestAnimationFrame(tick);
          };

          btn.addEventListener("click", start);
          skip.addEventListener("click", () => {
            reset(); audio.unlock(model.get("clips"));
            for (const p of Object.values(paths)) p.classList.add("cs-lit");
            phase = "countdown"; finish();
          });
          model.on("change:curves", reset);
          reset();
          return () => { cancelAnimationFrame(raf); for (const id of timers) clearTimeout(id); };
        }
        export default { render };
        """

        _css = r"""
        .cs-wrap { font: 13px system-ui, -apple-system, sans-serif; }
        .cs-stage { position: relative; background: #121821; border-radius: 10px; padding: 14px 14px 10px;
                    overflow: hidden; }
        .cs-stage::after { content: ""; position: absolute; inset: 0; pointer-events: none;
                           background: radial-gradient(ellipse at 50% 45%, transparent 68%, rgba(0,0,0,0.30)); }
        .cs-map { width: 100%; max-height: 460px; height: auto; display: block; background: transparent; }
        .cs-area { stroke: rgba(255,255,255,0.3); stroke-width: 0.7; transition: fill 120ms linear; }
        .cs-area.cs-lit { stroke: rgba(255,255,255,0.42); }
        .cs-area.cs-shout-a { stroke: #f6ad55; stroke-width: 2; }
        .cs-area.cs-origin { stroke: #dd6b20; stroke-width: 3; animation: cs-pulse 1.1s ease-out 3; }
        .cs-area.cs-pop { stroke: #2b6cb0; stroke-width: 3; }
        .cs-area.cs-stuck { stroke: #ff6b5a; stroke-width: 2.6; animation: cs-pulse 2.2s ease-in-out infinite; }
        @keyframes cs-pulse { 0%,100% { stroke-opacity: 1; } 50% { stroke-opacity: 0.25; } }

        .cs-card { opacity: 0; transition: transform 380ms cubic-bezier(.2,1.4,.4,1), opacity 260ms; }
        .cs-card.cs-in { opacity: 1; }
        .cs-card rect { fill: #1f2733; stroke: rgba(255,255,255,0.18); stroke-width: 0.8; }
        .cs-card .cs-bar { fill: #f6ad55; animation: cs-wave 0.7s ease-in-out infinite alternate; }
        .cs-card.cs-big rect:first-child { fill: #141b24; stroke: #dd6b20; stroke-width: 1.4; }
        .cs-name { fill: #fff; font: 600 11px system-ui; }
        .cs-sub { fill: #a0aec0; font: 9px system-ui; }
        @keyframes cs-wave { from { transform: scaleY(0.35); } to { transform: scaleY(1.5); } }
        .cs-card.cs-out { opacity: 0; transition: transform 520ms ease-in, opacity 520ms; }
        .cs-card.cs-shout rect { fill: #dd6b20; stroke: #ffd9b3; stroke-width: 1.6; }
        .cs-card.cs-shout .cs-bar { fill: #fff; animation-duration: 0.22s; }
        .cs-ring { fill: none; pointer-events: none; }
        .cs-ring.cs-front { stroke: #f6ad55; stroke-width: 3; opacity: 0.85; }
        .cs-ring.cs-echo { stroke: #f6ad55; stroke-width: 2; opacity: 0.7; }
        .cs-ring.cs-burst { stroke: #fff; stroke-width: 2.5; opacity: 0.9; }
        .cs-area.cs-hit { stroke: #f6ad55; stroke-width: 2.2; }
        .cs-ring.cs-done { stroke: #2d9e60; stroke-width: 3; opacity: 0.9; }
        .cs-tag { font: 600 13px system-ui; text-anchor: middle; paint-order: stroke;
                  stroke: rgba(0,0,0,0.85); stroke-width: 3.5px; fill: #fff; }
        .cs-tag tspan { font-weight: 400; font-size: 11px; fill: #ff9f8c; }

        .cs-hud { position: absolute; top: 14px; left: 18px; right: 18px; z-index: 3; display: flex;
                  align-items: baseline; gap: 12px; pointer-events: none; }
        .cs-phase { font-family: Newsreader, Georgia, serif; font-size: 17px; font-style: italic; color: #93a2b3; }
        .cs-clock { margin-left: auto; display: flex; align-items: baseline; gap: 8px; opacity: 0; transition: opacity 400ms; }
        .cs-dayw.cs-on { opacity: 1; }
        .cs-clock:has(.cs-on) { opacity: 1; }
        .cs-day { font-family: "IBM Plex Mono", monospace; font-size: 40px; color: #f6ad55; font-variant-numeric: tabular-nums;
                  text-shadow: 0 0 22px rgba(246,173,85,0.45); }
        .cs-dayw { color: #8b98a8; }
        .cs-speed { font-size: 11px; color: #71809000; }
        .cs-clock:hover .cs-speed, .cs-dayw.cs-on ~ .cs-speed { color: #718090; }
        .cs-count { position: absolute; top: 44px; right: 0; font-size: 12px; color: #8b98a8; }
        .cs-count b { color: #63b3ed; font-size: 18px; font-variant-numeric: tabular-nums; }

        .cs-board { position: absolute; right: 16px; bottom: 74px; width: 176px; pointer-events: none;
                    font-size: 11px; color: #8b98a8; z-index: 2; }
        .cs-bh { font-family: Newsreader, Georgia, serif; font-style: italic; font-size: 12px; margin-bottom: 5px; }
        .cs-br { display: flex; justify-content: space-between; padding: 1px 0; }
        .cs-br b { color: #f6ad55; font-variant-numeric: tabular-nums; }

        .cs-ev { position: absolute; left: 50%; top: 48%; transform: translate(-50%,-50%);
                 z-index: 4; min-width: 340px; padding: 18px 22px; opacity: 0; pointer-events: none;
                 background: rgba(6,10,14,0.94); border-left: 2px solid #9a7b1f;
                 transition: opacity 380ms ease; }
        .cs-ev.cs-on { opacity: 1; }
        .cs-ev-h { font-family: Newsreader, Georgia, serif; font-size: 14px; font-style: italic;
                   color: #93a2b3; margin-bottom: 12px; }
        .cs-ev-r { display: flex; justify-content: space-between; gap: 24px; padding: 3px 0;
                   font-size: 12px; color: #9aa7b6; opacity: 0; animation: cs-rowin 260ms ease forwards; }
        .cs-ev-r b { color: #e9eef5; font-weight: 600; }
        @keyframes cs-rowin { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: none; } }
        .cs-ev-f { margin-top: 12px; padding-top: 9px; border-top: 1px solid rgba(255,255,255,0.1);
                   font-size: 10px; color: #6c7a8a; max-width: 330px; line-height: 1.5; }

        .cs-mark { position: absolute; left: 50%; top: 30%; transform: translateX(-50%); z-index: 3;
                   font-size: 30px; font-weight: 300; letter-spacing: 0.04em; color: #fff;
                   opacity: 0; pointer-events: none; text-shadow: 0 2px 20px rgba(0,0,0,0.8); }
        .cs-mark.cs-flash { animation: cs-markin 2100ms ease forwards; }
        @keyframes cs-markin { 0% { opacity: 0; transform: translateX(-50%) scale(0.9); }
                               18% { opacity: 1; transform: translateX(-50%) scale(1); }
                               72% { opacity: 1; } 100% { opacity: 0; } }
        .cs-me { position: absolute; left: 18px; bottom: 86px; z-index: 3; font-size: 12px; color: #8b98a8; }
        .cs-me b { color: #ff9f8c; font-variant-numeric: tabular-nums; font-size: 15px; }

        .cs-bar { position: absolute; left: 18px; right: 18px; bottom: 74px; height: 4px; z-index: 3;
                  background: rgba(255,255,255,0.12); border-radius: 2px; opacity: 0; transition: opacity 400ms; }
        .cs-bar.cs-on { opacity: 1; }
        .cs-bar-done { display: block; height: 100%; width: 0; border-radius: 2px;
                       background: #2d9e60; transition: width 160ms linear; }

        .cs-end { position: absolute; left: 50%; top: 46%; transform: translate(-50%, -50%) scale(0.98);
                  z-index: 4; text-align: center; padding: 26px 34px; opacity: 0; pointer-events: none;
                  background: rgba(6,10,14,0.9); border-top: 2px solid #b83227;
                  border-bottom: 1px solid rgba(255,255,255,0.12);
                  transition: opacity 500ms ease, transform 500ms cubic-bezier(.2,1.2,.4,1); }
        .cs-end.cs-on { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        .cs-end-n { font-size: 15px; color: #cfd8e3; }
        .cs-end-n b { font-size: 34px; color: #2fbe74; font-variant-numeric: tabular-nums; }
        .cs-end-s { margin-top: 6px; font-size: 15px; color: #cfd8e3; }
        .cs-end-s b { font-size: 26px; color: #ff6b5a; font-variant-numeric: tabular-nums; }
        .cs-end-o { margin-top: 10px; font-size: 12px; color: #8b98a8; max-width: 280px; }
        .cs-end-o b { color: #ff9f8c; }

        .cs-cap { position: absolute; left: 0; right: 0; bottom: 0; min-height: 46px; z-index: 3;
                  padding: 14px 18px 16px; font-size: 17px; line-height: 1.4; color: #f2f4f7;
                  background: linear-gradient(transparent, rgba(0,0,0,0.8) 62%); }
        .cs-cap:empty { background: none; }
        .cs-cap b { color: #f6ad55; }
        .cs-ctrl { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
        .cs-play, .cs-skip { cursor: pointer; border: 1px solid rgba(127,127,127,0.4); border-radius: 4px;
                             background: transparent; color: inherit; font-size: 12px; padding: 5px 12px; }
        .cs-play { border-color: #dd6b20; color: #dd6b20; font-weight: 600; }
        .cs-play:disabled { opacity: 0.5; cursor: default; }
        .cs-note { font-size: 11px; color: #999; margin-left: auto; }
        """

        shapes = traitlets.List([]).tag(sync=True)
        size = traitlets.List([1000, 1000]).tag(sync=True)
        centroids = traitlets.Dict({}).tag(sync=True)
        bloom = traitlets.Dict({}).tag(sync=True)
        curves = traitlets.Dict({}).tag(sync=True)
        labels = traitlets.Dict({}).tag(sync=True)
        origin = traitlets.Unicode("").tag(sync=True)
        cues = traitlets.List([]).tag(sync=True)
        clips = traitlets.Dict({}).tag(sync=True)
        horizon = traitlets.Int(180).tag(sync=True)
        answered = traitlets.Float(0.25).tag(sync=True)
        evidence = traitlets.Dict({}).tag(sync=True)
    return (CallStorm,)


@app.cell
def _(MAP_SIZE, TriageExplorer, default_overall, map_shapes, mo):
    # Created once, so the selection survives slider moves. Scores and dots are pushed in by the cells below.
    # `?area=Cherry Hill` in the URL opens the app on that area (read once, never re-triggers this cell).
    _asked = mo.query_params().get("area")
    triage_widget = TriageExplorer(
        shapes=map_shapes,
        size=MAP_SIZE,
        selected=_asked if _asked in default_overall["csa"].to_list() else default_overall["csa"][0],
    )
    explorer = mo.ui.anywidget(triage_widget)
    return explorer, triage_widget


@app.cell
def _(FIX_HORIZON, FixClock, MAP_SIZE, map_shapes, mo):
    # Created once, like the gap map above; curves are pushed in by the cell below.
    clock_widget = FixClock(shapes=map_shapes, size=MAP_SIZE, horizon=FIX_HORIZON)
    fix_clock_view = mo.ui.anywidget(clock_widget)
    return clock_widget, fix_clock_view


@app.cell
def _(MAP_SIZE, NeglectSkyline, default_overall, map_centroids, map_shapes, mo):
    _asked = mo.query_params().get("area")
    skyline_widget = NeglectSkyline(
        shapes=map_shapes,
        size=MAP_SIZE,
        centroids=map_centroids,
        selected=_asked if _asked in default_overall["csa"].to_list() else default_overall["csa"][0],
    )
    skyline_view = mo.ui.anywidget(skyline_widget)
    return skyline_view, skyline_widget


@app.cell
def _(CallStorm, FIX_HORIZON, MAP_SIZE, map_centroids, map_shapes, mo):
    # Created once, like the maps above. Everything else is pushed in through the raw handle.
    storm_widget = CallStorm(
        shapes=map_shapes, size=MAP_SIZE, centroids=map_centroids, horizon=FIX_HORIZON
    )
    storm_view = mo.ui.anywidget(storm_widget)
    return storm_view, storm_widget


@app.cell
def _(
    DATA_DIR,
    STORM_ANSWERED,
    STORM_ISSUE,
    STORM_ORIGIN,
    STORM_PREMISE,
    STORM_TOPIC,
    base64,
    bloom_order,
    fix_calibration,
    fix_clock,
    fix_inputs,
    fix_model,
    fix_summary,
    map_centroids,
    np,
    pl,
    storm_widget,
):
    def storm_cues(premise, issue):
        """The running order, in milliseconds. Audio is fired at these marks but never drives them."""
        return [
            {"t": 0, "kind": "phase", "text": "Dialling 311"},
            {"t": 150, "kind": "ring"},
            {"t": 700, "kind": "camera", "to": "origin", "pad": 4.2, "ms": 1500},
            {"t": 1100, "kind": "origin_card"},
            {"t": 1500, "kind": "audio", "clip": "premise"},
            {"t": 1500, "kind": "caption", "text": premise, "type": True},
            {"t": 8600, "kind": "phase", "text": "Now the same call, from every neighborhood"},
            {"t": 8800, "kind": "caption", "text": "", "type": False},
            {"t": 8700, "kind": "camera", "to": "full", "ms": 2500},
            {"t": 8900, "kind": "bloom"},
            {"t": 11400, "kind": "unison"},
            {"t": 11400, "kind": "caption", "text": issue, "type": False},
            {"t": 13600, "kind": "phase", "text": "The model reads each one"},
            {"t": 13700, "kind": "evidence"},
            {"t": 17600, "kind": "phase", "text": "and predicts how long each will wait"},
            {"t": 17800, "kind": "collapse"},
            {"t": 19100, "kind": "phase", "text": "Predicted wait"},
            {"t": 19100, "kind": "countdown"},
        ]

    def storm_clips(data_dir):
        """Audio as base64 data URIs: the only transport that survives both run and static export.

        Only the clips this sequence actually fires. The call panel above has its own, larger
        recordings, and shipping those here would put a few hundred kilobytes on the wire for
        audio that never plays.
        """
        _d = data_dir / "demo_call"
        _want = lambda _f: _f.stem == "premise" or _f.stem.startswith(("issue_", "sfx_"))
        return {
            _f.stem: "data:audio/mpeg;base64," + base64.b64encode(_f.read_bytes()).decode()
            for _f in (sorted(_d.glob("*.mp3")) if _d.exists() else [])
            if _want(_f)
        }

    _rows = fix_summary.filter(
        (pl.col("domain") == STORM_TOPIC) & pl.col("csa").is_in(list(map_centroids))
    )
    _idx = {(_d, _c): _i for _i, (_d, _c) in enumerate(fix_clock["cells"].iter_rows())}
    _S = fix_clock["S"]

    storm_widget.curves = {
        _r["csa"]: np.rint(_S[_idx[(STORM_TOPIC, _r["csa"])]] * 100).astype(int).tolist()
        for _r in _rows.iter_rows(named=True)
    }
    def _answered_on(curve, threshold):
        """First day three in four of an area's reports are closed, or None if that never happens."""
        _hit = curve <= threshold
        return int(np.argmax(_hit)) if _hit.any() else None

    storm_widget.labels = {
        _r["csa"]: {
            "n": _r["n"],
            "clear": _answered_on(_S[_idx[(STORM_TOPIC, _r["csa"])]], STORM_ANSWERED),
            "open180": round(float(_r["still_open_at_horizon"]), 3),
        }
        for _r in _rows.iter_rows(named=True)
    }
    # What the model is handed for this request, shown on screen before it answers. A viewer who
    # cannot see the inputs has no way to tell a prediction from a recording of the past.
    _o = fix_inputs.filter((pl.col("domain") == STORM_TOPIC) & (pl.col("csa") == STORM_ORIGIN))
    _ex = _o.row(0, named=True) if _o.height else {}
    storm_widget.evidence = {
        "rows": [
            ["problem type", STORM_TOPIC],
            ["handled by", str(_ex.get("agency", "-"))],
            ["reported via", str(_ex.get("method", "-"))],
            ["city's own deadline", f"{_ex.get('sla_days', 0):.0f} days"],
            ["how much this area calls", f"{_ex.get('reports_per_1k', 0):.0f} per 1,000 residents"],
            ["vacant properties here", f"{_ex.get('vacancy', 0):.1f}%"],
            ["past reports like it", f"{int(_ex.get('n', 0)):,}"],
        ],
        "trained": f"{fix_model['n_train']:,}",
        "rounds": fix_model["rounds"],
        "tested": f"{int(fix_calibration['n'].max()):,}",
    }
    storm_widget.answered = STORM_ANSWERED
    storm_widget.origin = STORM_ORIGIN
    storm_widget.bloom = bloom_order(STORM_ORIGIN, map_centroids)
    storm_widget.cues = storm_cues(STORM_PREMISE, STORM_ISSUE)
    storm_widget.clips = storm_clips(DATA_DIR)
    return


@app.cell
def _(clock_topic, clock_widget, fix_clock, fix_summary, np, pl):
    # Pushed through the raw widget handle, never through the mo.ui wrapper: assigning a trait this
    # way reaches the browser without marking this cell dirty, so there is no reactive loop.
    _rows = fix_summary.filter(pl.col("domain") == clock_topic.value)
    _idx = {(_d, _c): _i for _i, (_d, _c) in enumerate(fix_clock["cells"].iter_rows())}
    _S = fix_clock["S"]

    # 0-100 integers rather than floats: 55 areas x 181 days lands around 10 KB of JSON, well inside
    # marimo's output size limit.
    clock_widget.curves = {
        _r["csa"]: np.rint(_S[_idx[(clock_topic.value, _r["csa"])]] * 100).astype(int).tolist()
        for _r in _rows.iter_rows(named=True)
    }
    clock_widget.labels = {
        _r["csa"]: {"n": _r["n"], "median": _r["median_days"]} for _r in _rows.iter_rows(named=True)
    }
    clock_widget.topic = f"{clock_topic.value} - resident-reported requests"
    return


@app.cell
def _(
    DOMAIN_ORDER,
    VACANCY,
    domain_scores,
    fix_days,
    pl,
    skyline_view,
    skyline_widget,
    weight_sliders,
):
    # A selected category behaves like the 2D Gap Card selector. "All topics" falls back to
    # the same topic weights as the 2D map.
    _focus = skyline_view.value.get("focus") or ""
    _domains = (
        [_focus]
        if _focus in DOMAIN_ORDER
        else [d for d in DOMAIN_ORDER if weight_sliders.value.get(d, 0) > 0]
    )
    _scores = {
        (_r["domain"], _r["csa"]): _r
        for _r in domain_scores.filter(pl.col("domain").is_in(_domains)).iter_rows(named=True)
    }
    _areas = {}
    for _csa in domain_scores["csa"].unique().to_list():
        _gnum = 0.0
        _gden = 0.0
        for _d in _domains:
            _r = _scores.get((_d, _csa))
            _w = 1.0 if _focus else float(weight_sliders.value.get(_d, 0))
            if _r is None or _w <= 0:
                continue
            if _r["gap"] is not None:
                _gnum += _w * float(_r["gap"])
                _gden += _w
        if _gden:
            _areas[_csa] = {
                "gap": round(_gnum / _gden, 4),
            }

    # Rank the exact gap painted in this view; it is topic-specific or the current weighted 311 gap.
    _ranked = sorted(
        ((c, r["gap"]) for c, r in _areas.items() if r["gap"] is not None),
        key=lambda x: x[1],
        reverse=True,
    )
    for _rank, (_csa, _) in enumerate(_ranked, 1):
        _areas[_csa]["rank"] = _rank

    _selected = skyline_view.value.get("selected") or ""
    _card = None
    if _selected:
        _card_rows = []
        for _r in domain_scores.filter(pl.col("csa") == _selected).iter_rows(named=True):
            _svc = "not enough requests" if _r["service_rate"] is None else f"{_r['service_rate']:.0%}"
            _svc_label = (
                "handled since 2023"
                if _r["domain"] == VACANCY
                else f"of the first {fix_days.value} days already closed"
            )
            _pro = "" if _r["proactive_share"] is None else f" · proactive share {_r['proactive_share']:.0%}"
            _card_rows.append(
                {
                    "domain": _r["domain"],
                    "need": _r["need_pct"],
                    "service": _r["service_pct"],
                    "gap": _r["gap"],
                    "detail": (
                        f"{_r['n_reports']:,} reports ({_r['need_rate']:.1f} per 1,000) · "
                        f"{_svc} {_svc_label}{_pro}"
                    ),
                }
            )
        _area = _areas.get(_selected)
        _card = {
            "csa": _selected,
            "subtitle": (
                f"gap rank {_area['rank']} of {len(_areas)} · current gap {_area['gap']:+.2f}"
                if _area else "not enough data for the selected view"
            ),
            "rows": _card_rows,
        }
    skyline_widget.data = {
        "areas": _areas,
        "card": _card,
    }
    return


@app.cell
def _(VACANCY, domain_scores, fix_days, overall, pl, triage_widget):
    def _detail(r):
        _svc = "not enough requests" if r["service_rate"] is None else f"{r['service_rate']:.0%}"
        _svc_label = "handled since 2023" if r["domain"] == VACANCY else f"of the first {fix_days.value} days already closed"
        _pro = "" if r["proactive_share"] is None else f" · proactive share {r['proactive_share']:.0%}"
        return f"{r['n_reports']:,} reports ({r['need_rate']:.1f} per 1,000) · {_svc} {_svc_label}{_pro}"

    _overall = {r["csa"]: r for r in overall.to_dicts()}
    _cards = {}
    for _r in domain_scores.sort(pl.col("gap").fill_null(-9), descending=True).to_dicts():
        _o = _overall.get(_r["csa"])
        _card = _cards.setdefault(
            _r["csa"],
            {"subtitle": f"gap rank {_o['rank']} of {overall.height} · overall gap {_o['gap']:+.2f}" if _o else "", "rows": []},
        )
        _card["rows"].append(
            {"domain": _r["domain"], "need": _r["need_pct"], "service": _r["service_pct"], "gap": _r["gap"], "detail": _detail(_r)}
        )
    # Uses the raw widget (not `explorer`), so pushing new scores never re-runs this cell.
    triage_widget.data = {
        "n": overall.height,
        "fix_days": fix_days.value,
        "overall": {c: {"gap": o["gap"], "rank": o["rank"]} for c, o in _overall.items()},
        "topics": {
            d: dict(zip(g["csa"].to_list(), g["gap"].to_list()))
            for (d,), g in domain_scores.group_by("domain")
        },
        "cards": _cards,
    }
    return


@app.cell
def _(default_overall, explorer, mo):
    # `picked_area` is empty after "Back to city": the map shows the whole city with nothing
    # outlined. `selected_area` keeps a fallback so the panels that always need an area still have
    # one; anything that should disappear when nothing is picked checks `picked_area` instead.
    picked_area = explorer.value.get("selected") or ""
    selected_area = picked_area or default_overall["csa"][0]
    focus_topic = explorer.value.get("focus") or ""
    if picked_area:
        mo.query_params().set("area", picked_area)
    return focus_topic, picked_area, selected_area


@app.cell
def _(
    VACANCY,
    area_requests,
    area_vacancy,
    fix_days,
    focus_topic,
    housing,
    pl,
    project,
    requests_311,
    selected_area,
    snapshot_meta,
    triage_widget,
    window,
):
    area_reqs = area_requests(
        requests_311, selected_area, snapshot_ts=snapshot_meta["snapshot_ts"],
        window_days=window.value, fix_days=fix_days.value,
        topic=focus_topic if focus_topic != VACANCY else None,
    )
    area_vac = area_vacancy(housing, selected_area)

    # Dots for the zoomed map: no topic picked = still-open requests + vacant buildings;
    # a 311 topic = all its requests; vacancy = vacant buildings only.
    _reqs = area_reqs.filter(pl.col("status") == "open") if not focus_topic else area_reqs
    _reqs = _reqs if focus_topic != VACANCY else _reqs.clear()
    _vac = area_vac if focus_topic in ("", VACANCY) else area_vac.clear()
    _items = []
    for _df, _tip in [
        (
            _reqs.with_columns(pl.col("status").alias("k")),
            lambda r: f"{r['domain']} · {r['address']} · "
            + (f"open {r['days']} days" if r["status"] == "open" else f"closed in {r['days']} days"),
        ),
        (
            _vac.with_columns(pl.when(pl.col("handled")).then(pl.lit("handled")).otherwise(pl.lit("vacant")).alias("k")),
            lambda r: f"{r['address']} · "
            + (f"{r['action']} {r['action_date']:%b %Y}" if r["handled"] else f"vacant notice since {r['notice_date']:%b %Y}, no action"),
        ),
    ]:
        if _df.height == 0:
            continue
        _x, _y = project(_df["x"].to_numpy(), _df["y"].to_numpy())
        for _r, _px, _py in zip(_df.to_dicts(), _x, _y):
            _age = _r.get("days") if _r["k"] == "open" else None
            _items.append(
                {
                    "x": round(float(_px), 1),
                    "y": round(float(_py), 1),
                    "k": _r["k"],
                    "r": 3.5 + min(_age, 180) / 40 if _age is not None else 3.4,
                    "t": _tip(_r),
                }
            )
    _n_open = area_reqs.filter(pl.col("status") == "open").height
    if focus_topic == VACANCY or not focus_topic:
        _note = f"{_n_open:,} open 311 requests · {area_vac.height:,} vacant buildings ({area_vac['handled'].mean() or 0:.0%} handled)"
        if focus_topic:
            _note = f"{area_vac.height:,} vacant buildings, {area_vac['handled'].mean() or 0:.0%} rehabbed or torn down since 2023"
    else:
        _fast = (area_reqs["status"] == "fast").mean() if area_reqs.height else 0
        _note = f"{area_reqs.height:,} {focus_topic.lower()} reports · {_n_open:,} still open · {_fast:.0%} closed within {fix_days.value} days"
    triage_widget.points = {"area": selected_area, "note": _note, "items": _items}
    return area_reqs, area_vac


@app.cell
def _(alt, mo, pl, robust):
    _top = robust.head(15)
    _order = _top["csa"].to_list()
    _colors = alt.Scale(domain=["Robust", "Weight sensitive", "Rarely top 10"], range=["#dd6b20", "#a0a0a0", "#d0d0d0"])
    _bars = alt.Chart(_top).mark_rule(strokeWidth=3).encode(
        y=alt.Y("csa:N", sort=_order, title=None),
        x=alt.X("best_rank:Q", title="Gap rank across 2,000 weightings (5th to 95th percentile)", scale=alt.Scale(domain=[1, 40])),
        x2="worst_rank:Q",
        color=alt.Color("verdict:N", scale=_colors, legend=alt.Legend(orient="bottom", title=None)),
    )
    _dots = alt.Chart(_top).mark_circle(size=70, color="#333").encode(
        y=alt.Y("csa:N", sort=_order),
        x="median_rank:Q",
        tooltip=[
            alt.Tooltip("csa:N", title="Area"),
            alt.Tooltip("top10_share:Q", title="In top 10", format=".0%"),
            alt.Tooltip("median_rank:Q", title="Median rank"),
        ],
    )
    _cut = alt.Chart().mark_rule(strokeDash=[4, 4], color="#888").encode(x=alt.datum(10.5))
    robust_chart = (_bars + _dots + _cut).properties(
        width=520, height=15 * 22, title="Orange bars stay in the top 10 no matter how you weigh the topics"
    )
    robust_table = mo.ui.table(
        _top.select(
            pl.col("csa").alias("Area"),
            pl.col("verdict").alias("Verdict"),
            (pl.col("top10_share") * 100).round(0).cast(pl.Int64).alias("% of weightings in top 10"),
            pl.col("median_rank").alias("Median rank"),
        ),
        selection=None,
        show_column_summaries=False,
    )
    return robust_chart, robust_table


@app.cell
def _(DOMAINS_311, VACANCY, pl):
    def find_quiet_areas(domain_scores, areas):
        """Compare inspector-recorded vacancy with how much residents report to 311.

        Areas in the top third for vacancy but the bottom half for reporting are flagged
        `quiet_but_bad`: their 311-based need scores are probably too low. (Violent crime per
        resident is shown for context only: it inflates areas where few people live but many visit.)
        """
        return (
            domain_scores.filter(pl.col("domain").is_in(list(DOMAINS_311)))
            .group_by("csa")
            .agg(pl.col("n_reports").sum())
            .join(areas.select("csa", "pop", "violent_crime_rate"), on="csa")
            .join(
                domain_scores.filter(pl.col("domain") == VACANCY).select("csa", pl.col("need_pct").alias("vacancy_pct")),
                on="csa",
            )
            .with_columns((pl.col("n_reports") / pl.col("pop") * 1000).alias("reports_per_1k"))
            .with_columns(((pl.col("reports_per_1k").rank() - 1) / (pl.len() - 1)).alias("reporting_pct"))
            .with_columns(((pl.col("vacancy_pct") >= 2 / 3) & (pl.col("reporting_pct") <= 1 / 2)).alias("quiet_but_bad"))
        )
    return (find_quiet_areas,)


@app.cell
def _(VACANCY_SINCE, datetime, pl, timedelta):
    _short_address = pl.col("address").str.replace(r",\s*Baltimore.*$", "")

    def area_requests(requests_311, csa, *, snapshot_ts, window_days, fix_days, topic=None):
        """One area's resident 311 reports in the time window, labeled open / slow / fast, with days open."""
        _end = datetime.fromisoformat(snapshot_ts)
        _start = _end - timedelta(days=window_days) if window_days else datetime(1900, 1, 1)
        _r = requests_311.filter((pl.col("csa") == csa) & ~pl.col("proactive") & (pl.col("created") >= _start))
        if topic:
            _r = _r.filter(pl.col("domain") == topic)
        return _r.with_columns(
            pl.when(pl.col("closed").is_null()).then(pl.lit("open"))
            .when(pl.col("closed") - pl.col("created") <= pl.duration(days=fix_days)).then(pl.lit("fast"))
            .otherwise(pl.lit("slow"))
            .alias("status"),
            (pl.coalesce("closed", pl.lit(_end)) - pl.col("created")).dt.total_days().alias("days"),
            _short_address,
        )

    def area_vacancy(housing, csa):
        """One area's vacant buildings, one row per parcel, matching the vacancy score:
        `handled` = got a rehab permit or demolition since VACANCY_SINCE."""
        _is_notice = pl.col("kind") == "open_notice"
        return (
            housing.filter(
                (pl.col("csa") == csa)
                & pl.col("blocklot").is_not_null()
                & (_is_notice | (pl.col("date") >= datetime.fromisoformat(VACANCY_SINCE)))
            )
            .sort("date", descending=True)
            .group_by("blocklot")
            .agg(
                pl.col("x", "y").first(),
                _short_address.first(),
                (~_is_notice).any().alias("handled"),
                pl.col("date").filter(_is_notice).min().alias("notice_date"),
                pl.col("kind").filter(~_is_notice).first().replace({"rehab": "rehab permit", "demolition": "demolished"}).alias("action"),
                pl.col("date").filter(~_is_notice).first().alias("action_date"),
            )
        )
    return area_requests, area_vacancy


@app.cell
def _(alt, areas, domain_scores, find_quiet_areas, mo, pl):
    _reports = find_quiet_areas(domain_scores, areas)
    _dots = (
        alt.Chart(_reports)
        .mark_circle(size=90, stroke="#333", strokeWidth=0.4)
        .encode(
            x=alt.X("vacancy_pct:Q", title="Vacancy, from inspectors' notices (percentile) →", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            y=alt.Y("reporting_pct:Q", title="Resident 311 reports per person (percentile) →", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            color=alt.condition("datum.quiet_but_bad", alt.value("#dd6b20"), alt.value("#bbbbbb")),
            tooltip=[
                alt.Tooltip("csa:N", title="Area"),
                alt.Tooltip("reports_per_1k:Q", title="311 reports per 1,000", format=".0f"),
                alt.Tooltip("violent_crime_rate:Q", title="Violent crime per 1,000", format=".1f"),
                alt.Tooltip("vacancy_pct:Q", title="Vacancy percentile", format=".0%"),
            ],
        )
    )
    _zone = alt.Chart(alt.Data(values=[{"x": 2 / 3, "x2": 1, "y": 0, "y2": 0.5}])).mark_rect(opacity=0.08, color="#dd6b20").encode(
        x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q"
    )
    undercount_chart = (_zone + _dots).properties(
        width=420, height=320, title="Orange dots: many vacant houses, but few residents calling 311"
    )
    _flagged = _reports.filter(pl.col("quiet_but_bad")).sort("vacancy_pct", descending=True)
    if _flagged.height:
        _names = ", ".join(f"**{n}**" for n in _flagged["csa"])
        undercount_note = mo.md(
            f"{_flagged.height} areas fall in the shaded corner: {_names}. Their 311-based need scores are "
            "probably too low, so their true gap is likely wider than the map shows."
        )
    else:
        undercount_note = mo.md("No area falls in the shaded corner with the current settings.")
    return undercount_chart, undercount_note


@app.cell
def _(mo, overall, robust, pl, fix_days, window, per):
    _csv = (
        overall.join(robust.select("csa", "top10_share", "verdict"), on="csa", how="left")
        .select(
            pl.col("rank").alias("gap_rank"),
            pl.col("csa").alias("area"),
            pl.col("gap").round(3),
            pl.col("need").round(3).alias("need_percentile"),
            pl.col("service").round(3).alias("service_percentile"),
            "widest_gaps",
            (pl.col("top10_share") * 100).round(0).alias("pct_of_weightings_in_top10"),
            "verdict",
        )
        .write_csv()
    )
    dispatch_download = mo.download(
        data=_csv.encode("utf-8"),
        filename="baltimore_triage_dispatch.csv",
        mimetype="text/csv",
        label=f"Download dispatch list (CSV) · clock horizon = {fix_days.value} days · {window.selected_key} · 311 need per 1,000 {'residents' if per.value == 'pop' else 'parcels'}",
    )
    return (dispatch_download,)


@app.cell
def _(VACANCY, alt, default_scores, mo, neglect_residual, pl, spearman):
    _v = default_scores.filter(pl.col("domain") == VACANCY).with_columns(
        ((pl.col("old_service_per_parcel").rank() - 1) / (pl.len() - 1)).alias("old_service_pct")
    )
    _r_old = spearman(_v["need_rate"], _v["old_service_per_parcel"])
    _r_new = spearman(_v["need_rate"], _v["service_rate"])
    _v = _v.with_columns(
        neglect_residual("old_service_pct").alias("gap_old"),
    ).with_columns(
        pl.col("gap_old").rank(descending=True, method="min").alias("rank_old"),
        pl.col("gap").rank(descending=True, method="min").alias("rank_new"),
    )
    _top5 = _v.sort("need_rate", descending=True).head(5)
    method_check_stats = {
        "r_old": _r_old,
        "r_new": _r_new,
        "top5_rank_old": float(_top5["rank_old"].mean()),
        "top5_rank_new": float(_top5["rank_new"].mean()),
    }
    _long = pl.concat(
        [
            _v.select("csa", "need_pct", pl.col("old_service_pct").alias("service_pct"), pl.lit("Old: rehabs + demolitions per 1,000 parcels").alias("measure")),
            _v.select("csa", "need_pct", "service_pct", pl.lit("New: share of vacant buildings handled").alias("measure")),
        ]
    )
    _chart = (
        alt.Chart(_long)
        .mark_circle(size=50, color="#555")
        .encode(
            x=alt.X("need_pct:Q", title="Vacancy need (percentile)", axis=alt.Axis(format=".0%")),
            y=alt.Y("service_pct:Q", title="Vacancy service (percentile)", axis=alt.Axis(format=".0%")),
            tooltip=["csa:N"],
        )
        .properties(width=260, height=220)
        .facet(column=alt.Column("measure:N", title=None))
        .properties(title="Old measure: service rises with need, so the gap cancels itself. New measure: it doesn't.")
    )
    _rows = "\n".join(
        f"| {r['csa']} | {r['rank_old']} | {r['rank_new']} |" for r in _top5.to_dicts()
    )
    method_check = mo.vstack(
        [
            mo.md(f"""
            Areas with more vacant houses get more demolitions and rehabs **just because they have more
            vacant houses**. If service were "demolitions per 1,000 parcels," the worst areas would look
            well served for being bad, and their gap would shrink.

            - Old way: need and service move together (rank correlation **{_r_old:+.2f}**).
            - New way (share of vacant buildings that got a rehab permit or were torn down): **{_r_new:+.2f}**.
              Areas with more vacancy get a *smaller* share handled. The city's response does not keep up.

            The 5 areas with the most vacancy, ranked by vacancy gap (1 = widest):

            | Area | Rank, old measure | Rank, new measure |
            | --- | --- | --- |
            {_rows}

            The same rule holds for every topic. 311 service is how long that topic's requests stay
            open: the share of the first week already closed, read off the same Fix Clock the map
            ranks. Proactive work is proactive tickets **per resident report**. Neither grows just
            because an area has more problems.
            """),
            _chart,
        ]
    )
    return method_check, method_check_stats


@app.cell
def _(
    DEFAULT_FIX_DAYS,
    ROBUST_SHARE,
    areas,
    default_overall,
    default_robust,
    default_scores,
    find_quiet_areas,
    method_check_stats,
    pl,
):
    _robust = default_robust.filter(pl.col("verdict") == "Robust")["csa"].to_list()
    _m = method_check_stats
    _lights = default_scores.filter((pl.col("domain") == "Streetlights") & pl.col("service_rate").is_not_null()).sort("service_rate")
    _worst, _best = _lights.head(1).to_dicts()[0], _lights.tail(1).to_dicts()[0]
    _quiet = find_quiet_areas(default_scores, areas).filter(pl.col("quiet_but_bad"))
    _top = default_overall.head(1).to_dicts()[0]
    _n = len(_robust)
    _robust_text = (
        f"{_n} {'area stays' if _n == 1 else 'areas stay'} in the top 10 under at least {ROBUST_SHARE:.0%} of "
        f"2,000 random topic weightings: **{', '.join(_robust)}**."
        if _n
        else f"No area stays in the top 10 under {ROBUST_SHARE:.0%} of random weightings, so weights really matter here."
    )
    _quiet_text = (
        "**" + ", ".join(_quiet["csa"]) + f"** {'has' if _quiet.height == 1 else 'have'} many vacant houses "
        "but few 311 calls, so the map probably understates their need."
        if _quiet.height
        else ""
    )
    insights = f"""
    All numbers use the default settings (equal weights, all of 2026, clock horizon = {DEFAULT_FIX_DAYS} days).

    1. **A short list holds up no matter what you weigh.** {_robust_text} The #1 gap under equal weights is
       **{_top["csa"]}** (widest topics: {_top["widest_gaps"]}). *See the robust top 10 chart.*

    2. **The usual way of measuring service hides the worst vacancy.** Counting rehabs and demolitions per
       parcel, need and service move almost in lockstep (rank correlation {_m["r_old"]:+.2f}), and the 5
       highest-vacancy areas sit at an average vacancy-gap rank of {_m["top5_rank_old"]:.0f}. Measured as the
       share of vacant buildings handled, they move to {_m["top5_rank_new"]:.0f}: the more vacancy an area
       has, the *smaller* the share the city gets to. *See "Why service is a share of need" in the Data overview.*

    3. **How long a fix takes depends on where you live.** Streetlight service (share of the first
       {DEFAULT_FIX_DAYS} days already closed, same clock as the map) ranges from
       {_worst["service_rate"]:.0%} in **{_worst["csa"]}** to {_best["service_rate"]:.0%} in **{_best["csa"]}**.
       {_quiet_text} *See the Gap Card and "These may be worse than they look."*
    """
    return (insights,)


if __name__ == "__main__":
    app.run()
