#!/usr/bin/env python
# coding=utf-8
# 纯净测试版：运行即后退 1 秒

import time
from roslibpy import Ros, Topic

# ====================== 配置参数 ======================
ROBOT_IP = "192.168.0.100"  # 小车IP
ROBOT_PORT = 9090  # rosbridge 端口


# =======================================================

def main():
    print("⏳ 正在连接小车...")
    # 1. 连接小车
    try:
        ros = Ros(ROBOT_IP, ROBOT_PORT)
        ros.run()
        if ros.is_connected:
            print("✅ 已连接小车！")
        else:
            print("❌ 连接超时")
            return
    except Exception as e:
        print(f"❌ 连接报错：{e}")
        return

    # 2. 创建速度控制话题 (⚠️ 这里已经帮你改成了 ROS 2 专属的带 /msg/ 的格式)
    cmd_topic = Topic(ros, '/cmd_vel', 'geometry_msgs/msg/Twist')
    cmd_topic.advertise()

    # 3. 构造指令
    # 后退指令：x 轴线速度给负数 (-0.2 m/s)
    move_back_twist = {
        "linear": {"x": -0.2, "y": 0.0, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
    }
    # 停止指令：全部归零
    stop_twist = {
        "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
    }

    try:
        print("🚗 指令发送中：小车后退...")
        # 4. 在 1 秒内连续发送 10 次指令 (频率 10Hz)
        # 很多小车底盘有“看门狗”机制，如果0.5秒收不到新指令就会自动急停，所以要循环发
        for _ in range(10):
            cmd_topic.publish(move_back_twist)
            time.sleep(0.1)

        print("🛑 1 秒已到，发送停止指令！")

    except Exception as e:
        print(f"❌ 运行报错：{e}")

    finally:
        # 5. 停止小车并清理连接
        cmd_topic.publish(stop_twist)
        time.sleep(0.1)  # 稍微等一下，确保停止指令发出去
        cmd_topic.publish(stop_twist)  # 稳妥起见，再发一次停止

        cmd_topic.unadvertise()
        ros.terminate()
        print("🔌 已断开连接，测试结束。")


if __name__ == '__main__':
    main()
