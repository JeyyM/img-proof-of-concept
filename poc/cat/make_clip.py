"""Build one 900-frame proof clip and a small x264 ladder.

Plain picture for frames 0-99, dense text for frames 100-119, plain again
through frame 899. Even sample centers on a 900-frame clip miss that text.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
FPS = 30
TOTAL = 900
TEXT_START = 100
TEXT_FRAMES = 20
CRFS = (28, 32, 36, 40, 44)


def run(args):
    subprocess.run([str(FFMPEG), "-y", "-hide_banner", *args], check=True)


def still(image, frames, dest):
    run(
        [
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(image),
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "ffv1",
            "-pix_fmt",
            "yuv444p",
            str(dest),
        ]
    )


def main():
    plain = ROOT / "plain.png"
    text = ROOT / "text.png"
    parts = ROOT / "_parts"
    parts.mkdir(exist_ok=True)
    head = parts / "head.mkv"
    hold = parts / "hold.mkv"
    tail = parts / "tail.mkv"
    still(plain, TEXT_START, head)
    still(text, TEXT_FRAMES, hold)
    still(plain, TOTAL - TEXT_START - TEXT_FRAMES, tail)

    listing = parts / "list.txt"
    listing.write_text(
        "file 'head.mkv'\nfile 'hold.mkv'\nfile 'tail.mkv'\n",
        encoding="utf-8",
    )
    reference = ROOT / "reference.mkv"
    run(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            str(reference),
        ]
    )

    encodes = ROOT / "encodes"
    encodes.mkdir(exist_ok=True)
    for crf in CRFS:
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
                str(encodes / f"crf{crf}.mp4"),
            ]
        )
    print(f"reference: {reference}")
    print(f"text frames: {TEXT_START} through {TEXT_START + TEXT_FRAMES - 1}")
    print(f"encodes: {', '.join(str(c) for c in CRFS)}")


if __name__ == "__main__":
    main()
