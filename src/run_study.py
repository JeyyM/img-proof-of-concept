"""Screen-picture study, boundary table, finer ladder, scene-cut, OCR, interval.

The text start times are drawn from a fixed seed and written down before any
even-frame index is allowed to change them. A draw that lands on an even
sample stays in the set.
"""

import csv
import difflib
import json
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "poc" / "study"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
DETECT = ROOT / "src" / "detect.exe"
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
TESS = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TEXT_PNG = ROOT / "poc" / "text.png"
SEED = 20261010
WIDTH, HEIGHT = 1024, 576
FPS = 30
TOTAL = 900
EVEN = (56, 168, 281, 393, 506, 618, 731, 843)
TARGET = 90.0
COARSE = (28, 32, 36, 40, 44)
FONT = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 42)
FONT_SM = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 28)
FONT_LG = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 64)


def run(args, cwd=None, **kwargs):
    subprocess.run([str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", *args], check=True, cwd=cwd, **kwargs)


def load_vmaf(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    frames = sorted(payload["frames"], key=lambda row: row["frameNum"])
    scores = [float(row["metrics"]["vmaf"]) for row in frames]
    if len(scores) != TOTAL:
        raise SystemExit(f"{path} has {len(scores)} scores")
    return scores


def nth_worst(scores, n):
    return sorted(enumerate(scores), key=lambda item: item[1])[n - 1]


def settled_indexes(start, hold):
    end = start + hold
    begin = start + 8
    if begin >= end:
        return ()
    return tuple(range(begin, min(begin + 8, end)))


def hits_even(start, hold):
    window = range(start, start + hold)
    return [frame for frame in EVEN if frame in window]


def encode_file(reference, dest, crf, scenecut_off):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    args = [
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
    ]
    if scenecut_off:
        args += ["-g", "999", "-keyint_min", "999", "-sc_threshold", "0"]
    args.append(str(dest))
    run(args)


def score_file(reference, distorted, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        return load_vmaf(log_path)
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
    return load_vmaf(log_path)


def build_reference(easy, text, start, hold, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    parts = dest.parent / "_parts"
    parts.mkdir(exist_ok=True)
    pieces = [
        (easy, start, parts / "head.mkv"),
        (text, hold, parts / "hold.mkv"),
        (easy, TOTAL - start - hold, parts / "tail.mkv"),
    ]
    for image, frames, path in pieces:
        if frames <= 0:
            raise SystemExit(f"bad span {frames} for {dest}")
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
                str(path),
            ]
        )
    listing = parts / "list.txt"
    listing.write_text("file 'head.mkv'\nfile 'hold.mkv'\nfile 'tail.mkv'\n", encoding="utf-8")
    run(["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)], cwd=parts)


def measure(reference, encode_dir, score_dir, crfs, start, hold, scenecut_off):
    rows = []
    settled = settled_indexes(start, hold)
    for crf in crfs:
        distorted = encode_dir / f"crf{crf}.mp4"
        encode_file(reference, distorted, crf, scenecut_off)
        scores = score_file(reference, distorted, score_dir / f"crf{crf}.json")
        ninth_frame, ninth = nth_worst(scores, 9)
        forty_frame, forty = nth_worst(scores, 45)
        text_vote = min(scores[i] for i in settled) if settled else None
        rows.append(
            {
                "crf": crf,
                "bytes": distorted.stat().st_size,
                "spread": min(scores[frame] for frame in EVEN),
                "text": text_vote,
                "ninth": ninth,
                "ninth_frame": ninth_frame,
                "fortyfifth": forty,
                "fortyfifth_frame": forty_frame,
                "shortfall": max(0.0, TARGET - ninth),
            }
        )
    return rows


def missing_steps(rows, key):
    ranked = sorted(rows, key=lambda row: row["crf"])
    legal = [row["crf"] for row in ranked if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return []
    best = max(legal)
    higher = [row["crf"] for row in ranked if row["crf"] > best]
    if not higher:
        return []
    return list(range(best + 1, min(higher)))


def choose(rows, key):
    legal = [row for row in rows if row[key] is not None and row[key] >= TARGET]
    if not legal:
        return None
    return max(legal, key=lambda row: row["crf"])


def ensure_clip(name, easy, start, hold, scenecut_off, crfs):
    clip = STUDY / "clips" / name
    reference = clip / "reference.mkv"
    build_reference(easy, TEXT_PNG, start, hold, reference)
    encode_dir = clip / ("encodes_b" if not scenecut_off else "encodes")
    score_dir = clip / ("scores_b" if not scenecut_off else "scores")
    rows = measure(reference, encode_dir, score_dir, crfs, start, hold, scenecut_off)
    if scenecut_off:
        extra = sorted(set(missing_steps(rows, "spread") + missing_steps(rows, "text")))
        if extra:
            print(f"  finer CRFs for {name}: {extra}")
            rows = measure(reference, encode_dir, score_dir, list(crfs) + extra, start, hold, True)
    write_rows(score_dir / "summary.csv", rows)
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_slides():
    out = STUDY / "slides"
    out.mkdir(parents=True, exist_ok=True)
    specs = [
        ("title", (248, 249, 252), "Week 4 recap", "One heading on a plain field"),
        ("bullets", (255, 255, 255), "Three points", "Read the chapter\nBring one question\nStart the lab"),
        ("diagram", (245, 248, 252), "A short path", "boxes"),
        ("form", (255, 255, 255), "Sign-in sheet", "form"),
        ("stat", (252, 252, 252), "Attendance", "86%"),
        ("quote", (255, 252, 246), "A short quote", "Measure the frame you would actually read."),
        ("columns", (255, 255, 255), "Two columns", "Left note goes here\n\nRight note goes here"),
        ("agenda", (250, 250, 250), "Agenda", "1  Open\n2  Example\n3  Close"),
        ("table", (255, 255, 255), "A small table", "table"),
        ("dark", (32, 36, 44), "Section break", "Plain dark slide"),
        ("equation", (255, 255, 255), "One line", "y = 90 - shortfall"),
        ("caption", (248, 248, 248), "Figure 2", "A caption under an empty box"),
    ]
    paths = []
    for name, bg, title, body in specs:
        image = Image.new("RGB", (WIDTH, HEIGHT), bg)
        draw = ImageDraw.Draw(image)
        fill = (20, 24, 28) if sum(bg) > 400 else (235, 238, 242)
        draw.text((70, 60), title, font=FONT_LG, fill=fill)
        if body == "boxes":
            draw.rounded_rectangle((80, 220, 300, 360), 12, outline=fill, width=4)
            draw.rounded_rectangle((400, 220, 620, 360), 12, outline=fill, width=4)
            draw.line((300, 290, 400, 290), fill=fill, width=4)
            draw.text((110, 260), "Input", font=FONT, fill=fill)
            draw.text((430, 260), "Score", font=FONT, fill=fill)
        elif body == "form":
            y = 200
            for label in ("Name", "Section", "Date"):
                draw.text((80, y), label, font=FONT, fill=fill)
                draw.line((280, y + 40, 900, y + 40), fill=fill, width=2)
                y += 100
        elif body == "table":
            for col in range(3):
                for row in range(3):
                    x = 80 + col * 280
                    y = 200 + row * 90
                    draw.rectangle((x, y, x + 260, y + 80), outline=fill, width=2)
                    draw.text((x + 20, y + 20), f"R{row + 1} C{col + 1}", font=FONT_SM, fill=fill)
        elif body == "A caption under an empty box":
            draw.rectangle((80, 180, 940, 430), outline=fill, width=3)
            draw.text((80, 460), body, font=FONT, fill=fill)
        else:
            draw.multiline_text((80, 220), body, font=FONT, fill=fill, spacing=16)
        path = out / f"{name}.png"
        image.save(path)
        paths.append(path)
    return paths


def detect_cuts(reference):
    ffmpeg = subprocess.Popen(
        [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-i", str(reference), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        stdout=subprocess.PIPE,
    )
    proc = subprocess.run(
        [str(DETECT), str(WIDTH), str(HEIGHT), "-"],
        stdin=ffmpeg.stdout,
        capture_output=True,
        text=True,
        check=True,
    )
    ffmpeg.stdout.close()
    ffmpeg.wait()
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
    return cuts


def ocr_text(image_path):
    cache = image_path.with_suffix(".txt")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    proc = subprocess.run(
        [str(TESS), str(image_path), "stdout", "--psm", "6"],
        capture_output=True,
        check=False,
    )
    text = (proc.stdout or b"").decode("utf-8", errors="replace")
    letters = "".join(ch.lower() for ch in text if ch.isalnum())
    cache.write_text(letters, encoding="utf-8")
    return letters


def frame_recall(reference_text, distorted_text):
    if not reference_text:
        return None
    return difflib.SequenceMatcher(None, reference_text, distorted_text).ratio()


def ocr_pair(reference, distorted, start, hold, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    ratios = []
    for frame in range(start, start + hold):
        ref_png = dest_dir / f"ref_{frame}.png"
        dist_png = dest_dir / f"dist_{frame}.png"
        if not ref_png.exists():
            run(["-i", str(reference), "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", str(ref_png)])
        if not dist_png.exists():
            run(["-i", str(distorted), "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", str(dist_png)])
        ratio = frame_recall(ocr_text(ref_png), ocr_text(dist_png))
        if ratio is not None:
            ratios.append(ratio)
    if not ratios:
        return None
    return sum(ratios) / len(ratios), min(ratios)


def decision_row(name, group, start, hold, scenecut_off, rows, cuts):
    spread = choose(rows, "spread")
    text = choose(rows, "text")
    return {
        "name": name,
        "group": group,
        "start": start,
        "hold": hold,
        "even_hit": " ".join(str(frame) for frame in hits_even(start, hold)),
        "cuts": " ".join(str(frame) for frame in cuts),
        "settled": " ".join(str(frame) for frame in settled_indexes(start, hold)),
        "scenecut_off": int(scenecut_off),
        "spread_crf": "" if spread is None else spread["crf"],
        "text_crf": "" if text is None else text["crf"],
        "spread_short": "" if spread is None else f"{spread['shortfall']:.2f}",
        "text_short": "" if text is None else f"{text['shortfall']:.2f}",
        "spread_bytes": "" if spread is None else spread["bytes"],
        "text_bytes": "" if text is None else text["bytes"],
        "spread_9th_frame": "" if spread is None else spread["ninth_frame"],
        "text_9th_frame": "" if text is None else text["ninth_frame"],
        "spread_45th_frame": "" if spread is None else spread["fortyfifth_frame"],
        "text_45th_frame": "" if text is None else text["fortyfifth_frame"],
        "separated": int(spread is not None and text is not None and spread["crf"] != text["crf"]),
    }


def bootstrap(diffs):
    rng = random.Random(SEED)
    means = []
    n = len(diffs)
    for _ in range(10000):
        draw = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(draw) / n)
    means.sort()
    return sum(diffs) / n, means[249], means[9749]


def rows_from_existing(summary, start, hold):
    loaded = []
    with summary.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            loaded.append(
                {
                    "crf": int(raw["crf"]),
                    "bytes": int(raw["bytes"]),
                    "spread": float(raw["spread_vote"]),
                    "text": float(raw["text_vote"]),
                    "ninth": float(raw["ninth"]),
                    "ninth_frame": int(raw["ninth_frame"]),
                    "fortyfifth": float(raw["fortyfifth"]),
                    "fortyfifth_frame": int(raw["fortyfifth_frame"]),
                    "shortfall": float(raw["shortfall"]),
                }
            )
    # Existing logs used a fixed text window of 108-115. Rebuild text vote if needed.
    return loaded


def rebuild_votes_from_json(score_dir, start, hold):
    rows = []
    settled = settled_indexes(start, hold)
    for path in sorted(score_dir.glob("crf*.json")):
        crf = int(path.stem.replace("crf", ""))
        scores = load_vmaf(path)
        ninth_frame, ninth = nth_worst(scores, 9)
        forty_frame, forty = nth_worst(scores, 45)
        mp4 = score_dir.parent / "encodes" / f"crf{crf}.mp4"
        rows.append(
            {
                "crf": crf,
                "bytes": mp4.stat().st_size,
                "spread": min(scores[frame] for frame in EVEN),
                "text": min(scores[i] for i in settled) if settled else None,
                "ninth": ninth,
                "ninth_frame": ninth_frame,
                "fortyfifth": forty,
                "fortyfifth_frame": forty_frame,
                "shortfall": max(0.0, TARGET - ninth),
            }
        )
    return rows


def main():
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / "seed.txt").write_text(f"{SEED}\n", encoding="utf-8")
    rng = random.Random(SEED)
    slides = make_slides()
    draws = [rng.randint(180, 700) for _ in slides]
    with (STUDY / "draws.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["slide", "start", "hold"])
        for path, start in zip(slides, draws):
            writer.writerow([path.name, start, 20])
        writer.writerow(["title-hold", 400, 8])
        writer.writerow(["title-hold", 400, 20])
        writer.writerow(["title-hold", 400, 60])
    print("draws written", draws)

    subprocess.run(
        [str(GCC), "-O2", "-mavx2", "-o", str(DETECT), str(ROOT / "src" / "detect.c"), str(ROOT / "src" / "sad_avx2.s")],
        check=True,
    )

    decisions = []
    for path, start in zip(slides, draws):
        name = path.stem
        print("clip", name, "start", start)
        rows = ensure_clip(name, path, start, 20, True, COARSE)
        cuts = detect_cuts(STUDY / "clips" / name / "reference.mkv")
        print("  cuts", cuts)
        decisions.append(decision_row(name, "screen", start, 20, True, rows, cuts))

    title = STUDY / "slides" / "title.png"
    for hold in (8, 20, 60):
        name = f"hold{hold}"
        print("hold", hold)
        rows = ensure_clip(name, title, 400, hold, True, COARSE)
        cuts = detect_cuts(STUDY / "clips" / name / "reference.mkv")
        decisions.append(decision_row(name, "hold", 400, hold, True, rows, cuts))

    existing = [
        ("blank", ROOT / "poc", 100, 20, "screen"),
        ("chart", ROOT / "poc" / "chart", 100, 20, "screen"),
        ("news", ROOT / "poc" / "news", 100, 20, "screen"),
        ("cat", ROOT / "poc" / "cat", 100, 20, "boundary"),
        ("gravel", ROOT / "poc" / "gravel", 100, 20, "boundary"),
        ("leaves", ROOT / "poc" / "leaves", 100, 20, "boundary"),
    ]
    for name, folder, start, hold, group in existing:
        print("existing", name)
        if name in ("chart", "news"):
            rows = measure(
                folder / "reference.mkv",
                folder / "encodes",
                folder / "scores",
                list(range(28, 37)),
                start,
                hold,
                True,
            )
        else:
            rows = rebuild_votes_from_json(folder / "scores", start, hold)
        decisions.append(decision_row(name, group, start, hold, True, rows, [start, start + hold]))

    for source_name, folder in (("chart", ROOT / "poc" / "chart"), ("news", ROOT / "poc" / "news")):
        print("scene-cut on", source_name)
        rows = measure(
            folder / "reference.mkv",
            STUDY / "scenecut" / source_name / "encodes",
            STUDY / "scenecut" / source_name / "scores",
            list(range(28, 37)) + [40, 44],
            100,
            20,
            False,
        )
        decisions.append(decision_row(f"{source_name}-scenecut", "scenecut", 100, 20, False, rows, [100, 120]))

    fields = list(decisions[0].keys())
    with (STUDY / "decisions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(decisions)

    finish(decisions)


def _num(row, key, kind):
    value = row[key]
    if value == "" or value is None:
        return None
    return kind(value)


def _in_hold(row, frame_key):
    frame = _num(row, frame_key, int)
    if frame is None:
        return False
    start = int(row["start"])
    return start <= frame < start + int(row["hold"])


def finish(decisions):
    for row in decisions:
        row["separated"] = int(row["separated"])

    screen = [
        row
        for row in decisions
        if row["group"] == "screen" and row["spread_short"] != "" and row["text_short"] != ""
    ]
    diffs = [float(row["spread_short"]) - float(row["text_short"]) for row in screen]
    mean, low, high = bootstrap(diffs) if diffs else (0, 0, 0)
    no_blank = [row for row in screen if row["name"] != "blank"]
    diffs_nb = [float(row["spread_short"]) - float(row["text_short"]) for row in no_blank]
    mean_nb, low_nb, high_nb = bootstrap(diffs_nb) if diffs_nb else (0, 0, 0)
    slides = [row for row in screen if row["name"] not in ("blank", "chart", "news")]
    slide_gaps = [float(row["spread_short"]) - float(row["text_short"]) for row in slides]
    slide_steps = [int(row["spread_crf"]) - int(row["text_crf"]) for row in slides]
    size_ratios = [
        int(row["text_bytes"]) / int(row["spread_bytes"])
        for row in screen
        if row["separated"] == 1 and row["spread_bytes"] not in ("", "0")
    ]
    tracked = [
        row
        for row in screen
        if _in_hold(row, "spread_9th_frame") and not _in_hold(row, "spread_45th_frame")
    ]
    even_hits = [row["name"] for row in slides if row["even_hit"].strip()]

    ocr_lines = []
    for source_name, folder, start in (
        ("chart", ROOT / "poc" / "chart", 100),
        ("news", ROOT / "poc" / "news", 100),
    ):
        chosen = next(row for row in decisions if row["name"] == source_name)
        if chosen["text_crf"] == "" or chosen["spread_crf"] == "":
            continue
        jobs = [("text", chosen["text_crf"]), ("spread", chosen["spread_crf"]), ("harsh", "44")]
        for label, crf in jobs:
            result = ocr_pair(
                folder / "reference.mkv",
                folder / "encodes" / f"crf{crf}.mp4",
                start,
                20,
                STUDY / "ocr" / f"{source_name}-{label}",
            )
            mean_ratio, worst_ratio = (None, None) if result is None else result
            ocr_lines.append((source_name, label, crf, mean_ratio, worst_ratio))
            print("ocr", source_name, label, crf, mean_ratio, worst_ratio)

    viewer_lines = [row for row in decisions if row["separated"] == 1 and row["group"] == "screen"]
    (STUDY / "viewer_pairs.csv").write_text(
        "name,spread_crf,text_crf,note\n"
        + "".join(
            f"{row['name']},{row['spread_crf']},{row['text_crf']},no viewers recruited\n"
            for row in viewer_lines
        ),
        encoding="utf-8",
    )

    boundary = [row for row in decisions if row["group"] == "boundary"]
    holds = [row for row in decisions if row["group"] == "hold"]
    scenes = [row for row in decisions if row["group"] == "scenecut"]
    mean_ratio = sum(size_ratios) / len(size_ratios) if size_ratios else 0
    lines = [
        "# Study results",
        "",
        f"Seed {SEED}. Text starts were drawn before any even-frame collision was repaired.",
        f"Seeded slides: {len(slides)}. Draws that landed on an even sample: {len(even_hits)}.",
        "",
        f"Screen clips with both choices: {len(diffs)}. Different CRF on {sum(row['separated'] for row in screen)} of them.",
        f"Mean shortfall gap, including the blank frame: {mean:.2f}.",
        f"95% bootstrap interval, including the blank frame: {low:.2f} to {high:.2f}.",
        f"Mean shortfall gap without the blank frame: {mean_nb:.2f}.",
        f"95% bootstrap interval without the blank frame: {low_nb:.2f} to {high_nb:.2f}.",
        f"Twelve generated slides, mean shortfall gap: {sum(slide_gaps) / len(slide_gaps):.2f}.",
        f"Twelve generated slides, mean CRF step (spread minus text-aware): {sum(slide_steps) / len(slide_steps):.2f}.",
        f"On screen clips where the rules differed, the text-aware file was {mean_ratio:.2f} times the spread file, on average.",
        f"Spread-chosen screen files whose 9th-worst frame is inside the text and whose 45th-worst frame is outside it: {len(tracked)} of {len(screen)}.",
        "",
        "A positive gap means the spread-out file misses 90 by more than the text-aware file.",
        "The interval is a 10,000-draw bootstrap of that paired gap, seed 20261010, using the 2.5 and 97.5 percentiles.",
        "",
        "Boundary clips (cat, gravel, leaves) are not in the mean above.",
    ]
    for row in boundary:
        lines.append(
            f"Boundary {row['name']}: spread CRF {row['spread_crf']}, text CRF {row['text_crf']}, "
            f"shortfall {row['spread_short']} vs {row['text_short']}, "
            f"9th frame {row['spread_9th_frame']}, 45th frame {row['spread_45th_frame']}."
        )
    lines += [
        "",
        "Scene-cut rows leave x264's scene-cut detection on. Chart and news only.",
    ]
    for row in scenes:
        lines.append(
            f"Scene-cut {row['name']}: spread CRF {row['spread_crf']}, text CRF {row['text_crf']}, "
            f"shortfall {row['spread_short']} vs {row['text_short']}, "
            f"9th frame {row['spread_9th_frame']}."
        )
    lines += [
        "",
        "Hold rows use the title slide, text starting at frame 400.",
        "An 8-frame hold ends before the quarter-second wait, so the text-aware rule has no frames.",
        "Eight bad frames also cannot fill the 9th-worst slot, so the file score can still clear 90.",
    ]
    for row in holds:
        text_crf = row["text_crf"] if row["text_crf"] != "" else "none"
        text_short = row["text_short"] if row["text_short"] != "" else "none"
        lines.append(
            f"Hold {row['hold']}: spread CRF {row['spread_crf']} shortfall {row['spread_short']}, "
            f"text CRF {text_crf} shortfall {text_short}, "
            f"spread 9th frame {row['spread_9th_frame']}."
        )
    lines += [
        "",
        "No real screen recording was made. The clips are still pictures joined in software.",
        "",
        "No viewers were recruited. viewer_pairs.csv lists the screen clips whose two rules chose different files.",
        "Those files were not shown to anyone, and no opinion scores were created.",
        "",
        "OCR is the mean, across the 20 text frames, of how much that frame's read lines up with the reference read.",
        "The harsh row is CRF 44, kept as a check that the reader can fail. It is not a file either rule chose.",
        "An empty OCR cell means the engine read nothing on the clean text page.",
        "",
    ]
    for source_name, label, crf, mean_ratio, worst_ratio in ocr_lines:
        if mean_ratio is None:
            shown = "empty"
        else:
            shown = f"mean {mean_ratio:.2f}, worst frame {worst_ratio:.2f}"
        lines.append(f"OCR {source_name} {label} CRF {crf}: {shown}")
    lines.append("")
    lines.append("See decisions.csv for every clip, including the 9th-worst and 45th-worst frame numbers.")
    (STUDY / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "finish":
        with (STUDY / "decisions.csv").open(encoding="utf-8", newline="") as handle:
            finish(list(csv.DictReader(handle)))
    else:
        main()
