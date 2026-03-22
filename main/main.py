import math
import threading
import time
from typing import List

from PyQt5 import QtGui
from PyQt5.QtCore import QThread, QTimer
import PyQt5.QtWidgets as qw
import sys
import RadarUi
import numpy as np

from RadarController.RadarKernel import RadarKernelClass

import cv2
from ultralytics import YOLO
from function import color_detect, cup_detect, person_detect
from zgrasp.PlateGraspClass import Grasp
from zcup.CupGraspClass import zcup
from SoundController.SpeechRecognitionClass import SpeechRecognition
from SoundController.TextToSpeechClass import TextToSpeech
from ArmController.serial.SerialRoboArm import SerialArmControllerClass

BLACK = 1
BLUE = 2
YELLOW = 3
RED = 4


class MainClass(qw.QWidget):
    cup_type = RED
    all_cnt = {
        "left": 0,
        "right": 0,
        "forward": 0,
        "backward": 0
    }
    r_rgb = None
    r_aligned_depth_frame = None
    r_depth_intrin = None
    r_processed_image = None

    l_rgb = None
    l_aligned_depth_frame = None
    l_depth_intrin = None
    l_processed_image = None

    forward_time = 0

    def __init__(self):
        super().__init__()
        print("主线程id:", threading.currentThread().ident)

        self.firstOperationReady = False
        self.secondOperationReady = False
        self.globalOperationBusy = False

        self.ui = RadarUi.Ui_Form()
        self.ui.setupUi(self)

        # self.armController_right = SerialArmControllerClass(serial_port="COM7")
        # self.armController_left = SerialArmControllerClass(serial_port="COM3")
        self.right_arm_port = "COM3"
        self.left_arm_port = "COM13"
        self.car_port = "COM12"

        self.radarThread = QThread()

        self.radarController = RadarKernelClass(serial_com='com14', max_dist_forward=350, max_dist_backward=500)
        self.radarController.moveToThread(self.radarThread)
        self.radarThread.start()
        self.radarController.signalThreadInit.connect(self.radarController.thread_radar_kernel_init)
        self.radarController.signalThreadInit.emit()

        self.timerRadarScan = QTimer()
        self.timerRadarScan.timeout.connect(self.radar_obstacle)
        self.timerRadarScan.start(300)
        # self.timerRightPicFlush = QTimer()
        # self.timerRightPicFlush.timeout.connect(self.right_pic_flush)
        # self.timerRightPicFlush.start(30)

        # self.carThread = QThread()
        # self.carController = CarControllerClass('com5')
        # self.carController.moveToThread(self.carThread)
        # self.carThread.start()
        # self.carController.signalCarInit.connect(self.carController.thread_car_init)
        # self.carController.signalCarInit.emit()

        # self.leftEyeThread = QThread()
        # self.leftEyeController = Eyes("932122061130")
        # self.leftEyeController.moveToThread(self.leftEyeThread)
        # self.leftEyeThread.start()
        # self.leftEyeController.signalThreadStart.connect(self.leftEyeController.run)
        # self.leftEyeController.signalThreadStart.emit()
        # self.leftEyeController.signalGetPictures.connect(self.slotGetLeftPicture)
        #
        # self.rightEyeThread = QThread()
        # self.rightEyeController = Eyes("036522073097")
        # self.rightEyeController.moveToThread(self.rightEyeThread)
        # self.rightEyeThread.start()
        # self.rightEyeController.signalThreadStart.connect(self.rightEyeController.run)
        # self.rightEyeController.signalThreadStart.emit()
        # self.rightEyeController.signalGetPictures.connect(self.slotGetRightPicture)

        self.radarController.signalRoundFinish.connect(self.slotRoundFinish)

        self.grasp_i = Grasp()
        # self.person_i = zperson()

        app_id = '64120543'
        api_key = 'jB79TAegVjEYYFwzJP95fHCJ'
        secret_key = 'pxZPDUf8VARMzKYIxyyM5AEl1SuYBwgb'
        self.recognizer = SpeechRecognition(app_id, api_key, secret_key)
        self.tts = TextToSpeech(app_id, api_key, secret_key)
        self.ui.pushButton.clicked.connect(self.operations)

    def right_pic_flush(self):
        pass

    def radar_obstacle(self):
        data = self.all_cnt
        warning_points = 10
        forward_cnt = data['forward']
        # print(data)
        print(f'forward_cnt:{forward_cnt}')

    def operations(self):
        audio_cmd = self.get_audio_cmd()
        if audio_cmd == 0:
            self.operation2()
        elif audio_cmd == 1:
            self.operation4()
        elif audio_cmd == 2:
            self.operation5_forward()
        elif audio_cmd == 3:
            self.operation7_obstacle()
        if audio_cmd == 4:
            self.operation8_findperson()

    def get_audio_cmd(self):
        while True:
            # 录音
            wav = self.recognizer.record_audio()
            # 将录音文件转换为文本
            prompt_text = self.recognizer.listen(wav)
            if "机械操作" in prompt_text:
                self.tts.speak_text("好的")
                return 0
            if "前往可乐" in prompt_text:
                self.tts.speak_text("即将前往可乐处")
                self.cup_type = RED
                self.forward_time = 0
                return 3
            if "可乐" in prompt_text:
                self.tts.speak_text("稍等，可乐马上准备好")
                self.cup_type = RED
                self.forward_time = 0
                return 1
            if '雪碧' in prompt_text:
                self.tts.speak_text("稍等，雪碧马上准备好")
                self.cup_type = BLUE
                self.forward_time = 0
                return 1
            if '开始测试' in prompt_text:
                return 4

    def operation2(self):

        armController_right = SerialArmControllerClass(serial_port=self.right_arm_port)
        armController_left = SerialArmControllerClass(serial_port=self.left_arm_port)
        time.sleep(5)
        armController_right.coord_ctrl(170, -4, 240, 170)
        time.sleep(1)
        offset_x = 205
        offset_y = 36
        offset_z = 240

        GRABBER_DELAY = 3

        base_position: List[float] = []
        camera_data = None
        # 2s
        # self.grasp_i.run(BLACK)
        for i in range(5):
            camera_data = self.grasp_i.get_location(BLACK)
            if 0 not in camera_data:
                break

        base_position: List[float] = [-camera_data[1] * 1000 + offset_x + 75,
                                      camera_data[0] * 1000 + offset_y - 40,
                                      -camera_data[2] * 1000 + offset_z + 80]
        # self.grasp_i.run(2)

        for i in range(5):
            camera_data = self.grasp_i.get_location(2)
            if 0 not in camera_data:
                break

        plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 75,
                                       camera_data[0] * 1000 + offset_y - 53,
                                       -camera_data[2] * 1000 + offset_z + 59]

        if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
            print(f'dist error')
            exit()

        armController_right.coord_ctrl(280, -14, 280, 90)

        # 抓起来圆盘，回到初始位置
        armController_right.coord_ctrl(plate_position[0]-10, plate_position[1], plate_position[2], 100, 220)

        armController_right.coord_ctrl(plate_position[0]-10, plate_position[1], plate_position[2], 100, 260)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        # 放到黑色上面
        armController_right.coord_ctrl(base_position[0]-10, base_position[1], base_position[2], 100, 260)

        armController_right.coord_ctrl(base_position[0]-10, base_position[1], base_position[2], 100, 220)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        # 识别黄色
        armController_right.coord_ctrl(170, -14, 240, 170)
        time.sleep(1)
        for i in range(5):
            camera_data = self.grasp_i.get_location(YELLOW)
            if 0 not in camera_data:
                break

        plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 62,
                                       camera_data[0] * 1000 + offset_y - 60,
                                       -camera_data[2] * 1000 + offset_z + 54]

        if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
            print(f'dist error')
            exit()

        armController_right.coord_ctrl(280, -14, 280, 90)

        # 抓起来圆盘，回到初始位置
        armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 100, 230)

        armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 100, 260)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        # 放到黑色上面
        armController_right.coord_ctrl(base_position[0] - 10, base_position[1] - 3, base_position[2] + 30, 100, 260)

        armController_right.coord_ctrl(base_position[0] - 10, base_position[1] - 3, base_position[2] + 30, 100, 180)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        armController_right.coord_ctrl(170, -14, 240, 170)
        time.sleep(1)
        for i in range(5):
            camera_data = self.grasp_i.get_location(4)
            if 0 not in camera_data:
                break

        plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 55,
                                       camera_data[0] * 1000 + offset_y - 60,
                                       -camera_data[2] * 1000 + offset_z + 46]

        if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
            print(f'dist error')
            exit()

        armController_right.coord_ctrl(280, -14, 280, 90)

        # 抓起来圆盘，回到初始位置
        armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 100, 230)

        armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 100, 260)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        # 放到黑色上面
        armController_right.coord_ctrl(base_position[0] - 10, base_position[1] - 7, base_position[2] + 50, 100, 260)

        armController_right.coord_ctrl(base_position[0] - 10, base_position[1] - 7, base_position[2] + 50, 100, 180)
        time.sleep(GRABBER_DELAY)
        armController_right.coord_ctrl(280, -14, 280, 90, 260)

        self.tts.speak_text("机械操作已经完成。")
        armController_right.arm_close()
        armController_left.arm_close()
        self.ui.pushButton.click()

    def operation4(self):
        # 倒水
        # 右臂从人的手里接水，左臂取饮料

        # 左臂150t值才平
        armController_right = SerialArmControllerClass(serial_port=self.right_arm_port)
        armController_left = SerialArmControllerClass(serial_port=self.left_arm_port)
        # ========================时刻1，初始化=========================================
        # 把右臂和左臂初始化到正前面
        armController_left.coord_ctrl()
        armController_right.coord_ctrl()
        time.sleep(2)
        armController_left.coord_ctrl(5, -280, 280, 90, 180)
        armController_left.coord_ctrl(5, -400, 150, 90, 180)
        armController_right.coord_ctrl(5, -240, 330, 90, 180)
        armController_right.coord_ctrl(-180, -180, 330, 90, 180)
        detect_person_position = [5, -240, 330]
        armController_right.coord_ctrl(detect_person_position[0], detect_person_position[1], detect_person_position[2],
                                       90, 180)
        camera_data = self.grasp_i.get_location_p()
        person_position = [camera_data[0] * 1000 + detect_person_position[0],
                           -camera_data[2] * 1000 + detect_person_position[1],
                           -camera_data[1] * 1000 + detect_person_position[2]]
        print(person_position)
        person_angle_rad = math.atan(person_position[0] / (-person_position[1]))
        person_angle = person_angle_rad / math.pi * 180
        if not -90 < person_angle < 90:
            person_angle = 45
            person_angle_rad = math.pi / 4
        person_detect_length = 250
        toward_person_x = person_detect_length * math.sin(person_angle_rad)
        toward_person_y = - person_detect_length * math.cos(person_angle_rad)
        armController_right.coord_ctrl(toward_person_x, toward_person_y, detect_person_position[2], 90, 180)

        self.tts.speak_text(
            f'人的坐标是前方{abs(int(person_position[1] / 10))}厘米,{"左" if person_position[0] < 0 else "右"}侧{abs(int(person_position[0] / 10))}厘米.')
        armController_right.coord_ctrl(280, 5, 280, 90, 180)

        grasp_entity = zcup()

        get_cup_z = 280  # 以280mm的高度从演示者手中接过杯子

        GENERAL_DELAY = 0.01
        GRABBER_DELAY = 3

        get_cup_arm_length = 280  # 从演示者手中接过杯子这一过程中的xoy平面的臂长

        get_cup_y = - get_cup_arm_length * math.cos(person_angle_rad)

        get_cup_x = get_cup_arm_length * math.sin(person_angle_rad)

        # 夹到杯子后，左臂需要回到一个中心点待命，我希望这个中心点在两臂最中间的前方
        left_arm_center_position = [325, 105, 40]

        # ================左臂从人手里拿到杯子的同时，右臂避开，左臂前往摄像头位置================================
        # armController_left.coord_ctrl(15, -280, 280, 90, 160)
        # time.sleep(GENERAL_DELAY)
        # 机械臂朝向声源，并且爪子开到最大
        armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 160)
        self.tts.speak_text("请把杯子递给我。")
        time.sleep(GENERAL_DELAY)
        # 机械臂尝试关闭，以夹取人手中的杯子
        armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 280)
        # 右臂给左臂腾出来空间
        armController_right.coord_ctrl(380, 10, 150, 90, 160)
        time.sleep(GRABBER_DELAY)

        # ======================================================

        # armController_left.coord_ctrl(15, -280, 280, 90, 280)
        # time.sleep(GENERAL_DELAY)
        detect_cup_position = [5, -200, 380]
        armController_left.coord_ctrl(detect_cup_position[0], detect_cup_position[1], detect_cup_position[2],
                                      70, 280)
        camera_data = grasp_entity.get_location(self.cup_type)

        cup_position: List[float] = [-camera_data[0] * 1000 + detect_cup_position[0],
                                     camera_data[2] * 1000 + detect_cup_position[1],
                                     -camera_data[1] * 1000 + detect_cup_position[2]]

        cup_position = self.cup_offset(cup_position)

        self.tts.speak_text(f'目标距离{int(cup_position[1] / 10 + 14)}厘米，开始朝向目标移动。')
        self.operation5_forward(self.cup_type == BLUE)

        # ====================右臂避开后左臂识别杯子的坐标参数================================================
        # TODO 调用识别函数
        camera_data = grasp_entity.get_location(self.cup_type)

        cup_position: List[float] = [-camera_data[0] * 1000 + detect_cup_position[0],
                                     camera_data[2] * 1000 + detect_cup_position[1],
                                     -camera_data[1] * 1000 + detect_cup_position[2]]

        cup_position = self.cup_offset(cup_position)

        if int(cup_position[1] / 10 + 14) > 65:
            # 太远了，遇到了障碍物
            self.tts.speak_text(f'前方遇到障碍物，停止移动，目标距离{int(cup_position[1] / 10 + 14)}厘米。')
            while True:
                time.sleep(0.1)
                print(self.radarController.forward_cnt)
                if self.radarController.forward_cnt <= 5:
                    break
            self.tts.speak_text('障碍物已经移除，开始继续移动')
            self.operation5_forward(obstacle=True)
            camera_data = grasp_entity.get_location(self.cup_type)
            cup_position = [-camera_data[0] * 1000 + detect_cup_position[0],
                            camera_data[2] * 1000 + detect_cup_position[1],
                            -camera_data[1] * 1000 + detect_cup_position[2]]

            cup_position = self.cup_offset(cup_position)

        self.tts.speak_text(f'已找到你需要的饮料，距离我{int(cup_position[1] / 10 + 14)}厘米。')
        # ====================获得参数后，左臂往正面走，前往中心姿态位置，右臂根据信息抓杯子========================
        # 右臂退出躲避相机的姿态
        armController_right.coord_ctrl(280, 15, 280, 90, 160)
        armController_left.coord_ctrl(15, -280, 280, 90, 280)
        time.sleep(GENERAL_DELAY)
        armController_right.coord_ctrl(15, 240, 320, 90, 160)
        armController_left.coord_ctrl(280, 15, 280, 90, 280)
        time.sleep(GENERAL_DELAY)
        # 右臂前往饮料位置
        armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 160)
        armController_left.coord_ctrl(left_arm_center_position[0], left_arm_center_position[1],
                                      left_arm_center_position[2], 90, 280)
        time.sleep(GENERAL_DELAY)
        # 右臂抓饮料
        armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 280)
        time.sleep(GRABBER_DELAY)

        # 抓到饮料后右臂前往初始位置
        armController_right.coord_ctrl(150, 150, 320, 90, 280)
        time.sleep(GENERAL_DELAY)
        armController_right.coord_ctrl(280, 15, 280, 90, 280)
        time.sleep(GENERAL_DELAY)
        # =====================确保左臂前往中心姿态位置后，右臂倒水，撤走=======================================
        drink_center_position = [210, -95, 180]
        # 做出倒水动作需要的t舵机倾角
        pull_coord_t = 190
        # 先前往中心位置
        armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
                                       90, 280)
        time.sleep(GENERAL_DELAY)
        # 再倾倒
        armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
                                       pull_coord_t, 280)
        time.sleep(GENERAL_DELAY)
        # 抖一下
        armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1],
                                       drink_center_position[2] - 40,
                                       pull_coord_t, 280)
        time.sleep(1.5)
        # 倒完回到水平位置
        # armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
        #                                90, 280)
        # time.sleep(GRABBER_DELAY)
        # 先回到正面
        armController_right.coord_ctrl(280, 15, 280, 90, 280)
        armController_left.coord_ctrl(280, 15, 280, 90, 280)
        time.sleep(GENERAL_DELAY)
        armController_right.coord_ctrl(160, 160, 320, 90, 280)
        armController_right.coord_ctrl(15, 280, 280, 90, 280)
        armController_left.coord_ctrl(15, -280, 280, 90, 280)
        time.sleep(GENERAL_DELAY)

        # ==========================左臂撤走，左臂右臂分别放下手里的杯子，两个臂初始化===================================
        # 左臂右臂前往拿杯子的地方
        armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 280)
        time.sleep(GENERAL_DELAY)
        armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 160)
        time.sleep(GRABBER_DELAY)
        self.operation6_backward()
        armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 280)
        if self.cup_type == RED:
            self.tts.speak_text("你的可乐倒好了。")
        else:
            self.tts.speak_text("你的雪碧倒好了。")
        # 左臂右臂松手
        armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 160)
        time.sleep(GRABBER_DELAY)
        # 左臂右臂回到预备位
        armController_right.coord_ctrl(15, 280, 280, 90, 160)
        armController_left.coord_ctrl(15, -280, 280, 90, 160)
        time.sleep(GENERAL_DELAY)
        # 直接初始化
        armController_right.arm_close()
        armController_left.arm_close()
        # armController_left.coord_ctrl()
        # armController_right.coord_ctrl()
        self.ui.pushButton.click()

    def operation5_forward(self, obstacle=False):
        # 小车向前移动，直到雷达监测到障碍
        from SoundController.CarControllerClass import CarControl
        carController = CarControl(self.car_port, 115200)
        self.tts.speak_text('前进。')
        carController.only_forward(obstacle)
        start = time.perf_counter()
        while True:
            cnt = self.radarController.forward_cnt
            print(f'forward:{cnt}')
            if cnt > 13:
                break
        print('car stop')
        end = time.perf_counter()
        print(f'forward time{self.forward_time}')
        self.forward_time += end - start
        print(f'forward time{self.forward_time}')
        carController.only_stop()
        self.tts.speak_text('停车。')
        carController.close()

    def operation6_backward(self):
        from SoundController.CarControllerClass import CarControl
        carController = CarControl(self.car_port, 115200)
        self.tts.speak_text('后退。')
        carController.only_backward()
        time.sleep(self.forward_time - 0.45)
        carController.only_stop()
        self.tts.speak_text('停车。')
        carController.close()
        self.forward_time = 0

    def operation7_obstacle(self):
        armController_right = SerialArmControllerClass(serial_port=self.right_arm_port)
        armController_left = SerialArmControllerClass(serial_port=self.left_arm_port)
        grasp_entity = zcup()
        time.sleep(3)

        get_cup_z = 280  # 以280mm的高度从演示者手中接过杯子

        GENERAL_DELAY = 0.05
        GRABBER_DELAY = 4

        get_cup_arm_length = 280  # 从演示者手中接过杯子这一过程中的xoy平面的臂长

        get_cup_theta = 45  # 调试时，没有声源定位给的角度，假设演示者在这个角度的方向发出声音

        get_cup_theta_rad = 2 * math.pi / 360 * get_cup_theta

        get_cup_x = get_cup_arm_length * math.cos(get_cup_theta_rad)

        get_cup_y = - get_cup_arm_length * math.sin(get_cup_theta_rad)

        # 夹到杯子后，左臂需要回到一个中心点待命，我希望这个中心点在两臂最中间的前方
        left_arm_center_position = [325, 105, 40]

        # 避免出现零，会导致逆解算的算法出现严重问题
        if abs(get_cup_x) < 4:
            get_cup_x += 10
        if abs(get_cup_y) < 4:
            get_cup_y += 10
        if abs(get_cup_y) < 4:
            get_cup_y += 10
        # ========================时刻1，初始化=========================================
        # 把右臂和左臂初始化到正前面
        armController_left.coord_ctrl()
        armController_right.coord_ctrl()
        time.sleep(2)

        # 右臂给左臂腾出来空间
        armController_right.coord_ctrl(380, 10, 150, 90, 160)
        time.sleep(GRABBER_DELAY)

        # ======================================================
        detect_cup_position = [5, -200, 380]
        armController_left.coord_ctrl(detect_cup_position[0], detect_cup_position[1], detect_cup_position[2],
                                      70, 280)
        # camera_data = grasp_entity.get_location(self.cup_type)
        # camera_data = grasp_entity.get_location(BLUE)
        # cup_position: List[float] = [-camera_data[0] * 1000 + detect_cup_position[0],
        #                              camera_data[2] * 1000 + detect_cup_position[1],
        #                              -camera_data[1] * 1000 + detect_cup_position[2]]
        #
        # cup_position = self.cup_offset(cup_position)
        #
        # self.tts.speak_text(f'目标距离{int(cup_position[1] / 10 + 14)}厘米，开始朝向目标移动。')
        self.operation5_forward(obstacle=True)

        # ====================右臂避开后左臂识别杯子的坐标参数================================================
        # TODO 调用识别函数
        camera_data = grasp_entity.get_location(self.cup_type)

        cup_position: List[float] = [-camera_data[0] * 1000 + detect_cup_position[0],
                                     camera_data[2] * 1000 + detect_cup_position[1],
                                     -camera_data[1] * 1000 + detect_cup_position[2]]

        cup_position = self.cup_offset(cup_position)

        if int(cup_position[1] / 10 + 14) > 65:
            # 太远了，遇到了障碍物
            self.tts.speak_text(f'前方遇到障碍物，停止移动，目标距离{int(cup_position[1] / 10 + 14)}厘米。')
            while True:
                time.sleep(0.1)
                if self.radarController.forward_cnt <= 5:
                    break
            self.tts.speak_text('障碍物已经移除，开始继续移动')
            time.sleep(3)
            self.operation5_forward()
            camera_data = grasp_entity.get_location(self.cup_type)
            cup_position = [-camera_data[0] * 1000 + detect_cup_position[0],
                            camera_data[2] * 1000 + detect_cup_position[1],
                            -camera_data[1] * 1000 + detect_cup_position[2]]

            cup_position = self.cup_offset(cup_position)

        self.tts.speak_text(f'已到达目标前方，距离目标{int(cup_position[1] / 10 + 14)}厘米。')
        armController_right.arm_close()
        armController_left.arm_close()
        self.ui.pushButton.click()

    def operation8_findperson(self):
        armController_right = SerialArmControllerClass(serial_port=self.right_arm_port)
        armController_left = SerialArmControllerClass(serial_port=self.left_arm_port)
        time.sleep(5)
        armController_left.coord_ctrl(5, -280, 280, 90, 180)
        armController_left.coord_ctrl(5, -400, 150, 90, 180)
        armController_right.coord_ctrl(5, -240, 330, 90, 180)
        armController_right.coord_ctrl(-180, -180, 330, 90, 180)
        detect_person_position = [5, -240, 330]
        armController_right.coord_ctrl(detect_person_position[0], detect_person_position[1], detect_person_position[2],
                                       90, 180)
        camera_data = self.person_i.get_location()
        person_position = [camera_data[0] * 1000 + detect_person_position[0],
                           camera_data[2] * 1000 + detect_person_position[1] - 200,
                           -camera_data[1] * 1000 + detect_person_position[2]]
        self.tts.speak_text(
            f'人的坐标是x等于{int(person_position[0] / 10)}厘米,y等于{int(person_position[1] / 10)}厘米,角度是{math.atan(person_position[0] / (-person_position[1])) / math.pi * 180}度')
        armController_right.coord_ctrl(280, 5, 280, 90, 180)

    @staticmethod
    def cup_offset(origin_coord):
        return [origin_coord[0] + 15,
                origin_coord[1] - 223,
                250]

    def slotRoundFinish(self, all_cnt):
        self.all_cnt = all_cnt

    def slotFirstOperation(self):
        # TODO: 调用叠叠乐函数
        if not self.firstOperationReady:
            return
        if self.globalOperationBusy:
            return

        raise NotImplementedError

    def slotSecondOperation(self, cmd="red"):
        raise NotImplementedError

    def slotGetRightPicture(self, pictures):
        self.r_rgb = pictures['rgb']
        self.r_aligned_depth_frame = pictures['aligned_depth_frame']
        self.r_depth_intrin = pictures['depth_intrin']
        showImage = QtGui.QImage(self.r_rgb.tobytes())
        self.ui.label_show_camera.setPixmap(QtGui.QPixmap.fromImage(showImage))

    def slotGetLeftPicture(self, pictures):
        self.l_rgb = pictures['rgb']
        self.l_aligned_depth_frame = pictures['aligned_depth_frame']
        self.l_depth_intrin = pictures['depth_intrin']

    # 识别色块进行抓取
    def colordetect(self, ret):
        locations = []  # 初始化列表存储所有location
        start_time = time.time()  # 记录开始时间

        while time.time() - start_time < 2:  # 循环运行2秒
            location = color_detect(self.r_rgb, self.r_depth_intrin, self.r_aligned_depth_frame,
                                    ret)  # 返回的location就是抓取中心点的坐标
            if isinstance(location, np.ndarray) and location.shape == (1, 3):
                location, self.processed_image = location.flatten()
                plate_position1 = [-location[1] * 100, location[0] * 100, -location[2] * 100]
                print(plate_position1)
                if 0 not in location:
                    locations.append(location)  # 将location添加到列表中
            else:
                print("警告：location不是预期的形状，跳过。")
        if locations:  # 如果列表不为空
            locations = np.array(locations)  # 将列表转换为numpy数组
            mean_location = np.mean(locations, axis=0)  # 计算平均值location
            std_dev = np.std(locations, axis=0)  # 计算标准差
            # 排除异常值，这里使用标准差作为阈值
            valid_indices = np.where((np.abs(locations - mean_location) <= 2 * std_dev).all(axis=1))
            filtered_locations = locations[valid_indices]
            final_location = np.mean(filtered_locations, axis=0)  # 计算最终的平均location
            print("Final location:", final_location)
            return final_location

    def cupdetect(self, ret):
        locations = []
        location = np.zeros((1, 3))  # 初始化列表存储所有location
        start_time = time.time()  # 记录开始时间
        model = YOLO('yolomodel/yolov8n.pt')
        while time.time() - start_time < 10:  # 循环运行2秒
            results = model(self.l_rgb, vid_stride=15, retina_masks=True)  # 两个参数分别是帧间距和高分辨掩膜
            annotated_frame = results[0].plot()
            for r in results:
                self.processed_image, location = cup_detect(results, r, annotated_frame, self.l_rgb,
                                                            self.l_depth_intrin, self.l_aligned_depth_frame, ret)
            if isinstance(location, np.ndarray) and location.shape == (1, 3):
                location = location.flatten()
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
            return final_location

    def persondetect(self, ret):
        locations = []
        location = np.zeros((1, 3))  # 初始化列表存储所有location
        start_time = time.time()  # 记录开始时间
        model = YOLO('yolomodel/yolov8n.pt')
        while time.time() - start_time < 10:  # 循环运行2秒
            results = model(self.r_rgb, vid_stride=15, retina_masks=True)  # 两个参数分别是帧间距和高分辨掩膜
            annotated_frame = results[0].plot()
            for r in results:
                self.processed_image, location = person_detect(results, r, annotated_frame, self.r_rgb,
                                                               self.r_depth_intrin, self.r_aligned_depth_frame)
            if isinstance(location, np.ndarray) and location.shape == (1, 3):
                location = location.flatten()
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
            return final_location


if __name__ == '__main__':
    app = qw.QApplication(sys.argv)
    form = MainClass()
    form.show()
    sys.exit(app.exec_())
