"""One file, four pictures, a strength for each settled picture.

Order: plain page, dense text, pie chart, gravel. Each picture stays up
for 120 frames. The cut finder is the usual brightness comparison. After
each cut the check waits 8 frames and reads the next 8. Each picture keeps
the strongest CRF whose own eight frames still score at least 90. Those
four strengths are then used in one x264 encode.
"""

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
DETECT = ROOT / "src" / "detect.exe"
WIDTH, HEIGHT = 1024, 576
FPS = 30
HOLD = 120
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)
PICTURES = (
    ("plain", ROOT / "poc" / "plain.png"),
    ("text", ROOT / "poc" / "text.png"),
    ("chart", ROOT / "poc" / "chart" / "plain.png"),
    ("gravel", ROOT / "poc" / "gravel" / "plain.png"),
)


def run(args, cwd=None):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def regions():
    rows = []
    for index, (name, image) in enumerate(PICTURES):
        start = index * HOLD
        rows.append(
            {
                "name": name,
                "image": image,
                "start": start,
                "end": start + HOLD - 1,
                "sample": tuple(range(start + 8, start + 16)),
            }
        )
    return rows


def build_reference(spans):
    reference = HERE / "reference.mkv"
    if reference.exists():
        return reference
    parts = HERE / "_parts"
    parts.mkdir(exist_ok=True)
    lines = []
    for span in spans:
        dest = parts / f"{span['name']}.mkv"
        run(
            [
                "-loop",
                "1",
                "-framerate",
                str(FPS),
                "-i",
                str(span["image"]),
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
        lines.append(f"file '{dest.name}'\n")
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


def encode_uniform(reference, crf):
    dest = HERE / "encodes" / f"crf{crf}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    print(f"encode uniform {crf}", flush=True)
    run(
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
        ]
    )
    return dest


def encode_zones(reference, spans):
    dest = HERE / "zoned.mp4"
    zone = "/".join(
        f"{span['start']},{span['end']},crf={span['crf']}" for span in spans
    )
    print(f"encode zones {zone}", flush=True)
    run(
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
        ]
    )
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


def measure(reference, crfs, spans, cache):
    for crf in crfs:
        if crf in cache:
            continue
        distorted = encode_uniform(reference, crf)
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
    for span in spans:
        if not span["image"].exists():
            raise SystemExit(f"missing {span['image']}")
    reference = build_reference(spans)
    cuts, mismatches = detect_cuts(reference)
    expected = [span["start"] for span in spans[1:]]
    print(f"cuts {cuts} mismatches {mismatches}", flush=True)
    if mismatches != 0 or cuts != expected:
        raise SystemExit(f"cut finder expected {expected}")

    cache = {}
    measure(reference, COARSE, spans, cache)
    if all(vote(cache[max(cache)], span) >= TARGET for span in spans):
        measure(reference, (48,), spans, cache)
    extra = sorted({crf for span in spans for crf in missing(cache, span)})
    if extra:
        print(f"fill {extra}", flush=True)
        measure(reference, extra, spans, cache)

    for span in spans:
        span["crf"] = choose(cache, span)
        span["vote"] = vote(cache[span["crf"]], span)

    zoned = encode_zones(reference, spans)
    zoned_scores = score_file(reference, zoned, HERE / "scores" / "zoned.json")

    gentle = min(span["crf"] for span in spans)
    first_only = spans[0]["crf"]
    gentle_scores = cache[gentle]
    first_scores = cache[first_only]

    rows = []
    for span in spans:
        z_vote = vote(zoned_scores, span)
        z_worst, z_frame = region_worst(zoned_scores, span)
        g_worst, g_frame = region_worst(gentle_scores, span)
        f_worst, f_frame = region_worst(first_scores, span)
        rows.append(
            {
                "picture": span["name"],
                "frames": f"{span['start']}-{span['end']}",
                "chosen_crf": span["crf"],
                "uniform_vote": f"{span['vote']:.2f}",
                "zoned_vote": f"{z_vote:.2f}",
                "zoned_worst": f"{z_worst:.2f}",
                "zoned_worst_frame": z_frame,
                "one_gentle_worst": f"{g_worst:.2f}",
                "one_gentle_frame": g_frame,
                "first_picture_worst": f"{f_worst:.2f}",
                "first_picture_frame": f_frame,
            }
        )

    table = HERE / "summary.csv"
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    gentle_file = HERE / "encodes" / f"crf{gentle}.mp4"
    first_file = HERE / "encodes" / f"crf{first_only}.mp4"
    lines = [
        "Pictures in order: plain, text, chart, gravel. 120 frames each.",
        f"Cut finder mismatches: {mismatches}. Cuts: {cuts}.",
        "Chosen strength is the highest CRF whose 8 settled frames still score at least 90.",
        f"Zoned file: {zoned.stat().st_size} bytes.",
        f"One strength for every picture, CRF {gentle}: {gentle_file.stat().st_size} bytes.",
        f"Strength taken from the first picture only, CRF {first_only}: {first_file.stat().st_size} bytes.",
        "",
    ]
    for row in rows:
        lines.append(
            f"{row['picture']}: CRF {row['chosen_crf']}, "
            f"zoned sample {row['zoned_vote']}, worst frame in that picture {row['zoned_worst']} "
            f"at frame {row['zoned_worst_frame']}"
        )
    text = "\n".join(lines) + "\n"
    (HERE / "result.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
