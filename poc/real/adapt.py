"""Give every settled picture its own strength on the 3-minute recording.

The first zoned file picked a strength from each picture, then left 21
samples under 90. This pass eases each picture whose own eight frames
fall short, and encodes again. Short pictures keep the previous strength.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_real as real

LADDER = (44, 40, 36, 32, 28, 24, 20, 16)
FLOOR = LADDER[-1]


def ease(crf):
    index = LADDER.index(crf)
    return LADDER[min(index + 1, len(LADDER) - 1)]


def zones(spans, nframes):
    rows = []
    for index, span in enumerate(spans):
        end = spans[index + 1]["start"] - 1 if index + 1 < len(spans) else nframes - 1
        rows.append({"start": span["start"], "end": end, "crf": span["crf"]})
    return rows


def encode_adapt(video_spans, label):
    dest = real.HERE / f"{label}.mp4"
    if dest.exists() and (real.HERE / "scores" / f"{label}.json").exists():
        return dest
    if dest.exists():
        dest.unlink()
    zone = "/".join(
        f"{span['start']},{span['end']},crf={span['crf']}" for span in video_spans
    )
    print(f"encode {label}", flush=True)
    real.run(
        [
            "-i",
            str(real.VIDEO),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(video_spans[0]["crf"]),
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


def percentile(scores):
    ordered = sorted(scores)
    k = max(1, __import__("math").ceil(0.01 * len(scores)))
    worst = ordered[k - 1]
    return k, worst, scores.index(worst)


def main():
    nframes, quiet, cuts = real.detect()
    spans = real.regions(nframes, cuts)
    cache = {}
    for crf in real.COARSE:
        cache[crf] = real.score(real.HERE / "encodes" / f"crf{crf}.mp4", f"crf{crf}")
    for span in spans:
        span["crf"] = real.choose(cache, span["sample"])

    scores = real.score(real.HERE / "zoned.mp4", "zoned")
    label = "zoned"
    for attempt in range(1, 5):
        failing = [span for span in spans if real.vmin(scores, span["sample"]) < real.TARGET]
        counts = {}
        for span in spans:
            counts[span["crf"]] = counts.get(span["crf"], 0) + 1
        print(
            f"attempt {attempt - 1}: under 90 = {len(failing)} of {len(spans)}; "
            + ", ".join(f"CRF {crf} x{counts[crf]}" for crf in sorted(counts)),
            flush=True,
        )
        if not failing:
            break
        if all(span["crf"] == FLOOR for span in failing):
            break
        for span in failing:
            span["crf"] = ease(span["crf"])
        label = f"adapt{attempt}"
        dest = encode_adapt(zones(spans, nframes), label)
        scores = real.score(dest, label)

    failing = [span for span in spans if real.vmin(scores, span["sample"]) < real.TARGET]
    counts = {}
    for span in spans:
        counts[span["crf"]] = counts.get(span["crf"], 0) + 1
    k, worst, frame = percentile(scores)
    adapted = real.HERE / f"{label}.mp4"
    gentle = real.HERE / "encodes" / "crf28.mp4"
    lines = [
        "Each settled picture keeps its own strength. A picture under 90 is eased one step and the file is encoded again.",
        "Steps: 44, 40, 36, 32, 28, 24, 20, 16.",
        f"Quiet pairs: {100.0 * quiet / (nframes - 1):.1f}%. Pictures sampled: {len(spans)}.",
        "Final strengths: " + ", ".join(f"CRF {crf} on {counts[crf]} pictures" for crf in sorted(counts)),
        f"Adapted file ({label}): {adapted.stat().st_size} bytes.",
        f"One strength CRF 28: {gentle.stat().st_size} bytes.",
        f"Settled samples still under 90: {len(failing)} of {len(spans)}.",
        f"{k}th-worst {worst:.2f} at frame {frame}.",
    ]
    text = "\n".join(lines) + "\n"
    (real.HERE / "adapt.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
