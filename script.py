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
# ]
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", app_title="Baltimore Triage", css_file="app.css")


@app.cell
def _():
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
    import shapely
    import traitlets
    return (
        Path,
        ThreadPoolExecutor,
        alt,
        anywidget,
        datetime,
        httpx,
        json,
        mo,
        np,
        pl,
        shapely,
        timedelta,
        traitlets,
    )


@app.cell
def _(default_overall, default_robust, mo, requests_311, snapshot_meta):
    _c = snapshot_meta["counts"]
    _open = requests_311.filter(requests_311["closed"].is_null() & ~requests_311["proactive"]).height
    _robust = default_robust.filter(default_robust["verdict"] == "Robust").height
    mo.vstack(
        [
            mo.Html(
                """
                <div class="hero">
                  <p class="hero-eyebrow">Open Baltimore · 55 Community Statistical Areas · 2026</p>
                  <h1>Baltimore Triage: what to fix next</h1>
                  <p class="hero-lede">Most city dashboards show where things are bad. This one shows where things
                  are bad <em>and the city is not responding</em>, down to the street address.</p>
                </div>
                """
            ),
            mo.hstack(
                [
                    mo.stat(f"{_c['requests_311'] + _c['open_notices'] + _c['rehabs'] + _c['demolitions']:,}", label="City records joined", caption="311 + vacant building files", bordered=True),
                    mo.stat(f"{_open:,}", label="Resident requests still open", caption=f"as of {snapshot_meta['snapshot_date']}", bordered=True),
                    mo.stat(default_overall["csa"][0], label="Widest gap, equal weights", caption="#1 of 55 areas", bordered=True),
                    mo.stat(f"{_robust}", label="Robust top-10 areas", caption="hold up under any weighting", bordered=True),
                ],
                widths="equal",
                gap=1,
            ),
        ],
        gap=1,
    )
    return


@app.cell
def _(live_banner):
    live_banner
    return


@app.cell
def _(ROBUST_SHARE, default_robust, method_check_stats, mo, snapshot_meta):
    _robust = default_robust.filter(default_robust["verdict"] == "Robust")["csa"].to_list()
    _names = ", ".join(f"**{n}**" for n in _robust[:3])
    _lead = (
        f"Under at least {ROBUST_SHARE:.0%} of 2,000 random ways to weigh the topics, {_names} "
        f"{'stays' if len(_robust) == 1 else 'stay'} in the top 10."
        if _robust
        else "No single area stays in the top 10 under nearly every weighting, so the ranking depends on your weights."
    )
    _moved_up = method_check_stats["top5_rank_new"] < method_check_stats["top5_rank_old"]
    _surprise = (
        "areas move up the ranking, where they belong."
        if _moved_up
        else "areas get a fairer score."
    )
    mo.md(f"""
    ## Executive summary

    Baltimore decides what to fix next mostly by waiting for complaints. Each agency works its own queue,
    so nobody sees the area that is failing on many fronts at once, or the area that has stopped calling 311.

    We score all 55 Community Statistical Areas on two things: **need** (how bad conditions are) and
    **service** (how well the city responds to that need). The **gap** between them is the priority.
    High need with low service is where the city is missing.

    {_lead} That result does not depend on anyone's opinion about which problem matters most.

    The surprise: counting demolitions and rehabs *per parcel* (the usual way) makes the worst vacancy
    areas look well served, just because they have the most vacant houses. We measure service as a
    share of the need instead, and those {_surprise} *(Data snapshot: {snapshot_meta["snapshot_date"]}.)*
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Problem statement

    Baltimore has a limited repair budget and a very long list of broken things. Today the order of work
    comes from three places, and all three have a blind spot:

    1. **Complaints.** 311 is reactive. Areas that call get served, so service follows who calls, not just what is broken.
    2. **Silos.** Housing, Transportation, BGE and Sanitation each rank only their own work. No one adds them up.
    3. **Politics.** Money split evenly by council district ignores where conditions are worst.

    **One block, three tickets.** A block that is 30% vacant, has a streetlight dark for four months, and has
    trash piling up shows up as three small tickets in three departments. It never shows up as one urgent
    problem, even though that combination is exactly what abandonment looks like.

    **Silence looks like satisfaction.** An area with few 311 calls looks healthy on every dashboard. It may
    instead be an area that stopped believing the city will come.

    **The question this notebook answers:** *given what the city already knows, where does the next dollar
    do the most good, and which areas are being missed?*
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
        ("311 Customer Service Requests (2026)", f'{_c["requests_311"]:,}', "Need (reports) and service (closing speed, proactive tickets)"),
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

    **Be careful with 311.** A 311 count measures *complaining*, not just conditions. Vacancy notices and
    crime reports are written by city staff, so they do not have this problem. We use them to catch areas
    that are bad but quiet (see "These may be worse than they look").

    We removed **{snapshot_meta["dropped"]["duplicate_or_transferred"]:,}** 311 requests marked duplicate or
    transferred, so the same pothole is not counted twice.
    """)
    return


