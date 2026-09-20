# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars==1.44.2",
#     "numpy==2.5.3",
#     "shapely==2.1.2",
#     "httpx==0.28.1",
#     "pyarrow",
# ]
# ///
"""Does leaving something broken cause harm nearby? A feasibility probe, run before writing any
notebook cell.

Usage:  uv run scripts/neglect_probe.py

Reads the committed snapshot in `data/` for 311 and for the area boundaries, downloads BPD NIBRS
Group A crime once into a local cache, and runs four tests:

  1. Area level (55 CSAs): slow service on each topic against night outdoor street crime, naive
     and after controlling for vacancy, density and reporting rate.
  2. Micro level: crime within R metres of a reported streetlight, in the W days before against
     the W days after, for lights left dark against lights fixed inside a week (difference in
     differences).
  3. The same micro test on daytime crime, where darkness cannot be the mechanism. This is the
     placebo: if it moves as much as the night number, the night number is not about darkness.
  4. The same design over every pair of 311 topics: does leaving X open breed Y nearby? Most
     pairs have no possible mechanism, so the matrix carries its own placebos.

The findings are written up in `neglect_plan.md`.
"""

import datetime
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import numpy as np
import polars as pl
import shapely

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / ".neglect_probe_cache.parquet"
NIBRS = ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services"
         "/NIBRS_GroupA_Crime_Data/FeatureServer/0")
CRIME_SINCE = "2025-12-01"  # a month before the 311 window, so January reports have a "before"

# NIBRS Group A descriptions that can plausibly happen on a street, which is the only kind a
# streetlight could bear on. Fraud, shoplifting and the like are excluded.
VIOLENT = ["HOMICIDE", "AGG. ASSAULT", "COMMON ASSAULT", "ROBBERY", "ROBBERY - COMMERCIAL",
           "ROBBERY - CARJACKING", "RAPE"]
STREET = VIOLENT + ["LARCENY", "LARCENY FROM AUTO", "AUTO THEFT",
                    "LARCENY OF MOTOR VEHICLE PARTS OR ACCESSORIES", "VANDALISM"]
NIGHT_FROM, NIGHT_TO = 21, 5  # local hours counted as night
# Metres per degree at Baltimore's latitude. Good to a few centimetres over a city, and it needs
# no projection library.
LAT_M, LON_M = 111_132.0, 111_320.0 * np.cos(np.radians(39.30))


def fetch_crime():
    """Download every Group A incident since CRIME_SINCE, with its point."""
    where = f"CrimeDateTime >= DATE '{CRIME_SINCE}'"
    with httpx.Client(timeout=120) as client:
        total = client.post(f"{NIBRS}/query",
                            data={"f": "json", "where": where, "returnCountOnly": "true"}).json()["count"]

        def page(offset):
            data = client.post(f"{NIBRS}/query", data={
                "f": "json", "where": where,
                "outFields": "CrimeDateTime,Inside_Outside,Description",
                "returnGeometry": "true", "outSR": 4326, "orderByFields": "RowID",
                "resultOffset": offset, "resultRecordCount": 2000}).json()
            return [{**f["attributes"],
                     "x": (f.get("geometry") or {}).get("x"),
                     "y": (f.get("geometry") or {}).get("y")}
                    for f in data["features"]]

        with ThreadPoolExecutor(max_workers=6) as pool:
            rows = [r for chunk in pool.map(page, range(0, total, 2000)) for r in chunk]
    if len(rows) != total:
        raise RuntimeError(f"Expected {total} crime rows, got {len(rows)}")
    print(f"downloaded {len(rows):,} crime incidents since {CRIME_SINCE}")
    return pl.DataFrame(rows, infer_schema_length=None)


