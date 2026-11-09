"""Playback copies for the 18 practice clips, so the viewer does not encode on first open."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clips"))
import build_clips

CACHE = ROOT / "ui" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

for number in range(1, 19):
    reference = ROOT / "clips" / f"{number:02d}.mkv"
    dest = CACHE / f"clips-{number:02d}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        print(f"have {dest.name}", flush=True)
        continue
    if not reference.exists():
        raise SystemExit(f"missing {reference}")
    print(f"build {dest.name}", flush=True)
    build_clips.run(
        [
            "-i", str(reference),
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "0",
            "-pix_fmt", "yuv420p",
            "-g", "999",
            "-keyint_min", "999",
            "-sc_threshold", "0",
            str(dest),
        ]
    )
    print(f"done {dest.name} {dest.stat().st_size}", flush=True)
