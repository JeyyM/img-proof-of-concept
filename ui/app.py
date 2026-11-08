"""Side-by-side viewer for the 18 development clips.

Run from the repository root:

    python -m streamlit run ui/app.py
"""

import csv
import json
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clips"))

import build_clips  # noqa: E402
import run_system  # noqa: E402

CACHE = Path(__file__).resolve().parent / "cache"
BUILT = Path(__file__).resolve().parent / "built"
WIDTH, HEIGHT = 1920, 1080

RULES = (
    ("spread", "Even frames"),
    ("settled", "After the cut"),
    ("cut", "On the cut"),
    ("random", "Random frames"),
    ("detail", "Highest detail"),
)
RULE_NAME = dict(RULES)


def load_official():
    log = {}
    with (ROOT / "clips" / "log.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] == "built":
                log[row["clip"]] = row
    clips = []
    with (ROOT / "clips" / "decisions.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            meta = log.get(row["clip"])
            if meta is None:
                continue
            clips.append(pack(row, meta, ROOT / "clips" / "work" / row["clip"] / "encodes"))
    clips.sort(key=lambda item: item["id"])
    return clips


def load_built():
    clips = []
    if not BUILT.exists():
        return clips
    for folder in sorted(BUILT.iterdir()):
        meta_path = folder / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "built":
            continue
        decision = meta.get("decision") or {"clip": meta["id"], "group": "built"}
        clips.append(pack(decision, meta, folder / "encodes", reference=folder / "reference.mkv"))
    return clips


def pack(decision, meta, encode_dir, reference=None):
    rules = {}
    for key, _label in RULES:
        crf = str(decision.get(f"{key}_crf") or "").strip()
        path = encode_dir / f"crf{crf}.mp4" if crf else None
        if path is not None and not path.exists():
            path = None
            crf = ""
        rules[key] = {
            "crf": crf,
            "ninth": decision.get(f"{key}_ninth") or "",
            "shortfall": decision.get(f"{key}_shortfall") or "",
            "shortfall80": decision.get(f"{key}_shortfall80") or "",
            "bytes": decision.get(f"{key}_bytes") or "",
            "path": path,
        }
    ref = reference if reference is not None else ROOT / "clips" / f"{meta['clip']}.mkv"
    easy = Path(str(meta.get("easy", ""))).stem.replace("-", " ")
    dense = Path(str(meta.get("dense", ""))).stem.replace("-", " ")
    return {
        "id": meta.get("clip", meta.get("id")),
        "group": meta.get("group", "built"),
        "easy": easy,
        "dense": dense,
        "start": int(meta["start"]),
        "hold": int(meta.get("hold", 20)),
        "reference": ref,
        "rules": rules,
        "scored": bool(decision.get("spread_crf") or decision.get("settled_crf")),
    }


def clip_label(clip):
    if clip["group"] == "built":
        kind = "Built here"
    elif clip["group"] == "comparison":
        kind = "Comparison"
    else:
        kind = "Busier screen"
    return f"{clip['id']}  ·  {kind}  ·  {clip['easy']} → {clip['dense']}"


def playback(reference):
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{reference.parent.name}-{reference.stem}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    build_clips.run(
        [
            "-i", str(reference),
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "0",
            "-pix_fmt", "yuv420p",
            "-g", "999",
            "-keyint_min", "999",
            "-sc_threshold", "0",
            str(dest),
        ]
    )
    return dest


def clock(frame):
    seconds = frame / 30
    return f"{int(seconds // 60)}:{seconds % 60:04.1f}"


def number(text, digits=2):
    if text is None or str(text).strip() == "":
        return None
    return float(text)


def bytes_label(text):
    value = number(text, 0)
    if value is None:
        return "—"
    return f"{int(value):,} bytes"


def rule_table(clip):
    rows = []
    for key, label in RULES:
        rule = clip["rules"][key]
        if not rule["crf"]:
            rows.append([label, "No file", "—", "—", "—", "—"])
            continue
        ninth = number(rule["ninth"])
        short = number(rule["shortfall"])
        short80 = number(rule["shortfall80"])
        rows.append([
            label,
            rule["crf"],
            f"{ninth:.2f}" if ninth is not None else "—",
            f"{short:.2f}" if short is not None else "—",
            f"{short80:.2f}" if short80 is not None else "—",
            bytes_label(rule["bytes"]),
        ])
    return rows


def comparison_line(clips):
    rows = [clip for clip in clips if clip["group"] == "comparison" and clip["scored"]]
    if not rows:
        return ""
    gaps = [number(clip["rules"]["spread"]["shortfall"]) for clip in rows]
    settled = [number(clip["rules"]["settled"]["shortfall"]) or 0 for clip in rows]
    ratios = []
    for clip in rows:
        left = number(clip["rules"]["spread"]["bytes"], 0)
        right = number(clip["rules"]["settled"]["bytes"], 0)
        if left and right:
            ratios.append(right / left)
    return (
        f"{len(rows)} comparison clips. Even-frame shortfall averages {sum(gaps) / len(gaps):.2f}. "
        f"Settled shortfall averages {sum(settled) / len(settled):.2f}. "
        f"Settled files average {(sum(ratios) / len(ratios) - 1) * 100:.0f}% larger."
    )


def prepare_picture(upload, dest):
    image = Image.open(upload).convert("RGB")
    width, height = image.size
    aspect = 16 / 9
    if width / height > aspect + 0.001:
        crop_w = int(round(height * aspect))
        left = (width - crop_w) // 2
        image = image.crop((left, 0, left + crop_w, height))
    elif height / width > (9 / 16) + 0.001 and width / height < aspect - 0.001:
        crop_h = int(round(width / aspect))
        top = (height - crop_h) // 2
        image = image.crop((0, top, width, top + crop_h))
    width, height = image.size
    if width < WIDTH or height < HEIGHT:
        return (
            f"{upload.name} is {width}×{height} after a 16:9 crop. "
            "The study does not upscale. Use a picture at least 1920×1080."
        )
    if (width, height) != (WIDTH, HEIGHT):
        image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return None


def score_folder(folder, reference):
    run_system.compile_detect()
    drawn = run_system.random_frames()
    crossings, easy_share, _kernel = run_system.crossings_of(reference)
    settled = run_system.settled_frames(crossings)
    on_cut = run_system.cut_frames(crossings)
    detail = run_system.detail_frames(reference, crossings)
    votes = {
        "spread": run_system.EVEN,
        "settled": settled,
        "cut": on_cut,
        "random": drawn,
        "detail": detail,
    }
    encode_dir = folder / "encodes"
    score_dir = folder / "scores"
    rows = run_system.measure(reference, encode_dir, score_dir, run_system.COARSE, [], votes)
    while True:
        extra = run_system.bracket(rows)
        extra += run_system.missing_steps(rows, "spread")
        extra += run_system.missing_steps(rows, "settled")
        have = {row["crf"] for row in rows}
        extra = sorted({crf for crf in extra if crf not in have})
        if not extra:
            break
        rows = run_system.measure(reference, encode_dir, score_dir, extra, rows, votes)
    decision = {
        "clip": folder.name,
        "group": "built",
        "cuts": " ".join(str(frame) for frame in crossings),
        "easy_below_2": f"{easy_share:.4f}",
        "settled_frames": " ".join(str(frame) for frame in settled),
        "detail_frames": " ".join(str(frame) for frame in detail),
    }
    for key in ("spread", "settled", "cut", "random", "detail"):
        picked = run_system.choose(rows, key)
        if picked is None:
            for suffix in ("crf", "ninth", "shortfall", "shortfall80", "bytes", "ninth_frame"):
                decision[f"{key}_{suffix}"] = ""
            continue
        decision[f"{key}_crf"] = picked["crf"]
        decision[f"{key}_ninth"] = f"{picked['ninth']:.4f}"
        decision[f"{key}_shortfall"] = f"{max(0.0, run_system.TARGET - picked['ninth']):.4f}"
        decision[f"{key}_shortfall80"] = f"{max(0.0, 80.0 - picked['ninth']):.4f}"
        decision[f"{key}_bytes"] = picked["bytes"]
        decision[f"{key}_ninth_frame"] = picked["ninth_frame"]
    return decision


def course_line():
    path = ROOT / "course" / "clip" / "timing.csv"
    if not path.exists():
        return ""
    medians = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            medians[row["method"]] = float(row["median_s"])
    plain = medians.get("plain_c")
    compiler = medians.get("autovectorized_c")
    avx = medians.get("avx2_asm")
    if not (plain and compiler and avx):
        return ""
    return (
        f"Course kernel, one clip. Plain {plain:.2f} s. "
        f"Compiler {compiler:.2f} s ({plain / compiler:.2f}×). "
        f"AVX2 {avx:.2f} s ({compiler / avx:.2f}×). Mismatches 0."
    )


def show_slot(title, path, caption):
    st.markdown(f"**{title}**")
    if path is None:
        st.info(caption)
        return
    st.video(str(path))
    st.caption(caption)


def watch(clips, official):
    labels = [clip_label(clip) for clip in clips]
    if not labels:
        st.write("No scored clips are on disk.")
        return
    choice = st.selectbox("Clip", labels, key="clip_choice")
    clip = clips[labels.index(choice)]
    names = [label for _key, label in RULES]
    keys = [key for key, _label in RULES]
    left_col, right_col = st.columns(2)
    with left_col:
        left_name = st.selectbox("Standard compression", names, index=0, key="left_rule")
    with right_col:
        right_name = st.selectbox(
            "Chosen when the frame changed", names, index=1, key="right_rule"
        )
    left = clip["rules"][keys[names.index(left_name)]]
    right = clip["rules"][keys[names.index(right_name)]]
    page = (
        f"Dense page at frame {clip['start']} ({clock(clip['start'])}), "
        f"for {clip['hold']} frames. Scene-cut is off on these files. "
        "Press play on each picture."
    )
    st.caption(page)
    original, standard, chosen = st.columns(3)
    with original:
        with st.spinner("Preparing the original for playback"):
            movie = playback(clip["reference"])
        show_slot("Original", movie, "Lossless reference, played back in 4:2:0 so the browser can show it.")
    with standard:
        if left["path"] is None:
            show_slot(left_name, None, "This rule had no CRF whose eight frames stayed at or above 90.")
        else:
            show_slot(
                left_name,
                left["path"],
                f"CRF {left['crf']}. 9th-worst {number(left['ninth']):.2f}. "
                f"Shortfall {number(left['shortfall']):.2f}. {bytes_label(left['bytes'])}.",
            )
    with chosen:
        if right["path"] is None:
            show_slot(right_name, None, "This rule had no CRF whose eight frames stayed at or above 90.")
        else:
            show_slot(
                right_name,
                right["path"],
                f"CRF {right['crf']}. 9th-worst {number(right['ninth']):.2f}. "
                f"Shortfall {number(right['shortfall']):.2f}. {bytes_label(right['bytes'])}.",
            )
    st.markdown("**This clip**")
    st.table(
        {
            "Rule": [row[0] for row in rule_table(clip)],
            "CRF": [row[1] for row in rule_table(clip)],
            "9th-worst": [row[2] for row in rule_table(clip)],
            "Below 90": [row[3] for row in rule_table(clip)],
            "Below 80": [row[4] for row in rule_table(clip)],
            "File size": [row[5] for row in rule_table(clip)],
        }
    )
    summary = comparison_line(official)
    if summary:
        st.caption(summary)
    if clip["group"] == "boundary":
        st.caption("This is a busier screen. It is shown here and kept out of the comparison mean.")
    if clip["group"] == "built" and not clip["scored"]:
        st.caption("This clip has an original only. Score it from Build a clip to fill the other two pictures.")


def build_tab():
    st.markdown("**Two pictures, one random cut**")
    st.write(
        "The first picture stays up. The second replaces it for 20 frames, then the first returns. "
        "The start is drawn uniformly from frame 180 through 700, and written down before the file is encoded. "
        "Pictures smaller than 1920×1080 are refused."
    )
    easy_file = st.file_uploader("Easy picture", type=["png", "jpg", "jpeg", "webp"], key="easy_up")
    dense_file = st.file_uploader("Dense page", type=["png", "jpg", "jpeg", "webp"], key="dense_up")
    if st.button("Build the clip", type="primary", disabled=not (easy_file and dense_file)):
        folder = BUILT / datetime.now().strftime("%H%M%S")
        while folder.exists():
            folder = BUILT / f"{datetime.now().strftime('%H%M%S')}-{random.SystemRandom().randrange(100, 999)}"
        folder.mkdir(parents=True)
        easy_path = folder / "easy.png"
        dense_path = folder / "dense.png"
        easy_error = prepare_picture(easy_file, easy_path)
        dense_error = prepare_picture(dense_file, dense_path)
        if easy_error or dense_error:
            shutil.rmtree(folder, ignore_errors=True)
            st.error(" ".join(part for part in (easy_error, dense_error) if part))
            return
        start = random.SystemRandom().randint(180, 700)
        meta = {
            "id": folder.name,
            "clip": folder.name,
            "group": "built",
            "easy": easy_file.name,
            "dense": dense_file.name,
            "start": start,
            "hold": 20,
            "frames": 900,
            "status": "drawn",
            "decision": None,
        }
        (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        reference = folder / "reference.mkv"
        with st.spinner("Encoding the 900-frame original"):
            build_clips.encode(easy_path, dense_path, start, reference)
        meta["status"] = "built"
        (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        st.session_state["built_id"] = folder.name
        st.rerun()

    built_id = st.session_state.get("built_id")
    if not built_id or not (BUILT / built_id / "meta.json").exists():
        return
    folder = BUILT / built_id
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    st.success(
        f"Clip {meta['id']}. The dense page starts at frame {meta['start']} "
        f"({clock(meta['start'])}) and stays for 20 frames."
    )
    show_slot("Original", playback(folder / "reference.mkv"), "The clip that was just built.")
    if meta.get("decision"):
        st.write("Scored. Open it from the clip list on Watch a clip.")
        return
    st.write(
        "Scoring runs the same CRF ladder as the 18 clips and writes the five choices. "
        "On this machine that takes a while."
    )
    if st.button("Score this clip"):
        with st.spinner("Scoring. Leave this page open."):
            decision = score_folder(folder, folder / "reference.mkv")
        meta["decision"] = decision
        meta["status"] = "built"
        (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        st.rerun()


def main():
    st.set_page_config(page_title="Page between the samples", layout="wide")
    st.title("The page between the samples")
    st.caption(
        "Original clip, the file a standard eight-frame check chose, "
        "and the file chosen from the frames after the cut."
    )
    kernel = course_line()
    if kernel:
        st.caption(kernel)
    official = load_official()
    clips = official + load_built()
    watch_tab, build = st.tabs(["Watch a clip", "Build a clip"])
    with watch_tab:
        watch(clips, official)
    with build:
        build_tab()


main()
