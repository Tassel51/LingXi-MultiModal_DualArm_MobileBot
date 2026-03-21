import time
import binascii
import serial
from PyQt5.QtCore import pyqtSignal, QObject
import threading
import matplotlib.pyplot as plt
import numpy as np
from deprecated.sphinx import deprecated


class RadarControllerClass(QObject):
    signalRadarInit = pyqtSignal()
    signalRadarScan = pyqtSignal()

    @deprecated(version='1.0', reason='单线程嵌套运行太慢了')
    def __init__(self, serial_com="com3", parent=None):
        super(RadarControllerClass, self).__init__(parent)
        self.__baud_rate = 115200
        self.__serial_com = serial_com
        self.__switch = False
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
        print("雷达静态初始化线程id:", threading.currentThread().ident)
        # self.thread_radar_init()

        self.__distance_array = []

        self.__angle_array = []

        self.scan_flag = False

        self.__forward_cnt = 0
        self.__backward_cnt = 0
        self.__left_cnt = 0
        self.__right_cnt = 0

        self.forward_cnt_round = 0
        self.backward_cnt_round = 0

    @property
    def distance_array(self) -> list:
        return self.__distance_array

    @property
    def angle_array(self) -> list:
        return self.__angle_array

    @property
    def forward_cnt(self) -> int:
        return self.__forward_cnt

    @property
    def backward_cnt(self) -> int:
        return self.__backward_cnt

    @property
    def left_cnt(self) -> int:
        return self.__left_cnt

    @property
    def right_cnt(self) -> int:
        return self.__right_cnt

    def clear_data(self):
        self.__angle_array = []
        self.__distance_array = []

    def thread_radar_init(self):
        """
        雷达线程级初始化
        :return:
        """
        print("雷达运行时初始化线程id:", threading.currentThread().ident)
        self.__serial_entity = serial.Serial(self.__serial_com, self.__baud_rate, timeout=None)
        self.get_health()
        # self.radar_scan()

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

    def radar_scan(self, times=1, max_distance=1000):
        counter = 0

        self.__forward_cnt = 0
        self.__backward_cnt = 0
        self.__left_cnt = 0
        self.__right_cnt = 0

        self.__serial_entity.write(self.__commands["SCAN"])
        self.__serial_entity.read_all()
        response_prefix = self.__serial_entity.read(7)
        print(f'scan prefix:{binascii.hexlify(response_prefix).decode("utf-8")}')
        if response_prefix != bytes.fromhex("a5 5a 05 00 00 40 81"):
            self.__serial_entity.read_all()
            return
        distances = []
        angles = []

        while True:
            data = self.__serial_entity.read(5)
            decode_data = self.__decode_classic_frame(data)
            if not decode_data['S']:
                counter = counter + 1
                if counter >= times:
                    break
            real_distance = decode_data["real_distance"]
            real_angle = decode_data["real_angle"]
            # print(f'distance={real_distance}\tangle={real_angle}')
            if real_distance < max_distance and real_distance != 0:
                distances.append(real_distance)
                angles.append(np.deg2rad(real_angle))
                if 45.0 <= real_angle < 135.0:
                    self.__right_cnt += 1
                elif 135.0 <= real_angle < 225.0:
                    self.__backward_cnt += 1
                elif 225.0 <= real_angle < 315.0:
                    self.__left_cnt += 1
                else:
                    self.__forward_cnt += 1

        self.radar_stop()
        self.__angle_array = angles
        self.__distance_array = distances
        print(f'left={self.__left_cnt},right={self.__right_cnt},up={self.__forward_cnt},back={self.__backward_cnt}')

    def draw_radar_map(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, polar=True)
        ax.scatter(self.angle_array, self.distance_array, c='r', marker='o', s=2)

        ax.set_title("Radar Scan")
        ax.set_rmax(max(self.distance_array) * 1.1)  # Set max radius slightly larger than max distance

        # Set the zero location to the top
        ax.set_theta_zero_location('N')

        # Set the direction of the angle to be clockwise
        ax.set_theta_direction(-1)

        ax.grid(True)
        plt.show()

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

    def radar_express_scan(self):
        raise NotImplementedError

    def radar_force_scan(self):
        raise NotImplementedError

    def get_info(self):
        raise NotImplementedError

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
