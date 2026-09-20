# Feature plan: does leaving things broken cause harm?

HopHacks 2026 · a proposed addition to `script.py` · 2026-09-19

Run `uv run scripts/neglect_probe.py` to reproduce every number below.

## The short version

**Yes, we can build it, and the data is already there.** But the answer is not the one the question
expects, and that is what makes it worth building.

We asked the question three ways — neglect against crime, neglect against crashes, and neglect
against every other kind of neglect — and got the same structural answer every time. The
correlations are large and confident. They are also **contradictory in sign, and strongest exactly
where no mechanism can exist.**

The headline number from the full sweep: leaving a dirty alley unfixed is followed by **+0.633 more
potholes** reported within 150 m, at 7.8 sigma. It is the single strongest result in the entire
matrix — stronger than dumping, stronger than rats. A dirty alley cannot open a pothole.

So the feature is not a correlation. It is **a panel that shows a reader how to not be fooled by
one**, and it now generalises past crime to the whole class of question.

## What we found

### 1. Crime: the area-level correlation is real, large, and useless

Slow service (share of reports *not* closed within 7 days) against night-time outdoor street crime
per 1,000 residents, across the 55 CSAs. Controls are rank-residual partial correlations.

| Topic | Naive | Controlling vacancy | + density + reporting rate |
| --- | ---: | ---: | ---: |
| Streetlights | −0.07 | −0.15 | −0.13 |
| Potholes | −0.46 | −0.41 | −0.42 |
| Roads | −0.42 | −0.28 | −0.28 |
| Illegal dumping | +0.15 | +0.20 | +0.18 |
| Dirty streets & alleys | **+0.58** | +0.35 | +0.34 |
| Rats | +0.25 | +0.42 | +0.39 |
| Graffiti | +0.39 | +0.41 | **+0.60** |
| Trees | +0.43 | +0.45 | +0.44 |
| *Vacancy % (a condition, not a service speed)* | *+0.52* | — | *+0.34* |

Read down the first column. These are not noise around zero: several are strong. They are also
mutually contradictory. Street cleaning says neglect is deadly; potholes say neglect is protective;
streetlights — the one topic with a randomized trial behind it — say nothing.

What they track is **what kind of neighbourhood you are standing in**. Dense rowhouse areas file
alley and rat complaints and have more street crime. Car-owning, lower-density areas file pothole
and road complaints and have less. The correlation is a map of Baltimore's housing stock wearing a
crime label. Controls shrink some of it and leave plenty behind — graffiti gets *stronger*, which is
a tell, not a discovery.

### 2. At the scale where the mechanism would have to work, there is nothing

If darkness causes crime, it causes it **near the dark light, while it is dark**. Tested directly on
6,209 real streetlight reports filed in 2026:

- Each report gets the count of night-time outdoor street crimes within *R* metres in the *W* days
  **before** it was filed, and the *W* days **after**.
- Reports still open after *W* days are the **dark** arm (n = 1,730 at W = 28). Reports closed
  inside a week are the **lit** arm (n = 3,555).
- The estimate is the difference in differences. Every fixed thing about the location cancels.

| Window | Radius | Night crime DiD | Daytime placebo |
| --- | --- | ---: | ---: |
| ±28 d | 100 m | −0.028 (1.6σ) | +0.020 (0.9σ) |
| ±28 d | 200 m | −0.001 (0.0σ) | +0.054 (1.2σ) |
| ±28 d | 400 m | +0.124 (1.7σ) | +0.090 (1.0σ) |
| ±56 d | 100 m | +0.030 (1.1σ) | +0.108 (2.7σ) |
| ±56 d | 200 m | +0.058 (1.0σ) | +0.283 (3.5σ) |
| ±56 d | 400 m | +0.524 (4.0σ) | **+0.960 (5.8σ)** |

At tight settings the effect is zero. At loose ones it looks significant — **and the placebo is
bigger**. Daytime crime, which no streetlight can touch, moves 5.8σ where night crime moves 4.0σ.

### 3. Potholes and crashes: the data does not exist

Checked properly, and the answer is no, not on this timeline:

| Source | Why it fails |
| --- | --- |
| MDOT SHA `NonFatalCrashes` | 2016–2019 only, and **0 rows in Baltimore City** — state highways only |
| MDOT SHA fatal crash layers | Fatalities only; far too few per area to estimate anything |
| `Motor_Vehicle_Crashes` on the city's own org | 276 rows, and the schema is an inspection table mislabelled |
| Maryland Open Data (Socrata) | No statewide crash dataset published there any more |
| `Crash_Data_2019_2024_Baltimore` and similar | Consultant-authored static layers, not authoritative open data |

Even the best of these ends in 2019. Our 311 window is 2026, so a correlation would run backwards in
time — the same flaw that ruled out BNIA's 2023 crime rate as an outcome.

Worth noting for Future work: this is the one test where the *right* design needs no join at all.
Maryland crash records carry `LIGHT` (including dark-with-no-street-lighting), `SURF_COND`,
`ROAD_COND` and `CONTRIB_V1` — the crash report states whether a road defect or an unlit street
contributed. With a current, city-covering crash extract you would read the answer straight off the
incident record instead of inferring it from repair backlogs. That extract is not open data today.

### 4. Every other pair fails the same way

The same DiD design, run over all 9 × 9 topic pairs: leaving X open 28+ days versus fixing it inside
a week, change in Y reports within 150 m. Most pairs have **no possible mechanism**, so the matrix
carries its own placebos.

| Cause left open | → Potholes | → Illegal dumping | → Rats | → Roads | → Streetlights |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dirty streets & alleys | **+0.633 (7.8σ)** | +0.202 (5.9σ) | +0.160 (4.4σ) | +0.133 (4.9σ) | +0.275 (3.0σ) |
| Streetlights | −0.328 (−5.8σ) | +0.022 (1.1σ) | −0.018 (−0.8σ) | −0.029 (−1.5σ) | −0.516 (−4.6σ) |
| Potholes | +0.593 (1.8σ) | +0.038 (1.1σ) | +0.089 (1.8σ) | −0.015 (−0.2σ) | +0.303 (3.1σ) |
| Trees | +0.014 (0.3σ) | +0.034 (1.9σ) | −0.000 (0.0σ) | +0.049 (3.0σ) | +0.011 (0.3σ) |

Two things to read off it.

**The no-mechanism cells are the biggest.** Dirty alley → pothole at 7.8σ beats dirty alley → rats
(4.4σ), which is the one pair here with a real physical story. Dirty alley → *flooding* comes out
significantly **negative** (−3.1σ). On significance alone, nothing here is a mechanism.

**The sign is set by the cause, not the mechanism.** Every streetlight row is negative, across
outcomes that have nothing to do with each other. Every dirty-alley row is positive. That is the
signature of a selection effect, not nine separate causal stories.

### 4b. Distance decay separates them, a little

Significance is the wrong test, because a wider circle catches more reports and sigma climbs with
it for any constant effect. The right test is **where** the effect sits. A mechanism is local:
rubbish breeds rats beside it, not four blocks away. So we split the DiD into rings — 0–50 m,
50–150 m, 150–400 m — and divide each by its area, giving reports per hectare.

This changes the ranking completely. The two headline significant pairs turn out to be **flat**:

| Pair | 0–50 m | 50–150 m | 150–400 m | decay |
| --- | ---: | ---: | ---: | ---: |
| Dirty alley → Potholes *(no mechanism, 7.8σ)* | +0.1321 | +0.0842 | +0.0853 | 1.5× |
| Streetlights → Potholes *(no mechanism, −5.8σ)* | −0.0527 | −0.0456 | −0.0496 | 1.1× |
| **Dirty alley → Rats** *(direct mechanism, 4.4σ)* | **+0.0361** | +0.0209 | +0.0143 | **2.5×** |

Flat density means the whole neighbourhood is drifting. Decaying density is what a mechanism looks
like. So the biggest numbers in the matrix are the emptiest, and dirty alley → rats — which
significance ranked sixth — is the one that behaves correctly.

**But decay alone still is not evidence.** Reports of anything cluster in space, so every pair from
a given cause inherits some inner-ring excess for free. The benchmark is not 1.0, it is how sharply
that same cause decays against outcomes it **cannot** produce. Against that bar dirty alley → rats
clears by very little — 2.5× against a placebo median of 2.2× — and dirty alley → **Roads**, which
is impossible, decays *more sharply* at 3.5×.