@app.cell
def _(mo, quality_panel, method_check):
    mo.accordion(
        {
            "Data quality checks (click to open)": quality_panel,
            "Why service is a share of need, not a count (click to open)": method_check,
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
def _(explorer):
    explorer
    return


@app.cell
def _(DEFAULT_FIX_DAYS, DOMAIN_ORDER, mo):
    weight_sliders = mo.ui.dictionary(
        {d: mo.ui.slider(0, 3, step=0.5, value=1, show_value=True, full_width=True) for d in DOMAIN_ORDER}
    )
    fix_days = mo.ui.slider(
        1, 60, step=1, value=DEFAULT_FIX_DAYS, show_value=True, label="Counts as a fast fix if closed within (days)"
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
def _(area_reqs, area_vac, focus_topic, mo, pl, selected_area, snapshot_meta, VACANCY):
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
                "Need and service are percentiles *within each topic*, averaged with your weights, so a +0.30 gap "
                "means the area ranks 30 points higher on need than on service."
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

    - **Time-to-fix curves** that follow still-open requests over time, not just a single cutoff.
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

    - **Reactivity made the method honest.** Sliders, the time window and the "fast fix" cutoff all feed
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
    DEFAULT_FIX_DAYS = 7  # at 30 days most sanitation topics are ~100% closed everywhere, so service can't tell areas apart
    ROBUST_SHARE = 0.8  # "robust" = in the top 10 under at least this share of random weightings

    # Colors: blue = over-served, orange = under-served (colorblind-safe pair).
    OVER, MID, UNDER = "#2b6cb0", "#f1f1f1", "#dd6b20"
    return (
        DEFAULT_FIX_DAYS,
        DOMAINS_311,
        DOMAIN_ORDER,
        MID,
        MIN_REQUESTS,
        OVER,
        ROBUST_SHARE,
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
                    "SRType,SRStatus,CreatedDate,CloseDate,Latitude,Longitude,Address",
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
            )
            _sr_in = _sr.filter(pl.col("csa").is_not_null()).select(
                "csa", "domain", "proactive", pl.col("SRType").alias("sr_type"), "created", "closed",
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
    return areas, areas_geo, housing, requests_311, snapshot_meta


@app.cell
def _(DOMAINS_311, LAYERS, live_count, mo, snapshot_meta):
    _lights = ",".join(f"'{t}'" for t in DOMAINS_311["Streetlights"]["reported"])
    _dark = live_count(LAYERS["sr311"], f"SRType IN ({_lights}) AND SRStatus IN ('Open','New')")
    _vbn = live_count(LAYERS["open_notices"], "1=1")
    if _dark is None or _vbn is None:
        live_banner = mo.callout(
            mo.md(
                f"**Live data unavailable right now.** Everything below uses the saved snapshot "
                f"from {snapshot_meta['snapshot_date']}, so the notebook works offline."
            ),
            kind="warn",
        )
    else:
        live_banner = mo.callout(
            mo.md(
                f"**Live right now:** {_dark:,} streetlight reports still open · {_vbn:,} open vacancy notices. "
                f"<small>(The analysis below uses the fixed snapshot from {snapshot_meta['snapshot_date']}, "
                f"so the numbers in the text always match the charts.)</small>"
            ),
            kind="info",
        )
    return (live_banner,)


@app.cell
def _(DOMAINS_311, MIN_REQUESTS, VACANCY, VACANCY_SINCE, datetime, pl, timedelta):
    def pct_rank(col):
        """Percentile rank (0 = lowest, 1 = highest) within each topic, ignoring missing values."""
        _c = pl.col(col)
        return ((_c.rank("average") - 1) / (_c.count() - 1)).over("domain")

    def score_areas(requests_311, housing, areas, *, snapshot_ts, window_days, fix_days, per):
        """Need and service per area and topic, as raw rates and percentiles, plus the gap.

        Service is always a share of need in the same topic (never a count per resident or parcel),
        so an area does not look well served just because it has a lot of problems.
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

        # Service 1: share of reports closed within `fix_days` (still-open ones count as not closed).
        # Only reports old enough to have had the full `fix_days` are counted.
        _fast = (
            _reported.filter(pl.col("created") <= _end - timedelta(days=fix_days))
            .with_columns(
                ((pl.col("closed") - pl.col("created")) <= pl.duration(days=fix_days)).fill_null(False).alias("fast")
            )
            .group_by("csa", "domain")
            .agg(pl.len().alias("n_service"), pl.col("fast").mean().alias("closed_fast_share"))
        )

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

        return (
            pl.concat([_s311, _svac], how="diagonal")
            .with_columns(pct_rank("need_rate").alias("need_pct"), pct_rank("_service_mix").alias("service_pct"))
            .with_columns((pl.col("need_pct") - pl.col("service_pct")).alias("gap"))
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
    return score_areas, summarize


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
    housing,
    rank_stability,
    requests_311,
    score_areas,
    snapshot_meta,
    summarize,
):
    # Fixed default settings: these back every number written in the text, so prose never drifts from charts.
    default_scores = score_areas(
        requests_311, housing, areas,
        snapshot_ts=snapshot_meta["snapshot_ts"], window_days=0, fix_days=DEFAULT_FIX_DAYS, per="pop",
    )
    default_overall = summarize(default_scores, {d: 1 for d in DOMAIN_ORDER})
    default_robust = rank_stability(default_scores)
    return default_overall, default_robust, default_scores


@app.cell
def _(
    areas,
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
    domain_scores = score_areas(
        requests_311, housing, areas,
        snapshot_ts=snapshot_meta["snapshot_ts"],
        window_days=window.value, fix_days=fix_days.value, per=per.value,
    )
    overall = summarize(domain_scores, weight_sliders.value)
    robust = rank_stability(domain_scores)
    return domain_scores, overall, robust


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
              : focus ? `${focus} only: orange areas need more than they get` : "Neglect gap: orange = high need, low service";
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
            if (!card) { $(".tx-card").innerHTML = ""; return; }
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
          $(".tx-back").addEventListener("click", () => zoomTo(null));
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
def _(VACANCY, domain_scores, fix_days, overall, pl, triage_widget):
    def _detail(r):
        _svc = "not enough requests" if r["service_rate"] is None else f"{r['service_rate']:.0%}"
        _svc_label = "handled since 2023" if r["domain"] == VACANCY else f"closed within {fix_days.value} days"
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
    selected_area = explorer.value.get("selected") or default_overall["csa"][0]
    focus_topic = explorer.value.get("focus") or ""
    mo.query_params().set("area", selected_area)
    return focus_topic, selected_area


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
        label=f"Download dispatch list (CSV) · fast fix = {fix_days.value} days · {window.selected_key} · 311 need per 1,000 {'residents' if per.value == 'pop' else 'parcels'}",
    )
    return (dispatch_download,)


@app.cell
def _(VACANCY, alt, default_scores, mo, pl, spearman):
    _v = default_scores.filter(pl.col("domain") == VACANCY).with_columns(
        ((pl.col("old_service_per_parcel").rank() - 1) / (pl.len() - 1)).alias("old_service_pct")
    )
    _r_old = spearman(_v["need_rate"], _v["old_service_per_parcel"])
    _r_new = spearman(_v["need_rate"], _v["service_rate"])
    _v = _v.with_columns(
        (pl.col("need_pct") - pl.col("old_service_pct")).alias("gap_old"),
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

            The same rule holds for every topic. 311 service is the **share** of that topic's requests closed
            in time, and proactive work is proactive tickets **per resident report**. Neither grows just
            because an area has more problems.
            """),
            _chart,
        ]
    )
    return method_check, method_check_stats


@app.cell
def _(DOMAIN_ORDER, VACANCY, areas, default_scores, mo, pl, snapshot_meta, spearman):
    _d = snapshot_meta["dropped"]
    _vac = default_scores.filter(pl.col("domain") == VACANCY).join(areas, on="csa")
    _bnia_r = spearman(_vac["need_rate"], _vac["bnia_vacant_pct"])
    _pct = default_scores.group_by("domain").agg(
        pl.col("need_pct").min().alias("lo"), pl.col("need_pct").max().alias("hi")
    )
    _svc = default_scores.filter(pl.col("service_rate").is_not_null())
    _checks = [
        ("All 55 areas loaded, each with population and parcels", areas.height == 55 and areas.filter((pl.col("pop") > 0) & (pl.col("parcels") > 0)).height == 55),
        ("Every area appears in every topic (none lost in the joins)", default_scores.height == 55 * len(DOMAIN_ORDER)),
        ("Need percentiles span 0 to 1 in every topic", _pct.filter((pl.col("lo") == 0) & (pl.col("hi") == 1)).height == len(DOMAIN_ORDER)),
        ("Every service share is between 0 and 1", _svc.filter(pl.col("service_rate").is_between(0, 1)).height == _svc.height),
        ("No service score without need behind it", _svc.filter(pl.col("n_service") < 1).height == 0),
        (f"Our vacancy rate agrees with BNIA's (rank correlation {_bnia_r:.2f} ≥ 0.8)", _bnia_r >= 0.8),
    ]
    _ok = all(p for _, p in _checks)
    _lines = "\n".join(f"| {'✅' if p else '❌'} | {name} |" for name, p in _checks)
    quality_panel = mo.vstack(
        [
            mo.callout(
                mo.md("**All checks pass.**" if _ok else "**Some checks failed. Read the numbers with care.**"),
                kind="success" if _ok else "danger",
            ),
            mo.md(f"""
            | | Check |
            | --- | --- |
            {_lines}

            **Rows kept and dropped**

            | Step | Rows |
            | --- | --- |
            | 311 requests fetched in our topics | {_d["requests_fetched"]:,} |
            | Dropped: marked duplicate or transferred | {_d["duplicate_or_transferred"]:,} |
            | Dropped: no location, or outside the 55 areas | {_d["requests_outside_areas"]:,} |
            | Housing records dropped: outside the 55 areas | {_d["housing_outside_areas"]:,} |
            | **311 requests used** | **{snapshot_meta["counts"]["requests_311"]:,}** |
            """),
        ]
    )
    return (quality_panel,)


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
    All numbers use the default settings (equal weights, all of 2026, fast fix = {DEFAULT_FIX_DAYS} days).

    1. **A short list holds up no matter what you weigh.** {_robust_text} The #1 gap under equal weights is
       **{_top["csa"]}** (widest topics: {_top["widest_gaps"]}). *See the robust top 10 chart.*

    2. **The usual way of measuring service hides the worst vacancy.** Counting rehabs and demolitions per
       parcel, need and service move almost in lockstep (rank correlation {_m["r_old"]:+.2f}), and the 5
       highest-vacancy areas sit at an average vacancy-gap rank of {_m["top5_rank_old"]:.0f}. Measured as the
       share of vacant buildings handled, they move to {_m["top5_rank_new"]:.0f}: the more vacancy an area
       has, the *smaller* the share the city gets to. *See "Why service is a share of need" in the Data overview.*

    3. **Response speed depends on where you live.** Streetlight reports closed within {DEFAULT_FIX_DAYS} days range from
       {_worst["service_rate"]:.0%} in **{_worst["csa"]}** to {_best["service_rate"]:.0%} in **{_best["csa"]}**.
       {_quiet_text} *See the Gap Card and "These may be worse than they look."*
    """
    return (insights,)


if __name__ == "__main__":
    app.run()
