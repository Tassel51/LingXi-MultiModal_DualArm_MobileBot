import math
import time
from typing import List

from SerialRoboArm import SerialArmControllerClass
from CupGraspClass import zcup

RED = 1
BLUE = 2
YELLOW = 3
OTHER = 4

if __name__ == "__main__":
    # 右臂从人的手里接水，左臂取饮料
    # 左臂150t值才平
    armController_right = SerialArmControllerClass(serial_port="COM3")
    armController_left = SerialArmControllerClass(serial_port="COM7")
    grasp_entity = zcup()
    time.sleep(10)
    # 右臂的操作告一段落，接下来操作左臂，做笔要根据传进来的参数，从场景中抓一个杯子过来，并在右臂杯子上方做出倒的动作
    # 假定左臂要找的饮料在左臂左前方45度处
    drink_x = 198
    drink_y = 198
    # 饮料杯子的高度应该是可以定死的，可以假定和中心位置右臂一样高
    drink_z = 280
    get_cup_z = 280  # 以280mm的高度从演示者手中接过杯子

    GENERAL_DELAY = 3
    GRABBER_DELAY = 6

    get_cup_arm_length = 280  # 从演示者手中接过杯子这一过程中的xoy平面的臂长

    get_cup_theta = 45  # 调试时，没有声源定位给的角度，假设演示者在这个角度的方向发出声音

    get_cup_theta_rad = 2 * math.pi / 360 * get_cup_theta

    get_cup_x = get_cup_arm_length * math.cos(get_cup_theta_rad)

    get_cup_y = - get_cup_arm_length * math.sin(get_cup_theta_rad)

    # 夹到杯子后，左臂需要回到一个中心点待命，我希望这个中心点在两臂最中间的前方
    left_arm_center_position = [300, 125, -20]

    print(get_cup_x, get_cup_y)

    # 外部传进来的参数也要避免出现零
    if abs(drink_x) < 4:
        drink_x += 10
    if abs(drink_y) < 4:
        drink_y += 10
    if abs(drink_z) < 4:
        drink_z += 10

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
    time.sleep(5)

    # ================左臂从人手里拿到杯子的同时，右臂避开，左臂前往摄像头位置================================
    armController_left.coord_ctrl(15, -280, 280, 90, 160)
    time.sleep(GENERAL_DELAY)
    # 机械臂朝向声源，并且爪子开到最大
    armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 160)
    time.sleep(GENERAL_DELAY)
    # 机械臂尝试关闭，以夹取人手中的杯子
    armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 280)
    time.sleep(GRABBER_DELAY)

    # ======================================================

    armController_left.coord_ctrl(15, -280, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    armController_right.coord_ctrl(380, 10, 150, 90, 160)
    time.sleep(GENERAL_DELAY)
    # TODO 这里要让右臂给左臂腾出来空间，左臂上的摄像头识别杯子的坐标
    detect_cup_position = [5, -200, 380]
    armController_left.coord_ctrl(detect_cup_position[0], detect_cup_position[1], detect_cup_position[2],
                                  70, 280)
    time.sleep(3)
    # ====================右臂避开后左臂识别杯子的坐标参数================================================
    # TODO 调用识别函数
    camera_data = grasp_entity.get_location(RED)

    cup_position: List[float] = [-camera_data[0] * 1000 + detect_cup_position[0] + 0,
                                camera_data[2] * 1000 + detect_cup_position[1] - 200,
                                 -camera_data[1] * 1000 + detect_cup_position[2] + 110]

    if abs(cup_position[0]) < 4:
        cup_position[0] += 10
    if abs(cup_position[1]) < 4:
        cup_position[1] += 10
    if abs(cup_position[2]) < 4:
        cup_position[2] += 10

    print(cup_position)

    # ====================获得参数后，左臂往正面走，前往中心姿态位置，右臂根据信息抓杯子========================
    # 右臂退出躲避相机的姿态
    armController_right.coord_ctrl(280, 15, 280, 90, 160)
    time.sleep(GENERAL_DELAY)
    armController_right.coord_ctrl(15, 280, 280, 90, 160)
    time.sleep(GENERAL_DELAY)
    # 右臂前往饮料位置
    armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 160)
    time.sleep(GENERAL_DELAY)
    # 右臂抓饮料
    armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 280)
    time.sleep(GRABBER_DELAY)

    # 抓到饮料后右臂前往初始位置
    armController_right.coord_ctrl(15, 260, 300, 90, 280)
    time.sleep(GENERAL_DELAY)
    armController_right.coord_ctrl(280, 15, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    # =====================确保左臂前往中心姿态位置后，右臂倒水，撤走=======================================
    armController_left.coord_ctrl(15, -280, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    armController_left.coord_ctrl(280, 15, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    armController_left.coord_ctrl(left_arm_center_position[0], left_arm_center_position[1],
                                  left_arm_center_position[2], 90, 280)
    time.sleep(GENERAL_DELAY)

    drink_center_position = [235, -54, 210]
    # 做出倒水动作需要的t舵机倾角
    pull_coord_t = 180
    # 先前往中心位置
    armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
                                   90, 280)
    time.sleep(GRABBER_DELAY)
    # 再倾倒
    armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
                                   pull_coord_t, 280)
    time.sleep(GRABBER_DELAY)
    # 倒完回到水平位置
    armController_right.coord_ctrl(drink_center_position[0], drink_center_position[1], drink_center_position[2],
                                   90, 280)
    time.sleep(GRABBER_DELAY)
    # 先回到正面
    armController_right.coord_ctrl(280, 15, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    armController_right.coord_ctrl(15, 280, 280, 90, 280)
    time.sleep(GENERAL_DELAY)

    # ==========================左臂撤走，左臂右臂分别放下手里的杯子，两个臂初始化===================================
    # 左臂抬起，准备左转
    armController_left.coord_ctrl(280, 15, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    # 左臂前往左预备位
    armController_left.coord_ctrl(15, -280, 280, 90, 280)
    time.sleep(GENERAL_DELAY)
    # 左臂右臂前往拿杯子的地方
    armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 280)
    armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 280)
    time.sleep(GENERAL_DELAY)
    # 左臂右臂松手
    armController_left.coord_ctrl(get_cup_x, get_cup_y, get_cup_z, 90, 160)
    armController_right.coord_ctrl(cup_position[0], cup_position[1], cup_position[2], 90, 160)
    time.sleep(GRABBER_DELAY)
    # 左臂右臂回到预备位
    armController_right.coord_ctrl(15, 280, 280, 90, 160)
    armController_left.coord_ctrl(15, -280, 280, 90, 160)
    time.sleep(GENERAL_DELAY)
    # 直接初始化
    armController_left.coord_ctrl()
    armController_right.coord_ctrl()
    while True:
        pass
