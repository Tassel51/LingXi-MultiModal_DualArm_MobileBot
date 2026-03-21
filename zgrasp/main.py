import argparse
import logging
import time

import cv2

import pyrealsense2 as rs
from camera import RealSenseCamera  # 修改这里导入适合计算机自带摄像头的相机类
from device import get_device
from camera_data import CameraData
from function import color_detect

# 小车控制部分
import serial
import threading

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

    # Connect to Camera
    logging.info('Connecting to camera...')
    cam = RealSenseCamera(device_id="036522073097")  # D435i
    cam.connect()
    cam_data = CameraData(include_depth=args.use_depth, include_rgb=args.use_rgb) # 有裁剪

    # Load Network
    logging.info('Loading model...')
    logging.info('Done')

    # Get the compute device
    device = get_device(args.force_cpu)
    ret = 4

    while True:
        image_bundle, depth_intrin, aligned_depth_frame = cam.get_image_bundle()
        rgb = image_bundle['rgb']  # 实际上这里返回的是BGR图，有点困惑这个
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        color_detect(rgb, depth_intrin, aligned_depth_frame, ret)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # 关闭串口
            print("系统终止")
            break
