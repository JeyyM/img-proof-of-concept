"""Choose a CRF for each practice clip, with scene-cut off.

The lossless clips already exist. This script finds the cuts, encodes a
ladder of CRF files, and scores every frame. Each rule keeps the highest
CRF whose eight frames still reach VMAF 90. A clip already in
decisions.csv is left alone.
"""

import csv
import json
import random
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = Path(__file__).resolve().parent
WORK = CLIPS / "work"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
NASM = Path(r"C:\winlibs\mingw64\bin\nasm.exe")
DETECT = ROOT / "src" / "detect.exe"

SEED = 20261010
WIDTH, HEIGHT = 1920, 1080
TOTAL = 900
NPIX = WIDTH * HEIGHT
TARGET = 90.0

# Eight frames spread through the 900. A 20-frame page fits between them.
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
COARSE = (28, 32, 36, 40, 44)
RULES = ("spread", "settled", "cut", "random", "detail")


def run(args, cwd=None):
    """Start FFmpeg. Stop the script if FFmpeg fails."""
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def compile_detect():
    """Build the cut finder. This is not the course timing clock."""
    build = ROOT / "src" / "build"
    build.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(NASM), "-f", "win64",
            "-o", str(build / "brightness_avx2.o"),
            str(ROOT / "src" / "brightness_avx2.asm"),
        ],
        check=True,
    )
    subprocess.run(
        [
            str(GCC), "-O2", "-mavx2", "-o", str(DETECT),
            str(ROOT / "src" / "detect.c"),
            str(build / "brightness_avx2.o"),
        ],
        check=True,
    )


def random_frames():
    """Eight shared frames. The first 18 draws are skipped so the page starts stay put."""
    path = CLIPS / "random_frames.txt"
    if path.exists():
        return tuple(int(part) for part in path.read_text(encoding="utf-8").split())
    rng = random.Random(SEED)
    for _ in range(18):
        rng.randint(180, 700)
    chosen = []
    while len(chosen) < 8:
        draw = rng.randrange(TOTAL)
        if draw not in chosen:
            chosen.append(draw)
    path.write_text(" ".join(str(frame) for frame in chosen) + "\n", encoding="utf-8")
    return tuple(chosen)


def cuts_from_rows(rows):
    """A cut is the first frame of a run whose mean brightness change is above 2."""
    found = []
    in_run = False
    for frame, _sad, above in rows:
        if above and not in_run:
            found.append(frame)
            in_run = True
        elif not above:
            in_run = False
    quiet = sum(1 for _frame, _sad, above in rows if not above)
    return found, quiet / len(rows)