def area_shapes():
    """The 55 CSA polygons, prepared for fast point-in-polygon."""
    geo = json.loads((DATA / "areas.geojson").read_text())
    shapes = [(f["properties"]["csa"], shapely.geometry.shape(f["geometry"])) for f in geo["features"]]
    for _, geom in shapes:
        shapely.prepare(geom)
    return shapes, pl.DataFrame([f["properties"] for f in geo["features"]])


def assign_area(x, y, shapes):
    """The area containing each point, or None outside the city."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    out = np.full(len(x), None, dtype=object)
    for name, geom in shapes:
        out[shapely.contains_xy(geom, x, y) & (out == None)] = name  # noqa: E711
    return out


def prepare_crime(raw, shapes):
    """Place incidents in areas, convert to local time, and label night / outdoor / street."""
    raw = raw.filter(pl.col("x").is_not_null())
    raw = raw.with_columns(pl.Series("csa", assign_area(raw["x"], raw["y"], shapes), dtype=pl.String))
    placed = raw.filter(pl.col("csa").is_not_null())
    print(f"placed in a CSA: {placed.height:,} of {raw.height:,}")
    out = placed.with_columns(
        # Stored as a true instant, so it has to be moved to Baltimore time before the hour means
        # anything. Checked: the hour histogram troughs at 04:00-07:00 local, as crime data should.
        pl.from_epoch("CrimeDateTime", time_unit="ms").dt.replace_time_zone("UTC")
        .dt.convert_time_zone("America/New_York").dt.replace_time_zone(None).alias("ts"),
    ).with_columns(pl.col("ts").dt.hour().alias("hour"), pl.col("ts").dt.minute().alias("minute"))
    # Incidents with an unknown time are stamped exactly midnight, which would pile into "night".
    stamped = out.filter((pl.col("hour") == 0) & (pl.col("minute") == 0)).height
    print(f"dropped exact-midnight stamps (unknown time): {stamped:,} ({100 * stamped / out.height:.1f}%)")
    return out.filter(~((pl.col("hour") == 0) & (pl.col("minute") == 0))).with_columns(
        ((pl.col("hour") >= NIGHT_FROM) | (pl.col("hour") < NIGHT_TO)).alias("night"),
        (pl.col("Inside_Outside") == "O").alias("outdoor"),
        pl.col("Description").is_in(STREET).alias("street"),
    )


def ranks(v):
    """Ranks of an array, as floats."""
    return np.asarray(v, dtype=float).argsort().argsort().astype(float)


def spearman(a, b):
    """Rank correlation, ignoring pairs with missing values."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ok = ~(np.isnan(a) | np.isnan(b))
    return float(np.corrcoef(ranks(a[ok]), ranks(b[ok]))[0, 1])


def partial_spearman(a, b, controls):
    """Rank correlation of a and b after regressing both on the ranked controls."""
    cols = [np.asarray(v, dtype=float) for v in [a, b, *controls]]
    ok = ~np.any([np.isnan(v) for v in cols], axis=0)
    r = [ranks(v[ok]) for v in cols]
    design = np.column_stack([np.ones(int(ok.sum()))] + r[2:])
    left, right = (x - design @ np.linalg.lstsq(design, x, rcond=None)[0] for x in r[:2])
    return float(np.corrcoef(left, right)[0, 1])


def area_table(crime, requests, areas):
    """Per-area night crime rate and the confounders any honest comparison has to hold fixed."""
    per_area = crime.group_by("csa").agg(
        (pl.col("outdoor") & pl.col("night") & pl.col("street")).sum().alias("night_crime"),
        (pl.col("outdoor") & ~pl.col("night") & pl.col("street")).sum().alias("day_crime"),
        pl.col("outdoor").sum().alias("outdoor_crime"),
    )
    volume = requests.filter(~pl.col("proactive")).group_by("csa").agg(pl.len().alias("n_311"))
    return (
        areas.select("csa", "pop", "parcels", "bnia_vacant_pct", "violent_crime_rate")
        .join(per_area, on="csa").join(volume, on="csa")
        .with_columns(
            (pl.col("night_crime") / pl.col("pop") * 1000).alias("night_rate"),
            (pl.col("outdoor_crime") / pl.col("pop") * 1000).alias("outdoor_rate"),
            (pl.col("parcels") / pl.col("pop")).alias("parcels_pc"),
            (pl.col("n_311") / pl.col("pop") * 1000).alias("reports_per_1k"),
        )
    )


