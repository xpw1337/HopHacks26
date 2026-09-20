# Agent log

Raw notes for the "Agentic tool usage" reflection (10% of the grade). Add an entry whenever an AI tool helps, gets something wrong, or teaches us something. Keep it short and specific.

Format: **date · tool · task** → what happened → how we checked → lesson.

---

**2026-09-19 · Claude Code · review old `prelim_script.py`** (since removed from the repo)
- Found the file is cut off mid-sentence at the end (line 1091), so it can't run.
- Found many guessed 311 type names (e.g. `DOT-Pothole`; the real one is `TRM-Pickup Pothole`).
- Found the type search would crash: one name has an open bracket `(BGE F`, which breaks the regex.
- Checked: by reading the code against the verified type list in `Bmore_plan.md`. Not yet confirmed by running it.
- Lesson: AI-written starter code can look complete and polished while being broken or built on made-up names. Check names against the real data.

**2026-09-19 · Claude Code · need/service overlap**
- A review pointed out that need and service share inputs (vacancy drives demolitions, and 311 counts sit on both sides). So the worst vacancy areas would look well served.
- The agent agreed it was a real problem and rewrote service as "response per unit of need, in the same topic" (e.g. rehabs per vacant building).
- Checked: planned test. Need and service should be much less linked after the fix, and the top-vacancy areas should rise in the ranking.
- Lesson: the flaw was caught by a critical review, not by the tool on its own. Ask the agent to attack the method, not just build it.

**2026-09-19 · Claude Code · writing `script.py` (the notebook)**
- Checked the live APIs before writing code. Found `TRM-Potholes` (12,286 requests), which the plan had missed. It is bigger than the one pothole type listed (`TRM-Pickup Pothole`, 4,715). Also found 4 request types with a `Proactive` twin, not 1.
- Found ~20% of topic requests are "Closed (Duplicate)" or "Closed (Transferred)". Dropped them (17,218 rows) so need isn't inflated.
- Verified the need/service fix on real data: old per-parcel measure correlates +0.94 with need; the new share measure −0.66. The top-5 vacancy areas move from avg vacancy-gap rank 17 to 3.
- Sanity-checked first results and changed two things: (1) "quiet but bad" flagged Downtown/Harbor East because violent crime *per resident* is extreme where few live, so it now uses vacancy only (flags Cherry Hill: lowest 311 reporting, top-third vacancy); (2) at a 30-day "fast fix" cutoff most sanitation topics were ~100% closed everywhere, so the default became 7 days.
- Headless run and HTML export passed, but a real browser test showed the map cell hit marimo's output size limit (1.7 MB boundaries). Fixed by simplifying shapes. Lesson: "runs without errors" is not the same as "works".
- Browser screenshots were often stale, which made early click tests land in the wrong place. Reading the page state with JavaScript confirmed the clicks worked.

**2026-09-19 · Claude Code · turning the notebook into a web app**
- Goal: stop "throwing a notebook at the judges". Same `script.py`, served with `marimo run`: sidebar controls, hero header, custom map explorer that zooms to real requests, work list per area, `?area=` share links.
- Tested the risky parts in a throwaway notebook first: widget updates from another cell, sidebar sliders, jump links, `css_file`. All worked.
- Rebuilt the snapshot to keep each record's point and address. First try rounded coordinates *before* placing points in areas, which pushed 10 edge points outside the city (369 → 379 dropped). Fixed by rounding only when saving. Rebuilt counts match the old snapshot (plus 4 new rehab permits); top area, robust area and the fix check (+0.94 → −0.66) unchanged.
- The Chrome extension wasn't connected, so the agent drove the installed Edge headlessly with Playwright to click through the app.
- Bug found only by that click-through: `mo.nav_menu` links reloaded the whole app once `?area=` was in the URL. Replaced with plain `#section` links.
- Dark mode: the browser's dark setting didn't change marimo's theme, so the first "dark" test was really light. Re-tested with marimo's theme set to dark; fixed a black ring that disappeared on the scatter.
- Lesson: test in the real product, and check the test really tested what you think (the dark-mode test didn't, at first).

**2026-09-19 · Claude Code · rubric check**
- Compared the plan to the judging rubric and added a checklist. Gaps found: no related-work box, headings not matching the rubric's words, the separate loader module hurt "self-contained", and there was no offline test.

**2026-09-19 · Claude Code · "does neglect cause crime?" → the alley/rats section**
- Asked whether slow repairs drive crime. The agent found the data (BPD NIBRS, 2022–2026, with a
  timestamp and an indoor/outdoor flag) and produced a strong answer: slow street cleaning tracks
  night crime at **+0.58** across the 55 areas.
- It then attacked its own result. Slow *potholes* track night crime at **−0.46**: the sign of the
  finding is chosen by whichever topic you pick, so the correlation is measuring neighbourhood type.
  A streetlight-level test (6,209 outages, crime before vs after, dark vs fixed-fast) came out at
  zero, and at the loose settings where it looked significant the **daytime placebo moved more**.
- Potholes vs crashes: checked five sources and found none usable. The only Baltimore crash layer
  ends in 2019 and has **0 rows inside the city** (state highways only).
- Swept all 81 topic pairs. The single strongest result, **dirty alley → pothole at 7.8σ**, is
  impossible. That is the finding: a request left open is not a random draw, so anything regressed
  on open-vs-closed moves.
- Dirty alley → rats survived further, but only after a mistake was caught. Ranking pairs by sigma
  is wrong (a wider circle holds more reports, so sigma climbs with radius for any constant effect).
  Switching to reports **per hectare per ring** reversed the ranking: the 7.8σ pair is flat, rats
  decays.
- Building the chart caught the last problem. The event study showed the two arms were never
  comparable: rat reports near alleys the city leaves open were already **2.3× rarer**, and already
  climbing before the alley was reported. Restricting to alleys that started clean drops the effect
  from +0.16 to **+0.07 (+28%, 2.3σ)** — and makes the decay test cleaner, 4.4× against 2.0×.
- Checked: `uv run scripts/neglect_probe.py` reproduces every number; the notebook's own figures were
  cross-checked against it; our 2026 crime rate agrees with BNIA's 2023 rate at +0.87.
- Lesson: the agent's first answer, its second, and its third were each wrong in a different way, and
  every correction came from a test we asked it to run against itself. Drawing the chart is a test —
  the baseline imbalance was invisible in the summary statistic and obvious the moment it was plotted.
