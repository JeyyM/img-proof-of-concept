"""Time the brightness sum on clip 01, then one full VMAF pass.

Clip 01 is the agenda slide and the article, built from images/simple and
images/dense. The sum is timed after the frames are in memory. Reading the
clip is outside that clock. The VMAF figure is the whole score command,
including reading both videos. It is one pass of the settled file, CRF 31.
"""

import subprocess
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
    BUILD.mkdir(parents=True, exist_ok=True)
    gcc(
        [
            "-O2",
            "-fno-tree-vectorize",
            "-fno-tree-slp-vectorize",
            "-DBRIGHTNESS_FUNCTION=brightness_ordinary_c",
            "-S",
            "-o",
            str(BUILD / "brightness_ordinary_c.s"),
            str(SRC / "brightness_c.c"),
        ]
    )
    gcc(
        [
            "-O2",
            "-mavx2",
            "-ftree-vectorize",
            "-DBRIGHTNESS_FUNCTION=brightness_compiler_c",
            "-S",
            "-o",
            str(BUILD / "brightness_compiler_c.s"),
            str(SRC / "brightness_c.c"),
        ]
    )
    subprocess.run(
        [
            str(NASM), "-f", "win64",
            "-o", str(BUILD / "brightness_avx2.o"),
            str(SRC / "brightness_avx2.asm"),
        ],
        check=True,
    )
    gcc(
        [
            "-O2",
            "-mavx2",
            "-o",
            str(BUILD / "time_kernel.exe"),
            str(SRC / "time_kernel.c"),
            str(BUILD / "brightness_ordinary_c.s"),
            str(BUILD / "brightness_compiler_c.s"),
            str(BUILD / "brightness_avx2.o"),
        ]
    )


def time_kernel():
    ff = subprocess.Popen(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(REFERENCE),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
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
    log_dir = CLIPS / "work" / "01" / "timing"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "vmaf_pass.json"
    if log_path.exists():
        log_path.unlink()
    print("vmaf pass", flush=True)
    proc = subprocess.run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(SETTLED),
            "-i",
            str(REFERENCE),
            "-lavfi",
            "[0:v]format=yuv420p,setpts=PTS-STARTPTS[dist];"
            "[1:v]format=yuv420p,setpts=PTS-STARTPTS[ref];"
            f"[dist][ref]libvmaf=log_fmt=json:log_path={log_path.name}:n_subsample=1:n_threads=8",
            "-f",
            "null",
            "-",
        ],
        cwd=log_dir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
    return None


def parse_kernel(text):
    rows = []
    header = None
    for line in text.splitlines():
        parts = line.split()
        if parts[0] == "pairs":
            header = parts
            continue
        rows.append(
            {
                "method": parts[0],
                "median_s": parts[2],
                "runs_s": " ".join(parts[4:]),
            }
        )
    return header, rows


def main():
    build()
    text = time_kernel()
    header, rows = parse_kernel(text)
    import time

    start = time.perf_counter()
    time_vmaf()
    elapsed = time.perf_counter() - start
    rows.append({"method": "vmaf_one_pass", "median_s": f"{elapsed:.6f}", "runs_s": f"{elapsed:.6f}"})
    by_name = {row["method"]: float(row["median_s"]) for row in rows}
    plain = by_name["brightness_ordinary_c"]
    compiler = by_name["brightness_compiler_c"]
    out = CLIPS / "timing.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        handle.write("method,median_s,runs_s,speedup_vs_ordinary,speedup_vs_compiler\n")
        for row in rows:
            name = row["method"]
            median = by_name[name]
            versus_plain = "" if name == "vmaf_one_pass" else f"{plain / median:.4f}"
            versus_compiler = ""
            if name not in ("brightness_ordinary_c", "vmaf_one_pass"):
                versus_compiler = f"{compiler / median:.4f}"
            handle.write(
                f"{name},{row['median_s']},{row['runs_s']},{versus_plain},{versus_compiler}\n"
            )
    note = CLIPS / "timing.txt"
    note.write_text(
        "\n".join(
            [
                "Clip: clips/01.mkv, agenda slide and article, 1920x1080, 900 frames, 899 pairs.",
                "brightness_ordinary_c: src/brightness_c.c, compiled -O2 with the vectorizer off.",
                "brightness_compiler_c: the same source, compiled -O2 -mavx2 with the vectorizer on. GCC widened the bytes. It did not emit the SAD instruction.",
                "brightness_avx2: src/brightness_avx2.asm, assembled with nasm -f win64, 32 bytes per vpsadbw. The clock covers the sum only, after frames are in memory.",
                "Five passes each. The table keeps the median, and the runs are sorted.",
                f"Speedup, compiler against plain: {plain / compiler:.2f}x.",
                f"Speedup, AVX2 against compiler: {compiler / by_name['brightness_avx2']:.2f}x.",
                "Encoding time is not in this table.",
                "vmaf_one_pass: one libvmaf score of clips/work/01/encodes/crf31.mp4, 8 threads, including reading both videos. It is not a speedup.",
                f"Kernel check: {' '.join(header)}.",
                "Cut lists, one per kernel: clips/cuts.txt.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    print(f"vmaf_one_pass {elapsed:.6f}")


if __name__ == "__main__":
    main()