def topic_service(requests, topic, fix_days=7):
    """Share of an area's reports on one topic closed inside `fix_days`."""
    return (
        requests.filter((pl.col("domain") == topic) & ~pl.col("proactive"))
        .group_by("csa").agg(
            pl.len().alias("n"),
            ((pl.col("closed") - pl.col("created")) <= pl.duration(days=fix_days))
            .fill_null(False).mean().alias("fast"),
        )
    )


def outage_did(crime, requests, end, *, window, radius):
    """Difference in differences around one streetlight report, for night and for daytime crime.

    Each report gets the crime count within `radius` metres in the `window` days before it was
    filed and in the `window` days after. Reports still open at `window` days are the dark arm;
    reports closed inside a week are the lit arm. The daytime run is the placebo.
    """
    lights = requests.filter(
        (pl.col("domain") == "Streetlights") & ~pl.col("proactive") & pl.col("x").is_not_null()
        & (pl.col("created") >= datetime.datetime(2026, 1, 1) + datetime.timedelta(days=window))
        & (pl.col("created") <= end - datetime.timedelta(days=window))
    ).with_columns(
        ((pl.coalesce("closed", pl.lit(end)) - pl.col("created")).dt.total_seconds() / 86400).alias("days_open")
    ).with_columns(
        pl.when(pl.col("days_open") <= 7).then(pl.lit("lit"))
        .when(pl.col("days_open") >= window).then(pl.lit("dark"))
        .otherwise(pl.lit("middle")).alias("arm")
    )
    light_pts = shapely.points(
        np.column_stack([lights["x"].to_numpy() * LON_M, lights["y"].to_numpy() * LAT_M])
    )
    filed = lights["created"].to_numpy().astype("datetime64[s]").astype("int64")
    arm = lights["arm"].to_numpy()

    def change(subset):
        pts = shapely.points(
            np.column_stack([subset["x"].to_numpy() * LON_M, subset["y"].to_numpy() * LAT_M])
        )
        near_light, near_crime = shapely.STRtree(pts).query(light_pts, predicate="dwithin", distance=radius)
        when = subset["ts"].to_numpy().astype("datetime64[s]").astype("int64")
        offset = (when[near_crime] - filed[near_light]) / 86400.0
        before = np.bincount(near_light[(offset >= -window) & (offset < 0)], minlength=lights.height)
        after = np.bincount(near_light[(offset >= 0) & (offset < window)], minlength=lights.height)
        return after - before

    out = {"n_dark": int((arm == "dark").sum()), "n_lit": int((arm == "lit").sum())}
    for label, subset in (
        ("night", crime.filter(pl.col("outdoor") & pl.col("night") & pl.col("street"))),
        ("day", crime.filter(pl.col("outdoor") & ~pl.col("night") & pl.col("street"))),
    ):
        delta = change(subset)
        dark, lit = delta[arm == "dark"], delta[arm == "lit"]
        did = dark.mean() - lit.mean()
        se = float(np.sqrt(dark.var(ddof=1) / len(dark) + lit.var(ddof=1) / len(lit)))
        out[label] = {"did": float(did), "se": se, "sigma": float(did / se)}
    return out


