"""Official development clip: 1920x1080, 30 fps, 900 frames.

The text start is the first row already written in poc/study/draws.csv
(seed 20261010). This script does not move that start. The eight spread-out
frame numbers are written only after the reference file exists.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CLIP = Path(__file__).resolve().parent / "clip"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
DETECT = ROOT / "src" / "detect.exe"
WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL = 900
START = 538
HOLD = 20
FONT_LG = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 120)
FONT = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 22)

PASSAGE = """
A screen recording is often easy to compress, except for a short moment of dense text.
That moment can be a slide, a menu, a formula, a table, or a paragraph, and it can last
less than a second. A check that looks at only a few frames spread through the clip can
miss it. The encoder is then allowed to compress the whole file more harshly. The file
gets smaller, and the text is the first thing that breaks. This page is that moment.
The heading above is large. The lines under it are small on purpose, so a harsh file
loses the letters before it loses the plain picture that comes before and after.
Frame difference uses brightness only. Each pixel contributes the absolute change from
the previous frame, and those changes are added into one sum. A cut is the first frame
of a run whose average rises above a fixed threshold of two levels. The sample used to
choose compression waits eight frames after that cut, then keeps the following frames
of the same picture until eight have been taken or the picture changes again. One
strength is then used for every frame in the file. The spread-out check uses eight
frames placed evenly through the nine hundred frames. Those two checks see different
pictures when the text occupies only twenty frames. The finished file is judged from
every frame, by the ninth-worst score, which can fall inside this page even when the
spread-out frames all landed on the easy picture. Ordinary code and AVX2 must return
the same sum. The clock covers that comparison only. Decoding, encoding, and the
quality score stay outside the timing table. This paragraph is repeated so the page
stays full of small letters rather than a short caption on an empty field.
""".strip()


def run(args, cwd=None):
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
        cwd=cwd,
    )


def write_lock():
    CLIP.mkdir(parents=True, exist_ok=True)
    (CLIP / "lock.txt").write_text(
        "\n".join(
            [
                "seed: 20261010",
                "draw: poc/study/draws.csv first row, title.png",
                f"start: {START}",
                f"hold: {HOLD}",
                f"size: {WIDTH}x{HEIGHT}",
                f"fps: {FPS}",
                f"frames: {TOTAL}",
                "even frames: not computed yet",
                "",
            ]
        ),
        encoding="utf-8",
    )


def render_pictures():
    slides = CLIP / "slides"
    slides.mkdir(parents=True, exist_ok=True)
    easy = Image.new("RGB", (WIDTH, HEIGHT), (248, 249, 252))
    draw = ImageDraw.Draw(easy)
    ink = (20, 24, 28)
    draw.text((131, 113), "Week 4 recap", font=FONT_LG, fill=ink)
    draw.text((131, 413), "One heading on a plain field", font=FONT_LG, fill=ink)
    easy_path = slides / "title.png"
    easy.save(easy_path)

    text = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(text)
    words = PASSAGE.split()
    lines = []
    line = ""
    for word in words * 4:
        trial = word if not line else f"{line} {word}"
        if draw.textlength(trial, font=FONT) > WIDTH - 160:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    y = 48
    for row in lines:
        if y > HEIGHT - 40:
            break
        draw.text((80, y), row, font=FONT, fill=ink)
        y += 30
    text_path = slides / "text.png"
    text.save(text_path)
    return easy_path, text_path


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


def build_reference(easy, text):
    reference = CLIP / "reference.mkv"
    if reference.exists():
        return reference
    parts = CLIP / "_parts"
    parts.mkdir(exist_ok=True)
    still(easy, START, parts / "head.mkv")
    still(text, HOLD, parts / "hold.mkv")
    still(easy, TOTAL - START - HOLD, parts / "tail.mkv")
    listing = parts / "list.txt"
    listing.write_text(
        "file 'head.mkv'\nfile 'hold.mkv'\nfile 'tail.mkv'\n",
        encoding="utf-8",
    )
    run(
        ["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(reference)],
        cwd=parts,
    )
    return reference


def frame_count(reference):
    proc = subprocess.run(
        [str(FFMPEG), "-i", str(reference), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    count = None
    for line in proc.stderr.splitlines():
        if "frame=" in line:
            token = line.split("frame=")[-1].split()[0]
            if token.isdigit():
                count = int(token)
    if count != TOTAL:
        raise SystemExit(f"reference has {count} frames, expected {TOTAL}")
    return count


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
    mismatches = None
    for line in proc.stderr.splitlines():
        if line.startswith("pairs "):
            mismatches = int(line.split()[3])
    return cuts, mismatches


def write_even_frames():
    frames = [int((i + 0.5) * TOTAL / 8) for i in range(8)]
    (CLIP / "even_frames.txt").write_text(
        "Computed after reference.mkv existed. Start was not moved.\n"
        + " ".join(str(frame) for frame in frames)
        + "\n",
        encoding="utf-8",
    )
    return frames


def main():
    write_lock()
    easy, text = render_pictures()
    reference = build_reference(easy, text)
    count = frame_count(reference)
    cuts, mismatches = detect_cuts(reference)
    even = write_even_frames()
    print(f"frames: {count}")
    print(f"text: {START} through {START + HOLD - 1}")
    print(f"cuts: {cuts}")
    print(f"mismatches: {mismatches}")
    print(f"even: {even}")
    print(f"reference: {reference} ({reference.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
