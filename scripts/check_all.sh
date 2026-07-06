#!/usr/bin/env bash
# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================
#
# Generate every offline-capable recipe sample and import each with the Pixano
# CLI (dry-run + real import into a throwaway data dir). This is the
# checkpoint-B loop for the cookbook in one command.
#
# Requirements: pixano >= 0.8 on PATH, pillow, numpy; opencv-python and
# `datasets` for the video/vqa recipes. Recipes needing local dataset roots run
# only when DAVIS_ROOT / FLIR_ADAS_ROOT are set.

set -u
cd "$(dirname "$0")/.."

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
PASS=()
SKIP=()
FAIL=()

run_import() { # name source_dir
    local name=$1 source_dir=$2 data_dir="$WORK/data_$1"
    mkdir -p "$data_dir/library"
    if pixano data import "$data_dir" "$source_dir" --dry-run >"$WORK/$name.dry.log" 2>&1 \
        && pixano data import "$data_dir" "$source_dir" --yes >"$WORK/$name.log" 2>&1; then
        PASS+=("$name: $(grep -o 'imported successfully.*' "$WORK/$name.log" | head -1)")
    else
        FAIL+=("$name")
        echo "--- $name FAILED; last log lines:"
        tail -5 "$WORK/$name.dry.log" "$WORK/$name.log" 2>/dev/null
    fi
}

echo "== mel (synthetic)"
python data_importation/mel/generate_sample.py "$WORK/mel_sample" --num-samples 5 >/dev/null \
    && run_import mel "$WORK/mel_sample" || FAIL+=("mel (generate)")

echo "== davis (synthetic)"
python data_importation/davis/generate_sample.py "$WORK/davis_sample" --synthetic 2 >/dev/null \
    && run_import davis "$WORK/davis_sample" || FAIL+=("davis (generate)")

echo "== unlabeled_images (synthetic inputs)"
python - "$WORK/raw_images" <<'EOF' >/dev/null
import sys
from pathlib import Path
from PIL import Image
folder = Path(sys.argv[1]); folder.mkdir(parents=True)
for i in range(3):
    Image.new("RGB", (64, 64), (40 * i, 90, 150)).save(folder / f"img_{i}.jpg")
EOF
python data_importation/unlabeled_images_folder/generate_sample.py \
    --input_folder "$WORK/raw_images" --output "$WORK/images_sample" >/dev/null \
    && run_import unlabeled_images "$WORK/images_sample" || FAIL+=("unlabeled_images (generate)")

echo "== unlabeled_videos (synthetic inputs)"
if python - "$WORK/raw_videos" <<'EOF' >/dev/null 2>&1
import sys
from pathlib import Path
import cv2
import numpy as np
folder = Path(sys.argv[1]); folder.mkdir(parents=True)
writer = cv2.VideoWriter(str(folder / "clip.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 12, (64, 64))
for i in range(24):
    frame = np.zeros((64, 64, 3), dtype=np.uint8); frame[:, (2 * i) % 64 :] = 200
    writer.write(frame)
writer.release()
EOF
then
    python data_importation/unlabeled_videos_folder/generate_sample.py \
        --input_folder "$WORK/raw_videos" --output "$WORK/videos_sample" >/dev/null \
        && run_import unlabeled_videos "$WORK/videos_sample" || FAIL+=("unlabeled_videos (generate)")
else
    SKIP+=("unlabeled_videos (opencv-python not installed)")
fi

echo "== voc (download, cached under ~/.cache/pixano/voc2007)"
if python data_importation/voc/generate_sample.py "$WORK/voc_sample" --num-samples 5 --splits train >/dev/null 2>&1; then
    run_import voc "$WORK/voc_sample"
else
    SKIP+=("voc (download failed — offline?)")
fi

echo "== vqav2 (HuggingFace download)"
if python data_importation/vqav2/generate_sample.py "$WORK/vqa_sample" --num-samples 5 >/dev/null 2>&1; then
    run_import vqav2 "$WORK/vqa_sample"
else
    SKIP+=("vqav2 (datasets not installed or offline)")
fi

echo "== davis (real root)"
if [ -n "${DAVIS_ROOT:-}" ]; then
    python data_importation/davis/generate_sample.py "$WORK/davis_real" "$DAVIS_ROOT" --num-samples 2 >/dev/null \
        && run_import davis_real "$WORK/davis_real" || FAIL+=("davis_real (generate)")
else
    SKIP+=("davis real (set DAVIS_ROOT to enable)")
fi

echo "== flir (real root, both modes)"
if [ -n "${FLIR_ADAS_ROOT:-}" ]; then
    python data_importation/flir/generate_sample.py "$WORK/flir_image" "$FLIR_ADAS_ROOT" --mode image --num-samples 5 >/dev/null \
        && run_import flir_image "$WORK/flir_image" || FAIL+=("flir_image (generate)")
    python data_importation/flir/generate_sample.py "$WORK/flir_video" "$FLIR_ADAS_ROOT" --mode video --num-samples 2 >/dev/null \
        && run_import flir_video "$WORK/flir_video" || FAIL+=("flir_video (generate)")
else
    SKIP+=("flir (set FLIR_ADAS_ROOT to enable)")
fi

echo
echo "================ SUMMARY ================"
for line in "${PASS[@]:-}"; do [ -n "$line" ] && echo "PASS  $line"; done
for line in "${SKIP[@]:-}"; do [ -n "$line" ] && echo "SKIP  $line"; done
for line in "${FAIL[@]:-}"; do [ -n "$line" ] && echo "FAIL  $line"; done
[ ${#FAIL[@]} -eq 0 ]