def topic_pair_did(requests, end, *, window, radius, fast_days=7, min_arm=100):
    """The same DiD over every pair of 311 topics: leaving X open, does Y appear nearby?

    Most pairs have no mechanism at all -- a dirty alley cannot open a pothole -- so the matrix
    supplies its own placebos. A cause whose no-mechanism pairs move as much as its plausible ones
    is not measuring a mechanism.
    """
    usable = requests.filter(~pl.col("proactive") & pl.col("x").is_not_null())
    topics = usable["domain"].unique().sort().to_list()
    outcomes = {t: usable.filter(pl.col("domain") == t) for t in topics}
    results = []
    for cause in topics:
        arms = usable.filter(
            (pl.col("domain") == cause)
            & (pl.col("created") >= datetime.datetime(2026, 1, 1) + datetime.timedelta(days=window))
            & (pl.col("created") <= end - datetime.timedelta(days=window))
        ).with_columns(
            ((pl.coalesce("closed", pl.lit(end)) - pl.col("created")).dt.total_seconds() / 86400).alias("open_days")
        ).with_columns(
            pl.when(pl.col("open_days") <= fast_days).then(pl.lit("fast"))
            .when(pl.col("open_days") >= window).then(pl.lit("left"))
            .otherwise(pl.lit("middle")).alias("arm")
        ).filter(pl.col("arm") != "middle")
        arm = arms["arm"].to_numpy()
        n_left, n_fast = int((arm == "left").sum()), int((arm == "fast").sum())
        if min(n_left, n_fast) < min_arm:
            # Roads almost never close fast, graffiti almost always does: no contrast to measure.
            results.append({"cause": cause, "outcome": None, "n_left": n_left, "n_fast": n_fast})
            continue
        cause_pts = shapely.points(
            np.column_stack([arms["x"].to_numpy() * LON_M, arms["y"].to_numpy() * LAT_M])
        )
        filed = arms["created"].to_numpy().astype("datetime64[s]").astype("int64")
        for outcome, subset in outcomes.items():
            pts = shapely.points(
                np.column_stack([subset["x"].to_numpy() * LON_M, subset["y"].to_numpy() * LAT_M])
            )
            near_cause, near_out = shapely.STRtree(pts).query(cause_pts, predicate="dwithin", distance=radius)
            when = subset["created"].to_numpy().astype("datetime64[s]").astype("int64")
            offset = (when[near_out] - filed[near_cause]) / 86400.0
            before = np.bincount(near_cause[(offset >= -window) & (offset < 0)], minlength=arms.height)
            after = np.bincount(near_cause[(offset > 0) & (offset < window)], minlength=arms.height)
            delta = after - before
            left, fast = delta[arm == "left"], delta[arm == "fast"]
            did = left.mean() - fast.mean()
            se = float(np.sqrt(left.var(ddof=1) / len(left) + fast.var(ddof=1) / len(fast)))
            results.append({"cause": cause, "outcome": outcome, "did": float(did), "se": se,
                            "sigma": float(did / se), "n_left": n_left, "n_fast": n_fast})
    return topics, results


# Our own judgement of whether a pair could work physically, written down BEFORE reading the
# numbers so the matrix cannot be re-labelled to fit whatever came out.
#   direct = a physical mechanism anyone would accept
#   weak   = indirect, "broken windows" style
#   none   = no mechanism exists; this pair is a placebo
#   self   = same topic, so repeat reports of the same problem contaminate it
MECHANISM = {
    ("Dirty streets & alleys", "Rats"): "direct",
    ("Dirty streets & alleys", "Illegal dumping"): "weak",
    ("Dirty streets & alleys", "Flooding"): "weak",
    ("Dirty streets & alleys", "Graffiti"): "weak",
    ("Illegal dumping", "Rats"): "direct",
    ("Illegal dumping", "Dirty streets & alleys"): "direct",
    ("Illegal dumping", "Flooding"): "weak",
    ("Illegal dumping", "Graffiti"): "weak",
    ("Flooding", "Potholes"): "direct",
    ("Flooding", "Roads"): "direct",
    ("Trees", "Flooding"): "direct",
    ("Trees", "Roads"): "weak",
    ("Trees", "Potholes"): "weak",
    ("Trees", "Streetlights"): "weak",
    ("Potholes", "Roads"): "weak",
    ("Potholes", "Flooding"): "weak",
    ("Roads", "Potholes"): "weak",
    ("Streetlights", "Illegal dumping"): "weak",
    ("Streetlights", "Graffiti"): "weak",
    ("Rats", "Dirty streets & alleys"): "weak",
}


