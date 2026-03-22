from typing import List
from CupGraspClass import zcup
from SerialRoboArm import SerialArmControllerClass
import time
import numpy as np

RED = 4
BLUE = 2
YELLOW = 3
OTHER = 1
def diediele():
    RED = 1
    BLUE = 2
    YELLOW = 3
    OTHER = 4
    grasp_entity = zcup()

    armController_right = SerialArmControllerClass(serial_port="COM10", baud_rate=115200)
    time.sleep(6)
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)


    # 摄像头和机械臂的偏移量
    offset_x = 170
    offset_y = -14
    offset_z = 240



    base_position: List[float] = []
    camera_data = None
    # 2s
    for i in range(5):
        camera_data = grasp_entity.get_location(RED)
        if 0 not in camera_data:
            break

    # 获取基准位置
    base_position: List[float] = [-camera_data[1] * 1000 + offset_x + 60,
                                  camera_data[0] * 1000 + offset_y - 68,
                                  -camera_data[2] * 1000 + offset_z + 60]

    for i in range(5):
        camera_data = grasp_entity.get_location(BLUE)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 70,
                                   -camera_data[2] * 1000 + offset_z + 50]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()



    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)


    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)

    # 识别红色
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)
    for i in range(5):
        camera_data = grasp_entity.get_location(YELLOW)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 68,
                                   -camera_data[2] * 1000 + offset_z + 45]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()

    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)
    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25, 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)

    for i in range(5):
        camera_data = grasp_entity.get_location(RED)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 68,
                                   -camera_data[2] * 1000 + offset_z + 45]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()

    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)
    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25 * 2, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25 * 2, 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)


if __name__ == '__main__':
    grasp_entity = zcup()

    armController_right = SerialArmControllerClass(serial_port="COM10")
    time.sleep(6)
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)

    offset_x = 170
    offset_y = -14
    offset_z = 240

    base_position: List[float] = []
    camera_data = None
    # 2s
    for i in range(5):
        camera_data = grasp_entity.get_location(RED)
        if 0 not in camera_data:
            break

    base_position: List[float] = [-camera_data[1] * 1000 + offset_x + 60,
                                  camera_data[0] * 1000 + offset_y - 68,
                                  -camera_data[2] * 1000 + offset_z + 60]

    for i in range(5):
        camera_data = grasp_entity.get_location(BLUE)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 70,
                                   -camera_data[2] * 1000 + offset_z + 50]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()

    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)
    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)

    # 识别红色
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)
    for i in range(5):
        camera_data = grasp_entity.get_location(YELLOW)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 68,
                                   -camera_data[2] * 1000 + offset_z + 45]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()

    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)
    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25, 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(170, -14, 240, 170)
    time.sleep(3)

    for i in range(5):
        camera_data = grasp_entity.get_location(RED)
        if 0 not in camera_data:
            break

    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 65,
                                   camera_data[0] * 1000 + offset_y - 68,
                                   -camera_data[2] * 1000 + offset_z + 45]

    if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 200:
        print(f'dist error')
        exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()

    armController_right.coord_ctrl(280, -14, 280, 90)
    time.sleep(3)
    # 抓起来圆盘，回到初始位置
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    # 放到黑色上面
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25*2, 90, 260)
    time.sleep(3)
    armController_right.coord_ctrl(base_position[0] + 5, base_position[1] + 3, base_position[2] + 25*2, 90, 180)
    time.sleep(6)
    armController_right.coord_ctrl(280, -14, 280, 90, 260)
    time.sleep(3)
    while True:
        pass
