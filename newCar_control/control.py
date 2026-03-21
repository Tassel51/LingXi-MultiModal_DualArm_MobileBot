import os
import time
import paramiko
import sys

# ================= 配置区 =================
WIFI_SSID = "WHEELTEC_RDK_X5_humble_"
ROBOT_IP = "192.168.0.100"
SSH_USER = "wheeltec"
SSH_PWD = "dongguan"

# 组合环境变量：确保每次发送命令前，都激活了 ROS2 环境
# (根据标准 Wheeltec ROS2 系统结构配置)
ROS2_SETUP = "source /opt/ros/humble/setup.bash && source ~/wheeltec_ros2/install/setup.bash"


# ==========================================

def connect_wifi():
    print(f"[*] 正在检查并连接小车 WiFi: {WIFI_SSID} ...")
    # Windows 连 WiFi 指令 (依赖于系统已保存过该WiFi)
    os.system(f'netsh wlan connect name="{WIFI_SSID}"')
    print("[*] 等待 5 秒钟以确保获取到小车的分配 IP...")
    time.sleep(5)


def run_interactive_terminal():
    print(f"[*] 正在建立与小车 {ROBOT_IP} 的 SSH 通道...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动信任密钥，免除报错

    try:
        ssh.connect(hostname=ROBOT_IP, username=SSH_USER, password=SSH_PWD, timeout=10)
        print("✅ SSH 底层连接成功！")

        # 建立交互式 Shell
        channel = ssh.invoke_shell()
        time.sleep(1)
        # 清除开机登录的欢迎信息
        if channel.recv_ready():
            channel.recv(4096)

        print("\n" + "=" * 50)
        print("🚗 Wheeltec ROS2 极客控制终端已就绪！")
        print("=" * 50)
        print("💡 使用说明：")
        print("  - 你可以输入下方【快捷键】快速启动常用节点。")
        print("  - 你也可以直接粘贴你那份列表里的【任何完整 ros2 命令】。")
        print("  - 节点运行时，按下【Ctrl+C】可以停止当前节点并回到此菜单。")
        print("=" * 50)
        print("【快捷菜单】")
        print("  [1] 打开机器人底盘 (turn_on_wheeltec_robot)")
        print("  [2] 打开雷达、相机和底盘 (wheeltec_sensors)")
        print("  [3] 打开键盘控制 (wheeltec_keyboard)")
        print("  [4] 运行 Gmapping 2D建图")
        print("  [q] 退出控制台并断开连接")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n[Wheeltec 控制台] >>> ").strip()

                if not user_input:
                    continue
                if user_input.lower() == 'q':
                    break

                # 快捷键映射
                if user_input == '1':
                    cmd = "ros2 launch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch.py"
                elif user_input == '2':
                    cmd = "ros2 launch turn_on_wheeltec_robot wheeltec_sensors.launch.py"
                elif user_input == '3':
                    cmd = "ros2 run wheeltec_robot_keyboard wheeltec_keyboard"
                elif user_input == '4':
                    cmd = "ros2 launch slam_gmapping slam_gmapping.launch.py"
                else:
                    cmd = user_input  # 支持直接粘贴原生命令

                # 拼接完整命令：激活环境 + 执行命令 + 回车
                full_cmd = f"{ROS2_SETUP} && {cmd}\n"

                print(f"[*] 正在向小车发送指令: {cmd}")
                print("[*] (提示: 按 Ctrl+C 随时中止该节点)\n")
                channel.send(full_cmd)

                # 持续监听小车返回的日志输出
                while True:
                    if channel.recv_ready():
                        output = channel.recv(1024).decode('utf-8', errors='ignore')
                        # 实时打印 ROS2 日志
                        sys.stdout.write(output)
                        sys.stdout.flush()
                    time.sleep(0.05)

            except KeyboardInterrupt:
                # 捕获我们在 Windows 终端按下的 Ctrl+C
                print("\n\n[!] 收到中断信号，正在向小车发送停止指令 (Ctrl+C)...")
                channel.send('\x03')  # 发送 ASCII 中的 Ctrl+C 信号给小车终端
                time.sleep(1)  # 给小车一点时间关闭节点
                # 清理残留输出
                if channel.recv_ready():
                    channel.recv(4096)
                print("[*] 节点已停止，已返回主菜单。")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请检查：1. WiFi是否确实连上了？ 2. 小车是否已经开机并启动完毕？")
    finally:
        print("\n[*] 正在安全断开小车连接...")
        ssh.close()
        print("👋 再见！")


if __name__ == "__main__":
    connect_wifi()
    run_interactive_terminal()
