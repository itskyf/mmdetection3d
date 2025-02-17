# Copyright (c) OpenMMLab. All rights reserved.
import os.path as osp
from typing import Callable, List, Optional, Union

import numpy as np

from mmdet3d.registry import DATASETS
from mmdet3d.structures import CameraInstance3DBoxes
from .det3d_dataset import Det3DDataset
from .kitti_dataset import KittiDataset


@DATASETS.register_module()
class WaymoDataset(KittiDataset):
    """Waymo Dataset.

    This class serves as the API for experiments on the Waymo Dataset.

    Please refer to `<https://waymo.com/open/download/>`_for data downloading.
    It is recommended to symlink the dataset root to $MMDETECTION3D/data and
    organize them as the doc shows.

    Args:
        data_root (str): Path of dataset root.
        ann_file (str): Path of annotation file.
        data_prefix (dict): data prefix for point cloud and
            camera data dict. Default to dict(
                                    pts='velodyne',
                                    CAM_FRONT='image_0',
                                    CAM_FRONT_RIGHT='image_1',
                                    CAM_FRONT_LEFT='image_2',
                                    CAM_SIDE_RIGHT='image_3',
                                    CAM_SIDE_LEFT='image_4')
        pipeline (list[dict], optional): Pipeline used for data processing.
            Defaults to None.
        modality (dict, optional): Modality to specify the sensor data used
            as input. Defaults to dict(use_lidar=True).
        default_cam_key (str, optional): Default camera key for lidar2img
            association. Defaults to 'CAM_FRONT'.
        box_type_3d (str, optional): Type of 3D box of this dataset.
            Based on the `box_type_3d`, the dataset will encapsulate the box
            to its original format then converted them to `box_type_3d`.
            Defaults to 'LiDAR' in this dataset. Available options includes:

            - 'LiDAR': Box in LiDAR coordinates.
            - 'Depth': Box in depth coordinates, usually for indoor dataset.
            - 'Camera': Box in camera coordinates.
        filter_empty_gt (bool, optional): Whether to filter empty GT.
            Defaults to True.
        test_mode (bool, optional): Whether the dataset is in test mode.
            Defaults to False.
        pcd_limit_range (list[float], optional): The range of point cloud
            used to filter invalid predicted boxes.
            Defaults to [-85, -85, -5, 85, 85, 5].
        cam_sync_instances (bool, optional): If use the camera sync label
            supported from waymo version 1.3.1. Defaults to False.
        load_interval (int, optional): load frame interval.
            Defaults to 1.
        task (str, optional): task for 3D detection (lidar, mono3d).
            lidar: take all the ground trurh in the frame.
            mono3d: take the groundtruth that can be seen in the cam.
            Defaults to 'lidar'.
        max_sweeps (int, optional): max sweep for each frame. Defaults to 0.
    """
    METAINFO = {'CLASSES': ('Car', 'Pedestrian', 'Cyclist')}

    def __init__(self,
                 data_root: str,
                 ann_file: str,
                 data_prefix: dict = dict(
                     pts='velodyne',
                     CAM_FRONT='image_0',
                     CAM_FRONT_RIGHT='image_1',
                     CAM_FRONT_LEFT='image_2',
                     CAM_SIDE_RIGHT='image_3',
                     CAM_SIDE_LEFT='image_4'),
                 pipeline: List[Union[dict, Callable]] = [],
                 modality: Optional[dict] = dict(use_lidar=True),
                 default_cam_key: str = 'CAM_FRONT',
                 box_type_3d: str = 'LiDAR',
                 filter_empty_gt: bool = True,
                 test_mode: bool = False,
                 pcd_limit_range: List[float] = [0, -40, -3, 70.4, 40, 0.0],
                 cam_sync_instances=False,
                 load_interval=1,
                 task='lidar_det',
                 max_sweeps=0,
                 **kwargs):
        self.load_interval = load_interval
        # set loading mode for different task settings
        self.cam_sync_instances = cam_sync_instances
        # construct self.cat_ids for vision-only anns parsing
        self.cat_ids = range(len(self.METAINFO['CLASSES']))
        self.cat2label = {cat_id: i for i, cat_id in enumerate(self.cat_ids)}
        self.max_sweeps = max_sweeps
        self.task = task
        # we do not provide file_client_args to custom_3d init
        # because we want disk loading for info
        # while ceph loading for KITTI2Waymo
        super().__init__(
            data_root=data_root,
            ann_file=ann_file,
            pipeline=pipeline,
            modality=modality,
            box_type_3d=box_type_3d,
            filter_empty_gt=filter_empty_gt,
            pcd_limit_range=pcd_limit_range,
            default_cam_key=default_cam_key,
            data_prefix=data_prefix,
            test_mode=test_mode,
            **kwargs)

    def parse_ann_info(self, info: dict) -> dict:
        """Get annotation info according to the given index.

        Args:
            info (dict): Data information of single data sample.

        Returns:
            dict: annotation information consists of the following keys:

                - bboxes_3d (:obj:`LiDARInstance3DBoxes`):
                    3D ground truth bboxes.
                - bbox_labels_3d (np.ndarray): Labels of ground truths.
                - gt_bboxes (np.ndarray): 2D ground truth bboxes.
                - gt_labels (np.ndarray): Labels of ground truths.
                - difficulty (int): Difficulty defined by KITTI.
                    0, 1, 2 represent xxxxx respectively.
        """
        ann_info = Det3DDataset.parse_ann_info(self, info)
        if ann_info is None:
            # empty instance
            ann_info = {}
            ann_info['gt_bboxes_3d'] = np.zeros((0, 7), dtype=np.float32)
            ann_info['gt_labels_3d'] = np.zeros(0, dtype=np.int64)

        ann_info = self._remove_dontcare(ann_info)
        # in kitti, lidar2cam = R0_rect @ Tr_velo_to_cam
        # convert gt_bboxes_3d to velodyne coordinates with `lidar2cam`
        if 'gt_bboxes' in ann_info:
            gt_bboxes = ann_info['gt_bboxes']
            gt_bboxes_labels = ann_info['gt_bboxes_labels']
        else:
            gt_bboxes = np.zeros((0, 4), dtype=np.float32)
            gt_bboxes_labels = np.zeros(0, dtype=np.int64)
        if 'centers_2d' in ann_info:
            centers_2d = ann_info['centers_2d']
            depths = ann_info['depths']
        else:
            centers_2d = np.zeros((0, 2), dtype=np.float32)
            depths = np.zeros((0), dtype=np.float32)

        if self.task == 'mono_det':
            gt_bboxes_3d = CameraInstance3DBoxes(
                ann_info['gt_bboxes_3d'],
                box_dim=ann_info['gt_bboxes_3d'].shape[-1],
                origin=(0.5, 0.5, 0.5))

        else:
            # in waymo, lidar2cam = R0_rect @ Tr_velo_to_cam
            # convert gt_bboxes_3d to velodyne coordinates with `lidar2cam`
            lidar2cam = np.array(
                info['images'][self.default_cam_key]['lidar2cam'])
            gt_bboxes_3d = CameraInstance3DBoxes(
                ann_info['gt_bboxes_3d']).convert_to(self.box_mode_3d,
                                                     np.linalg.inv(lidar2cam))
        ann_info['gt_bboxes_3d'] = gt_bboxes_3d

        anns_results = dict(
            gt_bboxes_3d=gt_bboxes_3d,
            gt_labels_3d=ann_info['gt_labels_3d'],
            gt_bboxes=gt_bboxes,
            gt_bboxes_labels=gt_bboxes_labels,
            centers_2d=centers_2d,
            depths=depths)

        return anns_results

    def load_data_list(self) -> List[dict]:
        """Add the load interval."""
        data_list = super().load_data_list()
        data_list = data_list[::self.load_interval]
        return data_list

    def parse_data_info(self, info: dict) -> dict:
        """if task is lidar or multiview det, use super() method elif task is
        mono3d, split the info from frame-wise to img-wise."""
        if self.task != 'mono_det':
            if self.cam_sync_instances:
                # use the cam sync labels
                info['instances'] = info['cam_sync_instances']
            return super().parse_data_info(info)
        else:
            # in the mono3d, the instances is from cam sync.
            data_list = []
            if self.modality['use_lidar']:
                info['lidar_points']['lidar_path'] =  \
                    osp.join(
                        self.data_prefix.get('pts', ''),
                        info['lidar_points']['lidar_path'])

            if self.modality['use_camera']:
                for cam_key, img_info in info['images'].items():
                    if 'img_path' in img_info:
                        cam_prefix = self.data_prefix.get(cam_key, '')
                        img_info['img_path'] = osp.join(
                            cam_prefix, img_info['img_path'])

            for (cam_key, img_info) in info['images'].items():
                camera_info = dict()
                camera_info['images'] = dict()
                camera_info['images'][cam_key] = img_info
                if 'cam_instances' in info \
                        and cam_key in info['cam_instances']:
                    camera_info['instances'] = info['cam_instances'][cam_key]
                else:
                    camera_info['instances'] = []
                camera_info['ego2global'] = info['ego2global']
                if 'image_sweeps' in info:
                    camera_info['image_sweeps'] = info['image_sweeps']

                # TODO check if need to modify the sample id
                # TODO check when will use it except for evaluation.
                camera_info['sample_idx'] = info['sample_idx']

                if not self.test_mode:
                    # used in training
                    camera_info['ann_info'] = self.parse_ann_info(camera_info)
                if self.test_mode and self.load_eval_anns:
                    info['eval_ann_info'] = self.parse_ann_info(info)
                data_list.append(camera_info)
            return data_list
