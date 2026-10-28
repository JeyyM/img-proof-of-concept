"""Compress the official clip and score every frame.

Coarse rungs are 28, 32, 36, 40, and 44, with scene-cut off. Integer rungs
between the last passing vote and the next failing vote are filled after
those scores exist. If 44 still passes, 48 is added once. The text start
is not moved, and the target stays 90.
"""

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIP = Path(__file__).resolve().parent / "clip"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
REFERENCE = CLIP / "reference.mkv"
ENCODES = CLIP / "encodes"
SCORES = CLIP / "scores"
TOTAL = 900
START = 538
HOLD = 20
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)


def run(args, cwd=None):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def settled_indexes():
    end = START + HOLD
    begin = START + 8
    if begin >= end:
        return ()
    return tuple(range(begin, min(begin + 8, end)))


def encode_file(crf):
    dest = ENCODES / f"crf{crf}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"encode {crf}: exists", flush=True)
        return dest
    print(f"encode {crf}", flush=True)
    run(
        [
            "-i",
            str(REFERENCE),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-g",
            "999",
            "-keyint_min",
            "999",
            "-sc_threshold",
            "0",
            str(dest),
        ]
    )
    return dest


def load_vmaf(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    frames = sorted(payload["frames"], key=lambda row: row["frameNum"])
    scores = [float(row["metrics"]["vmaf"]) for row in frames]
    if len(scores) != TOTAL:
        raise SystemExit(f"{path} has {len(scores)} scores")
    return scores


def nth_worst(scores, n):
    return sorted(enumerate(scores), key=lambda item: item[1])[n - 1]


def score_file(crf):
    log_path = SCORES / f"crf{crf}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    distorted = ENCODES / f"crf{crf}.mp4"
    if not log_path.exists():
        print(f"score {crf}", flush=True)
        run(
            [
                "-i",
                str(distorted),
                "-i",
                str(REFERENCE),
                "-lavfi",
                "[0:v]format=yuv420p,setpts=PTS-STARTPTS[dist];"
                "[1:v]format=yuv420p,setpts=PTS-STARTPTS[ref];"
                f"[dist][ref]libvmaf=log_fmt=json:log_path={log_path.name}:n_subsample=1:n_threads=8",
                "-f",
                "null",
                "-",
            ],
            cwd=log_path.parent,
        )
    else:
        print(f"score {crf}: exists", flush=True)
    scores = load_vmaf(log_path)
    ninth_frame, ninth = nth_worst(scores, 9)
    forty_frame, forty = nth_worst(scores, 45)
    settled = settled_indexes()
    return {
        "crf": crf,
        "bytes": distorted.stat().st_size,
        "spread": min(scores[frame] for frame in EVEN),
        "text": min(scores[i] for i in settled),
        "ninth": ninth,
        "ninth_frame": ninth_frame,
        "fortyfifth": forty,
        "fortyfifth_frame": forty_frame,
        "shortfall": max(0.0, TARGET - ninth),
    }


def measure(crfs, rows):
    have = {row["crf"] for row in rows}
    for crf in crfs:
        if crf in have:
            continue
        encode_file(crf)
        rows.append(score_file(crf))
        have.add(crf)
    rows.sort(key=lambda row: row["crf"])
    return rows


def missing_steps(rows, key):
    ranked = sorted(rows, key=lambda row: row["crf"])
    legal = [row["crf"] for row in ranked if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return []
    best = max(legal)
    higher = [row["crf"] for row in ranked if row["crf"] > best]
    if not higher:
        return []
    return list(range(best + 1, min(higher)))


def choose(rows, key):
    legal = [row for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def write_summary(rows):
    path = SCORES / "summary.csv"
    fields = [
        "crf",
        "bytes",
        "spread",
        "text",
        "ninth",
        "ninth_frame",
        "fortyfifth",
        "fortyfifth_frame",
        "shortfall",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def main():
    if not REFERENCE.exists():
        raise SystemExit(f"missing {REFERENCE}")
    rows = measure(COARSE, [])
    if rows and rows[-1]["spread"] >= TARGET and rows[-1]["text"] >= TARGET:
        print("both votes still pass at the top rung; adding 48 once", flush=True)
        rows = measure((48,), rows)
    extra = sorted(set(missing_steps(rows, "spread") + missing_steps(rows, "text")))
    if extra:
        print(f"fill: {extra}", flush=True)
        rows = measure(extra, rows)
    path = write_summary(rows)
    spread = choose(rows, "spread")
    text = choose(rows, "text")
    print(f"summary: {path}", flush=True)
    for name, row in (("spread", spread), ("text", text)):
        if row is None:
            print(f"{name}: no rung kept the sample at {TARGET}", flush=True)
            continue
        print(
            f"{name}: crf {row['crf']} shortfall {row['shortfall']:.2f} "
            f"ninth {row['ninth']:.2f} frame {row['ninth_frame']} bytes {row['bytes']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
