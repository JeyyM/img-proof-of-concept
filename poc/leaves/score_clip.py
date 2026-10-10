"""Score the one proof clip and compare the two frame choices.

One full VMAF pass per encode. Sample votes are indexes into that list.
"""

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
REFERENCE = ROOT / "reference.mkv"
ENCODES = ROOT / "encodes"
SCORES = ROOT / "scores"
TARGET = 90.0
BASE_CRFS = (28, 32, 36, 40, 44)
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
TEXT = tuple(range(108, 116))
JUMP = tuple(range(100, 108))
TEXT_HOLD = range(100, 120)


def run(args):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", *args],
        check=True,
        cwd=ROOT,
    )


def encode(crf):
    dest = ENCODES / f"crf{crf}.mp4"
    if dest.exists():
        return dest
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


def score_vmaf(crf, distorted):
    SCORES.mkdir(exist_ok=True)
    log_path = SCORES / f"crf{crf}.json"
    if not log_path.exists():
        run(
            [
                "-i",
                str(distorted),
                "-i",
                str(REFERENCE),
                "-lavfi",
                "[0:v]format=yuv420p,setpts=PTS-STARTPTS[dist];"
                "[1:v]format=yuv420p,setpts=PTS-STARTPTS[ref];"
                f"[dist][ref]libvmaf=log_fmt=json:log_path=scores/crf{crf}.json:"
                "n_subsample=1:n_threads=8",
                "-f",
                "null",
                "-",
            ]
        )
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    frames = sorted(payload["frames"], key=lambda row: row["frameNum"])
    scores = [float(row["metrics"]["vmaf"]) for row in frames]
    if len(scores) != 900:
        raise SystemExit(f"CRF {crf} scored {len(scores)} frames, expected 900")
    return scores


def worst(scores, indexes):
    return min(scores[i] for i in indexes)


def nth_worst(scores, n):
    ordered = sorted(enumerate(scores), key=lambda item: item[1])
    frame, value = ordered[n - 1]
    return value, frame


def row_for(crf, scores):
    ninth, ninth_frame = nth_worst(scores, 9)
    fortyfifth, fortyfifth_frame = nth_worst(scores, 45)
    return {
        "crf": crf,
        "bytes": (ENCODES / f"crf{crf}.mp4").stat().st_size,
        "spread_vote": worst(scores, EVEN),
        "text_vote": worst(scores, TEXT),
        "jump_vote": worst(scores, JUMP),
        "ninth": ninth,
        "ninth_frame": ninth_frame,
        "fortyfifth": fortyfifth,
        "fortyfifth_frame": fortyfifth_frame,
        "shortfall": max(0.0, TARGET - ninth),
    }


def choose(rows, vote_key):
    legal = [row for row in rows if row[vote_key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def blank_frame(frame):
    return frame not in TEXT_HOLD


def main():
    crfs = list(BASE_CRFS)
    rows = []
    for crf in crfs:
        scores = score_vmaf(crf, encode(crf))
        rows.append(row_for(crf, scores))

    if all(row["ninth"] >= TARGET for row in rows):
        scores = score_vmaf(48, encode(48))
        rows.append(row_for(48, scores))

    fields = [
        "crf",
        "bytes",
        "spread_vote",
        "text_vote",
        "jump_vote",
        "ninth",
        "ninth_frame",
        "fortyfifth",
        "fortyfifth_frame",
        "shortfall",
    ]
    SCORES.mkdir(exist_ok=True)
    with (SCORES / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    header = (
        f"{'crf':>4} {'bytes':>8} {'spread':>8} {'text':>8} {'jump':>8} "
        f"{'9th':>8} {'9th#':>5} {'45th':>8} {'45th#':>5} {'short':>8}"
    )
    print(header)
    for row in rows:
        print(
            f"{row['crf']:4d} {row['bytes']:8d} {row['spread_vote']:8.2f} "
            f"{row['text_vote']:8.2f} {row['jump_vote']:8.2f} "
            f"{row['ninth']:8.2f} {row['ninth_frame']:5d} "
            f"{row['fortyfifth']:8.2f} {row['fortyfifth_frame']:5d} "
            f"{row['shortfall']:8.2f}"
        )

    spread = choose(rows, "spread_vote")
    text = choose(rows, "text_vote")
    print()
    if spread is None or text is None:
        missing = []
        if spread is None:
            missing.append("spread-out")
        if text is None:
            missing.append("text-aware")
        print(f"No legal file for: {', '.join(missing)}. No CRF kept a vote of at least 90.")
        return

    print(
        f"Spread-out chose CRF {spread['crf']} "
        f"(shortfall {spread['shortfall']:.2f}, {spread['bytes']} bytes)."
    )
    print(
        f"Text-aware chose CRF {text['crf']} "
        f"(shortfall {text['shortfall']:.2f}, {text['bytes']} bytes)."
    )
    if spread["crf"] == text["crf"]:
        print("Both rules chose the same file. This ladder did not separate them.")

    h1 = text["shortfall"] < spread["shortfall"]
    h2 = text["ninth_frame"] in TEXT_HOLD and blank_frame(text["fortyfifth_frame"])
    h2_spread = spread["ninth_frame"] in TEXT_HOLD and blank_frame(spread["fortyfifth_frame"])
    h4 = h1 and text["bytes"] > spread["bytes"]
    print(f"Hypothesis 1 leans with the claim: {h1}")
    print(
        "Hypothesis 2 on the text-aware file: "
        f"{h2} (9th frame {text['ninth_frame']}, 45th frame {text['fortyfifth_frame']})"
    )
    print(
        "Hypothesis 2 on the spread-out file: "
        f"{h2_spread} (9th frame {spread['ninth_frame']}, 45th frame {spread['fortyfifth_frame']})"
    )
    print(f"Hypothesis 4 leans with the claim: {h4}")


if __name__ == "__main__":
    main()
