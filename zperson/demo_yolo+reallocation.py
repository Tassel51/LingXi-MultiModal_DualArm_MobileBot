# 检测谁会
import argparse
import logging
import time
# 从摄像头进行读取和处理
import cv2
from ultralytics import YOLO

import pyrealsense2 as rs
from camera import RealSenseCamera  # 修改这里导入适合计算机自带摄像头的相机类
from device import get_device
from camera_data import CameraData
# from function import cup_detect
from function import person_detect


logging.basicConfig(level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate network')
    parser.add_argument('--use-depth', type=int, default=1,
                        help='Use Depth image for evaluation (1/0)')
    parser.add_argument('--use-rgb', type=int, default=1,
                        help='Use RGB image for evaluation (1/0)')
    parser.add_argument('--cpu', dest='force_cpu', action='store_true', default=False,
                        help='Force code to run in CPU mode')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    model = YOLO('yolomodel/yolov8n.pt')

    # Connect to Camera
    logging.info('Connecting to camera...')
    # cam = RealSenseCamera(device_id=138322251749) # D455
    # cam = RealSenseCamera(device_id=932122061130) # D415
    cam = RealSenseCamera(device_id="036522073097")  # D435i
    cam.connect()
    cam_data = CameraData(include_depth=args.use_depth, include_rgb=args.use_rgb) # 有裁剪

    # Get the compute device
    device = get_device(args.force_cpu)
    while True:
        image_bundle, depth_intrin, aligned_depth_frame = cam.get_image_bundle()
        rgb = image_bundle['rgb']  # 实际上这里返回的是BGR图，有点困惑这个
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        depth = image_bundle['aligned_depth']
        x, depth_img, rgb_img = cam_data.get_data(rgb=rgb, depth=depth)

        results = model(rgb, vid_stride = 15 ,retina_masks=True) # 两个参数分别是帧间距和高分辨掩膜
        annotated_frame = results[0].plot()

        for r in results:
            annotated_frame = cup_detect(results, r, annotated_frame, rgb, aligned_depth_frame, depth_intrin)
        cv2.imshow("YOLOv8 Inference", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # 关闭串口
            print("系统终止")
            break



