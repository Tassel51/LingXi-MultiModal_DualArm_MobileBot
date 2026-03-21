import time
from ArmController.serial.SerialRoboArm import (SerialArmControllerClass)

GENERAL_DELAY = 0.01
GRABBER_DELAY = 3
armController_right = SerialArmControllerClass(serial_port="COM6", baud_rate=115200)#调用serialRoboArmClass
armController_right.coord_ctrl(280, -14, 280, 90)
time.sleep(5)
armController_right.coord_ctrl(170, -4, 240, 170)
time.sleep(1)
 # 抓起来圆盘，回到初始位置
armController_right.coord_ctrl(280, -14, 280, 90, 260)
time.sleep(3)
# 放到黑色上面

armController_right.coord_ctrl(280, -14, 280, 90, 260)
time.sleep(2)
armController_right.coord_ctrl(280, -20, 270, 100, 230)
time.sleep(2)
armController_right.coord_ctrl(200, -16, 280, 100, 250)
time.sleep(GRABBER_DELAY)
armController_right.coord_ctrl(280, -14, 280, 90, 260)
time.sleep(2)
# 放到黑色上面
armController_right.coord_ctrl(180 - 10, -10 - 3, 210 + 30, 100, 260)
time.sleep(2)
armController_right.coord_ctrl(250 - 10, -16 - 3, 220 + 30, 100, 180)
time.sleep(GRABBER_DELAY)
armController_right.coord_ctrl(280, -14, 280, 90, 260)
time.sleep(2)
armController_right.coord_ctrl(170, -14, 240, 170)
time.sleep(1)