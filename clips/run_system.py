"""Run the practice clips through the locked selector.

Scene-cut off, preset medium, yuv420. Coarse rungs 28, 32, 36, 40, 44.
The file-score ladder steps outward by 2 until the 9th-worst brackets 90,
stopping at CRF 18 or 42. Integer rungs between a rule's last passing vote
and the next failing vote are filled for the spread sample and the settled
sample only. Cuts come from the luma kernel. The scripted start is not an input.
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
DETECT = ROOT / "src" / "detect.exe"
SEED = 20261010
WIDTH, HEIGHT = 1920, 1080
TOTAL = 900
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)
NPIX = WIDTH * HEIGHT


def run(args, cwd=None):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def compile_detect():
    subprocess.run(
        [
            str(GCC), "-O2", "-mavx2", "-o", str(DETECT),
            str(ROOT / "src" / "detect.c"),
            str(ROOT / "src" / "sad_avx2.s"),
        ],
        check=True,
    )


def random_frames():
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


def crossings_of(clip):
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

    threads = [threading.Thread(target=pump), threading.Thread(target=read_out), threading.Thread(target=read_err)]
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
    found = []
    in_run = False
    for frame, _sad, above in rows:
        if above and not in_run:
            found.append(frame)
            in_run = True
        elif not above:
            in_run = False
    below = sum(1 for _frame, _sad, above in rows if not above)
    return found, below / len(rows), err.strip()


def settled_frames(crossings):
    chosen = []
    for index, crossing in enumerate(crossings):
        nxt = crossings[index + 1] if index + 1 < len(crossings) else TOTAL
        frame = crossing + 8
        if frame >= nxt:
            continue
        while frame < nxt and len(chosen) < 8:
            chosen.append(frame)
            frame += 1
        if len(chosen) == 8:
            break
    return tuple(chosen)


def cut_frames(crossings):
    chosen = []
    for index, crossing in enumerate(crossings):
        nxt = crossings[index + 1] if index + 1 < len(crossings) else TOTAL
        frame = crossing
        while frame < nxt and len(chosen) < 8:
            chosen.append(frame)
            frame += 1
        if len(chosen) == 8:
            break
    return tuple(chosen)


def gray_frame(clip, number):
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
    total = sum(raw)
    squares = sum(value * value for value in raw)
    mean = total / NPIX
    return squares / NPIX - mean * mean


def detail_frames(clip, crossings):
    if not crossings:
        return tuple(range(8))
    easy = variance(gray_frame(clip, 0))
    text = variance(gray_frame(clip, crossings[0]))
    if text > easy:
        return tuple(range(crossings[0], crossings[0] + 8))
    return tuple(range(8))


def load_vmaf(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_num = {}
    for row in payload["frames"]:
        by_num[int(row["frameNum"])] = float(row["metrics"]["vmaf"])
    missing = [frame for frame in range(TOTAL) if frame not in by_num]
    if missing:
        raise SystemExit(f"{path} is missing frames {missing[:5]}")
    return [by_num[frame] for frame in range(TOTAL)]


def nth_worst(scores, n):
    return sorted(enumerate(scores), key=lambda item: item[1])[n - 1]


def encode_file(reference, dest, crf):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-i", str(reference), "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-g", "999", "-keyint_min", "999", "-sc_threshold", "0",
            str(dest),
        ]
    )


def score_file(reference, distorted, log_path):
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                "-i", str(distorted), "-i", str(reference),
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
    legal = [row["crf"] for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return []
    best = max(legal)
    higher = [row["crf"] for row in rows if row["crf"] > best]
    if not higher:
        return []
    return list(range(best + 1, min(higher)))


def choose(rows, key):
    legal = [row for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def bracket(rows):
    extra = []
    if rows and min(row["ninth"] for row in rows) >= TARGET and rows[-1]["crf"] < 42:
        extra.append(min(42, rows[-1]["crf"] + 2))
    if rows and max(row["ninth"] for row in rows) < TARGET and rows[0]["crf"] > 18:
        extra.append(max(18, rows[0]["crf"] - 2))
    return extra


def clip_ids():
    rows = []
    with (CLIPS / "log.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] == "built":
                rows.append(row)
    return rows


def main():
    compile_detect()
    drawn = random_frames()
    print("random frames", drawn, flush=True)
    decisions_path = CLIPS / "decisions.csv"
    decisions = []
    done = set()
    if decisions_path.exists():
        with decisions_path.open(encoding="utf-8", newline="") as handle:
            decisions = list(csv.DictReader(handle))
        done = {row["clip"] for row in decisions}
    fields = list(decisions[0].keys()) if decisions else None
    for meta in clip_ids():
        name = meta["clip"]
        if name in done:
            print("skip", name, flush=True)
            continue
        reference = CLIPS / f"{name}.mkv"
        encode_dir = WORK / name / "encodes"
        score_dir = WORK / name / "scores"
        print("clip", name, flush=True)
        crossings, easy_share, kernel = crossings_of(reference)
        print(" ", kernel, "cuts", crossings, f"easy_below_2={easy_share:.3f}", flush=True)
        settled = settled_frames(crossings)
        on_cut = cut_frames(crossings)
        detail = detail_frames(reference, crossings)
        votes = {
            "spread": EVEN,
            "settled": settled,
            "cut": on_cut,
            "random": drawn,
            "detail": detail,
        }
        rows = measure(reference, encode_dir, score_dir, COARSE, [], votes)
        while True:
            extra = bracket(rows)
            extra += missing_steps(rows, "spread")
            extra += missing_steps(rows, "settled")
            extra = sorted({crf for crf in extra if crf not in {row["crf"] for row in rows}})
            if not extra:
                break
            print("  fill", extra, flush=True)
            rows = measure(reference, encode_dir, score_dir, extra, rows, votes)
        summary = score_dir / "summary.csv"
        with summary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        record = {
            "clip": name,
            "group": meta["group"],
            "cuts": " ".join(str(frame) for frame in crossings),
            "easy_below_2": f"{easy_share:.4f}",
            "settled_frames": " ".join(str(frame) for frame in settled),
            "detail_frames": " ".join(str(frame) for frame in detail),
        }
        for key in ("spread", "settled", "cut", "random", "detail"):
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
        decisions.append(record)
        fields = list(record.keys())
        with decisions_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(decisions)
        print("clip", name, "done", flush=True)


if __name__ == "__main__":
    main()
