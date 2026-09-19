# Baltimore Triage: What to Fix Next

HopHacks 2026 · marimo Data Visualization track · 2026-09-19

## Executive summary

Baltimore decides what to fix next by waiting for someone to complain. Housing tracks vacant buildings, Transportation tracks potholes, BGE tracks streetlights, Sanitation tracks trash. Each agency runs its own queue, so no system sees the block that is failing on all four at once, and no system notices the block failing silently because nobody living there calls 311 anymore.

**Baltimore Triage** is a marimo notebook that scores all 55 of Baltimore's Community Statistical Areas on two separate things: how bad conditions are (*need*), and how much the city is already doing about it (*service*). Priority is the **gap** between them. High need with high service means the system is already responding. High need with low service is where the city is absent, and that is where the next dollar should go.

The notebook ships with no opinion about which problem matters most. Officials set the weights themselves with sliders, and the tool reports which areas stay in the top 10 no matter how those sliders are set. That makes the recommendation weight independent, which is the one thing composite-index dashboards almost never do.

**What a judge sees in 30 seconds:** a map of Baltimore colored by neglect gap, sliders that visibly move the ranking, and a short table of the areas that refuse to leave the top 10.

> **What changed while building (2026-09-19).** Where this plan and `script.py` disagree, the code wins.
> - **It's a web app now, not just a notebook.** Run `uvx marimo run --sandbox script.py`: code hidden, hero header, and a sidebar holding the section links and all the controls, which stays on screen while you scroll.
> - **We built our own map widget.** marimo can't click Altair maps, so the "Triage Explorer" (anywidget, plain SVG) holds the map and the Gap Card. Click an area to zoom to its streets, where every dot is a real request or vacant building. Click a Gap Card row to color the map by that topic. A **work list** below shows the oldest still-open requests, with addresses and a CSV. `?area=` links open the app on an area.
> - **Settings:** fast fix = **7 days** by default (at 30 days most sanitation topics are ~100% closed everywhere). "Robust" = in the top 10 under **80%** of 2,000 random weightings (at 90% almost nothing qualifies).
> - **Dropped:** geopandas (shapely alone does the point-in-area work), Impact Investment Areas (no usable layer found), pydeck, 911 data.
> - "Quiet but bad" uses **vacancy only**. Violent crime per resident is extreme where few people live, which flagged Downtown and Harbor East.

## Rubric checklist (how we get scored)

Source: `dsai_marimo_track_guideline_for_hackers.pdf`. Check every box before submitting.

### 1. Creativity & Impact (20%)
- [ ] **Fresh angle:** we map the *gap* (need minus service), not just need. Say this in the first screen.
- [ ] **Fresh angle:** the `Proactive` 311 flag as a "is the city looking?" signal. Nobody else uses it this way.
- [ ] **Fresh angle:** the "quiet but bad" panel (areas that stopped calling 311).
- [ ] **Beyond summarizing:** a new chart type (Gap Card) and a robust top 10 that holds under any weights.
- [ ] **Related work:** a short "What others found" box that we build on (see Problem statement section of the notebook).
- [ ] **Real-world use:** the dispatch CSV an official can take to a meeting.
- [ ] **Many datasets:** show a line in the data overview: "8 Open Baltimore datasets, joined by parcel and location."

### 2. Storytelling & Visual Design (30%, the biggest)
- [ ] **Section headings use the rubric's exact words:** Executive summary, Problem statement, Data overview, Core visualization, Insight synthesis, Discussion / Future work. Judges tick these off.
- [ ] **5-minute read:** the answer is on the first screen. Detail (data checks, method math) goes inside `mo.accordion` so it is there but not in the way.
- [ ] **Cells build on each other:** load → clean → score → chart → findings. No cell jumps ahead.
- [ ] **Every chart title states the finding**, not the axes ("East Baltimore has the widest gaps", not "Gap by CSA").
- [ ] **Color:** one diverging palette for gap (centered at 0), one sequential for size, category colors only for topics. Colorblind-safe.
- [ ] **Marks fit the data:** map for places, dots for need-vs-service, dumbbells for gaps, bars for counts. No pie charts.
- [ ] **Typography:** one font, clear size steps (title / section / body / caption). Numbers right-aligned in tables.
- [ ] **Clear images:** check every chart at laptop width. No overlapping labels.
- [ ] **Invite exploration:** one line above the controls: "Move a slider. Watch the map change. Click an area."

