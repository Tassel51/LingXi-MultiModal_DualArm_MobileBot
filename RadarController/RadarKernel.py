import time
import binascii
import serial
from PyQt5.QtCore import pyqtSignal, QObject
import threading
import matplotlib.pyplot as plt
import numpy as np


class RadarKernelClass(QObject):
    signalThreadInit = pyqtSignal()
    signalRoundFinish = pyqtSignal(object)

    def __init__(self, serial_com="com3", max_dist_forward=550, max_dist_backward=550, parent=None):
        super(RadarKernelClass, self).__init__(parent)
        self.__baud_rate = 115200
        self.__serial_com = serial_com
        self.__commands = {
            "STOP": bytes.fromhex("a5 25"),
            "RESET": bytes.fromhex("a5 40"),
            "SCAN": bytes.fromhex("a5 20"),
            "EXPRESS_SCAN": bytes.fromhex("a5 82"),
            "FORCE_SCAN": bytes.fromhex("a5 21"),
            "GET_INFO": bytes.fromhex("a5 50"),
            "GET_HEALTH": bytes.fromhex("a5 52"),
            "GET_SAMPLERATE": bytes.fromhex("a5 59"),
            "GET_LIDAR_CONF": bytes.fromhex("a5 84")
        }
        self.__serial_entity = serial.Serial()
        print("雷达核心静态初始化线程id:", threading.currentThread().ident)

        self.max_distance_forward = max_dist_forward
        self.max_distance_backward = max_dist_backward
        self.max_distance = max(self.max_distance_backward, self.max_distance_backward)

        self.distance_array = []
        self.angle_array = []

        self.forward_cnt = 0
        self.backward_cnt = 0
        self.left_cnt = 0
        self.right_cnt = 0

        self.forward_dist_avg = 0.0
        self.backward_dist_avg = 0.0

        self.most_forward_dist = 0.0
        self.most_backward_dist = 0.0

        self.most_forward_angle = 15.0
        self.most_backward_angle = 15.0

    def clear_data(self):
        self.angle_array = []
        self.distance_array = []

        self.forward_cnt = 0
        self.backward_cnt = 0
        self.left_cnt = 0
        self.right_cnt = 0

    def thread_radar_kernel_init(self):
        try:
            print("雷达核心运行时初始化线程id:", threading.currentThread().ident)
            self.__serial_entity = serial.Serial(self.__serial_com, self.__baud_rate, timeout=None)
            self.get_health()

            self.__serial_entity.write(self.__commands["SCAN"])
            self.__serial_entity.read_all()
            response_prefix = self.__serial_entity.read(7)
            print(f'scan prefix:{binascii.hexlify(response_prefix).decode("utf-8")}')
            if response_prefix != bytes.fromhex("a5 5a 05 00 00 40 81"):
                self.__serial_entity.read_all()
                exit(-1)
            self.clear_data()
            distances = []
            angles = []
            forward_cnt = 0
            backward_cnt = 0
            left_cnt = 0
            right_cnt = 0
            while True:
                data = self.__serial_entity.read(5)
                decode_data = self.__decode_classic_frame(data)
                if not decode_data['S']:  # 读满一周
                    self.most_backward_angle = 15
                    self.most_backward_angle = 15
                    self.angle_array = angles
                    self.distance_array = distances
                    # print(f'left={self.left_cnt},right={self.right_cnt},up={self.forward_cnt},back={self.backward_cnt}')
                    distances = []
                    angles = []

                    self.right_cnt = right_cnt
                    self.left_cnt = left_cnt
                    self.backward_cnt = backward_cnt
                    self.forward_cnt = forward_cnt

                    self.signalRoundFinish.emit({
                        "left": self.left_cnt,
                        "right": self.right_cnt,
                        "forward": self.forward_cnt,
                        "backward": self.backward_cnt
                    })

                    forward_cnt = 0
                    backward_cnt = 0
                    left_cnt = 0
                    right_cnt = 0


                real_distance = decode_data["real_distance"]
                real_angle = decode_data["real_angle"]
                # print(f'distance={real_distance}\tangle={real_angle}')
                if real_distance <= self.max_distance and real_distance != 0:
                    distances.append(real_distance)
                    angles.append(np.deg2rad(real_angle))
                    if 15.0 <= real_angle < 135.0:
                        right_cnt += 1
                        if self.forward_dist_avg == 0:
                            self.forward_dist_avg = real_distance
                        else:
                            self.forward_dist_avg = (self.forward_dist_avg + real_distance) / 2
                        if abs(real_angle) < self.most_forward_angle:
                            self.most_forward_angle = abs(real_angle)
                            self.most_forward_dist = real_distance
                    elif 175.0 <= real_angle < 205.0 and real_distance <= self.max_distance_backward:
                        backward_cnt += 1
                    elif 225.0 <= real_angle < 345.0:
                        left_cnt += 1
                    elif real_distance <= self.max_distance_forward:
                        forward_cnt += 1
                        if self.forward_dist_avg == 0:
                            self.forward_dist_avg = real_distance
                        else:
                            self.forward_dist_avg = (self.forward_dist_avg + real_distance) / 2
                        if abs(real_angle - 180) < self.most_backward_angle:
                            self.most_backward_angle = abs(real_angle - 180)
                            self.most_backward_dist =real_distance
        finally:
            self.radar_stop()

    def radar_stop(self) -> None:
        """
        雷达停止扫描\n
        这个请求没有响应报文，调用后线程会在这里阻塞5ms
        :return: None
        """
        self.__serial_entity.write(self.__commands["STOP"])
        # 需要延时至少1ms
        time.sleep(0.005)
        return

    def radar_reset(self) -> None:
        """
        雷达初始化\n
        运行该函数后雷达将回到刚刚上电后的状态\n
        该函数用于尝试将雷达从保护性停机的状态转移至正常工作状态\n
        这个请求没有响应报文，调用后线程会在这里阻塞5ms\n
        :return: None
        """
        self.__serial_entity.write(self.__commands["RESET"])
        # 需要延时至少2ms
        time.sleep(0.005)
        self.get_health()
        return

    @staticmethod
    def __decode_classic_frame(frame):
        # Ensure the frame is 5 bytes
        if len(frame) != 5:
            raise ValueError("Frame must be 5 bytes long")

        # Convert each byte to its binary representation
        bin_frame = [format(byte, '08b') for byte in frame]

        # Decode signal strength (first 6 bits of the first byte)
        signal_strength = int(bin_frame[0][:6], 2)

        # Decode S and non-S (7th and 8th bits of the first byte)
        S = bin_frame[0][6] == '1'
        non_S = bin_frame[0][7] == '1'

        # Decode angle (7 bits from the second byte and all 8 bits from the third byte)
        angle = int(bin_frame[2] + bin_frame[1][:7], 2)

        # Decode check bit C (8th bit of the second byte)
        C = bin_frame[1][7] == '1'

        # Decode distance (all 8 bits from the fourth and fifth bytes)
        distance = int(bin_frame[4] + bin_frame[3], 2)

        return {
            'signal_strength': signal_strength,
            'S': S,
            'non_S': non_S,
            'angle': angle,
            'real_angle': angle / 64.0,
            'C': C,
            'distance': distance,
            'real_distance': distance / 4.0
        }

    def get_health(self) -> int:
        """
        获取雷达健康状态
        :return: 状态码
        """
        err_code_int = -1
        self.__serial_entity.flush()
        self.__serial_entity.write(self.__commands["GET_HEALTH"])
        serial_data = self.__serial_entity.read(10)
        # self.__serial_entity.flush()
        if serial_data[:7] == bytes.fromhex("a5 5a 03 00 00 00 06"):
            status_code = int.from_bytes(serial_data[7:8], byteorder='big')
            err_code = serial_data[8:10]
            err_code_int = int.from_bytes(err_code, byteorder='big')
            status_dic = {
                0: "状态良好",
                1: "警告",
                2: "错误"
            }
            print(f'雷达健康状态：{status_dic[status_code]}')
            print(f'错误码：{bin(err_code_int)[2:].zfill(16)}')
        else:
            print("错误的prefix")
        return err_code_int

    def get_samplerate(self):
        raise NotImplementedError

    def get_radar_conf(self):
        raise NotImplementedError


if __name__ == '__main__':
    radarController = RadarControllerClass()
    radarController.thread_radar_init()

    time1 = time.time()
    radarController.radar_scan(1, 1000)
    time2 = time.time()
    radarController.radar_scan(2, 1000)
    time3 = time.time()
    print(time3 - 2 * time2 + time1)
