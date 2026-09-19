# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx==0.28.1",
# ]
# ///
"""Generate the cached voice-intake demo assets for the notebook.

Run by hand, never imported: the notebook makes zero network calls at run time,
so every mp3 and the transcript are baked into data/demo_call/ ahead of time.

    uv run scripts/make_call_demo.py [--voice VOICE_ID] [--force]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
AREAS = ROOT / "data" / "areas.geojson"
OUT_DIR = ROOT / "data" / "demo_call"

# "Rachel", ElevenLabs' documented default public voice.
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"
TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Scripted resident complaints. Each domain must match a notebook 311 domain and
# each csa must be a real CSA name (validated against areas.geojson below).
# Roads is the slowest category in the data, so it carries the demo contrast.
CALLS = [
    {
        "text": (
            "Hi, I'm calling about the streetlights on my block. Three of them on North Fulton "
            "have been out for weeks and it is pitch black by the time people walk home from the bus."
        ),
        "domain": "Streetlights",
        "csa": "Sandtown-Winchester/Harlem Park",
        "address": "1700 N Fulton Ave",
    },
    {
        "text": (
            "The road outside my house is falling apart. The whole stretch is broken up, not just one "
            "pothole, and the school bus has to swing into the other lane to get around it."
        ),
        "domain": "Roads",
        "csa": "Brooklyn/Curtis Bay/Hawkins Point",
        "address": "3900 10th St",
    },
    {
        "text": (
            "Someone dumped a couch, a mattress, and a pile of construction debris in the alley behind "
            "East Chase Street. It has been sitting there since the weekend and the rats are all over it."
        ),
        "domain": "Illegal dumping",
        "csa": "Greenmount East",
        "address": "1800 E Chase St",
    },
]

DOMAINS = {
    "Streetlights", "Potholes", "Roads", "Illegal dumping",
    "Dirty streets & alleys", "Rats", "Graffiti", "Trees", "Flooding",
}


def validate(calls):
    """Fail loudly here rather than shipping a call the notebook cannot join."""
    known = {f["properties"]["csa"] for f in json.loads(AREAS.read_text())["features"]}
    bad_csa = sorted({c["csa"] for c in calls} - known)
    bad_domain = sorted({c["domain"] for c in calls} - DOMAINS)
    if bad_csa or bad_domain:
        sys.exit(f"invalid demo calls -- unknown csa: {bad_csa}, unknown domain: {bad_domain}")


def synthesize(client, api_key, voice_id, text):
    """Return mp3 bytes, or None with a readable message if ElevenLabs refuses."""
    try:
        r = client.post(
            TTS_URL.format(voice_id=voice_id),
            headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            timeout=120,
        )
        r.raise_for_status()
        return r.content
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:300].strip()
        print(f"  ElevenLabs returned {e.response.status_code}: {detail}")
    except httpx.HTTPError as e:
        print(f"  ElevenLabs request failed: {type(e).__name__}: {e}")
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--voice", default=DEFAULT_VOICE, help="ElevenLabs voice id")
    p.add_argument("--force", action="store_true", help="re-synthesize audio that already exists")
    args = p.parse_args()

    validate(CALLS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY not set -- writing transcript.json only, skipping audio.")

    records, client = [], httpx.Client() if api_key else None
    try:
        for i, call in enumerate(CALLS, start=1):
            name = f"call_{i:02d}.mp3"
            path = OUT_DIR / name
            audio = None
            if api_key and path.exists() and not args.force:
                print(f"{name}: already present, skipping (use --force to regenerate)")
                audio = name
            elif api_key:
                print(f"{name}: synthesizing {len(call['text'])} chars")
                mp3 = synthesize(client, api_key, args.voice, call["text"])
                if mp3:
                    path.write_bytes(mp3)
                    audio = name
            records.append({"id": i, **call, "audio": audio})
    finally:
        if client:
            client.close()

    # Rewritten every run so the transcript always matches CALLS.
    (OUT_DIR / "transcript.json").write_text(
        json.dumps([{k: r[k] for k in ("id", "text", "domain", "csa", "address", "audio")} for r in records], indent=2)
    )
    print(f"wrote {OUT_DIR / 'transcript.json'} ({len(records)} calls, "
          f"{sum(r['audio'] is not None for r in records)} with audio)")


if __name__ == "__main__":
    main()
