"""Decode the course clip once and write the three cut lists."""

import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSE = Path(__file__).resolve().parent
FFMPEG = Path(
    r"C:\Users\asus\AppData\Local\Programs\Python\Python313\Lib\site-packages"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
GCC = Path(r"C:\winlibs\mingw64\bin\gcc.exe")
BUILD = COURSE / "build"
EXE = BUILD / "list_cuts.exe"
CLIP = COURSE / "clip" / "reference.mkv"


def compile_lister():
    BUILD.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(GCC), "-O2", "-fno-tree-vectorize", "-fno-tree-slp-vectorize",
            "-DSAD_NAME=sad_plain", "-c", "-o", str(BUILD / "sad_plain.o"),
            str(ROOT / "src" / "sad_scalar.c"),
        ],
        check=True,
    )
    subprocess.run(
        [
            str(GCC), "-O2", "-mavx2", "-ftree-vectorize",
            "-DSAD_NAME=sad_autovec", "-c", "-o", str(BUILD / "sad_autovec.o"),
            str(ROOT / "src" / "sad_scalar.c"),
        ],
        check=True,
    )
    subprocess.run(
        [
            str(GCC), "-O2", "-mavx2", "-o", str(EXE),
            str(COURSE / "list_cuts.c"),
            str(BUILD / "sad_plain.o"),
            str(BUILD / "sad_autovec.o"),
            str(ROOT / "src" / "sad_avx2.s"),
        ],
        check=True,
    )


def main():
    compile_lister()
    ff = subprocess.Popen(
        [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-i", str(CLIP), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        stdout=subprocess.PIPE,
    )
    det = subprocess.Popen(
        [str(EXE), "1920", "1080"],
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

    out = []
    err = []
    threads = [
        threading.Thread(target=pump),
        threading.Thread(target=lambda: out.append(det.stdout.read())),
        threading.Thread(target=lambda: err.append(det.stderr.read())),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    det.wait()
    ff.wait()
    text = b"".join(out).decode("utf-8")
    if det.returncode != 0:
        raise SystemExit(b"".join(err).decode("utf-8", "replace") or f"list_cuts exited {det.returncode}")
    dest = COURSE / "clip" / "cuts.txt"
    dest.write_text(
        "Course clip course/clip/reference.mkv. A cut is the first frame of a run whose mean absolute luma difference exceeds 2.\n"
        "The three kernels were run on the same decoded frames. The lists are the frames each kernel marked.\n"
        + text,
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main()