### 3. Code Quality (20%)
- [ ] **One file runs alone.** All loader code lives in the notebook, not a separate module. PEP 723 header with pinned versions.
- [ ] **Works offline.** A parquet snapshot of all data ships with the repo. The notebook reads it first. Only the live banner calls the API, and if that fails it shows "live data unavailable" instead of crashing.
- [ ] **No errors, ever.** Errors = disqualified. Run a fresh clean run before submitting (see Block 7).
- [ ] **Clean code:** short functions, one-line docstring each, clear names, no dead or commented-out code, no leftover debug prints.
- [ ] **Visible checks:** the data-quality panel (row counts, nulls, no area lost in joins).

### 4. Interactivity & UX (20%)
- [ ] **Every widget changes a conclusion.** No decorative controls. Each one answers a question:
  - Topic weight sliders → "does the top 10 change if I care more about vacancy?"
  - "Closed within X days" slider → "what counts as a fast response?"
  - Time window → "is this recent or long-running?"
  - Map click → "what is going on in this area?"
- [ ] **Uses the reactive model fully:** map click drives the Gap Card, scatter and table. Gap Card click filters the map back. Say this out loud in the text.
- [ ] **Custom widget:** the Gap Card, built with anywidget, JS kept inline in the notebook. Explain in one line why a stock chart can't do it.
- [ ] **Feels fast:** the rank-stability run is cached (`mo.cache`) so sliders don't lag.
- [ ] **marimo feedback section (strongly recommended):** what we liked, what was hard, what we'd ask for. Written from real notes in `marimo_feedback.md`, kept during the build.

### 5. Agentic Tool Usage (10%)
- [ ] **Reflection section** in the notebook: where the AI helped, where it was wrong, how we caught it, what we learned.
- [ ] **Real examples, not general talk.** Pulled from `agent_log.md`, which we fill in as we go, not at the end.
- [ ] **Show the check step:** the 311 type mapping JSON was proposed by an AI and reviewed by hand. Say how many it got wrong.

## Problem statement

Baltimore has a finite repair budget and an effectively infinite list of broken things. Someone has to decide the order. Today that order comes from three places, and all three are flawed.

1. **Complaint volume.** 311 is reactive by design. Neighborhoods that call get served, which means service tracks civic confidence as much as actual condition.
2. **Departmental silos.** Each agency ranks work only within its own domain. Nothing in the city's systems adds a vacancy, an outage and a dumping complaint together into one number.
3. **Political geography.** Allocation by council district spreads money evenly across boundaries that have nothing to do with where conditions are worst.

Three consequences follow.

**Compound neglect is invisible.** A block that is 30% vacant, has had a streetlight dark for four months, and has standing uncollected trash appears in city systems as three unrelated low-priority tickets in three departments. Nowhere does it appear as one urgent problem, even though that combination is exactly what abandonment looks like on the ground.

**Silence reads as satisfaction.** An area with low 311 volume looks healthy in every existing dashboard. It may instead be an area that has stopped believing the city will come. A system driven by complaints will systematically underserve the places that have given up on it, and it will never detect that it is doing so.

**There is no leverage logic.** A block that is 20% vacant and a block that is 80% vacant are treated as the same kind of problem, although the first can still be saved and the second probably cannot.

The question this dashboard answers: **given everything the city already knows, where does the next dollar do the most good, and which areas are being missed entirely?**

## The core insight: need is not the same as neglect

Almost every civic dashboard maps need. Need maps tell officials what they already know, that East and West Baltimore are struggling. That is a description, not a decision.

So we compute two scores per area instead of one.

**Need** is how bad conditions are: vacancy rate, streetlight outages, illegal dumping, missing tree canopy, road complaints.

