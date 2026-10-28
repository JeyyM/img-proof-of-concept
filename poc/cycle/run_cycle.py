"""Cycle four pictures every 20 frames and give each visit its own strength.

Order repeats: plain page, dense text, pie chart, gravel. Eleven cycles is
880 frames, about 29 seconds at 30 fps. 900 does not divide evenly by
20 times 4. After each cut the check waits 8 frames and reads the next 8.
Each visit keeps the strongest CRF whose own eight frames still score at
least 90. The clock for x264 is one encode. The brightness-sum clock is
the existing kernel timer, after the frames are in memory.
"""

import csv
import json
import math
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
DETECT = ROOT / "src" / "detect.exe"
TIMER = ROOT / "course" / "build" / "time_kernel.exe"
WIDTH, HEIGHT = 1024, 576
FPS = 30
HOLD = 20
CYCLES = 11
NFRAMES = HOLD * 4 * CYCLES
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)
PICTURES = (
    ("plain", ROOT / "poc" / "plain.png"),
    ("text", ROOT / "poc" / "text.png"),
    ("chart", ROOT / "poc" / "chart" / "plain.png"),
    ("gravel", ROOT / "poc" / "gravel" / "plain.png"),
)
ENCODED = re.compile(r"encoded (\d+) frames, ([0-9.]+) fps")


def run(args, cwd=None, level="error"):
    started = time.perf_counter()
    proc = subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", level, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    wall = time.perf_counter() - started
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-2000:])
    match = ENCODED.search(proc.stderr)
    if match and float(match.group(2)) > 0:
        encode_s = int(match.group(1)) / float(match.group(2))
    else:
        encode_s = wall
    return encode_s, wall


def regions():
    rows = []
    visit = {name: 0 for name, _image in PICTURES}
    for _cycle in range(CYCLES):
        for name, image in PICTURES:
            start = len(rows) * HOLD
            visit[name] += 1
            rows.append(
                {
                    "name": name,
                    "visit": visit[name],
                    "image": image,
                    "start": start,
                    "end": start + HOLD - 1,
                    "sample": tuple(range(start + 8, start + 16)),
                }
            )
    return rows


