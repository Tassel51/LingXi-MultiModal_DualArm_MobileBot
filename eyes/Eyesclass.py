import argparse
import logging

import cv2
from PyQt5.QtCore import pyqtSignal, QObject

from eyes.camera import RealSenseCamera  # 修改这里导入适合计算机自带摄像头的相机类
from eyes.camera_data import CameraData
from eyes.device import get_device

# 设置日志级别
logging.basicConfig(level=logging.INFO)


class Eyes(QObject):
    signalGetPictures = pyqtSignal(object)
    signalThreadStart = pyqtSignal()

    def __init__(self, id, parent=None):
        super(Eyes,self).__init__(parent)
        # 解析命令行参数
        self.args = self.parse_args()

        # 连接到相机
        # self.cam = RealSenseCamera(device_id="036522073097")  # D435i
        # self.cam = RealSenseCamera(device_id="932122061130")  # D415 zo
        self.cam = RealSenseCamera(device_id=id)
        self.cam.connect()
        self.cam_data = CameraData(include_depth=self.args.use_depth, include_rgb=self.args.use_rgb)
        # 获取计算设备
        self.device = get_device(self.args.force_cpu)

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='zcup')
        parser.add_argument('--use-depth', type=int, default=1,
                            help='Use Depth image for evaluation (1/0)')
        parser.add_argument('--use-rgb', type=int, default=1,
                            help='Use RGB image for evaluation (1/0)')
        parser.add_argument('--cpu', dest='force_cpu', action='store_true', default=False,
                            help='Force code to run in CPU mode')
        return parser.parse_args()

    def run(self):
        while True:
            image_bundle, depth_intrin, aligned_depth_frame = self.cam.get_image_bundle()
            rgb = image_bundle['rgb']  # 这里返回的是BGR图
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            depth = image_bundle['aligned_depth']
            # TODD: 返回 aligned_depth_frame、 rgb、 depth_intrin
            self.signalGetPictures.emit({
                'rgb': rgb,
                'aligned_depth_frame': aligned_depth_frame,
                'depth_intrin': depth_intrin
            })



# 运行的接口
if __name__ == '__main__':
    app = Eyes()
    app.run()