So the verdict on the pair we most wanted to be real: it is the only direct-mechanism pair in the
matrix that clears its own placebo baseline, and the margin is too thin to call it a finding. It is
the best candidate here, and it is not proof. Full table in `pair_review.md`.

The explanation is structural, and it is worth stating plainly because it applies to any dashboard
built on 311: **a request left open is not a random draw.** It is selected on something happening at
that location. Regress anything on open-versus-closed and it moves — including outcomes that cannot
possibly be caused.

Four topics could not be tested at all, which is its own finding about the city: **Roads** almost
never closes fast (2,104 left open, 61 fixed fast), **Graffiti** and **Rats** almost always do
(0 and 1 left open). No contrast, no comparison.

### 5. What does hold up

Vacancy — an **observed condition**, not a response time — tracks night street crime at +0.52, and
+0.34 after density and reporting rate. It is the one relationship here coherent across
specifications, and the one with a citywide randomized trial behind it (Branas et al. 2018, already
cited in the notebook).

**If you want to use this tool for public safety, the lever is the vacant-building backlog, not
repair turnaround.**

## The data

One new source, 9 datasets to 10.

| Field | Value |
| --- | --- |
| Layer | `NIBRS_GroupA_Crime_Data`, same ArcGIS org as the 311 layer |
| URL | `.../services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/NIBRS_GroupA_Crime_Data/FeatureServer/0` |
| Coverage | 2022-01-01 → 2026-09-16, 272,242 incidents; 38,981 in 2026 |
| Fields used | `CrimeDateTime`, `Inside_Outside`, `Description`, geometry |
| Placed in a CSA | 38,948 of 38,977 with a point |

Three things this gives us that BNIA's `viol23` cannot, all load-bearing:

- **A timestamp**, so night separates from day. That is the placebo.
- **`Inside_Outside`**, so only outdoor crime counts. A streetlight has no bearing on what happens
  in a kitchen, and 62% of incidents are indoors.
- **Points and dates aligned with our 311 window**, so a before/after test is possible at all.

Two traps found while checking it, both handled in `scripts/neglect_probe.py`:

- `CrimeDateTime` is a true instant in UTC. Read raw it puts Baltimore's small hours in the
  afternoon. Converted to `America/New_York` the hour histogram troughs at 04:00–07:00, which is
  what crime data should look like.
- 2.5% of incidents are stamped exactly 00:00, the unknown-time placeholder. Left in they pile into
  the night bucket and inflate every night number. We drop them.

**Cross-check:** our 2026 outdoor crime rate agrees with BNIA's 2023 violent crime rate at rank
correlation **+0.87**. Two independent sources, three years apart. This becomes a row in the
existing data-quality panel.

## What gets built

A new section, **"Does neglect cause harm?"**, placed after the undercounted panel and before
*Insight synthesis*. Four beats, one chart each.

**Beat 1 — the correlation, and the trap.** A topic dropdown over a scatter: slow service on x,
night outdoor street crime per 1,000 on y, one dot per area, fitted line, correlation in the title.
Every widget in this notebook has to change a conclusion; this one **changes the sign of the
conclusion**, which no other control here does. Beside it, a lollipop of all eight topics, naive
against controlled, so the contradiction is visible at once.

**Beat 2 — go to the right scale.** The streetlight DiD as dots with error bars: night crime and
the daytime placebo side by side across the six window/radius settings. Two controls let a reader
walk from the honest null at 100 m out to the flattering number at 400 m, and watch the placebo
overtake it. Title states the finding: *the placebo moves more than the effect.*

**Beat 3 — the same trap, nine topics wide, and one survivor.** A 9 × 9 heatmap of the pair matrix, diverging palette
centred at zero, sigma on hover, the no-mechanism cells outlined. One click puts any cell in Beat 2's
before/after view. This is the beat that turns a result about streetlights into a result about the
method, and it needs **no new data at all** — it runs off the 311 snapshot already committed.

**Beat 4 — what survives.** Vacancy against night crime, the Branas citation, one line on what it
means for the dispatch list. Crime stays out of the gap score. It was already out, for a reason the
notebook asserted in prose; now that reason is demonstrated.

### Cells and reuse

All new cells, appended in their own block, so this does not collide with dashboard work in flight.

