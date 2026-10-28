"""Cut check on the downloaded Commons screen recording.

The file is already compressed. This pass only asks whether the picture
sits still and where it jumps. It does not choose a strength.
"""

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


def main():
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

    rows = []
    for line in proc.stdout.splitlines()[1:]:
        frame_s, sad_s, above_s = line.split(",")
        rows.append((int(frame_s), int(sad_s), int(above_s) == 1))

    cuts = []
    in_run = False
    quiet = 0
    for frame, _sad, above in rows:
        if not above:
            quiet += 1
            in_run = False
        elif not in_run:
            cuts.append(frame)
            in_run = True
        else:
            in_run = True

    settled = []
    for index, cut in enumerate(cuts):
        nxt = cuts[index + 1] if index + 1 < len(cuts) else len(rows) + 1
        start = cut + 8
        if start >= nxt:
            continue
        end = min(start + 8, nxt)
        settled.append((cut, start, end))

    quiet_pct = 100.0 * quiet / len(rows) if rows else 0.0
    lines = [
        f"pairs {len(rows)} quiet {quiet} ({quiet_pct:.1f}%) cuts {len(cuts)}",
        f"settled visits with 8-frame wait: {len(settled)}",
        "cuts: " + ", ".join(str(cut) for cut in cuts[:40]),
    ]
    if len(cuts) > 40:
        lines.append(f"... {len(cuts) - 40} more cuts")
    hold = []
    for cut, start, end in settled:
        frames = end - start
        hold.append(f"{cut}->sample {start}-{end - 1} ({frames} frames)")
    lines.append("samples: " + "; ".join(hold[:12]))
    text = "\n".join(lines) + "\n"
    (HERE / "inspect.txt").write_text(text, encoding="utf-8")
    err = [line for line in proc.stderr.splitlines() if line.startswith("pairs ")]
    if err:
        print(err[0])
    print(text, end="")


if __name__ == "__main__":
    main()
