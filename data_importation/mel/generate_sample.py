# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

"""Generate a synthetic multimodal entity-linking (MEL) sample folder.

Each sample pairs a generated image (colored shapes on a plain background)
with a short text mentioning the shapes. Entities link an image bounding box
to the character span of their mention in the text.

Produces a Pixano-compatible folder structure with metadata.jsonl files
ready to import with `pixano data import`.

Requirements:
    pip install pillow

Usage:
    python data_importation/mel/generate_sample.py ./mel_sample --num-samples 10

Then import into Pixano:
    pixano data import ./my_data ./mel_sample
"""

import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw


DATASET_YAML = """\
pixano: 2
format: pixano_jsonl
dataset:
  name: mel_sample
  workspace: image_text_entity_linking
schema:
  views:
    image: { kind: image }
    text: { kind: text }
  entity:
    attrs:
      name: str
  annotations: [bbox, mask, text_span]
"""

_HEADER = json.dumps({"$pixano": "jsonl/2", "defaults": {"bbox": {"format": "xywh", "is_normalized": True}}})

_SHAPES = [
    ("red square", (220, 60, 60)),
    ("blue circle", (60, 90, 220)),
    ("green triangle", (60, 180, 90)),
    ("yellow diamond", (230, 200, 60)),
]

_IMAGE_SIZE = 256


def _draw_shape(draw: ImageDraw.ImageDraw, name: str, color: tuple, box: tuple) -> None:
    x0, y0, x1, y1 = box
    if "circle" in name:
        draw.ellipse(box, fill=color)
    elif "triangle" in name:
        draw.polygon([(x0, y1), ((x0 + x1) // 2, y0), (x1, y1)], fill=color)
    elif "diamond" in name:
        mid_x, mid_y = (x0 + x1) // 2, (y0 + y1) // 2
        draw.polygon([(mid_x, y0), (x1, mid_y), (mid_x, y1), (x0, mid_y)], fill=color)
    else:
        draw.rectangle(box, fill=color)


def generate_sample(index: int, images_dir: Path, rng: random.Random) -> dict:
    """Draw 1-3 shapes, describe them in a sentence, and link mentions to boxes."""
    shapes = rng.sample(_SHAPES, rng.randint(1, 3))
    image = Image.new("RGB", (_IMAGE_SIZE, _IMAGE_SIZE), (240, 240, 235))
    draw = ImageDraw.Draw(image)

    entities = []
    mentions = []
    text = "The picture shows "
    for shape_index, (name, color) in enumerate(shapes):
        side = rng.randint(40, 70)
        x0 = rng.randint(4, _IMAGE_SIZE - side - 4)
        y0 = rng.randint(4, _IMAGE_SIZE - side - 4)
        _draw_shape(draw, name, color, (x0, y0, x0 + side, y0 + side))

        if shape_index > 0:
            text += " and " if shape_index == len(shapes) - 1 else ", "
        start = len(text) + 2  # skip "a "
        text += f"a {name}"
        mentions.append((name, start, start + len(name), (x0, y0, side)))
    text += "."

    for name, start, end, (x0, y0, side) in mentions:
        entities.append(
            {
                "attrs": {"name": name},
                "annotations": [
                    {
                        "kind": "bbox",
                        "view": "image",
                        "coords": [
                            round(x0 / _IMAGE_SIZE, 6),
                            round(y0 / _IMAGE_SIZE, 6),
                            round(side / _IMAGE_SIZE, 6),
                            round(side / _IMAGE_SIZE, 6),
                        ],
                    },
                    {
                        "kind": "text_span",
                        "view": "text",
                        "mention": name,
                        "spans_start": [start],
                        "spans_end": [end],
                    },
                ],
            }
        )

    filename = f"image_{index:03d}.jpg"
    image.save(images_dir / filename, "JPEG")
    return {
        "views": {"image": f"images/{filename}", "text": {"content": text}},
        "attrs": {"status": "validated"},
        "entities": entities,
    }


def main():
    """Generate a synthetic MEL sample folder."""
    parser = argparse.ArgumentParser(description="Generate a synthetic MEL sample folder.")
    parser.add_argument("output_dir", type=Path, help="Output directory (e.g. ./mel_sample).")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of samples (default: 10).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    if output_dir.exists():
        parser.error(f"Output directory '{output_dir}' already exists. Remove it or choose another path.")

    rng = random.Random(args.seed)
    split_dir = output_dir / "train"
    images_dir = split_dir / "images"
    images_dir.mkdir(parents=True)
    (output_dir / "dataset.yaml").write_text(DATASET_YAML, encoding="utf-8")

    lines = [_HEADER]
    for index in range(args.num_samples):
        lines.append(json.dumps(generate_sample(index, images_dir, rng), ensure_ascii=False))
    (split_dir / "metadata.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Done. {args.num_samples} samples generated in {output_dir}")
    print("\nTo import into Pixano:")
    print(f"  pixano data import ./my_data {output_dir}")


if __name__ == "__main__":
    main()
