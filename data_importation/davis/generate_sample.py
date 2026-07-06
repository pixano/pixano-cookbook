# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

r"""Generate a sample folder from DAVIS 2017 video object segmentation dataset.

Produces a Pixano-compatible folder structure with metadata.jsonl files
ready to import with `pixano data import`.

Usage:
    python data_importation/davis/generate_sample.py ./davis_sample /path/to/DAVIS --num-samples 5
    python data_importation/davis/generate_sample.py ./davis_sample --synthetic 2   # no DAVIS download needed

Requirements (only for --synthetic):
    pip install pillow numpy

Then import into Pixano:
    pixano data import ./my_data ./davis_sample
"""

import argparse
import json
import random
import shutil
from pathlib import Path


DATASET_YAML = """\
pixano: 2
format: pixano_jsonl
dataset:
  name: davis_2017
  workspace: video
schema:
  views:
    image: { kind: sequence_frames }
  entity:
    attrs:
      category: { type: str, default: object }
  annotations: [mask, tracklet]
"""


def _metadata_line(video_name: str, fps: int = 24) -> str:
    entry = {
        "attrs": {"status": "validated"},
        "views": {
            "image": {"frame_pattern": f"frames/{video_name}/*.jpg", "fps": fps},
        },
        "annotation_files": [
            {
                "kind": "mask",
                "view": "image",
                "pattern": f"masks/{video_name}/*.png",
                "encoding": "index_png",
                "entity_map": "auto",
            },
        ],
    }
    return json.dumps(entry, ensure_ascii=False)


def export_synthetic(output_dir: Path, num_videos: int, seed: int) -> int:
    """Write tiny synthetic frame/mask sequences — checkpoint-friendly, no DAVIS download."""
    import numpy as np
    from PIL import Image

    rng = random.Random(seed)
    split_dir = output_dir / "train"
    metadata_lines: list[str] = []
    for video_index in range(num_videos):
        video_name = f"synthetic_{video_index:02d}"
        frames_dir = split_dir / "frames" / video_name
        masks_dir = split_dir / "masks" / video_name
        frames_dir.mkdir(parents=True)
        masks_dir.mkdir(parents=True)
        for frame_index in range(4):
            frame = np.full((64, 64, 3), rng.randrange(64, 192), dtype=np.uint8)
            mask = np.zeros((64, 64), dtype=np.uint8)
            # two objects drifting right, one pixel value each (0 = background)
            for object_value in (1, 2):
                x = 8 + 12 * object_value + 3 * frame_index
                frame[10 * object_value : 10 * object_value + 12, x : x + 12] = 255
                mask[10 * object_value : 10 * object_value + 12, x : x + 12] = object_value
            Image.fromarray(frame).save(frames_dir / f"{frame_index:05d}.jpg")
            Image.fromarray(mask).save(masks_dir / f"{frame_index:05d}.png")
        metadata_lines.append(_metadata_line(video_name))
    (split_dir / "metadata.jsonl").write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")
    print(f"  train: generated {num_videos} synthetic videos in {split_dir}")
    return num_videos


def _load_split_video_names(davis_root: Path, split: str) -> list[str]:
    """Read video names for a split from ImageSets/2017/{split}.txt."""
    split_file = davis_root / "ImageSets" / "2017" / f"{split}.txt"
    if not split_file.exists():
        raise FileNotFoundError(f"Split file not found: {split_file}")
    return [line.strip() for line in split_file.read_text().splitlines() if line.strip()]


def export_split(output_dir: Path, split: str, num_samples: int, seed: int, davis_root: Path) -> int:
    """Export a sample of a DAVIS split to a Pixano-compatible folder.

    Args:
        output_dir: Root output directory (e.g. ./davis_sample).
        split: Split name ("train" or "val").
        num_samples: Maximum number of videos to export for this split.
        seed: Random seed for reproducible sampling.
        davis_root: Path to the DAVIS dataset root.

    Returns:
        Number of videos actually exported.
    """
    split_dir = output_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)

    video_names = _load_split_video_names(davis_root, split)

    rng = random.Random(seed)
    num_samples = min(num_samples, len(video_names))
    sampled_videos = sorted(rng.sample(video_names, num_samples))

    jpeg_dir = davis_root / "JPEGImages" / "Full-Resolution"
    anno_dir = davis_root / "Annotations" / "Full-Resolution"

    metadata_lines: list[str] = []

    for video_name in sampled_videos:
        # Copy frame JPEGs
        src_frames = jpeg_dir / video_name
        dst_frames = split_dir / "frames" / video_name
        dst_frames.mkdir(parents=True, exist_ok=True)
        for frame_file in sorted(src_frames.glob("*.jpg")):
            shutil.copy2(frame_file, dst_frames / frame_file.name)

        # Copy mask PNGs
        src_masks = anno_dir / video_name
        dst_masks = split_dir / "masks" / video_name
        dst_masks.mkdir(parents=True, exist_ok=True)
        for mask_file in sorted(src_masks.glob("*.png")):
            shutil.copy2(mask_file, dst_masks / mask_file.name)

        # Build metadata entry with glob patterns (JSONL v2)
        metadata_lines.append(_metadata_line(video_name))

    # Write metadata.jsonl
    metadata_path = split_dir / "metadata.jsonl"
    metadata_path.write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")

    print(f"  {split}: exported {num_samples} videos to {split_dir}")
    return num_samples


def main():
    """Generate a Pixano-compatible sample folder from DAVIS 2017."""
    parser = argparse.ArgumentParser(
        description="Generate a Pixano-compatible sample folder from DAVIS 2017.",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Output directory for the sample dataset (e.g. ./davis_sample).",
    )
    parser.add_argument(
        "davis_root",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the DAVIS dataset root (containing JPEGImages/, Annotations/, ImageSets/).",
    )
    parser.add_argument(
        "--synthetic",
        type=int,
        default=0,
        metavar="N",
        help="Generate N tiny synthetic videos instead of sampling DAVIS (no download needed).",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=5,
        help="Number of videos to sample per split (default: 5).",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        choices=["train", "val"],
        help="Splits to export (default: train val).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42).",
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    if output_dir.exists():
        parser.error(f"Output directory '{output_dir}' already exists. Remove it or choose another path.")

    if args.synthetic <= 0 and args.davis_root is None:
        parser.error("Provide a DAVIS root directory, or use --synthetic N to generate tiny sample videos.")

    output_dir.mkdir(parents=True)
    (output_dir / "dataset.yaml").write_text(DATASET_YAML, encoding="utf-8")
    print(f"Generating DAVIS 2017 sample in {output_dir}")

    total = 0
    if args.synthetic > 0:
        total = export_synthetic(output_dir, args.synthetic, args.seed)
    else:
        davis_root: Path = args.davis_root
        if not davis_root.is_dir():
            parser.error(f"DAVIS root directory '{davis_root}' does not exist.")
        for split in args.splits:
            total += export_split(output_dir, split, args.num_samples, args.seed, davis_root)

    print(f"\nDone. {total} videos exported.")
    print("\nTo import into Pixano:")
    print(f"  pixano data import ./my_data {output_dir}")


if __name__ == "__main__":
    main()
