# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

"""Dataset info for nuScenes multi-sensor folder imports (LIDAR_TOP + 6 cameras).

Run generate_sample.py first to produce samples/metadata.jsonl inside the
nuScenes root, then import with:

    pixano data import ./my_data ./v1.0-mini \
        --info pixano-cookbook/data_importation/nuscenes_lidar_top/info.py:dataset_info
"""

from pixano.datasets import DatasetInfo
from pixano.datasets.workspaces import WorkspaceType
from pixano.schemas import BBox, Entity, Image, KeyPoints, PointCloud, Record


dataset_info = DatasetInfo(
    name="nuScenes LIDAR_TOP mini",
    description="Multi-sensor dataset import for nuScenes mini: LIDAR_TOP + 6 cameras.",
    workspace=WorkspaceType.POINT_CLOUD,
    record=Record,
    entity=Entity,
    bbox=BBox,
    keypoint=KeyPoints,
    views={
        "point_cloud": PointCloud,
        "cam_front": Image,
        "cam_front_left": Image,
        "cam_front_right": Image,
        "cam_back": Image,
        "cam_back_left": Image,
        "cam_back_right": Image,
    },
)
