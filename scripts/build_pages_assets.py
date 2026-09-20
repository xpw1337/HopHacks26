"""Prepare browser-served snapshot and media files for the marimo WASM build."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from shapely import geometry, set_precision


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data"
TARGET = ROOT / "public" / "data"


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)

    for name in ("requests_311.parquet", "housing.parquet", "snapshot_meta.json"):
        shutil.copy2(SOURCE / name, TARGET / name)
    if (SOURCE / "precomputed").exists():
        shutil.copytree(
            SOURCE / "precomputed",
            TARGET / "precomputed",
            dirs_exist_ok=True,
        )

    areas = json.loads((SOURCE / "areas.geojson").read_text(encoding="utf-8"))
    for feature in areas["features"]:
        shape = set_precision(
            geometry.shape(feature["geometry"]).simplify(1e-4, preserve_topology=True),
            1e-5,
        )
        feature["geometry"] = geometry.mapping(shape)
    (TARGET / "areas.geojson").write_text(
        json.dumps(areas, separators=(",", ":")),
        encoding="utf-8",
    )

    demo_target = TARGET / "demo_call"
    demo_target.mkdir(exist_ok=True)
    for source in (SOURCE / "demo_call").iterdir():
        if source.suffix in {".mp3", ".json"}:
            shutil.copy2(source, demo_target / source.name)

    (ROOT / "public" / ".nojekyll").touch()
    print(f"Prepared GitHub Pages assets in {TARGET}")


if __name__ == "__main__":
    main()
