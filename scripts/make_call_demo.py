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
import shutil
import subprocess
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

# The unison sequence. One caller sets the scene, then the same sentence comes back in several
# voices at once. The chorus is assembled in the browser at geographically staggered offsets, so
# these stay separate files rather than being mixed here.
STORM_ORIGIN = "Westport/Mount Winans/Lakeland"
STORM_PREMISE = (
    "Hi... yeah, hi. My name's Denise. I'm over in Westport, just off Annapolis Road. "
    "I've called about this before, honestly."
)
STORM_ISSUE = "The streetlights on my block have been out. Three weeks now."

# Documented public ElevenLabs voices, kept distinct so the chorus sounds like a crowd.
CHORUS_VOICES = [
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "AZnzlk1XvdvUeBnXmlld",  # Domi
    "EXAVITQu4vr4xnSDxMaL",  # Bella
    "ErXwobaYiN019PkySvjV",  # Antoni
    "TxGEqnHWrfWFTfGW9XjX",  # Josh
]

# 96 kbps mono keeps speech clean. 48 kbps saved space but put a fizz on every sibilant, which read
# as "robotic" far more than the model choice did.
MP3_BITRATE = "96k"

# Eleven v3 is markedly more expressive than multilingual_v2 for short conversational lines.
MODEL_ID = "eleven_v3"


