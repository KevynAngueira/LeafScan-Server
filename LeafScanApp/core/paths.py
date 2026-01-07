import os
from pathlib import Path

STATIC_DIR = Path("static")
IMAGE_DIR = STATIC_DIR / "images"
VIDEO_DIR = STATIC_DIR / "videos"
PARAMS_DIR = STATIC_DIR / "params"

RESULTS_DIR = Path("Results")
SLICES_DIR = RESULTS_DIR / "tmp_slices"
OUT_DIR = RESULTS_DIR / "tmp_out"

def ensure_dirs():
    for d in [STATIC_DIR, IMAGE_DIR, VIDEO_DIR, PARAMS_DIR, RESULTS_DIR, OUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if SLICES_DIR.exists():
        import shutil
        shutil.rmtree(SLICES_DIR)
    SLICES_DIR.mkdir(parents=True, exist_ok=True)
