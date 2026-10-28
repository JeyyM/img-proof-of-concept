"""Strength check on the Commons account screen recording.

The download is already an AV1 file, so the scores are against that file,
not against a camera original. Coarse CRF steps only: 28, 32, 36, 40, 44.
Scene-cut is off and the GOP is longer than the clip. This file is not
part of the locked study.
"""

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
DETECT = ROOT / "src" / "detect.exe"
VIDEO = HERE / "commons-account.webm"
WIDTH, HEIGHT = 1920, 1080
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)


def run(args, cwd=None):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def detect():
    ffmpeg = subprocess.Popen(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(VIDEO),
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    proc = subprocess.run(
        [str(DETECT), str(WIDTH), str(HEIGHT), "-"],
        stdin=ffmpeg.stdout,
        capture_output=True,
        text=True,
    )
    ffmpeg.stdout.close()
    ffmpeg.wait()
    if proc.returncode not in (0, 1):
        raise SystemExit(proc.stderr)
    cuts = []
    in_run = False
    quiet = 0
    pairs = 0
    for line in proc.stdout.splitlines()[1:]:
        frame_s, _sad, above_s = line.split(",")
        pairs += 1
        above = int(above_s) == 1
        if above and not in_run:
            cuts.append(int(frame_s))
            in_run = True
        elif not above:
            quiet += 1
            in_run = False
    return pairs + 1, quiet, cuts


def regions(nframes, cuts):
    bounds = [0, *cuts, nframes]
    rows = []
    for start, end in zip(bounds, bounds[1:]):
        if end - start <= 8:
            continue
        sample = tuple(range(start + 8, min(start + 16, end)))
        if len(sample) < 8:
            continue
        rows.append({"start": start, "end": end - 1, "sample": sample})
    return rows


def even_frames(nframes):
    return [math.floor((index + 0.5) * nframes / 8) for index in range(8)]


def encode(crf):
    dest = HERE / "encodes" / f"crf{crf}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    print(f"encode uniform {crf}", flush=True)
    run(
        [
            "-i",
            str(VIDEO),
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
            "20000",
            "-keyint_min",
            "20000",
            "-sc_threshold",
            "0",
            str(dest),
        ]
    )
    return dest


def encode_zones(spans):
    dest = HERE / "zoned.mp4"
    if dest.exists():
        return dest
    zone = "/".join(f"{span['start']},{span['end']},crf={span['crf']}" for span in spans)
    print(f"encode zones ({len(spans)} pictures)", flush=True)
    run(
        [
            "-i",
            str(VIDEO),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(spans[0]["crf"]),
            "-pix_fmt",
            "yuv420p",
            "-g",
            "20000",
            "-keyint_min",
            "20000",
            "-sc_threshold",
            "0",
            "-x264-params",
            f"zones={zone}",
            str(dest),
        ]
    )
    return dest


def score(distorted, name):
    log_path = HERE / "scores" / f"{name}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        print(f"score {name}", flush=True)
        run(
            [
                "-i",
                str(distorted),
                "-i",
                str(VIDEO),
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
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    frames = sorted(payload["frames"], key=lambda row: row["frameNum"])
    return [float(row["metrics"]["vmaf"]) for row in frames]


def vmin(scores, frames):
    return min(scores[frame] for frame in frames)


def choose(cache, frames):
    legal = [crf for crf in sorted(cache) if vmin(cache[crf], frames) >= TARGET]
    if not legal:
        return min(cache)
    return max(legal)


def file_score(scores):
    ordered = sorted(scores)
    k = max(1, math.ceil(0.01 * len(scores)))
    return ordered[k - 1], k, ordered.index(ordered[k - 1]) if False else None


def main():
    nframes, quiet, cuts = detect()
    quiet_pct = 100.0 * quiet / (nframes - 1)
    spans = regions(nframes, cuts)
    spread = even_frames(nframes)
    print(
        f"frames {nframes} quiet {quiet_pct:.1f}% cuts {len(cuts)} settled {len(spans)}",
        flush=True,
    )
    print(f"spread frames {spread}", flush=True)
    print(f"first settled sample {spans[0]['sample']}", flush=True)

    cache = {}
    for crf in COARSE:
        cache[crf] = score(encode(crf), f"crf{crf}")
        if all(vmin(cache[crf], span["sample"]) >= TARGET for span in spans) and vmin(
            cache[crf], spread
        ) >= TARGET:
            continue

    for span in spans:
        span["crf"] = choose(cache, span["sample"])

    # Short visits keep the previous picture's strength.
    zoned_spans = []
    for index, span in enumerate(spans):
        nxt = spans[index + 1]["start"] - 1 if index + 1 < len(spans) else nframes - 1
        zoned_spans.append({"start": span["start"], "end": nxt, "crf": span["crf"]})

    spread_crf = choose(cache, spread)
    settled_crf = choose(cache, spans[0]["sample"])
    zoned = encode_zones(zoned_spans)
    zoned_scores = score(zoned, "zoned")

    counts = {}
    below = 0
    for span in spans:
        counts[span["crf"]] = counts.get(span["crf"], 0) + 1
        if vmin(zoned_scores, span["sample"]) < TARGET:
            below += 1

    def report(label, crf, scores):
        vote_spread = vmin(scores, spread)
        vote_first = vmin(scores, spans[0]["sample"])
        ordered = sorted(scores)
        k = max(1, math.ceil(0.01 * len(scores)))
        worst = ordered[k - 1]
        frame = scores.index(ordered[k - 1])
        size = (HERE / "encodes" / f"crf{crf}.mp4").stat().st_size
        return (
            f"{label}: CRF {crf}, spread vote {vote_spread:.2f}, "
            f"first-page vote {vote_first:.2f}, {k}th-worst {worst:.2f} at frame {frame}, "
            f"{size} bytes"
        )

    lines = [
        "Source: Wikimedia Commons, CC BY-SA 4.0.",
        "File: How to create a Wikimedia Commons account, screen recording tutorial.",
        "Already AV1 at about 1080 kb/s, 1920x1080, 60 fps, 3 minutes. Scores use that file as the reference.",
        f"Quiet pairs: {quiet_pct:.1f}%. Cuts: {len(cuts)}. Pictures long enough to sample: {len(spans)}.",
        "Eight frames is about 0.13 s at 60 fps.",
        report("Spread check, one strength", spread_crf, cache[spread_crf]),
        report("First settled page, one strength", settled_crf, cache[settled_crf]),
        f"Per picture: " + ", ".join(f"CRF {crf} on {counts[crf]} pictures" for crf in sorted(counts)),
        f"Zoned file: {zoned.stat().st_size} bytes. Settled samples under 90 after zoning: {below} of {len(spans)}.",
    ]
    ordered = sorted(zoned_scores)
    k = max(1, math.ceil(0.01 * len(zoned_scores)))
    lines.append(
        f"Zoned {k}th-worst {ordered[k - 1]:.2f} at frame {zoned_scores.index(ordered[k - 1])}."
    )
    text = "\n".join(lines) + "\n"
    (HERE / "result.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
