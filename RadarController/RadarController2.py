from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal, QObject

# from RadarController.RadarKernel import RadarKernelClass


class RadarControllerClass(QObject):
    signalRadarInit = pyqtSignal()
    signalRoundFinish = pyqtSignal(object)
    all_cnt = {
        "left": 0,
        "right": 0,
        "forward": 0,
        "backward": 0
    }

    def __init__(self, serial_com="com3", max_dist=550, parent=None):
        super(RadarControllerClass, self).__init__(parent)
        self.radarKernelThread: QThread = None
        self.__radarKernel = RadarKernelClass(serial_com=serial_com, max_dist=max_dist)
        self.__baud_rate = 115200
        self.__serial_com = serial_com
        self.__radarKernel.signalRoundFinish.connect(self.slotRoundFinish)

    def thread_radar_init(self):
        self.radarKernelThread = QThread()

        self.__radarKernel.moveToThread(self.radarKernelThread)
        self.radarKernelThread.start()
        self.__radarKernel.signalThreadInit.connect(self.__radarKernel.thread_radar_kernel_init)
        self.__radarKernel.signalThreadInit.emit()
        print(self.__radarKernel.forward_cnt)

    def distance(self) -> dict:
        return self.__radarKernel.distance_array

    def angle(self) -> dict:
        return self.__radarKernel.angle_array

    def left_cnt(self) -> int:
        return self.__radarKernel.left_cnt

    def right_cnt(self) -> int:
        return self.__radarKernel.right_cnt

    def forward_cnt(self) -> int:
        return self.__radarKernel.forward_cnt

    def backward_cnt(self) -> int:
        return self.__radarKernel.backward_cnt

    def all_cnt(self):
        return {
            "left": self.__radarKernel.left_cnt,
            "right": self.__radarKernel.right_cnt,
            "forward": self.__radarKernel.forward_cnt,
            "backward": self.__radarKernel.backward_cnt
        }

    def slotRoundFinish(self, all_cnt):
        self.all_cnt = all_cnt
        self.signalRoundFinish.emit(all_cnt)

