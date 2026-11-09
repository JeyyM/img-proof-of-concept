"""Practice clips: 1920x1080, 30 fps, 900 frames, 20-frame dense hold.

Starts are the first 18 draws of seed 20261010, uniform on frames 180 through 700.
The file is written down before any clip is encoded. The encoder is lossless RGB
x264 with one group of pictures for the whole clip, so a still screen is stored
once instead of nine hundred times.
"""

import csv
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
SEED = 20261010
WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL = 900
HOLD = 20
FRAME_BYTES = WIDTH * HEIGHT * 3

SIMPLE = [
    IMAGES / "simple" / "agenda slide.png",
    IMAGES / "simple" / "empty dashboard.png",
    IMAGES / "simple" / "empty-editor.png",
    IMAGES / "simple" / "section divider.png",
    IMAGES / "simple" / "grid-desktop.png",
    IMAGES / "simple" / "editor-desktop.png",
]
MEDIUM = [
    IMAGES / "medium" / "analytics.png",
    IMAGES / "medium" / "blank-writer.png",
    IMAGES / "medium" / "board.png",
    IMAGES / "medium" / "control-panel.png",
    IMAGES / "medium" / "file-manager.png",
    IMAGES / "medium" / "appearance.png",
]
DENSE = [
    IMAGES / "dense" / "article.png",
    IMAGES / "dense" / "code-editor.png",
    IMAGES / "dense" / "rfc-body.png",
    IMAGES / "dense" / "spec-columns.png",
    IMAGES / "dense" / "spreadsheet.png",
    IMAGES / "dense" / "terminal-log.png",
]


def pairs():
    rows = []
    for index in range(6):
        rows.append(("comparison", SIMPLE[index], DENSE[index]))
    for index in range(6):
        rows.append(("comparison", SIMPLE[index], DENSE[(index + 1) % 6]))
    for index in range(6):
        rows.append(("boundary", MEDIUM[index], DENSE[(index + 2) % 6]))
    return rows


def starts():
    rng = random.Random(SEED)
    return [rng.randint(180, 700) for _ in range(18)]


def run(args):
    subprocess.run([str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def picture_filter(path):
    with Image.open(path) as image:
        size = image.size
    if size == (WIDTH, HEIGHT):
        return "format=rgb24,setsar=1"
    return f"scale={WIDTH}:{HEIGHT}:flags=lanczos,format=rgb24,setsar=1"


def encode(easy, dense, start, dest):
    easy_chain = picture_filter(easy)
    dense_chain = picture_filter(dense)
    graph = (
        f"[0:v]{easy_chain}[e];"
        f"[1:v]{dense_chain}[d];"
        f"[e][d]overlay=format=rgb:enable='between(n,{start},{start + HOLD - 1})',format=rgb24"
    )
    run(
        [
            "-loop", "1", "-framerate", str(FPS), "-i", str(easy),
            "-loop", "1", "-framerate", str(FPS), "-i", str(dense),
            "-filter_complex", graph,
            "-frames:v", str(TOTAL),
            "-fps_mode", "cfr",
            "-an",
            "-c:v", "libx264rgb",
            "-qp", "0",
            "-preset", "medium",
            "-pix_fmt", "rgb24",
            "-x264-params", "keyint=900:min-keyint=900:scenecut=0",
            str(dest),
        ]
    )


def raw_still(path):
    vf = picture_filter(path)
    proc = subprocess.run(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-vf", vf, "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        check=True, capture_output=True,
    )
    if len(proc.stdout) != FRAME_BYTES:
        raise SystemExit(f"{path.name} scaled to {len(proc.stdout)} bytes")
    return proc.stdout


def raw_frame(clip, number):
    proc = subprocess.run(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error",
            "-i", str(clip),
            "-vf", f"select=eq(n\\,{number})",
            "-vframes", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        check=True, capture_output=True,
    )
    if len(proc.stdout) != FRAME_BYTES:
        raise SystemExit(f"{clip.name} frame {number} is {len(proc.stdout)} bytes")
    return proc.stdout


def frame_count(clip):
    proc = subprocess.run(
        [str(FFMPEG), "-i", str(clip), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    count = None
    for line in proc.stderr.splitlines():
        if "frame=" in line:
            token = line.split("frame=")[-1].split()[0]
            if token.isdigit():
                count = int(token)
    return count


def luma_mad(left, right):
    a = Image.frombytes("RGB", (WIDTH, HEIGHT), left).convert("L")
    b = Image.frombytes("RGB", (WIDTH, HEIGHT), right).convert("L")
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def write_log(log_path, fields, plan):
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(plan)


def main():
    OUT.mkdir(exist_ok=True)
    drawn = starts()
    plan = []
    for number, (group, easy, dense) in enumerate(pairs(), start=1):
        plan.append(
            {
                "clip": f"{number:02d}",
                "group": group,
                "easy": "" if easy is None else str(easy.relative_to(ROOT)),
                "dense": "" if dense is None else str(dense.relative_to(ROOT)),
                "start": drawn[number - 1],
                "hold": HOLD,
                "status": "waiting on still" if easy is None or dense is None else "pending",
            }
        )
    log_path = OUT / "log.csv"
    fields = ["clip", "group", "easy", "dense", "start", "hold", "frames", "bytes", "easy_match", "dense_match", "cut_on", "cut_back", "status"]
    prior = {}
    if log_path.exists():
        with log_path.open(encoding="utf-8", newline="") as handle:
            for old in csv.DictReader(handle):
                prior[old["clip"]] = old
    paired = list(zip(plan, pairs()))
    for row, (group, easy, dense) in paired:
        if easy is None or dense is None:
            continue
        dest = OUT / f"{row['clip']}.mkv"
        old = prior.get(row["clip"])
        if dest.exists() and old and old.get("status") == "built":
            for key in fields:
                if old.get(key):
                    row[key] = old[key]
    write_log(log_path, fields, plan)
    print("starts written", [row["start"] for row in plan])

    for row, (group, easy, dense) in paired:
        if row["status"] == "built":
            print("keep", row["clip"])
            continue
        if easy is None or dense is None:
            print("skip", row["clip"])
            continue
        dest = OUT / f"{row['clip']}.mkv"
        print("encode", row["clip"], "start", row["start"])
        encode(easy, dense, row["start"], dest)
        count = frame_count(dest)
        easy_frame = raw_frame(dest, 0)
        dense_frame = raw_frame(dest, row["start"])
        before = raw_frame(dest, row["start"] - 1)
        after = raw_frame(dest, row["start"] + HOLD)
        row["frames"] = count
        row["bytes"] = dest.stat().st_size
        row["easy_match"] = int(easy_frame == raw_still(easy))
        row["dense_match"] = int(dense_frame == raw_still(dense))
        row["cut_on"] = f"{luma_mad(before, dense_frame):.2f}"
        row["cut_back"] = f"{luma_mad(dense_frame, after):.2f}"
        row["status"] = "built" if count == TOTAL and row["easy_match"] and row["dense_match"] else "check failed"
        print(row["clip"], row["status"], row["frames"], row["bytes"], row["cut_on"], row["cut_back"])
        write_log(log_path, fields, plan)


if __name__ == "__main__":
    main()
