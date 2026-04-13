# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

"""Generate metadata.jsonl for a nuScenes mini multi-sensor import.

Reads the nuScenes metadata JSON files and writes a ``samples/metadata.jsonl``
file inside the nuScenes root directory.  Each line maps one key-frame sample
token to the 7 sensor files (LIDAR_TOP + 6 cameras) using paths relative to
``<nuscenes_root>/samples/``, which is the split directory expected by
PointCloudFolderBuilder.

Usage:
    python generate_sample.py /path/to/v1.0-mini

After running, import with:
    pixano data import ./my_data /path/to/v1.0-mini \\
        --info pixano-cookbook/data_importation/nuscenes_lidar_top/info.py:dataset_info
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


# Maps nuScenes channel names to the logical view names declared in info.py
CHANNEL_TO_VIEW: dict[str, str] = {
    "LIDAR_TOP": "point_cloud",
    "CAM_FRONT": "cam_front",
    "CAM_FRONT_LEFT": "cam_front_left",
    "CAM_FRONT_RIGHT": "cam_front_right",
    "CAM_BACK": "cam_back",
    "CAM_BACK_LEFT": "cam_back_left",
    "CAM_BACK_RIGHT": "cam_back_right",
}

REQUIRED_CHANNELS = set(CHANNEL_TO_VIEW.keys())
SAMPLES_PREFIX = "samples/"


def _channel_from_filename(filename: str) -> str | None:
    """Extract the sensor channel name from a nuScenes filename path."""
    # filename looks like "samples/LIDAR_TOP/scene__LIDAR_TOP__timestamp.pcd.bin"
    parts = Path(filename).parts
    if len(parts) >= 2:
        return parts[1]  # e.g. "LIDAR_TOP" or "CAM_FRONT"
    return None


def _resolve_rel_path(samples_dir: Path, nominal_rel: str) -> str:
    """Return a path relative to samples_dir that points to an existing file.

    The nuScenes JSON stores paths like ``LIDAR_TOP/<file>``, but the actual
    layout on disk may nest files one level deeper (e.g.
    ``LIDAR_TOP/train/<file>``).  This helper checks the nominal path first,
    then looks for the file inside subdirectories.
    """
    if (samples_dir / nominal_rel).is_file():
        return nominal_rel
    # Check one-level-deep subdirectories (e.g. LIDAR_TOP/train/<file>)
    sensor_dir = nominal_rel.split("/")[0]
    filename = Path(nominal_rel).name
    for subdir in sorted((samples_dir / sensor_dir).iterdir()):
        if subdir.is_dir() and (subdir / filename).is_file():
            return f"{sensor_dir}/{subdir.name}/{filename}"
    return nominal_rel


def generate_metadata(nuscenes_root: Path) -> None:
    """Read nuScenes metadata and write samples/metadata.jsonl."""
    meta_dir = nuscenes_root / "v1.0-mini"
    if not meta_dir.is_dir():
        raise FileNotFoundError(f"nuScenes metadata directory not found: {meta_dir}")

    samples_dir = nuscenes_root / "samples"
    sample_data: list[dict] = json.loads((meta_dir / "sample_data.json").read_text())

    # Group key-frame entries by sample_token, keeping only the 7 sensors we care about
    by_sample: dict[str, dict[str, str]] = defaultdict(dict)
    for entry in sample_data:
        if not entry.get("is_key_frame"):
            continue
        channel = _channel_from_filename(entry["filename"])
        if channel not in CHANNEL_TO_VIEW:
            continue
        view_name = CHANNEL_TO_VIEW[channel]
        # Store path relative to samples/ so FolderBaseBuilder can resolve it
        # from source_dir/split_name/ = <nuscenes_root>/samples/
        nominal_rel = entry["filename"].removeprefix(SAMPLES_PREFIX)
        rel_path = _resolve_rel_path(samples_dir, nominal_rel)
        by_sample[entry["sample_token"]][view_name] = rel_path

    # Only emit samples that have all 7 sensors
    output_path = nuscenes_root / "samples" / "metadata.jsonl"
    complete = 0
    skipped = 0
    with output_path.open("w") as f:
        for sample_token, views in sorted(by_sample.items()):
            present_channels = {CHANNEL_TO_VIEW[c] for c in REQUIRED_CHANNELS}
            if not present_channels.issubset(views.keys()):
                skipped += 1
                continue
            record = {"id": sample_token, "views": views}
            f.write(json.dumps(record) + "\n")
            complete += 1

    print(f"Wrote {complete} records to {output_path} ({skipped} samples skipped due to missing sensors).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("nuscenes_root", type=Path, help="Path to the nuScenes root directory (e.g. v1.0-mini/)")
    args = parser.parse_args()
    generate_metadata(args.nuscenes_root)