**Service** is how well the city responds to that need. It is not how much work the city did.

This matters. Areas with more vacant houses get more demolitions just because they have more vacant houses. If service counted demolitions per 1,000 parcels, the worst areas would look well served for being bad, and their gap would shrink. So every service number is divided by the need it answers, in the same topic:

| Topic | Service measure |
| --- | --- |
| Vacancy | Share of vacant buildings that got a rehab permit |
| Vacancy | Share of vacant buildings that got torn down |
| 311 topics (lights, potholes, dumping, trash, trees, roads, flooding) | Share of that topic's requests closed within X days. Still-open requests count as not closed |
| Trash | Proactive requests divided by all requests, for `SW-Dirty Street` only (the one type with a proactive twin) |

The vacant building count for these shares is open notices plus the ones fixed or torn down in the time window. Using open notices alone would flatter areas that fix a lot, since fixing lowers the open count. The `VBN` to `NoticeNum` link gives us the fixed ones.

**Neglect Gap = need percentile minus service percentile, per topic, then a weighted average across topics.**

Two rules follow from this:

- Every topic in the score needs both a need number and a service number. Crime has no service number (911 data has no response times), so crime is a context layer on the map, not part of the gap.
- Impact Investment Areas are not in the score. The city picks them partly because of need, which is the same overlap problem. They show as an outline on the map.

That single subtraction reorganizes the whole city into four groups:

|  | High service | Low service |
| --- | --- | --- |
| **High need** | Already being worked | **PRIORITY** |
| **Low need** | Over-served | Fine |

The top right cell is the product. It is a much more useful answer than a need map, because it excludes the places where money is already flowing and isolates the places where it is not.

### The proactive flag

While checking the 311 schema we found that Baltimore tags some requests as `Proactive`, meaning a city employee opened the ticket rather than a resident. Sanitation uses it: `SW-Dirty Street` and `SW-Dirty Street Proactive` are separate request types.

That single word is a direct measure of whether the city is **looking** in an area or merely **answering** it. The ratio of proactive to citizen-reported requests per area becomes a service-side signal that owes nothing to how much residents complain, which is exactly what we need to break the reporting-bias problem. The column is sitting in the open data and we have not found any published analysis that uses it this way.

## Data overview

