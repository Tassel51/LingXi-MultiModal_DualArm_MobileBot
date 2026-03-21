from typing import List
from CupGraspClass import zcup
from SerialRoboArm import SerialArmControllerClass
import time
import numpy as np
from openai import OpenAI
from typing import List
import sys
# 改正
RED = 4
BLUE = 2
YELLOW = 3
OTHER = 1

a = ("ai 提示词：你现在是一个数据处理机器人，需要控制一个机械臂的运动，这个机械臂只需要给他传这个变量：目标位置（在xyz坐标系中表示）。所以当我给你说“机械臂向右移动时”，你就将它的目标位置的y轴数据加80覆盖掉原来的y轴初始值，下一次的初始值就是70，以此类推，说“机械臂向左移动时”，你就将它的目标位置的y轴数据减80，下一次的初始值就是-90，以此类推。当我说了开始叠杯子的意思的话后，返回参数x=183,y=-14,z=242。"
     "三个数据分别为x,y,z坐标,基础数据为x=183,y=-10,z=242;之后你需要根据我的提示返回一组新的x,y,z值，【只能以[x,y,z]的形式返回】实例：我说向前移动时，你就返回[290,-10,280]！！！！！！请记住无论什么情况只能返回[x,y,z]这种形式的数组，不要任何汉字形式的【说明】")
def deepseek_init():
    client = OpenAI(api_key="sk-7f60db8ef22f4ca2a16af1e528186c3f", base_url="https://api.deepseek.com")
    # 机械臂初始化
    #armController_right = SerialArmControllerClass(serial_port="COM5")
    #armController_right.coord_ctrl(280, -10, 280, 90)
    # Round 1
    messages = [{"role": "user", "content": a}]
    i = 1

    for i in range(1):
        print("please ask a question:")

        question = input()
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        messages.append(response.choices[0].message)
        # print(response)
        # print(response.choices[0].message)
        # print(messages[-1].content)
        new_xyz = eval(messages[-1].content)
        print(new_xyz[1])
        armController_right.coord_ctrl(183, new_xyz[1],242,140,260)
        return new_xyz[1]

