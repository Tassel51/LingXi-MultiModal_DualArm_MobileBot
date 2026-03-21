#!/usr/bin/env python
# coding=utf-8
# Windows 纯 Python 远程控制小车（官方代码改写版）
# 功能：和 wheeltec_keyboard.py 完全一致，Windows 直接运行

import os
import time
from roslibpy import Ros, Topic

# ====================== 配置参数 ======================
ROBOT_IP = "192.168.0.100"  # 小车IP
ROBOT_PORT = 9090             # rosbridge 端口（默认9090）
# =======================================================

# Windows 键盘监听
if os.name == 'nt':
    import msvcrt
else:
    # 非 Windows 系统（备用）
    import termios
    import tty
    import select
    import sys

# 速度参数（和官方一致）
LIN_VEL_STEP_SIZE = 0.01
ANG_VEL_STEP_SIZE = 0.1

# 控制提示
msg = """
Control Your carrrrrrrrrr!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%
space key, k : force stop
anything else : stop smoothly
b : switch to OmniMode/CommonMode
CTRL-C to quit
"""

# 键值对应移动/转向方向
moveBindings = {
    'i': (1, 0),
    'o': (1, -1),
    'j': (0, 1),
    'l': (0, -1),
    'u': (1, 1),
    ',': (-1, 0),
    '.': (-1, 1),
    'm': (-1, -1),
}

# 键值对应速度增量
speedBindings = {
    'q': (1.1, 1.1),
    'z': (0.9, 0.9),
    'w': (1.1, 1),
    'x': (0.9, 1),
    'e': (1, 1.1),
    'c': (1, 0.9),
}

# 获取键值函数（Windows 专用）
def get_key():
    if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')
    else:
        # 非 Windows 系统备用
        settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                key = sys.stdin.read(1)
            else:
                key = ''
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

# 打印当前速度
def print_vels(speed, turn):
    print('currently:\tspeed {0}\t turn {1} '.format(speed, turn))

def main():
    # 1. 连接小车
    try:
        ros = Ros(ROBOT_IP, ROBOT_PORT)
        ros.run()
        print("✅ 已连接小车！")
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        return

    # 2. 创建速度控制话题
    cmd_topic = Topic(ros, '/cmd_vel', 'geometry_msgs/Twist')
    cmd_topic.advertise()

    # 3. 初始化变量
    speed = 0.2  # 默认移动速度 m/s
    turn = 1.0   # 默认转向速度 rad/s
    x = 0.0       # 前进后退方向
    th = 0.0      # 转向/横向移动方向
    count = 0.0   # 键值计数
    target_speed = 0.0
    target_turn = 0.0
    target_HorizonMove = 0.0
    control_speed = 0.0
    control_turn = 0.0
    control_HorizonMove = 0.0
    Omni = 0  # 0: 普通模式, 1: 全向模式

    try:
        print(msg)
        print_vels(speed, turn)

        while True:
            key = get_key()

            # 切换全向模式
            if key == 'b':
                Omni = ~Omni
                if Omni:
                    print("Switch to OmniMode")
                    moveBindings['.'] = [-1, -1]
                    moveBindings['m'] = [-1, 1]
                else:
                    print("Switch to CommonMode")
                    moveBindings['.'] = [-1, 1]
                    moveBindings['m'] = [-1, -1]

            # 移动/转向控制
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                th = moveBindings[key][1]
                count = 0

            # 速度调节
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]
                count = 0
                print_vels(speed, turn)

            # 紧急停止
            elif key == ' ' or key == 'k':
                x = 0
                th = 0.0
                control_speed = 0.0
                control_turn = 0.0
                control_HorizonMove = 0.0

            # 其他按键：平滑停止
            else:
                count = count + 1
                if count > 4:
                    x = 0
                    th = 0.0
                if key == '\x03':  # Ctrl+C
                    break

            # 计算目标速度
            target_speed = speed * x
            target_turn = turn * th
            target_HorizonMove = speed * th

            # 平滑控制：前进后退
            if target_speed > control_speed:
                control_speed = min(target_speed, control_speed + 0.1)
            elif target_speed < control_speed:
                control_speed = max(target_speed, control_speed - 0.1)
            else:
                control_speed = target_speed

            # 平滑控制：转向
            if target_turn > control_turn:
                control_turn = min(target_turn, control_turn + 0.5)
            elif target_turn < control_turn:
                control_turn = max(target_turn, control_turn - 0.5)
            else:
                control_turn = target_turn

            # 平滑控制：横向移动（全向模式）
            if target_HorizonMove > control_HorizonMove:
                control_HorizonMove = min(target_HorizonMove, control_HorizonMove + 0.1)
            elif target_HorizonMove < control_HorizonMove:
                control_HorizonMove = max(target_HorizonMove, control_HorizonMove - 0.1)
            else:
                control_HorizonMove = target_HorizonMove

            # 构造速度指令
            twist = {
                "linear": {
                    "x": control_speed,
                    "y": 0.0 if Omni == 0 else control_HorizonMove,
                    "z": 0.0
                },
                "angular": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": control_turn if Omni == 0 else 0.0
                }
            }

            # 发布指令
            cmd_topic.publish(twist)

    except Exception as e:
        print(f"❌ 错误：{e}")

    finally:
        # 停止小车
        stop_twist = {
            "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
        }
        cmd_topic.publish(stop_twist)
        print("\n🛑 小车已停止")
        ros.terminate()

if __name__ == '__main__':
    main()