def emit_pair_review(requests, end, path, *, window=28, radii=(50, 150, 400)):
    """Write every topic pair to a markdown table for review, with a distance-decay test.

    Decay is the column that decides it. A real mechanism is local: rubbish breeds rats beside it,
    not four blocks away, so almost all of the effect should sit in the inner ring. A selection
    effect -- the reports left open sit where reports of everything are rising -- spreads evenly
    over the whole block.

    Comparing sigma between radii will not show this, because a wider circle holds more reports and
    sigma climbs with it for any constant effect. So we compare **density**: the DiD inside each
    ring divided by that ring's area. Local mechanism means the inner ring is denser than the outer
    one; flat density means whatever is happening is happening to the whole neighbourhood.
    """
    per_radius = {r: {(p["cause"], p["outcome"]): p
                      for p in topic_pair_did(requests, end, window=window, radius=r)[1]}
                  for r in radii}
    topics, base = topic_pair_did(requests, end, window=window, radius=radii[1])
    untestable = {p["cause"]: p for p in base if p["outcome"] is None}
    # Ring areas in hectares, so the densities are comparable between rings.
    ring_ha = [np.pi * (radii[0] ** 2) / 10_000]
    ring_ha += [np.pi * (radii[i] ** 2 - radii[i - 1] ** 2) / 10_000 for i in range(1, len(radii))]

    rows = []
    for p in base:
        if p["outcome"] is None:
            continue
        cause, outcome = p["cause"], p["outcome"]
        kind = "self" if cause == outcome else MECHANISM.get((cause, outcome), "none")
        cumulative = [per_radius[r].get((cause, outcome), {}).get("did") for r in radii]
        sigmas = [per_radius[r].get((cause, outcome), {}).get("sigma") for r in radii]
        if any(v is None for v in cumulative):
            continue
        # Cumulative DiD differenced into rings, then divided by each ring's area.
        rings = [cumulative[0]] + [cumulative[i] - cumulative[i - 1] for i in range(1, len(radii))]
        density = [d / a for d, a in zip(rings, ring_ha)]
        # Local when the inner ring is at least twice as dense as the outer, and points the same
        # way. Anything flatter than that is a neighbourhood-wide drift, not a mechanism.
        local = (density[0] * density[-1] > 0) and abs(density[0]) >= 2 * abs(density[-1])
        decay = abs(density[0]) / abs(density[-1]) if density[-1] else float("inf")
        rows.append({"cause": cause, "outcome": outcome, "kind": kind, "did": p["did"],
                     "se": p["se"], "sigma": p["sigma"], "sigmas": sigmas, "density": density,
                     "local": local, "decay": decay, "n_left": p["n_left"], "n_fast": p["n_fast"]})

    # Reports of anything cluster in space, so every pair from a given cause inherits some inner-ring
    # excess that owes nothing to a mechanism. The benchmark for a pair is therefore not 1.0, it is
    # how sharply that same cause decays against outcomes it cannot possibly produce.
    for cause in {r["cause"] for r in rows}:
        placebos = [r["decay"] for r in rows
                    if r["cause"] == cause and r["kind"] == "none" and np.isfinite(r["decay"])]
        baseline = float(np.median(placebos)) if placebos else None
        for r in rows:
            if r["cause"] == cause:
                r["baseline"] = baseline
                r["beats"] = baseline is not None and r["decay"] > baseline
    rows.sort(key=lambda r: -abs(r["sigma"]))

    order = {"direct": 0, "weak": 1, "self": 2, "none": 3}
    lines = [
        "# Every topic pair, for review",
        "",
        f"Generated by `uv run scripts/neglect_probe.py --review`. Window +/-{window} days, "
        f"radii {', '.join(str(r) + ' m' for r in radii)}.",
        "",
        "`DiD` is the change in nearby reports of the outcome after the cause was filed, for causes "
        "left open 28+ days minus causes fixed inside a week, within 150 m. `mechanism` was written "
        "down before the numbers were read.",
        "",
        "The three `ring` columns are the DiD **per hectare** inside 0-50 m, 50-150 m and "
        "150-400 m. A real mechanism is local, so its inner ring should be far denser than its "
        "outer one. Flat or rising density means the whole neighbourhood is drifting and the pair "
        "is measuring selection, not cause. `decay` is inner density over outer.",
        "",
        "`decay` on its own is not enough, because reports of anything cluster in space, so every "
        "pair from a given cause inherits some inner-ring excess for free. `placebo` is the median "
        "decay of that same cause against outcomes it **cannot** produce. A pair is only evidence "
        "of a mechanism if it decays faster than its own cause's placebos -- that is the `beats?` "
        "column, and it is the one to read.",
        "",
        f"{len(rows)} pairs estimable, {81 - len(rows)} not.",
        "",
        "| # | Cause left open | Outcome nearby | mechanism | DiD | SE | sigma | ring 0-50 | 50-150 | 150-400 | decay | placebo | beats? |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for i, r in enumerate(sorted(rows, key=lambda r: (order[r["kind"]], -abs(r["sigma"]))), 1):
        cells = " | ".join(f"{d:+.4f}" for d in r["density"])
        base = "--" if r.get("baseline") is None else f"{r['baseline']:.1f}x"
        beats = "--" if r["kind"] == "none" else ("**yes**" if r.get("beats") else "no")
        lines.append(f"| {i} | {r['cause']} | {r['outcome']} | {r['kind']} | {r['did']:+.3f} | "
                     f"{r['se']:.3f} | {r['sigma']:+.1f} | {cells} | {r['decay']:.1f}x | "
                     f"{base} | {beats} |")
    lines += ["", "## Not estimable", "",
              "| Cause | Left open 28+ d | Fixed inside 7 d | Why |",
              "| --- | ---: | ---: | --- |"]
    for cause, p in sorted(untestable.items()):
        why = "almost nothing closes fast" if p["n_fast"] < 100 else "almost everything closes fast"
        lines.append(f"| {cause} | {p['n_left']:,} | {p['n_fast']:,} | {why} |")
    lines += ["", "## Strongest results, in order", ""]
    for r in rows[:10]:
        lines.append(f"- **{r['cause']} -> {r['outcome']}** ({r['kind']}): "
                     f"{r['did']:+.3f}, {r['sigma']:+.1f} sigma")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path.name}: {len(rows)} estimable pairs, {len(untestable)} causes with no contrast")