if __name__ == '__main__':
    grasp_entity = zcup()



    # 初始化
    armController_right = SerialArmControllerClass(serial_port="COM5",baud_rate=115200)
    time.sleep(6)
    #armController_right.coord_ctrl(210, -14, 166, 100)
   # armController_right.coord_ctrl(150, -14, 333, 120)
    armController_right.coord_ctrl(183, -14, 242,140)
    time.sleep(5)

    offset_x = 170
    offset_y = -14
    offset_z = 240

    base_position: List[float] = []
    camera_data = None
    # 2s

   # camera_data = grasp_entity.get_location(RED)
   # print(camera_data)





    #
    # #倒水
    for i in range(4):
        camera_data = grasp_entity.get_location(RED)
        if camera_data is not None and all(value != 0 for value in camera_data):  # 检查所有元素是否都不为 0
            # 检查所有元素是否都不为 0
            break
        else :
            pass
    if camera_data is None:
        print("camera_data2 为 None，程序终止。")
        sys.exit()  # 终止程序
    plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 215,#220
                                   camera_data[0] * 1000 + offset_y - 62,#55
                                   -camera_data[2] * 1000 + offset_z + 180]#150

    #if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 100 or plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 > 300:
    #    print(f'dist error')
    #    exit()


    if 0 in plate_position:
        print(f'0 zero error')
        exit()
    if plate_position[0]>=550:
        plate_position[0] = 550
    if plate_position[0] <=50:
        plate_position[0] = 50
    if plate_position[1] >=180 :
        plate_position[1] = 180
    if plate_position[1] <=-180 :
        plate_position[1] = -180
    if plate_position[2]>=500:
        plate_position[2] = 500
    if plate_position[2] <= 20:
        plate_position[2] = 20
    armController_right.coord_ctrl(280, -10, 280, 90)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 160)
    time.sleep(3)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 280)
    time.sleep(6)
    armController_right.coord_ctrl(277, plate_position[1], 277, 90, 280)#初始化
    time.sleep(3)
    #接deepseek,检测被倒的杯子
    camera_data2 = None
    new_xyz=-10
    while camera_data2 is None or any(value == 0 for value in camera_data2):
     new_xyz=deepseek_init()
     time.sleep(5)
     armController_right.coord_ctrl(120,new_xyz ,230, 150, 270)
     time.sleep(5)
    # 2s
     for j in range(3):
        camera_data2 = grasp_entity.get_location(BLUE)
        if camera_data2 is None :  # 如果返回值为 None，继续尝试获取数据
            print(f"第 {j + 1} 次尝试获取 camera_data2 失败")
            continue
        if all(value != 0 for value in camera_data2):  # 检查所有元素是否都不为 0
            print("获取到了有效数据，退出循环")
            break
        else :
            print("有元素为 0，继续尝试")

    #armController_right.coord_ctrl(183, -14, 242, 140)#扫视


    base_position: List[float] = [-camera_data2[1] * 1000 + offset_x -100,
                                  camera_data2[0] * 1000 + offset_y -177,
                                  -camera_data2[2] * 1000 + offset_z + 255]
    #if base_position[0] ** 2 + base_position[1] ** 2 + base_position[2] ** 2 < 100 or base_position[0] ** 2 + base_position[1] ** 2 + base_position[2] ** 2 > 300:
    #   print(f'dist error')
    #   exit()

    if 0 in base_position:
        print(f'0 zero error')
        exit()

    if base_position[0] >= 460:
        base_position[0] = 460
    if base_position[0] <= 50:
        base_position[0] = 50
    if base_position[1] >= 180:
        base_position[1] = 180
    if base_position[1] <= -180:
        base_position[1] = -180
    if base_position[2] >= 450:
        base_position[2] = 450
    if base_position[2] <= 20:
        base_position[2] = 20
    armController_right.coord_ctrl(277, base_position[1], 240, 90, 260)  # 初始化
    time.sleep(6)
    # 倒水
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 220, 260)
    time.sleep(5)
    armController_right.coord_ctrl(base_position[0], base_position[1], base_position[2], 220, 250)
    time.sleep(6)

    #armController_right.coord_ctrl(141, base_position[1], 160, 215, 240)#倒水 145 -183 114 215
    #放回杯子
    armController_right.coord_ctrl(277, -14, 277, 90, 260)
    time.sleep(4)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(4)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(3)
    armController_right.coord_ctrl(277, -14, 277, 90, 180)

    #叠杯子
    camera_data = None
    while camera_data is None or any(value == 0 for value in camera_data):
        deepseek_init()
        time.sleep(5)
        # 2s
        for j in range(3):
            camera_data = grasp_entity.get_location(RED)
            if camera_data is None:  # 如果返回值为 None，继续尝试获取数据
                print(f"第 {j + 1} 次尝试获取 camera_data 失败")
                continue
            if all(value != 0 for value in camera_data):  # 检查所有元素是否都不为 0
                print("获取到了有效数据，退出循环")
                break
            else:
                print("有元素为 0，继续尝试")

    # plate_position: List[float] = [-camera_data[1] * 1000 + offset_x + 205,  # 220
    #                                camera_data[0] * 1000 + offset_y - 64,  # 55
    #                                -camera_data[2] * 1000 + offset_z + 180]  # 150

    base_position: List[float] = [-camera_data2[1] * 1000 + offset_x + 10,  # 159
                                  camera_data2[0] * 1000 + offset_y - 174,  # 68
                                  -camera_data2[2] * 1000 + offset_z + 40]  # 60



    #if plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 < 100 or plate_position[0] ** 2 + plate_position[1] ** 2 + plate_position[2] ** 2 >400:
        #print(f'dist error')
        #exit()

    if 0 in plate_position:
        print(f'0 zero error')
        exit()
    if plate_position[0] >= 550:
        plate_position[0] = 550
    if plate_position[0] <= 50:
        plate_position[0] = 50
    if plate_position[1] >= 180:
        plate_position[1] = 180
    if plate_position[1] <= -180:
        plate_position[1] = -180
    if plate_position[2] >= 500:
        plate_position[2] = 500
    if plate_position[2] <= 20:
        plate_position[2] = 20
    #armController_right.coord_ctrl(280, -10, 280, 90,180)#初始化
    #拿起第二个杯子
    camera_data2 = None
    new_xyz = -10
    while camera_data2 is None or any(value == 0 for value in camera_data2):
        new_xyz = deepseek_init()
        time.sleep(3)
        armController_right.coord_ctrl(120, new_xyz, 230, 150, 270)
        time.sleep(6)
        # 2s
        for j in range(3):
            camera_data2 = grasp_entity.get_location(OTHER)
            if camera_data2 is None:  # 如果返回值为 None，继续尝试获取数据
                print(f"第 {j + 1} 次尝试获取 camera_data2 失败")
                continue
            if all(value != 0 for value in camera_data2):  # 检查所有元素是否都不为 0
                print("获取到了有效数据，退出循环")
                break
            else:
                print("有元素为 0，继续尝试")

    # armController_right.coord_ctrl(183, -14, 242, 140)#扫视
    base_position: List[float] = [-camera_data2[1] * 1000 + offset_x + 10,  # 159
                                  camera_data2[0] * 1000 + offset_y - 174,  # 68
                                  -camera_data2[2] * 1000 + offset_z + 40]  # 60

    #if base_position[0] ** 2 + base_position[1] ** 2 + base_position[2] ** 2 < 100 or base_position[0] ** 2 +  base_position[1] ** 2 + base_position[2] ** 2 > 300:
    #   print(f'dist error')
    #   exit()

    if 0 in base_position:
        print(f'0 zero error')
        exit()

    if base_position[0] >= 460:
        base_position[0] = 460
    if base_position[0] <= 50:
        base_position[0] = 50
    if base_position[1] >= 180:
        base_position[1] = 180
    if base_position[1] <= -180:
        base_position[1] = -180
    if base_position[2] >= 450:
        base_position[2] = 450
    if base_position[2] <= 20:
        base_position[2] = 20
    time.sleep(2)
    armController_right.coord_ctrl(280, base_position[1]+new_xyz, 280, 90, 170)
    time.sleep(2)
    armController_right.coord_ctrl(base_position[0], base_position[1]+ new_xyz, base_position[2], 90, 170)
    time.sleep(3)
    #armController_right.coord_ctrl(base_position[0], base_position[1]+new_xyz, base_position[2], 90, 170)
    armController_right.coord_ctrl(base_position[0]+40, base_position[1] + new_xyz, base_position[2], 90, 170)
    time.sleep(6)
    armController_right.coord_ctrl(base_position[0]+40, base_position[1] + new_xyz, base_position[2], 90, 260)
    #放在第一个杯子上
    time.sleep(6)
    armController_right.coord_ctrl(277, plate_position[1], 277, 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2]+50, 90, 260)
    time.sleep(2)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2]+50, 90, 180)
    time.sleep(4)
    armController_right.coord_ctrl(277, base_position[1], 277, 90, 180)#初始化

    # 拿起第三个杯子
    camera_data2 = None
    new_xyz = -10
    while camera_data2 is None or any(value == 0 for value in camera_data2):
        new_xyz = deepseek_init()
        time.sleep(5)
        armController_right.coord_ctrl(120, new_xyz, 230, 150, 270)
        time.sleep(5)
        # 2s
        for j in range(3):
            camera_data2 = grasp_entity.get_location(YELLOW)
            if camera_data2 is None:  # 如果返回值为 None，继续尝试获取数据
                print(f"第 {j + 1} 次尝试获取 camera_data2 失败")
                continue
            if all(value != 0 for value in camera_data2):  # 检查所有元素是否都不为 0
                print("获取到了有效数据，退出循环")
                break
            else:
                print("有元素为 0，继续尝试")

    # armController_right.coord_ctrl(183, -14, 242, 140)#扫视
    base_position: List[float] = [-camera_data2[1] * 1000 + offset_x + 10,  # 159
                                  camera_data2[0] * 1000 + offset_y - 174,  # 68
                                  -camera_data2[2] * 1000 + offset_z + 40]  # 60

    #if base_position[0] ** 2 + base_position[1] ** 2 + base_position[2] ** 2 < 100 or base_position[0] ** 2 +  base_position[1] ** 2 + base_position[2] ** 2 > 300:
    #   print(f'dist error')
    #   exit()

    if 0 in base_position:
        print(f'0 zero error')
        exit()

    if base_position[0] >= 460:
        base_position[0] = 460
    if base_position[0] <= 50:
        base_position[0] = 50
    if base_position[1] >= 180:
        base_position[1] = 180
    if base_position[1] <= -180:
        base_position[1] = -180
    if base_position[2] >= 450:
        base_position[2] = 450
    if base_position[2] <= 20:
        base_position[2] = 20
    time.sleep(2)
    armController_right.coord_ctrl(280, base_position[1] + new_xyz, 280, 90, 170)
    time.sleep(2)
    armController_right.coord_ctrl(base_position[0], base_position[1] + new_xyz, base_position[2], 90, 170)
    time.sleep(3)
    # armController_right.coord_ctrl(base_position[0], base_position[1]+new_xyz, base_position[2], 90, 170)
    armController_right.coord_ctrl(base_position[0] + 40, base_position[1] + new_xyz, base_position[2], 90, 170)
    time.sleep(6)
    armController_right.coord_ctrl(base_position[0] + 40, base_position[1] + new_xyz, base_position[2], 90, 260)
    # 放在第一个杯子上
    time.sleep(6)
    armController_right.coord_ctrl(277, plate_position[1], 277, 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(2)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(4)
    armController_right.coord_ctrl(277, base_position[1], 277, 90, 180)  # 初始化

    # 拿起第四个杯子
    camera_data2 = None
    new_xyz = -10
    while camera_data2 is None or any(value == 0 for value in camera_data2):
        new_xyz = deepseek_init()
        time.sleep(5)
        armController_right.coord_ctrl(96, new_xyz, 232, 165, 260)
        time.sleep(5)
        # 2s
        for j in range(3):
            camera_data2 = grasp_entity.get_location(BLUE)
            if camera_data2 is None:  # 如果返回值为 None，继续尝试获取数据
                print(f"第 {j + 1} 次尝试获取 camera_data2 失败")
                continue
            if all(value != 0 for value in camera_data2):  # 检查所有元素是否都不为 0
                print("获取到了有效数据，退出循环")
                break
            else:
                print("有元素为 0，继续尝试")

    # armController_right.coord_ctrl(183, -14, 242, 140)#扫视
    base_position: List[float] = [-camera_data2[1] * 1000 + offset_x + 10,  # 159
                                  camera_data2[0] * 1000 + offset_y - 174,  # 68
                                  -camera_data2[2] * 1000 + offset_z + 40]  # 60

    if base_position[0] ** 2 + base_position[1] ** 2 + base_position[2] ** 2 < 100 or base_position[0] ** 2 + \
            base_position[1] ** 2 + base_position[2] ** 2 > 300:
        print(f'dist error')
        exit()

    if 0 in base_position:
        print(f'0 zero error')
        exit()

    if base_position[0] >= 460:
        base_position[0] = 460
    if base_position[0] <= 50:
        base_position[0] = 50
    if base_position[1] >= 180:
        base_position[1] = 180
    if base_position[1] <= -180:
        base_position[1] = -180
    if base_position[2] >= 450:
        base_position[2] = 450
    if base_position[2] <= 20:
        base_position[2] = 20
    # 拿起第三个杯子
    time.sleep(2)
    armController_right.coord_ctrl(280, base_position[1] + new_xyz, 280, 90, 170)
    time.sleep(2)
    armController_right.coord_ctrl(base_position[0], base_position[1] + new_xyz, base_position[2], 90, 170)
    time.sleep(3)
    # armController_right.coord_ctrl(base_position[0], base_position[1]+new_xyz, base_position[2], 90, 170)
    armController_right.coord_ctrl(base_position[0] + 40, base_position[1] + new_xyz, base_position[2], 90, 170)
    time.sleep(6)
    armController_right.coord_ctrl(base_position[0] + 40, base_position[1] + new_xyz, base_position[2], 90, 260)
    # 放在第一个杯子上
    time.sleep(6)
    armController_right.coord_ctrl(277, plate_position[1], 277, 90, 260)
    time.sleep(6)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 260)
    time.sleep(2)
    armController_right.coord_ctrl(plate_position[0], plate_position[1], plate_position[2], 90, 180)
    time.sleep(4)
    armController_right.coord_ctrl(277, base_position[1], 277, 90, 180)  # 初始化






    """
    # 识别huang色
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
"""
    # while True:
    #     pass