def read_api_key():
    """Environment first, then a private file, so the key never has to be typed into a shell."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key.strip()
    env_file = Path.home() / ".config" / "elevenlabs.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "ELEVENLABS_API_KEY":
                return value.strip().strip("'\"")
    return None


def compress(path):
    """Down to mono at a low bitrate, if ffmpeg is around. Skipped quietly when it is not."""
    if not shutil.which("ffmpeg"):
        return
    tmp = path.with_suffix(".tmp.mp3")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
           "-ac", "1", "-b:a", MP3_BITRATE, str(tmp)]
    if subprocess.run(cmd, check=False).returncode == 0 and tmp.exists():
        before, after = path.stat().st_size, tmp.stat().st_size
        tmp.replace(path)
        print(f"  compressed {before // 1024} KB -> {after // 1024} KB")
    elif tmp.exists():
        tmp.unlink()


SFX_URL = "https://api.elevenlabs.io/v1/sound-generation"
MUSIC_URL = "https://api.elevenlabs.io/v1/music"

# Sound design, generated rather than sourced. A real ring beats a synthesised one, and the
# underscore is what turns a chart animation into something you sit through.
SFX = {
    "sfx_ring": ("an old telephone ringing twice, dry close recording, no room", 3.5),
    "sfx_burst": ("a deep sub impact with a short upward whoosh, cinematic transition", 2.0),
}
MUSIC_PROMPT = (
    "Tense minimal underscore for a documentary. Slow pulse, low strings, sparse piano, "
    "no drums, no melody, restrained and patient, building very slightly."
)
MUSIC_MS = 22000


def post_audio(client, api_key, url, payload, label):
    """Shared POST for the non-speech endpoints, with the same never-raise contract."""
    try:
        r = client.post(url, headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
                        json=payload, timeout=240)
        r.raise_for_status()
        return r.content
    except httpx.HTTPStatusError as e:
        print(f"  {label}: ElevenLabs returned {e.response.status_code}: {e.response.text[:200].strip()}")
    except httpx.HTTPError as e:
        print(f"  {label}: request failed: {type(e).__name__}: {e}")
    return None


def make_sound_design(client, api_key, force):
    """Sound effects and one music bed. Skipped silently if the account cannot reach them."""
    made = 0
    for stem, (prompt, secs) in SFX.items():
        path = OUT_DIR / f"{stem}.mp3"
        if path.exists() and not force:
            print(f"{path.name}: already present, skipping")
            made += 1
            continue
        print(f"{path.name}: generating sound effect")
        mp3 = post_audio(client, api_key, SFX_URL,
                         {"text": prompt, "duration_seconds": secs, "prompt_influence": 0.6}, stem)
        if mp3:
            path.write_bytes(mp3)
            compress(path)
            made += 1

    path = OUT_DIR / "sfx_bed.mp3"
    if path.exists() and not force:
        print(f"{path.name}: already present, skipping")
        return made + 1
    print(f"{path.name}: generating {MUSIC_MS // 1000}s underscore")
    mp3 = post_audio(client, api_key, MUSIC_URL,
                     {"prompt": MUSIC_PROMPT, "music_length_ms": MUSIC_MS}, "sfx_bed")
    if mp3:
        path.write_bytes(mp3)
        compress(path)
        made += 1
    return made


def make_storm(client, api_key, force):
    """premise.mp3 plus one issue clip per chorus voice."""
    wanted = [("premise", STORM_PREMISE, CHORUS_VOICES[0])]
    wanted += [(f"issue_{i}", STORM_ISSUE, v) for i, v in enumerate(CHORUS_VOICES, start=1)]
    made = 0
    for stem, text, voice in wanted:
        path = OUT_DIR / f"{stem}.mp3"
        if path.exists() and not force:
            print(f"{path.name}: already present, skipping (use --force to regenerate)")
            made += 1
            continue
        print(f"{path.name}: synthesizing with voice {voice}")
        mp3 = synthesize(client, api_key, voice, text)
        if mp3:
            path.write_bytes(mp3)
            compress(path)
            made += 1
    return made


def validate(calls):
    """Fail loudly here rather than shipping a call the notebook cannot join."""
    known = {f["properties"]["csa"] for f in json.loads(AREAS.read_text())["features"]}
    bad_csa = sorted({c["csa"] for c in calls} - known)
    bad_domain = sorted({c["domain"] for c in calls} - DOMAINS)
    if bad_csa or bad_domain:
        sys.exit(f"invalid demo calls -- unknown csa: {bad_csa}, unknown domain: {bad_domain}")


def synthesize(client, api_key, voice_id, text):
    """Return mp3 bytes, or None with a readable message if ElevenLabs refuses.

    Low stability is what stops this sounding like a station announcement: the default keeps the
    delivery flat, and these are meant to be people who are fed up rather than a narrator.
    """
    try:
        r = client.post(
            TTS_URL.format(voice_id=voice_id),
            headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
            params={"output_format": "mp3_44100_128"},
            json={
                "text": text,
                "model_id": MODEL_ID,
                "voice_settings": {
                    "stability": 0.32,
                    "similarity_boost": 0.75,
                    "style": 0.45,
                    "use_speaker_boost": True,
                },
            },
            timeout=180,
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

    api_key = read_api_key()
    if not api_key:
        print("No API key found. Set ELEVENLABS_API_KEY, or put it in ~/.config/elevenlabs.env.")
        print("Writing transcript.json only, skipping audio -- the notebook plays silent without it.")

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
                    compress(path)
                    audio = name
            records.append({"id": i, **call, "audio": audio})
        if api_key:
            print(f"unison sequence: {make_storm(client, api_key, args.force)} clips ready")
            print(f"sound design: {make_sound_design(client, api_key, args.force)} assets ready")
    finally:
        if client:
            client.close()

    # Rewritten every run so the transcript always matches CALLS.
    (OUT_DIR / "transcript.json").write_text(
        json.dumps([{k: r[k] for k in ("id", "text", "domain", "csa", "address", "audio")} for r in records], indent=2)
    )
    print(f"wrote {OUT_DIR / 'transcript.json'} ({len(records)} calls, "
          f"{sum(r['audio'] is not None for r in records)} with audio)")
    total = sum(f.stat().st_size for f in OUT_DIR.glob("*.mp3"))
    if total:
        print(f"audio on disk: {total // 1024} KB across {len(list(OUT_DIR.glob('*.mp3')))} files")


if __name__ == "__main__":
    main()