Everything comes from [Open Baltimore](https://data.baltimorecity.gov/). Every count below was verified by querying the live ArcGIS REST endpoints on 19 September 2026, not taken from documentation.

| Dataset | Records | What it gives us | Freshness |
| --- | --- | --- | --- |
| 311 Customer Service Requests | 4,538 filed in the last 2 days; 60,410 since Sep 1 | The backbone. Most domains come from here | **Daily** |
| Vacant Building Notices (open) | 11,512 | Vacancy, with notice dates back to Nov 2004 | Current |
| Rehabs of Vacant Buildings | 12,860 | Service signal. `VBN` joins to `NoticeNum` | Current |
| Completed City Demolitions | 4,280 | Service signal, with start and finish dates | Current |
| Real Property | \~230,000 parcels | The denominator. `VACIND`, `YEAR_BUILD`, `FULLCASH`, `PERMHOME` | Periodic |
| 911 Calls for Service | 2,001,447 in 2025 | Public safety load by priority. No response times, so context layer only, not scored | Daily |
| Receivership, Bid List, Adopt-A-Lot, Foreclosures | in the same DHCD service | Additional city-program presence | Current |
| Impact Investment Areas | polygons | The city's own designated investment geography. Map outline only, not scored | Static |
| Baltimore Tree Inventory | citywide | Canopy and tree condition | Periodic |

### Domains, and the request types behind them

We verified the actual `SRType` strings rather than guessing:

| Domain | Verified SRType values |
| --- | --- |
| Streetlights | `BGE-StLight(s) Out`, `TRM-Street Light Out`, `RP-Street Lighting Repairs` |
| Potholes | `TRM-Pickup Pothole` |
| Illegal dumping | `HCD-Illegal Dumping` |
| Trash and cleanliness | `SW-Mixed Refuse`, `SW-Dirty Street`, `SW-Dirty Street Proactive`, `SW-City Trash Can or Recycling Can Issue` |
| Trees | `FOR-Tree Maintenance`, `FOR-Down Tree`, `FOR-Broken Branch in Tree`, `HCD-Trees and Shrubs` |
| Roads | `TRM-Street Repairs`, `TEC-Street Repair (Misc)`, `TR-Street Cut Issues`, `TRT-Street and Crosswalk Markings` |
| Flooding | `WW-Storm Flooded Street` |
| Homeless services | `MOHS-Homeless Outreach` |

Two things that surprised us and that change the analysis:

**Streetlights have three separate request types across three owners.** Anyone who filters on one of them undercounts outages badly. We union all three. For reference, `BGE-StLight(s) Out` alone holds 6,799 reports, of which **1,303 have no close date**, meaning they are recorded as still dark.

**Homelessness has no true geographic count in open data.** `MOHS-Homeless Outreach` counts *requests for outreach*, not people. We include it as a request-volume layer, label it as such in the notebook, and never present it as a population estimate. Getting this wrong would be the single most misleading thing we could do, so it is called out at the point of use, not buried in a footnote.

### Join keys

`BLOCKLOT` (format `0702 050`, four-digit block plus three-digit lot) links every housing dataset at the parcel level. 311 and 911 carry latitude and longitude, so they join to areas by point in polygon. `VBN` to `NoticeNum` links a rehab permit back to the specific vacancy notice it resolves, which is what makes a genuine lifecycle possible rather than a spatial approximation.

## How the priority score works

### Spatial unit

**Community Statistical Areas (55).** Chosen because census denominators exist for them, city agencies and BNIA already use them, and 55 is few enough to rank and read on one screen. Neighborhoods (278, wildly uneven) are too noisy for a citywide ranking, and blocks (\~13,000) are the drill-down rather than the overview.

### Normalization

Every domain becomes a rate before it becomes a score. **Need** rates use a size denominator: per 1,000 residents, per 1,000 parcels, or per road mile, whichever is honest for that domain. **Service** rates use the need itself as the denominator (rehabs per vacant building, not per 1,000 parcels). Otherwise need leaks into service and the gap cancels itself out. Rates then become **percentile ranks** across the 55 areas, one topic at a time.

Percentiles rather than z-scores or raw values, because the underlying units are incommensurable. There is no defensible exchange rate between a pothole and a vacant house, and pretending otherwise by summing raw counts just lets whichever domain has the biggest numbers silently dominate the index.

### Reporting-bias correction

This is the part that makes the tool defensible, and it is the first thing a knowledgeable judge will probe.

Raw 311 counts measure complaining, not condition. Three mitigations:

1. **Anchor on observed data where it exists.** Vacancy notices are written by inspectors. Crime comes from police records. Canopy comes from the tree inventory. These are observed rather than reported, so they do not inherit complaint bias.
2. **Use the proactive share.** The ratio of city-opened to resident-opened requests measures municipal attention directly, independent of resident behavior.
3. **Estimate reporting propensity per area** from total 311 volume per capita, then flag areas with **low reporting and high observed need** as likely undercounted. These get surfaced in their own panel rather than being allowed to sink quietly down the ranking.

That third step inverts the usual failure mode. In a complaint-driven system, quiet areas disappear. Here, quiet plus visibly bad becomes its own alarm.

### No invented weights

The dashboard does not assert that vacancy matters more than trash. It opens with equal weights and exposes a slider per domain.

Then it does the thing that makes a weighted index trustworthy: **rank-stability analysis.** Sample a large number of weight vectors from a Dirichlet distribution, recompute the ranking for each, and record the distribution of each area's rank.

The output is a short list of areas that land in the top 10 under nearly every reasonable weighting. That claim survives any argument about weights, because it holds for all of them. An area whose rank swings from 3rd to 40th depending on slider positions is reported as **weight sensitive** and explicitly not presented as a robust priority.

This converts the standard weakness of composite indices into the central feature. The tool is not claiming to know the right weights. It is showing which conclusions do not depend on knowing them.

## Tech stack

### Core

- **marimo** for the notebook. Cells form a dependency graph, so moving a slider recomputes only what depends on it. `mo.ui` for controls, `mo.md` for narrative, `mo.stop` to guard cells against half-built state.
- **Python 3.12**
- **polars** for all tabular work, with lazy frames for the large 311 and 911 loads.
- **uv** with PEP 723 inline dependency metadata, run as `marimo edit --sandbox`. One command sets up the environment from the notebook file itself. That is real one-step reproducibility and it is a marimo feature worth showing off.

### Data access

- **httpx** against the ArcGIS REST endpoints, paginating with `resultOffset` (layers cap at 1,000 to 2,000 records per request).
- Loader code inside the notebook itself (not a separate module), so the notebook file runs on its own. An on-disk **parquet snapshot** ships with the repo and is read first. Live query only for the freshness banner, wrapped so a failed call shows "live data unavailable" instead of an error. The snapshot backs every written finding, so the numbers in the prose never drift out of sync with the charts.

### Geospatial

- **shapely** for point-in-polygon joins of 311 and housing records into areas (geopandas turned out to be unnecessary).
- Community Statistical Area boundaries from Open Baltimore.

### Visualization

- **Altair** for the scatter, robust top 10, quiet-areas and method-check charts. (Plan was an Altair choropleth with click selection, but marimo 0.24.2 disables selection on geoshape charts, so the map became our own widget, below.)

### The custom widget: the Gap Card (now inside the "Triage Explorer" map widget)

Built with **anywidget**. For the selected area it draws one row per domain, each row a dumbbell showing the need percentile and the service percentile as two points with the gap drawn between them, sorted widest gap first, diverging color by gap direction.

Why it has to be custom: an official does not need to know that an area scores badly, they need to know **which truck to send**. That requires an ordered gap ranking, compact enough to sit beside the map, that also accepts clicks to filter the map to a single domain. No built-in marimo element and no stock Altair chart does all three in one component.

Stretch goal: a bump chart showing how each area's rank moves across weight scenarios.

### LLM and agentic use

- **SRType taxonomy mapping.** Baltimore has hundreds of request-type strings with agency prefixes. An LLM proposes the mapping from string to domain, we review it by hand, and the result is committed as a checked-in JSON file. The notebook makes **no LLM calls at run time**, which keeps it reproducible and means it cannot fail live in front of a judge.
- **Per-area plain-English briefings** generated ahead of time and cached alongside the data.
- Running notes in `agent_log.md` on where agentic tooling helped and where it was wrong, for the reflection section. Same for marimo in `marimo_feedback.md`. Write entries as they happen, not at the end.

### Quality gates

Assertion cells after every join: row counts before and after, null rates per column, percentiles spanning 0 to 1, and no area silently lost in a spatial join. These render as a visible data-quality panel in the notebook, which doubles as evidence of rigor for the code-quality score.

## What the final product looks like

The track guidelines say judges expect to read a submission in **under five minutes**. So the notebook is ordered to put the payoff on the first screen and keep the rigor available below it, rather than building up to a conclusion nobody scrolls far enough to reach.

Top to bottom:

**1. Header and live banner.** Title, a one-sentence thesis, and a live count pulled at run time: *as of \[timestamp\], N streetlights reported out, M open vacancy notices.* Clearly labelled as live, so nobody mistakes it for the pinned figures used in the prose.

**2. Executive summary.** Four sentences. The claim, the method in one line, the top three priority areas, and the one thing that surprised us.

**3. Problem statement.** Short, with the three-tickets-one-block example, because that example does more work than a paragraph of explanation. Ends with a small **"What others found"** box: 3 or 4 studies we build on, one line each (for example, research showing 311 reporting differs by neighborhood, Chalfin et al. on streetlights and crime, Branas et al. on fixing vacant lots). Check every citation before quoting it.

**4. Data overview.** The source table with record counts, a line saying how many Open Baltimore datasets we join, the data-quality panel (inside an accordion), and the reporting-bias caveat stated plainly rather than hidden.

**5. The control panel.** A weight slider per domain, a "closed within X days" slider, a normalization toggle, and a time-window selector. Placed *above* the map, so the reader understands from the start that the map is theirs to change and not a verdict being handed to them. One line invites them in: *Move a slider. Watch the map change. Click an area.*

**6. Core visualization.** A choropleth of Baltimore's 55 areas, colored by neglect gap on a **diverging** palette centered at zero, so over-served and under-served read as opposite directions instead of merely more and less. Click any area to select it, and every panel below follows.

**7. The Gap Card.** The custom anywidget. Renders for whichever area is selected, ranking domains by gap width. This is the panel that answers *what do we actually send*.

**8. The quadrant scatter.** Need on the x axis, service on the y, one dot per area, quadrant lines drawn, priority quadrant labelled. This single chart explains the entire method at a glance and is probably the most important image in the submission.

**9. The robust top ten.** A table of the areas that stay in the top 10 across nearly all weightings, with each one's rank range. This is the defensible recommendation.

**10. The undercounted panel.** Areas with low reporting and high observed need, under a heading that says what it means: *these may be worse than they look.*

**11. Insight synthesis.** Three findings, each one sentence with the single chart that supports it.

**12. Discussion / Future work.** Limits, misuse risks, and future work, from the section below.

**13. marimo feedback and agentic tooling reflection.** Both are explicitly requested by the rubric, the second worth 10%. Two separate headings so judges can find each one. Built from real notes in `marimo_feedback.md` and `agent_log.md`, with specific examples.

Headings in the notebook use the rubric's exact words (Executive summary, Problem statement, Data overview, Core visualization, Insight synthesis, Discussion / Future work), so a judge can tick them off.

**14. Download.** A dispatch CSV: ranked areas with their widest domain gaps. The artifact an official would actually carry into a meeting, which is the difference between a visualization and a tool.

### Design rules we hold to

One diverging palette for gaps, one sequential palette for magnitudes, categorical color only for domains. Colorblind-safe throughout. The same area ordering in every chart so the eye can track one place across panels. No chart ships without a title that states its claim rather than naming its axes.

Marks match the data: map for places, dots for need vs service, dumbbells for gaps, bars for counts. One font with clear size steps. Numbers right-aligned in tables. Every chart checked at laptop width for overlapping labels.

## Build plan

Blocks rather than clock times, so it survives a late start.

| Block | Hours | Work |
| --- | --- | --- |
| 1 | \~4 | Loader, parquet cache, area boundaries, spatial joins working. Assertion cells. Nothing pretty. If this is not solid, nothing downstream works |
| 2 | \~4 | Domain aggregation, normalization, percentiles. Need and service computed. First ugly choropleth on screen |
| 3 | \~4 | Interactivity: sliders, Altair selection, reactive recompute. Quadrant scatter |
| 4 | \~4 | The Gap Card anywidget. This is the differentiator, so it gets real time rather than leftovers |
| 5 | \~3 | Rank-stability sampling, undercounted panel, dispatch CSV export |
| 6 | \~3 | Narrative. Every markdown section written properly. marimo feedback and agentic reflection sections written from the logs |
| 7 | \~2 | Full clean run in a fresh environment, fix every error, record the demo |
| All | ongoing | Add to `agent_log.md` and `marimo_feedback.md` whenever something notable happens. Two minutes each time |

Two rules about the build table.

**Block 6 is 30% of the grade.** Storytelling and visual design is the single heaviest criterion, heavier than code quality and heavier than interactivity. Writing it in the last twenty minutes is the most common way good hackathon projects lose.

**Block 7 is non-negotiable.** The guidelines state that notebooks with errors are disqualified. A clean run from scratch in a fresh environment is the only way to know, because the notebook you have been editing for 30 hours has state in it that a judge's machine will not.

Block 7 steps:
1. Copy the repo to a new folder. Run `uvx marimo edit --sandbox notebook.py`. Every cell must run with no red errors.
2. Run it again with Wi-Fi off. It must still work from the parquet snapshot.
3. Run `uvx marimo export html --sandbox notebook.py`. It must finish with no errors.
4. Walk the rubric checklist at the top of this file and tick every box.
5. Time a read-through. Under 5 minutes to get the main point.

### What to reuse from `prelim_script.py` (Block 1 to 3)

The old script is a different idea and its file is cut off at the end, so it does not run. Copy only these pieces:

- `SR_311_URL`, the 311 API link.
- `fetch_arcgis_layer`, the paging loop. Fix it first: remove the 15,000 row cap, ask for lat/long, and check for API error replies.
- The ms-to-date parsing in `load_311`.
- The closed / late / days-open logic in `score_categories`. This is the base for the service closure rates.
- `VACANT_URL` (vacancy by `CSA2010`), to cross-check our own vacancy numbers.
- The quadrant chart code (median lines and corner labels), for the need-vs-service scatter.
- Citations Chalfin 2021 (streetlights) and Branas 2018 (vacant lots), for the narrative. Check them before quoting.

Do not reuse: the fake data fallback, its request type names (many are wrong), its regex type matching (crashes on `(BGE F`), its effect sizes as weights, or grouping by `Neighborhood`.

### How we check the service fix works

1. Across the 55 areas, need and service should move together much less than under the old per-parcel measures. If they are still strongly linked, need is still leaking into service.
2. The 5 highest-vacancy areas should rank higher by gap with the new measure than with the old one.
3. Assertion cell: every service share is between 0 and 1, and no area has a service number with zero need behind it.

### Cut order if behind

In this order: the pydeck 3D view, then the bump chart, then rank-stability sampling (fall back to three preset weight scenarios, which keeps the argument intact), then the undercounted panel.

Never cut the narrative, the clean-run check, the Gap Card (the rubric asks for a custom widget), or the marimo feedback and agentic reflection sections (cheap to write, directly scored).

## Honest limits and future work

### What this tool cannot claim

**It does not measure need. It measures recorded need.** Conditions nobody wrote down are invisible to it, and that is a property of the data, not a bug we can engineer away.

**The homeless services layer is not a count of homelessness.** It counts requests for outreach. Treating it as a population figure would be the most misleading thing this project could do, so it is labelled at the point of use.

**It shows association, not causation.** A wide gap does not prove that neglect caused the conditions, or that closing the gap would fix them.

**Percentile ranks compress real differences.** The area at the 99th percentile may be far worse than the one at the 95th, and the map will not show that. Anyone acting on the ranking should look at the underlying rates too.

**Small numbers swing a lot.** An area with only a few requests in a topic can jump from 0% to 100% closed on one ticket. We hide an area's score for a topic when it has fewer than N requests there.

### How it could be misused

A priority ranking can be read backwards, as a license to withdraw service from areas that score *fine*. This tool is for allocating the next dollar, never for justifying a cut, and the notebook says so.

Publishing block-level distress scores could plausibly affect property values and insurance pricing for the people living there. That is why the public view stays at area level and the block view exists as a drill-down for officials rather than as a published map.

### Future work

**A contagion hazard model** to make tipping points empirical instead of assumed. Model, for each property in each year, whether it received a vacancy notice, with the previous year's neighboring vacancies as a predictor. The fitted coefficient gives a real threshold rather than one we picked.

**Survival analysis of time-to-fix**, by domain and area. The obvious approach, averaging how long completed repairs took, is biased toward the ones that got done. Censored methods handle the requests still sitting open, which is where the real story is.

**Owner entity resolution** on Real Property owner names to identify the largest private holders of neglected property. Name variants defeat exact matching, which makes this a genuine entity-resolution problem and one where an LLM is the right tool rather than an ornament.

**A prospective test.** Freeze today's ranking, then check in six months whether the high-gap areas actually received more service.

That last one matters most. A priority tool nobody ever scores is just an opinion with a map attached.
