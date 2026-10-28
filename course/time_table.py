"""Time the brightness sum on the official clip, then one full VMAF pass.

The sum is timed after the frames are in memory. Reading the clip is outside
that clock. The VMAF figure is the whole score command, including reading
both videos. It is one pass of the text-chosen file, CRF 30.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIP = Path(__file__).resolve().parent / "clip"
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
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
            "-DSAD_NAME=sad_plain",
            "-S",
            "-o",
            str(BUILD / "sad_plain.s"),
            str(SRC / "sad_scalar.c"),
        ]
    )
    gcc(
        [
            "-O2",
            "-mavx2",
            "-ftree-vectorize",
            "-DSAD_NAME=sad_autovec",
            "-S",
            "-o",
            str(BUILD / "sad_autovec.s"),
            str(SRC / "sad_scalar.c"),
        ]
    )
    gcc(
        [
            "-O2",
            "-mavx2",
            "-o",
            str(BUILD / "time_kernel.exe"),
            str(SRC / "time_kernel.c"),
            str(BUILD / "sad_plain.s"),
            str(BUILD / "sad_autovec.s"),
            str(SRC / "sad_avx2.s"),
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
            str(CLIP / "reference.mkv"),
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
    log_dir = CLIP / "timing"
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
            str(CLIP / "encodes" / "crf30.mp4"),
            "-i",
            str(CLIP / "reference.mkv"),
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
    out = CLIP / "timing.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        handle.write("method,median_s,runs_s\n")
        for row in rows:
            handle.write(f"{row['method']},{row['median_s']},{row['runs_s']}\n")
    note = CLIP / "timing.txt"
    note.write_text(
        "\n".join(
            [
                "Clip: course/clip/reference.mkv, 1920x1080, 900 frames, 899 pairs.",
                "plain_c: the detect.c loop, compiled -O2 with the vectorizer off.",
                "autovectorized_c: the same loop, compiled -O2 -mavx2 with the vectorizer on. GCC widened the bytes. It did not emit the SAD instruction.",
                "avx2_asm: src/sad_avx2.s, 32 bytes per vpsadbw. The clock covers the sum only, after frames are in memory.",
                "Five passes each. The table keeps the median, and the runs are sorted.",
                "vmaf_one_pass: one libvmaf score of encodes/crf30.mp4, 8 threads, including reading both videos.",
                f"Kernel check: {' '.join(header)}.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    print(f"vmaf_one_pass {elapsed:.6f}")


if __name__ == "__main__":
    main()
