# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

r"""Arrange a folder of unannotated images into a Pixano-importable source.

Media-only import: a split folder of images with NO metadata.jsonl imports
as one record per file. The only other thing Pixano needs is the
dataset.yaml manifest this script writes at the source root.

Produced structure::

    output_root/
    ├── dataset.yaml
    └── val/
        ├── <image_name_0>.jpg
        └── <image_name_1>.jpg

Usage:
    python data_importation/unlabeled_images_folder/generate_sample.py --input_folder ./images --output ./sample_images

Then import into Pixano:
    pixano data import ./my_data ./sample_images
"""

import argparse
import shutil
from pathlib import Path


DATASET_YAML = """\
pixano: 2
format: pixano_jsonl
dataset:
  name: my_images
  workspace: image
schema:
  entity:
    attrs:
      category: str
      sub_category: str
      is_occluded: { type: bool, default: false }
      custom_value: { type: float, default: 0.0 }
  annotations: [bbox, mask]
"""


def generate_image_dataset(input_folder: Path, output_root: Path):
    """Copy images into a media-only Pixano source (no metadata.jsonl needed)."""
    val_images = output_root / "val"
    val_images.mkdir(parents=True, exist_ok=True)
    (output_root / "dataset.yaml").write_text(DATASET_YAML, encoding="utf-8")

    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tif"]
    copied = 0
    for img_path in sorted(input_folder.iterdir()):
        if img_path.suffix.lower() not in image_extensions:
            continue
        shutil.copy2(img_path, val_images / img_path.name)
        copied += 1

    print(f"Dataset generation complete ({copied} images).")
    print(f"\nTo import into Pixano:\n  pixano data import ./my_data {output_root}")


def main():
    """Generate a Pixano-compatible sample folder from a folder of images."""
    parser = argparse.ArgumentParser(
        description="Generate a Pixano-compatible dataset from a folder of unannotated images."
    )
    parser.add_argument("--input_folder", required=True, type=Path, help="Folder containing image files to process.")
    parser.add_argument("--output", required=True, type=Path, help="Root output directory for the dataset.")
    args = parser.parse_args()

    if not args.input_folder.is_dir():
        parser.error(f"Input folder '{args.input_folder}' does not exist.")
    if args.output.exists():
        parser.error(f"Output directory '{args.output}' already exists. Remove it or choose another path.")

    args.output.mkdir(parents=True, exist_ok=True)
    generate_image_dataset(args.input_folder, args.output)


if __name__ == "__main__":
    main()
