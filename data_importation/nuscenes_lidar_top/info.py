# =====================================
# Copyright: CEA-LIST/DIASI/SIALV/LVA
# Author : pixano@cea.fr
# License: CECILL-C
# =====================================

"""Dataset info for nuScenes LIDAR_TOP point-cloud folder imports.

Usage:
    pixano data import ./my_data ./v1.0-mini/samples/LIDAR_TOP \
        --info examples/nuscenes_lidar_top/info.py:dataset_info
"""

from pixano.datasets import DatasetInfo
from pixano.datasets.workspaces import WorkspaceType
from pixano.schemas import BBox, Entity, KeyPoints, PointCloud, Record


dataset_info = DatasetInfo(
    name="nuScenes LIDAR_TOP mini",
    description="Point-cloud dataset import for nuScenes LIDAR_TOP samples.",
    workspace=WorkspaceType.POINT_CLOUD,
    record=Record,
    entity=Entity,
    bbox=BBox,
    keypoint=KeyPoints,
    views={"point_cloud": PointCloud},
)
