"""Times the brightness sum on clip 01, and then times one full VMAF pass.

Clip 01 is the agenda slide + the article (from images/simple and
images/dense). For the brightness sum, the frames are already loaded into
memory, so reading the video isn't counted. The VMAF time is the whole
ffmpeg command though, including reading both videos. It's one pass on the
settled file (CRF 31).
"""

import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "clips"
REFERENCE = CLIPS / "01.mkv"
SETTLED = CLIPS / "work" / "01" / "encodes" / "crf31.mp4"

FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
NASM = Path(r"C:\winlibs\mingw64\bin\nasm.exe")

SRC = ROOT / "src"
BUILD = Path(__file__).resolve().parent / "build"
WIDTH, HEIGHT, FRAMES = 1920, 1080, 900


def gcc(args):
    subprocess.run([str(GCC), *args], check=True)


def build():
    """Compiles the 3 versions and links them into time_kernel.exe."""
    BUILD.mkdir(parents=True, exist_ok=True)
    source = str(SRC / "brightness_c.c")
    plain_s = str(BUILD / "brightness_ordinary_c.s")
    compiler_s = str(BUILD / "brightness_compiler_c.s")
    asm_obj = str(BUILD / "brightness_avx2.o")

    # plain C: vectorizer turned off
    gcc(["-O2", "-fno-tree-vectorize", "-fno-tree-slp-vectorize",
         "-DBRIGHTNESS_FUNCTION=brightness_ordinary_c", "-S", "-o", plain_s, source])

    # same C file, but let gcc vectorize it with AVX2
    gcc(["-O2", "-mavx2", "-ftree-vectorize",
         "-DBRIGHTNESS_FUNCTION=brightness_compiler_c", "-S", "-o", compiler_s, source])

    # our assembly version
    subprocess.run(
        [str(NASM), "-f", "win64", "-o", asm_obj, str(SRC / "brightness_avx2.asm")],
        check=True,
    )

    gcc(["-O2", "-mavx2", "-o", str(BUILD / "time_kernel.exe"),
         str(SRC / "time_kernel.c"), plain_s, compiler_s, asm_obj])


def time_kernel():
    """Pipes the decoded gray frames into time_kernel.exe and returns what it prints."""
    ff = subprocess.Popen(
        [str(FFMPEG), "-hide_banner", "-loglevel", "error",
         "-i", str(REFERENCE), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        stdout=subprocess.PIPE,
    )
    proc = subprocess.run(
        [str(BUILD / "time_kernel.exe"), str(WIDTH), str(HEIGHT), str(FRAMES)],
        stdin=ff.stdout,
        capture_output=True,
        text=True,
    )
    ff.stdout.close()
    ff.wait()
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or proc.stdout)
    print(proc.stdout, end="")
    return proc.stdout


def time_vmaf():
    """Runs one VMAF pass (settled CRF 31 file vs the lossless clip)."""
    log_dir = CLIPS / "work" / "01" / "timing"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "vmaf_pass.json"
    if log_path.exists():
        log_path.unlink()

    print("vmaf pass", flush=True)
    proc = subprocess.run(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error",
            "-i", str(SETTLED),
            "-i", str(REFERENCE),
            "-lavfi",
            "[0:v]format=yuv420p,setpts=PTS-STARTPTS[dist];"
            "[1:v]format=yuv420p,setpts=PTS-STARTPTS[ref];"
            f"[dist][ref]libvmaf=log_fmt=json:log_path={log_path.name}:n_subsample=1:n_threads=8",
            "-f", "null", "-",
        ],
        cwd=log_dir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)


def parse_kernel(text):
    """Splits time_kernel.exe's output into the check line and one row per method.
    """
    header = None
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if parts[0] == "pairs":
            header = parts
            continue
        rows.append({
            "method": parts[0],
            "median_s": parts[2],
            "runs_s": " ".join(parts[4:]),
        })
    return header, rows


def main():
    build()
    header, rows = parse_kernel(time_kernel())

    start = time.perf_counter()
    time_vmaf()
    elapsed = time.perf_counter() - start
    rows.append({"method": "vmaf_one_pass", "median_s": f"{elapsed:.6f}", "runs_s": f"{elapsed:.6f}"})

    medians = {row["method"]: float(row["median_s"]) for row in rows}
    plain = medians["brightness_ordinary_c"]
    compiler = medians["brightness_compiler_c"]
    avx2 = medians["brightness_avx2"]

    out = CLIPS / "timing.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("method,median_s,runs_s,speedup_vs_ordinary,speedup_vs_compiler\n")
        for row in rows:
            name = row["method"]
            median = medians[name]
            # vmaf isn't a speedup so leave those columns blank
            vs_plain = "" if name == "vmaf_one_pass" else f"{plain / median:.4f}"
            vs_compiler = ""
            if name not in ("brightness_ordinary_c", "vmaf_one_pass"):
                vs_compiler = f"{compiler / median:.4f}"
            f.write(f"{name},{row['median_s']},{row['runs_s']},{vs_plain},{vs_compiler}\n")

    notes = [
        "Clip: clips/01.mkv, agenda slide and article, 1920x1080, 900 frames, 899 pairs.",
        "brightness_ordinary_c: src/brightness_c.c, compiled with -O2 and the vectorizer off.",
        "brightness_compiler_c: same source, compiled with -O2 -mavx2 and the vectorizer on. GCC widened the bytes but didn't use the SAD instruction.",
        "brightness_avx2: src/brightness_avx2.asm, built with nasm -f win64, 32 bytes per vpsadbw. Only the sum is timed, after the frames are in memory.",
        "Each one ran 5 times. The table shows the median, and the runs are sorted.",
        f"Speedup, compiler vs plain: {plain / compiler:.2f}x.",
        f"Speedup, AVX2 vs compiler: {compiler / avx2:.2f}x.",
        "Encoding time isn't in this table.",
        "vmaf_one_pass: one libvmaf score of clips/work/01/encodes/crf31.mp4, 8 threads, including reading both videos. Not a speedup.",
        f"Kernel check: {' '.join(header)}.",
        "Cut lists for each kernel: clips/cuts.txt.",
        "",
    ]
    (CLIPS / "timing.txt").write_text("\n".join(notes), encoding="utf-8")

    print(f"wrote {out}")
    print(f"vmaf_one_pass {elapsed:.6f}")


if __name__ == "__main__":
    main()
