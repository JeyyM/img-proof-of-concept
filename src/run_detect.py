"""Find cuts with the C kernel, then choose a file from saved VMAF scores."""

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
DETECT = Path(__file__).resolve().parent / "detect.exe"
WIDTH = 1024
HEIGHT = 576
TARGET = 90.0
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
CRFS = (28, 32, 36, 40, 44)
CLIPS = (
    ("blank", ROOT / "poc"),
    ("cat", ROOT / "poc" / "cat"),
)


def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)


def gray_path(clip_dir):
    dest = clip_dir / "gray.raw"
    if dest.exists() and dest.stat().st_size == 900 * WIDTH * HEIGHT:
        return dest
    run(
        [
            str(FFMPEG),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(clip_dir / "reference.mkv"),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            str(dest),
        ]
    )
    return dest


def crossings_from(rows):
    found = []
    in_run = False
    for frame, _sad, above in rows:
        if above and not in_run:
            found.append(frame)
            in_run = True
        elif not above:
            in_run = False
    return found


def settled_frames(crossings, limit=900):
    chosen = []
    for index, crossing in enumerate(crossings):
        nxt = crossings[index + 1] if index + 1 < len(crossings) else limit
        start = crossing + 8
        if start >= nxt:
            continue
        frame = start
        while frame < nxt and len(chosen) < 8:
            chosen.append(frame)
            frame += 1
        if len(chosen) == 8:
            break
    return chosen


def load_scores(clip_dir, crf):
    payload = json.loads((clip_dir / "scores" / f"crf{crf}.json").read_text(encoding="utf-8"))
    frames = sorted(payload["frames"], key=lambda row: row["frameNum"])
    return [float(row["metrics"]["vmaf"]) for row in frames]


def nth_worst(scores, n):
    ordered = sorted(enumerate(scores), key=lambda item: item[1])
    return ordered[n - 1]


def choose(rows, key):
    legal = [row for row in rows if row[key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def main():
    src = Path(__file__).resolve().parent
    run(
        [
            str(GCC),
            "-O2",
            "-mavx2",
            "-o",
            str(DETECT),
            str(src / "detect.c"),
            str(src / "sad_avx2.s"),
        ]
    )
    print(f"{'clip':<8} {'crossings':<16} {'settled'}")
    for name, clip_dir in CLIPS:
        raw = gray_path(clip_dir)
        proc = subprocess.run(
            [str(DETECT), str(WIDTH), str(HEIGHT), str(raw)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(proc.stderr.strip())
        rows = []
        for line in proc.stdout.splitlines()[1:]:
            frame_s, sad_s, above_s = line.split(",")
            rows.append((int(frame_s), int(sad_s), int(above_s)))
        cuts = crossings_from(rows)
        settled = settled_frames(cuts)
        easy = [above for frame, _sad, above in rows if frame < cuts[0]] if cuts else []
        easy_ok = 1.0 - (sum(easy) / len(easy)) if easy else 0.0
        print(f"{name:<8} {str(cuts):<16} {settled} easy_at_or_below_2={easy_ok:.2%}")

        scored = []
        for crf in CRFS:
            scores = load_scores(clip_dir, crf)
            ninth_frame, ninth = nth_worst(scores, 9)
            fortyfifth_frame, fortyfifth = nth_worst(scores, 45)
            scored.append(
                {
                    "crf": crf,
                    "bytes": (clip_dir / "encodes" / f"crf{crf}.mp4").stat().st_size,
                    "spread": min(scores[i] for i in EVEN),
                    "text": min(scores[i] for i in settled),
                    "ninth": ninth,
                    "ninth_frame": ninth_frame,
                    "fortyfifth": fortyfifth,
                    "fortyfifth_frame": fortyfifth_frame,
                    "shortfall": max(0.0, TARGET - ninth),
                }
            )
        spread = choose(scored, "spread")
        text = choose(scored, "text")
        out = clip_dir / "scores" / "detected.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(scored[0].keys()))
            writer.writeheader()
            writer.writerows(scored)
        if spread is None or text is None:
            print(f"  no file stayed at or above {TARGET:.0f}")
            continue
        print(
            f"  spread CRF {spread['crf']} shortfall {spread['shortfall']:.2f} "
            f"{spread['bytes']} bytes"
        )
        print(
            f"  settled CRF {text['crf']} shortfall {text['shortfall']:.2f} "
            f"{text['bytes']} bytes "
            f"9th frame {text['ninth_frame']} 45th frame {text['fortyfifth_frame']}"
        )
        same = spread["crf"] == text["crf"]
        print(f"  separated: {not same}")


if __name__ == "__main__":
    main()
