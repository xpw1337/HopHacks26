# Agent log

Raw notes for the "Agentic tool usage" reflection (10% of the grade). Add an entry whenever an AI tool helps, gets something wrong, or teaches us something. Keep it short and specific.

Format: **date · tool · task** → what happened → how we checked → lesson.

---

**2026-09-19 · Claude Code · review old `prelim_script.py`**
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
