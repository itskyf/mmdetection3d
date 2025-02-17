# Inference

## Introduction

We provide scripts for multi-modality/single-modality (LiDAR-based/vision-based), indoor/outdoor 3D detection and 3D semantic segmentation demos. The pre-trained models can be downloaded from [model zoo](https://github.com/open-mmlab/mmdetection3d/blob/master/docs/en/model_zoo.md/). We provide pre-processed sample data from KITTI, SUN RGB-D, nuScenes and ScanNet dataset. You can use any other data following our pre-processing steps.

## Testing

### 3D Detection

#### Single-modality demo

To test a 3D detector on point cloud data, simply run:

```shell
python demo/pcd_demo.py ${PCD_FILE} ${CONFIG_FILE} ${CHECKPOINT_FILE} [--device ${GPU_ID}] [--score-thr ${SCORE_THR}] [--out-dir ${OUT_DIR}] [--show]
```

The visualization results including a point cloud and predicted 3D bounding boxes will be saved in `${OUT_DIR}/PCD_NAME`, which you can open using [MeshLab](http://www.meshlab.net/). Note that if you set the flag `--show`, the prediction result will be displayed online using [Open3D](http://www.open3d.org/).

Example on KITTI data using [SECOND](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/second) model:

```shell
python demo/pcd_demo.py demo/data/kitti/000008.bin configs/second/second_hv-secfpn_8xb6-80e_kitti-3d-car.py checkpoints/second_hv-secfpn_8xb6-80e_kitti-3d-car_20200620_230238-393f000c.pth
```

Example on SUN RGB-D data using [VoteNet](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/votenet) model:

```shell
python demo/pcd_demo.py demo/data/sunrgbd/sunrgbd_000017.bin configs/votenet/votenet_8xb16_sunrgbd-3d.py checkpoints/votenet_8xb16_sunrgbd-3d_20200620_230238-4483c0c0.pth
```

Remember to convert the VoteNet checkpoint if you are using mmdetection3d version >= 0.6.0. See its [README](https://github.com/open-mmlab/mmdetection3d/blob/master/configs/votenet/README.md/) for detailed instructions on how to convert the checkpoint.

#### Multi-modality demo

To test a 3D detector on multi-modality data (typically point cloud and image), simply run:

```shell
python demo/multi_modality_demo.py ${PCD_FILE} ${IMAGE_FILE} ${ANNOTATION_FILE} ${CONFIG_FILE} ${CHECKPOINT_FILE} [--device ${GPU_ID}] [--score-thr ${SCORE_THR}] [--out-dir ${OUT_DIR}] [--show]
```

where the `ANNOTATION_FILE` should provide the 3D to 2D projection matrix. The visualization results including a point cloud, an image, predicted 3D bounding boxes and their projection on the image will be saved in `${OUT_DIR}/PCD_NAME`.

Example on KITTI data using [MVX-Net](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/mvxnet) model:

```shell
python demo/multi_modality_demo.py demo/data/kitti/000008.bin demo/data/kitti/000008.png demo/data/kitti/000008.pkl configs/mvxnet/mvx_fpn-dv-second-secfpn_8xb2-80e_kitti-3d-3class.py checkpoints/mvx_fpn-dv-second-secfpn_8xb2-80e_kitti-3d-3class_20200621_003904-10140f2d.pth
```

Example on SUN RGB-D data using [ImVoteNet](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/imvotenet) model:

```shell
python demo/multi_modality_demo.py demo/data/sunrgbd/sunrgbd_000017.bin demo/data/sunrgbd/sunrgbd_000017.jpg demo/data/sunrgbd/sunrgbd_000017_infos.pkl configs/imvotenet/imvotenet_stage2_8xb16_sunrgbd.py checkpoints/imvotenet_stage2_8xb16_sunrgbd_20210323_184021-d44dcb66.pth
```

### Monocular 3D Detection

To test a monocular 3D detector on image data, simply run:

```shell
python demo/mono_det_demo.py ${IMAGE_FILE} ${ANNOTATION_FILE} ${CONFIG_FILE} ${CHECKPOINT_FILE} [--device ${GPU_ID}] [--cam-type ${CAM_TYPE}] [--score-thr ${SCORE-THR}] [--out-dir ${OUT_DIR}] [--show]
```

where the `ANNOTATION_FILE` should provide the 3D to 2D projection matrix (camera intrinsic matrix), and `CAM_TYPE` should be specified according to dataset. For example, if you want to inference on the front camera image, the `CAM_TYPE` should be set as `CAM_2` for KITTI, and `CAM_FRONT` for nuScenes. By specifying `CAM_TYPE`, you can even infer on any camera images for datasets with multi-view cameras, such as nuScenes and Waymo. `SCORE-THR` is the 3D bbox threshold while visualization. The visualization results including an image and its predicted 3D bounding boxes projected on the image will be saved in `${OUT_DIR}/IMG_NAME`.

Example on nuScenes data using [FCOS3D](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/fcos3d) model:

```shell
python demo/mono_det_demo.py demo/data/nuscenes/n015-2018-07-24-11-22-45+0800__CAM_BACK__1532402927637525.jpg demo/data/nuscenes/n015-2018-07-24-11-22-45+0800__CAM_BACK__1532402927637525.pkl configs/fcos3d/fcos3d_r101-caffe-dcn-fpn-head-gn_8xb2-1x_nus-mono3d_finetune.py checkpoints/fcos3d_r101-caffe-dcn-fpn-head-gn_8xb2-1x_nus-mono3d_finetune_20210717_095645-8d806dc2.pth
```

Note that when visualizing results of monocular 3D detection for flipped images, the camera intrinsic matrix should also be modified accordingly. See more details and examples in PR [#744](https://github.com/open-mmlab/mmdetection3d/pull/744).

### 3D Segmentation

To test a 3D segmentor on point cloud data, simply run:

```shell
python demo/pcd_seg_demo.py ${PCD_FILE} ${CONFIG_FILE} ${CHECKPOINT_FILE} [--device ${GPU_ID}] [--out-dir ${OUT_DIR}] [--show]
```

The visualization results including a point cloud and its predicted 3D segmentation mask will be saved in `${OUT_DIR}/PCD_NAME`.

Example on ScanNet data using [PointNet++ (SSG)](https://github.com/open-mmlab/mmdetection3d/tree/master/configs/pointnet2) model:

```shell
python demo/pc_seg_demo.py demo/data/scannet/scene0000_00.bin configs/pointnet2/pointnet2_ssg_2xb16-cosine-200e_scannet-seg.py checkpoints/pointnet2_ssg_2xb16-cosine-200e_scannet-seg_20210514_143644-ee73704a.pth
```
