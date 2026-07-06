# Pixano Cookbook

Ready-to-run recipes that turn public or local datasets into Pixano-importable sources.

Every recipe produces the same thing: a **source folder** with a `dataset.yaml` manifest at
its root and one `metadata.jsonl` per split (JSONL v2 — see the
[Importing Data](https://pixano.github.io/pixano/getting_started/importing_data/) reference).
Import any of them with a single command, no Python schema files needed:

```sh
pixano data import ./my_data ./<sample_folder>
```

Requires **pixano ≥ 0.8** (`pip install pixano`).

## Recipes

| Recipe | Task | Data source | Extra deps |
|--------|------|-------------|------------|
| `data_importation/voc` | Object detection (bbox) | Pascal VOC 2007, auto-downloaded | `pillow` |
| `data_importation/davis` | Video object segmentation (mask sidecars, tracklets) | DAVIS 2017 root, or `--synthetic N` (no download) | `pillow numpy` (synthetic) |
| `data_importation/flir` | Multi-view RGB+thermal detection (image or video mode) | FLIR ADAS v2 root (manual download) | — |
| `data_importation/vqav2` | Visual question answering (conversations) | HuggingFace `merve/vqav2-small` | `datasets pillow` |
| `data_importation/mel` | Image–text entity linking (bbox + text spans) | Fully synthetic | `pillow` |
| `data_importation/unlabeled_images_folder` | Media-only import (no metadata at all) | Your image folder | — |
| `data_importation/unlabeled_videos_folder` | Frame-sequence import from raw videos | Your video folder | `opencv-python` |

Each `generate_sample.py` has a docstring with its exact usage; every script ends by printing
the import command for the folder it just produced. Use `pixano data import … --dry-run` to
validate a source and preview the plan without writing anything.

## Check everything at once

```sh
bash scripts/check_all.sh
```

Generates a small sample for every offline-capable recipe and runs a dry-run **and** a real
import for each (into a temporary data directory). Recipes needing local dataset roots run
only when `DAVIS_ROOT` / `FLIR_ADAS_ROOT` are set; the VQAv2 recipe needs network access to
HuggingFace and is skipped otherwise.
