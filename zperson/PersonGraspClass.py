import argparse
import logging
import time
from typing import List
import cv2
from ultralytics import YOLO
import pyrealsense2 as rs
from zperson.camera import RealSenseCamera  # 修改这里导入适合计算机自带摄像头的相机类
from zperson.device import get_device
from zperson.camera_data import CameraData
from zperson.function import person_detect
import numpy as np

# 设置日志级别
logging.basicConfig(level=logging.INFO)


class zperson:
    def __init__(self):
        self.cam_data = None
        self.cam = None
        self.model = None
        self.args = None
        self.device = None

    # # 解析命令行参数
        # self.args = self.parse_args()
        # self.model = YOLO('yolomodel/yolov8n.pt')
        #
        # # # 连接到相机
        # self.cam = RealSenseCamera(device_id="036522073097")  # D435i
        # #
        # # self.cam = RealSenseCamera(device_id="044322072386")  # D435
        # self.cam.connect()
        # self.cam_data = CameraData(include_depth=self.args.use_depth, include_rgb=self.args.use_rgb)
        # #
        # # # 获取计算设备
        # self.device = get_device(self.args.force_cpu)

    def runtime_init(self):
        # 解析命令行参数
        self.args = self.parse_args()
        self.model = YOLO('yolomodel/yolov8n.pt')

        # # 连接到相机
        self.cam = RealSenseCamera(device_id="036522073097")  # D435i
        #
        # self.cam = RealSenseCamera(device_id="044322072386")  # D435
        self.cam.connect()
        self.cam_data = CameraData(include_depth=self.args.use_depth, include_rgb=self.args.use_rgb)
        #
        # # 获取计算设备
        self.device = get_device(self.args.force_cpu)

    def garbage_collect(self):
        self.cam.disconnect()

    def parse_args(self):
        parser = argparse.ArgumentParser(description='zperson')
        parser.add_argument('--use-depth', type=int, default=1,
                            help='Use Depth image for evaluation (1/0)')
        parser.add_argument('--use-rgb', type=int, default=1,
                            help='Use RGB image for evaluation (1/0)')
        return parser.parse_args()

    def run(self):
        self.runtime_init()
        while True:
            image_bundle, depth_intrin, aligned_depth_frame = self.cam.get_image_bundle()
            rgb = image_bundle['rgb']  # 这里返回的是BGR图
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            depth = image_bundle['aligned_depth']
            x, depth_img, rgb_img = self.cam_data.get_data(rgb=rgb, depth=depth)

            results = self.model(rgb, vid_stride=15, retina_masks=True)  # 两个参数分别是帧间距和高分辨掩膜
            annotated_frame = results[0].plot()

            for r in results:
                annotated_frame, location = person_detect(results, r, annotated_frame, aligned_depth_frame,
                                                          depth_intrin)  # 输出图像和杯子位置
                print(location)
            cv2.imshow("YOLOv8 Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("系统终止")
                break
        self.garbage_collect()

    def get_location(self):
        locations = []
        location = np.zeros((1, 3))  # 初始化列表存储所有location
        start_time = time.time()  # 记录开始时间
        self.runtime_init()
        while time.time() - start_time < 3:  # 循环运行2秒
            image_bundle, depth_intrin, aligned_depth_frame = self.cam.get_image_bundle()
            rgb = image_bundle['rgb']  # 这里返回的是BGR图
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            depth = image_bundle['aligned_depth']

            results = self.model(rgb, vid_stride=15, retina_masks=True)  # 两个参数分别是帧间距和高分辨掩膜
            annotated_frame = results[0].plot()
            for r in results:
                annotated_frame, location = person_detect(results, r, annotated_frame, aligned_depth_frame,
                                                          depth_intrin)  # 输出图像和杯子位置
                print(location)

            # print(location)
            # 检查location是否是数组且形状是否为(3,)
            if isinstance(location, np.ndarray) and location.shape == (1, 3):
                location = location.flatten()
                # print("loc",location)
                # original_position: List[float] = [location[2] * 1000,
                #                                   location[0] * 1000,
                #                                   -location[1] * 1000]
                # print("ori",original_position)
                # theta = 33.428
                #
                # theta_rad = np.deg2rad(theta)
                # R = np.array([[np.cos(theta_rad), np.sin(theta_rad), 0],
                #             [-np.sin(theta_rad), np.cos(theta_rad), 0],
                #             [0, 0, 1]])
                # new_position = np.dot(R, original_position)
                # print("new",new_position)
                if 0 not in location:
                    locations.append(location)  # 将location添加到列表中
            else:
                print("警告：location不是预期的形状，跳过。")
            cv2.imshow("YOLOv8 Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("系统终止")
                break

        if locations:  # 如果列表不为空
            # print(locations)
            locations = np.array(locations)  # 将列表转换为numpy数组
            median_location = np.median(locations, axis=0)  # 计算中位数location
            mean_location = np.mean(locations, axis=0)  # 计算平均值location
            std_dev = np.std(locations, axis=0)  # 计算标准差

            # 排除异常值，这里使用标准差作为阈值
            valid_indices = np.where((np.abs(locations - mean_location) <= 2 * std_dev).all(axis=1))
            filtered_locations = locations[valid_indices]

            final_location = np.mean(filtered_locations, axis=0)  # 计算最终的平均location
            print("Final location:", final_location)
            cv2.destroyAllWindows()
            self.garbage_collect()
            return final_location
        cv2.destroyAllWindows()
        self.garbage_collect()


# 运行的接口
if __name__ == '__main__':
    app = zperson()
    #app.run(1)
    app.get_location()  # 1 red 2 blue 3 yellow