def build_reference():
    reference = HERE / "reference.mkv"
    if reference.exists():
        return reference
    parts = HERE / "_parts"
    parts.mkdir(exist_ok=True)
    for name, image in PICTURES:
        dest = parts / f"{name}.mkv"
        if dest.exists():
            continue
        run(
            [
                "-loop",
                "1",
                "-framerate",
                str(FPS),
                "-i",
                str(image),
                "-frames:v",
                str(HOLD),
                "-an",
                "-c:v",
                "ffv1",
                "-pix_fmt",
                "yuv444p",
                str(dest),
            ]
        )
    lines = []
    for _cycle in range(CYCLES):
        for name, _image in PICTURES:
            lines.append(f"file '{name}.mkv'\n")
    listing = parts / "list.txt"
    listing.write_text("".join(lines), encoding="utf-8")
    run(
        ["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(reference)],
        cwd=parts,
    )
    return reference


def detect_cuts(reference):
    ffmpeg = subprocess.Popen(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(reference),
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
    for line in proc.stdout.splitlines()[1:]:
        frame_s, _sad, above_s = line.split(",")
        above = int(above_s) == 1
        if above and not in_run:
            cuts.append(int(frame_s))
            in_run = True
        elif not above:
            in_run = False
    mismatches = 0
    for line in proc.stderr.splitlines():
        if line.startswith("pairs "):
            mismatches = int(line.split()[3])
    return cuts, mismatches


def time_kernel(reference):
    if not TIMER.exists():
        return "kernel timer missing"
    ffmpeg = subprocess.Popen(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(reference),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    proc = subprocess.run(
        [str(TIMER), str(WIDTH), str(HEIGHT), str(NFRAMES)],
        stdin=ffmpeg.stdout,
        capture_output=True,
        text=True,
    )
    ffmpeg.stdout.close()
    ffmpeg.wait()
    if proc.returncode not in (0, 1):
        raise SystemExit(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def encode_uniform(reference, crf, timed):
    dest = HERE / "encodes" / f"crf{crf}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    print(f"encode uniform {crf}", flush=True)
    encode_s, wall = run(
        [
            "-i",
            str(reference),
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
        ],
        level="info",
    )
    timed[f"uniform-{crf}"] = (encode_s, wall, dest.stat().st_size)
    return dest


def encode_zones(reference, spans, timed, label):
    dest = HERE / f"{label}.mp4"
    zone = "/".join(
        f"{span['start']},{span['end']},crf={span['crf']}" for span in spans
    )
    print(f"encode {label}", flush=True)
    encode_s, wall = run(
        [
            "-i",
            str(reference),
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
            "999",
            "-keyint_min",
            "999",
            "-sc_threshold",
            "0",
            "-x264-params",
            f"zones={zone}",
            str(dest),
        ],
        level="info",
    )
    timed[label] = (encode_s, wall, dest.stat().st_size)
    return dest


def score_file(reference, distorted, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        print(f"score {log_path.stem}", flush=True)
        run(
            [
                "-i",
                str(distorted),
                "-i",
                str(reference),
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


def vote(scores, span):
    return min(scores[frame] for frame in span["sample"])


def region_worst(scores, span):
    window = scores[span["start"] : span["end"] + 1]
    worst = min(window)
    frame = span["start"] + window.index(worst)
    return worst, frame


def file_score(scores):
    ordered = sorted(scores)
    k = max(1, math.ceil(0.01 * len(scores)))
    return ordered[k - 1], k


def measure(reference, crfs, spans, cache, timed):
    for crf in crfs:
        if crf in cache:
            continue
        distorted = encode_uniform(reference, crf, timed)
        scores = score_file(reference, distorted, HERE / "scores" / f"crf{crf}.json")
        cache[crf] = scores
    return cache


def missing(cache, span):
    ranked = sorted(cache)
    legal = [crf for crf in ranked if vote(cache[crf], span) >= TARGET]
    if not legal:
        return []
    best = max(legal)
    higher = [crf for crf in ranked if crf > best]
    if not higher:
        return []
    return list(range(best + 1, min(higher)))


def choose(cache, span):
    legal = [crf for crf in sorted(cache) if vote(cache[crf], span) >= TARGET]
    if not legal:
        return min(cache)
    return max(legal)


def main():
    spans = regions()
    for _name, image in PICTURES:
        if not image.exists():
            raise SystemExit(f"missing {image}")
    reference = build_reference()
    cuts, mismatches = detect_cuts(reference)
    expected = list(range(HOLD, NFRAMES, HOLD))
    print(f"cuts {len(cuts)} mismatches {mismatches}", flush=True)
    if mismatches != 0 or cuts != expected:
        raise SystemExit(f"cut finder expected {len(expected)} cuts, got {cuts[:8]}...")
    kernel = time_kernel(reference)
    print(kernel, flush=True)

    timed = {}
    cache = {}
    measure(reference, COARSE, spans, cache, timed)
    if all(vote(cache[max(cache)], span) >= TARGET for span in spans):
        measure(reference, (48,), spans, cache, timed)
    extra = sorted({crf for span in spans for crf in missing(cache, span)})
    if extra:
        print(f"fill {extra}", flush=True)
        measure(reference, extra, spans, cache, timed)

    for span in spans:
        span["crf"] = choose(cache, span)
        span["uniform_vote"] = vote(cache[span["crf"]], span)

    zoned_scores = None
    for attempt in range(1, 6):
        label = "zoned" if attempt == 1 else f"zoned-repair{attempt - 1}"
        zoned = encode_zones(reference, spans, timed, label)
        zoned_scores = score_file(reference, zoned, HERE / "scores" / f"{label}.json")
        failing = [span for span in spans if vote(zoned_scores, span) < TARGET]
        if not failing:
            break
        print(f"repair {attempt}: {len(failing)} visits below {TARGET}", flush=True)
        for span in failing:
            span["crf"] = max(28, span["crf"] - 1)
        if all(span["crf"] == 28 for span in failing):
            break

    for span in spans:
        if span["crf"] in cache:
            span["uniform_vote"] = vote(cache[span["crf"]], span)

    gentle = min(span["crf"] for span in spans)
    harsh = max(span["crf"] for span in spans)
    gentle_scores = cache[gentle]
    harsh_scores = cache[harsh]

    rows = []
    for span in spans:
        z_vote = vote(zoned_scores, span)
        z_worst, z_frame = region_worst(zoned_scores, span)
        rows.append(
            {
                "picture": span["name"],
                "visit": span["visit"],
                "frames": f"{span['start']}-{span['end']}",
                "chosen_crf": span["crf"],
                "uniform_vote": f"{span['uniform_vote']:.2f}",
                "zoned_vote": f"{z_vote:.2f}",
                "zoned_worst": f"{z_worst:.2f}",
                "zoned_worst_frame": z_frame,
            }
        )

    table = HERE / "summary.csv"
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    last_label = [key for key in timed if key.startswith("zoned")][-1]
    zoned_s, zoned_wall, zoned_bytes = timed[last_label]
    gentle_path = HERE / "encodes" / f"crf{gentle}.mp4"
    harsh_path = HERE / "encodes" / f"crf{harsh}.mp4"
    z_file, z_k = file_score(zoned_scores)
    g_file, g_k = file_score(gentle_scores)
    h_file, h_k = file_score(harsh_scores)

    lines = [
        f"Cycling plain, text, chart, gravel every {HOLD} frames. {CYCLES} cycles, {NFRAMES} frames.",
        f"Cut finder mismatches: {mismatches}. Cuts: {len(cuts)}.",
        "Chosen strength is the highest CRF whose 8 settled frames still score at least 90.",
        f"Final zone encode ({last_label}): {zoned_bytes} bytes, x264 {zoned_s:.2f} s, wall {zoned_wall:.2f} s.",
        f"One strength everywhere, CRF {gentle}: {gentle_path.stat().st_size} bytes.",
        f"Harshest single strength, CRF {harsh}: {harsh_path.stat().st_size} bytes.",
        f"File score, {z_k}th-worst: zoned {z_file:.2f}, CRF {gentle} {g_file:.2f}, CRF {harsh} {h_file:.2f}.",
        "",
    ]
    for name, _image in PICTURES:
        group = [row for row in rows if row["picture"] == name]
        crfs = sorted({int(row["chosen_crf"]) for row in group})
        votes = [float(row["zoned_vote"]) for row in group]
        worst = min(group, key=lambda row: float(row["zoned_worst"]))
        lines.append(
            f"{name}: CRF {crfs}, sample {min(votes):.2f} to {max(votes):.2f}, "
            f"worst frame {worst['zoned_worst']} at frame {worst['zoned_worst_frame']}"
        )
    lines.append("")
    lines.append("Brightness sum, five passes, median is the middle run:")
    lines.append(kernel)
    lines.append("")
    lines.append("x264 encode times (seconds from the encoder's own frame rate):")
    for key, (encode_s, wall, size) in timed.items():
        lines.append(f"{key}: encode {encode_s:.2f} s, wall {wall:.2f} s, {size} bytes")

    text = "\n".join(lines) + "\n"
    (HERE / "result.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