def main():
    shapes, areas = area_shapes()
    if CACHE.exists():
        raw = pl.read_parquet(CACHE)
        print(f"using cached crime download ({raw.height:,} rows); delete {CACHE.name} to refresh")
    else:
        raw = fetch_crime()
        raw.write_parquet(CACHE)
    crime = prepare_crime(raw, shapes)
    requests = pl.read_parquet(DATA / "requests_311.parquet")
    meta = json.loads((DATA / "snapshot_meta.json").read_text())
    end = datetime.datetime.fromisoformat(meta["snapshot_ts"])

    table = area_table(crime, requests, areas)
    print(f"\nCross-check: our 2026 outdoor crime rate against BNIA's 2023 violent crime rate, "
          f"rank correlation {spearman(table['violent_crime_rate'], table['outdoor_rate']):+.2f}")

    print("\n=== 1. AREA LEVEL: slow service against night outdoor street crime (55 areas)")
    print(f"{'topic':<26}{'naive':>8}{'| vacancy':>11}{'| vac+dens+reporting':>21}")
    controls_all = [table["bnia_vacant_pct"].to_numpy(), table["parcels_pc"].to_numpy(),
                    table["reports_per_1k"].to_numpy()]
    for topic in ["Streetlights", "Potholes", "Roads", "Illegal dumping",
                  "Dirty streets & alleys", "Rats", "Graffiti", "Trees"]:
        joined = table.join(topic_service(requests, topic), on="csa").filter(pl.col("n") >= 10)
        slow = 1 - joined["fast"].to_numpy()
        night = joined["night_rate"].to_numpy()
        vac = [joined["bnia_vacant_pct"].to_numpy()]
        full = vac + [joined["parcels_pc"].to_numpy(), joined["reports_per_1k"].to_numpy()]
        print(f"{topic:<26}{spearman(slow, night):>+8.2f}{partial_spearman(slow, night, vac):>+11.2f}"
              f"{partial_spearman(slow, night, full):>+21.2f}")
    print(f"\n{'vacancy % (a condition,':<26}{spearman(table['bnia_vacant_pct'], table['night_rate']):>+8.2f}"
          f"{'--':>11}"
          f"{partial_spearman(table['bnia_vacant_pct'], table['night_rate'], controls_all[1:]):>+21.2f}")
    print(f"{' not a service speed)':<26}")

    print("\n=== 2 & 3. MICRO LEVEL: around one reported streetlight, with a daytime placebo")
    for window in (28, 56):
        for radius in (100, 200, 400):
            r = outage_did(crime, requests, end, window=window, radius=radius)
            print(f"  +/-{window:>2}d  {radius:>3}m  dark={r['n_dark']:>4} lit={r['n_lit']:>4}   "
                  f"night {r['night']['did']:+.3f} (SE {r['night']['se']:.3f}, {r['night']['sigma']:+.1f}s)"
                  f"   | placebo {r['day']['did']:+.3f} (SE {r['day']['se']:.3f}, {r['day']['sigma']:+.1f}s)")

    print("\n=== 4. EVERY TOPIC PAIR: leaving X open for 28+ days, do Y reports appear within 150 m?")
    topics, pairs = topic_pair_did(requests, end, window=28, radius=150)
    print(f"{'cause \\ outcome':<24}" + "".join(f"{t[:11]:>14}" for t in topics))
    for cause in topics:
        row = [p for p in pairs if p["cause"] == cause]
        if row and row[0]["outcome"] is None:
            print(f"{cause[:23]:<24}  no contrast to measure "
                  f"(left open {row[0]['n_left']}, fixed fast {row[0]['n_fast']})")
            continue
        by_outcome = {p["outcome"]: p for p in row}
        cells = "".join(f"{by_outcome[t]['did']:>+8.3f}({by_outcome[t]['sigma']:>+4.1f})".rjust(14)
                        for t in topics)
        print(f"{cause[:23]:<24}{cells}   [left={row[0]['n_left']} fast={row[0]['n_fast']}]")
    cross = sorted((p for p in pairs if p["outcome"] and p["cause"] != p["outcome"]),
                   key=lambda p: -abs(p["sigma"]))
    print("\n  Strongest cross-topic results, which is where the mechanisms should be:")
    for p in cross[:6]:
        print(f"    {p['cause']:<24} -> {p['outcome']:<24} "
              f"DiD {p['did']:+.3f} (SE {p['se']:.3f}, {p['sigma']:+.1f} sigma)")


def review():
    """Just the pair table, written to pair_review.md. No crime download needed."""
    requests = pl.read_parquet(DATA / "requests_311.parquet")
    end = datetime.datetime.fromisoformat(
        json.loads((DATA / "snapshot_meta.json").read_text())["snapshot_ts"])
    emit_pair_review(requests, end, ROOT / "pair_review.md")


if __name__ == "__main__":
    review() if "--review" in sys.argv else main()