| Cell | Contents | Reuses |
| --- | --- | --- |
| Constants | `CRIME_SINCE`, `NIGHT_FROM/TO`, `STREET_CRIMES`, `DID_WINDOWS`, `DID_RADII` | new cell, not the shared one |
| `LAYERS` | one entry, `"nibrs"` (`"crime"` is taken by the BNIA layer) | existing cell, 1 line |
| `build_crime_snapshot(data_dir)` | download → place in areas → local time → `data/crime.parquet` | `arcgis_query`, `fetch_rows`, `assign_area` |
| Guard + load | builds only the crime file if absent, leaves the 311/housing snapshot alone | pattern of the existing loader cell |
| `crime_area_stats` | per-area night/day counts, per-topic slow service, naive and partial correlations | `spearman`, `MIN_REQUESTS` |
| `partial_spearman` | rank-residual partial correlation | new, 6 lines, sits beside `spearman` |
| `outage_did` | the streetlight DiD, `mo.cache`d | `shapely.STRtree` |
| `topic_pair_did` | the 9 × 9 matrix, `mo.cache`d | same helper, no new data |
| 4 chart cells + 2 markdown cells | the beats above | Altair conventions, `OVER`/`UNDER` palette |

Every function in `scripts/neglect_probe.py` is written to be lifted into the notebook as-is.

**Do not rebuild the whole snapshot.** Give crime its own file and its own guard. A full rebuild
pulls fresher 311 data and silently moves every number already written in the prose, hours before
submission.

### Checks to add

- Crime rate cross-check against BNIA, +0.87 ≥ 0.8 — one row in the existing quality panel.
- Every incident used has a point and lands in one of the 55 areas.
- Night share of outdoor crime is between 0 and 1 in every area.
- A DiD cell is shown only where both arms clear 100 reports, so the four degenerate topics render
  as "no contrast to measure" rather than as noise.
- The placebo is reported **every time** the estimate is, in the same chart. Never one alone.

## Scope

| Tier | Work | Cut if behind |
| --- | --- | --- |
| **Must** | Beat 3, the 9 × 9 matrix | never — it needs no download and carries the whole argument |
| **Should** | crime snapshot + Beat 1 | the argument survives on 311 alone |
| **Should** | Beat 2, the streetlight DiD with its placebo | folds into Beat 3 as one highlighted row |
| **Nice** | Beat 4, quality-panel row, data-overview row | one markdown line |

Beat 3 is roughly 60 minutes and has no download risk, which is why it now leads. Beats 1 and 2 are
about 90 minutes each including the crime fetch. The probe script holds working code for all three.

## Risks, stated plainly

**It reports a null.** Deliberately. The alternative is publishing +0.58 for street cleaning and
letting a reader conclude that late trash pickup causes assaults, which the pothole row (−0.46)
disproves on the same page. A dashboard that shows its own favourite finding failing a placebo test
is a stronger submission than one more choropleth, and it is the only version we can defend when a
judge pushes.

**It is still observational.** The DiD handles fixed features of a place, not a place whose
trajectory was already changing. We say so, and the placebo is the evidence that this matters rather
than a caveat in a footnote.

**Nine months is short.** 5,476 night outdoor incidents citywide in 2026. Widening to 2022 tightens
the intervals but breaks alignment with the 311 window. Not worth it before the deadline; a line in
Future work.

**Crime data carries harm.** Area level only, as the notebook already commits to for block-level
distress scores. No block-level crime map, no demographic fields — `Race`, `Gender`, `Age` and
`Ethnicity` are in the layer and we do not download them.

## How this scores

- **Creativity & impact (20%).** A dashboard that refuses to draw the correlation it could easily
  draw, and shows the reader why. Judges have not seen that.
- **Interactivity (20%).** A control that flips the sign of a finding is the strongest possible
  answer to "does every widget change a conclusion?"
- **Storytelling (30%).** Four beats, one chart each, every title stating its claim. The placebo
  chart is the most quotable image in the submission.
- **Agentic tooling (10%).** A log entry that writes itself: asked whether neglect drives crime, the
  probe found a strong correlation and the placebo killed it; asked the same of potholes and
  crashes, the probe found the data does not exist; asked it of all 81 topic pairs, the strongest
  result in the matrix was one with no possible mechanism. Checked before a line of notebook code
  was written.