def crossings_of(clip):
    """Decode the clip to gray and ask detect.exe where the picture changes."""
    ff = subprocess.Popen(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error",
            "-i", str(clip),
            "-f", "rawvideo", "-pix_fmt", "gray", "-",
        ],
        stdout=subprocess.PIPE,
    )
    det = subprocess.Popen(
        [str(DETECT), str(WIDTH), str(HEIGHT), "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    def pump():
        try:
            while True:
                chunk = ff.stdout.read(1 << 20)
                if not chunk:
                    break
                det.stdin.write(chunk)
        finally:
            det.stdin.close()
            ff.stdout.close()

    out_chunks = []
    err_chunks = []

    def read_out():
        out_chunks.append(det.stdout.read())

    def read_err():
        err_chunks.append(det.stderr.read())

    # Three threads, so a full pipe cannot stall the decoder or the cut finder.
    threads = [
        threading.Thread(target=pump),
        threading.Thread(target=read_out),
        threading.Thread(target=read_err),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    det.wait()
    ff.wait()

    err = b"".join(err_chunks).decode("utf-8", "replace")
    if det.returncode not in (0, None):
        raise SystemExit(err.strip() or f"detect exited {det.returncode}")
    rows = []
    for line in b"".join(out_chunks).decode("utf-8").splitlines()[1:]:
        frame_s, sad_s, above_s = line.split(",")
        rows.append((int(frame_s), int(sad_s), int(above_s)))
    cuts, quiet_share = cuts_from_rows(rows)
    return cuts, quiet_share, err.strip()


def frames_from(crossings, offset):
    """Up to eight frames from the first cut that has room for them."""
    chosen = []
    for index, crossing in enumerate(crossings):
        nxt = crossings[index + 1] if index + 1 < len(crossings) else TOTAL
        frame = crossing + offset
        if frame >= nxt:
            continue
        while frame < nxt and len(chosen) < 8:
            chosen.append(frame)
            frame += 1
        if len(chosen) == 8:
            break
    return tuple(chosen)


def settled_frames(crossings):
    """Eight frames starting eight after a cut. The page, after the jump."""
    return frames_from(crossings, 8)


def cut_frames(crossings):
    """Eight frames starting on the cut itself."""
    return frames_from(crossings, 0)


def gray_frame(clip, number):
    """One grayscale frame, used only to compare detail."""
    proc = subprocess.run(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error",
            "-i", str(clip),
            "-vf", f"select=eq(n\\,{number})",
            "-vframes", "1",
            "-f", "rawvideo", "-pix_fmt", "gray", "-",
        ],
        check=True,
        capture_output=True,
    )
    if len(proc.stdout) != NPIX:
        raise SystemExit(f"{clip.name} frame {number} gray is {len(proc.stdout)} bytes")
    return proc.stdout


def variance(raw):
    """How spread out the gray values are. A page of text scores higher than a flat slide."""
    total = sum(raw)
    squares = sum(value * value for value in raw)
    mean = total / NPIX
    return squares / NPIX - mean * mean


def detail_frames(clip, crossings):
    """Eight frames on the busier picture, either the opening screen or the page."""
    if not crossings:
        return tuple(range(8))
    easy = variance(gray_frame(clip, 0))
    page = variance(gray_frame(clip, crossings[0]))
    if page > easy:
        return tuple(range(crossings[0], crossings[0] + 8))
    return tuple(range(8))


def load_vmaf(path):
    """900 frame scores, in frame order."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_num = {}
    for row in payload["frames"]:
        by_num[int(row["frameNum"])] = float(row["metrics"]["vmaf"])
    missing = [frame for frame in range(TOTAL) if frame not in by_num]
    if missing:
        raise SystemExit(f"{path} is missing frames {missing[:5]}")
    return [by_num[frame] for frame in range(TOTAL)]


def nth_worst(scores, n):
    """The frame at position n when scores are sorted from worst to best."""
    return sorted(enumerate(scores), key=lambda item: item[1])[n - 1]


def encode_file(reference, dest, crf):
    """One scene-cut-off file for the whole clip. An existing file is kept."""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-i", str(reference),
            "-an",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-g", "999",
            "-keyint_min", "999",
            "-sc_threshold", "0",
            str(dest),
        ]
    )


def score_file(reference, distorted, log_path):
    """VMAF for every frame. The compressed file is compared with the lossless clip."""
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                "-i", str(distorted),
                "-i", str(reference),
                "-lavfi",
                "[0:v]format=yuv420p,setpts=PTS-STARTPTS[dist];"
                "[1:v]format=yuv420p,setpts=PTS-STARTPTS[ref];"
                f"[dist][ref]libvmaf=log_fmt=json:log_path={log_path.name}:n_subsample=1:n_threads=8",
                "-f", "null", "-",
            ],
            cwd=log_path.parent,
        )
    return load_vmaf(log_path)


def measure(reference, encode_dir, score_dir, crfs, rows, votes):
    """Encode and score any CRF that is not already in the ladder."""
    have = {row["crf"]: row for row in rows}
    for crf in crfs:
        if crf in have:
            continue
        print(f"  crf {crf}", flush=True)
        distorted = encode_dir / f"crf{crf}.mp4"
        encode_file(reference, distorted, crf)
        scores = score_file(reference, distorted, score_dir / f"crf{crf}.json")
        ninth_frame, ninth = nth_worst(scores, 9)
        forty_frame, forty = nth_worst(scores, 45)
        row = {
            "crf": crf,
            "bytes": distorted.stat().st_size,
            "ninth": ninth,
            "ninth_frame": ninth_frame,
            "fortyfifth": forty,
            "fortyfifth_frame": forty_frame,
        }
        for name, frames in votes.items():
            row[name] = min(scores[frame] for frame in frames) if frames else None
        rows.append(row)
        have[crf] = row
    rows.sort(key=lambda row: row["crf"])
    return rows


def missing_steps(rows, key):
    """Integers between the last CRF whose vote still reaches 90 and the next one that does not."""
    legal = [row["crf"] for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return []
    best = max(legal)
    higher = [row["crf"] for row in rows if row["crf"] > best]
    if not higher:
        return []
    return list(range(best + 1, min(higher)))


def choose(rows, key):
    """Highest CRF whose eight-frame vote is still at least 90."""
    legal = [row for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def bracket(rows):
    """Step the ladder by 2 until the 9th-worst score falls on either side of 90."""
    extra = []
    if rows and min(row["ninth"] for row in rows) >= TARGET and rows[-1]["crf"] < 42:
        extra.append(min(42, rows[-1]["crf"] + 2))
    if rows and max(row["ninth"] for row in rows) < TARGET and rows[0]["crf"] > 18:
        extra.append(max(18, rows[0]["crf"] - 2))
    return extra


def clip_ids():
    """Built clips, in the order stored by build_clips.py."""
    rows = []
    with (CLIPS / "log.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] == "built":
                rows.append(row)
    return rows


def votes_for(reference, drawn):
    """The five sets of eight frames. The page start in the log is not used."""
    crossings, easy_share, kernel = crossings_of(reference)
    votes = {
        "spread": EVEN,
        "settled": settled_frames(crossings),
        "cut": cut_frames(crossings),
        "random": drawn,
        "detail": detail_frames(reference, crossings),
    }
    return crossings, easy_share, kernel, votes


def fill_ladder(reference, encode_dir, score_dir, votes):
    """Coarse CRFs first, then the steps that put a vote on either side of 90."""
    rows = measure(reference, encode_dir, score_dir, COARSE, [], votes)
    while True:
        extra = bracket(rows)
        extra += missing_steps(rows, "spread")
        extra += missing_steps(rows, "settled")
        extra = sorted({crf for crf in extra if crf not in {row["crf"] for row in rows}})
        if not extra:
            return rows
        print("  fill", extra, flush=True)
        rows = measure(reference, encode_dir, score_dir, extra, rows, votes)


def write_summary(score_dir, rows):
    summary = score_dir / "summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def decision_row(meta, crossings, easy_share, votes, rows):
    """One decisions.csv row: the CRF each rule kept, and the file score at that CRF."""
    record = {
        "clip": meta["clip"],
        "group": meta["group"],
        "cuts": " ".join(str(frame) for frame in crossings),
        "easy_below_2": f"{easy_share:.4f}",
        "settled_frames": " ".join(str(frame) for frame in votes["settled"]),
        "detail_frames": " ".join(str(frame) for frame in votes["detail"]),
    }
    for key in RULES:
        picked = choose(rows, key)
        if picked is None:
            record[f"{key}_crf"] = ""
            record[f"{key}_ninth"] = ""
            record[f"{key}_shortfall"] = ""
            record[f"{key}_shortfall80"] = ""
            record[f"{key}_bytes"] = ""
            record[f"{key}_ninth_frame"] = ""
            print(f"  {key}: no rung at {TARGET:.0f}", flush=True)
            continue
        record[f"{key}_crf"] = picked["crf"]
        record[f"{key}_ninth"] = f"{picked['ninth']:.4f}"
        record[f"{key}_shortfall"] = f"{max(0.0, TARGET - picked['ninth']):.4f}"
        record[f"{key}_shortfall80"] = f"{max(0.0, 80.0 - picked['ninth']):.4f}"
        record[f"{key}_bytes"] = picked["bytes"]
        record[f"{key}_ninth_frame"] = picked["ninth_frame"]
        print(
            f"  {key}: crf {picked['crf']} ninth {picked['ninth']:.2f} "
            f"shortfall {max(0.0, TARGET - picked['ninth']):.2f} bytes {picked['bytes']}",
            flush=True,
        )
    return record


def write_decisions(path, decisions):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0].keys()))
        writer.writeheader()
        writer.writerows(decisions)


def load_decisions(path):
    if not path.exists():
        return [], set()
    with path.open(encoding="utf-8", newline="") as handle:
        decisions = list(csv.DictReader(handle))
    return decisions, {row["clip"] for row in decisions}


def main():
    compile_detect()
    drawn = random_frames()
    print("random frames", drawn, flush=True)

    decisions_path = CLIPS / "decisions.csv"
    decisions, done = load_decisions(decisions_path)

    for meta in clip_ids():
        name = meta["clip"]
        if name in done:
            print("skip", name, flush=True)
            continue

        reference = CLIPS / f"{name}.mkv"
        encode_dir = WORK / name / "encodes"
        score_dir = WORK / name / "scores"
        print("clip", name, flush=True)

        crossings, easy_share, kernel, votes = votes_for(reference, drawn)
        print(" ", kernel, "cuts", crossings, f"easy_below_2={easy_share:.3f}", flush=True)
        rows = fill_ladder(reference, encode_dir, score_dir, votes)
        write_summary(score_dir, rows)
        decisions.append(decision_row(meta, crossings, easy_share, votes, rows))
        write_decisions(decisions_path, decisions)
        print("clip", name, "done", flush=True)


if __name__ == "__main__":
    main()
