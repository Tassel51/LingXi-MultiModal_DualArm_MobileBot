import os
import sys
import time
import threading
import paramiko
import msvcrt

# ================= 配置区 =================
WIFI_SSID = "WHEELTEC_RDK_X5_humble_"
ROBOT_IP = "192.168.0.100"
SSH_USER = "wheeltec"
SSH_PWD = "dongguan"

ROS2_SETUP = "source /opt/ros/humble/setup.bash && source ~/wheeltec_ros2/install/setup.bash"
# ==========================================

is_node_running = False


def connect_wifi():
    print(f"[*] 正在检查 WiFi: {WIFI_SSID} ...")
    os.system(f'netsh wlan connect name="{WIFI_SSID}"')
    time.sleep(3)


def read_ssh_output(channel_main, channel_kb):
    """后台线程：同时监听两个纯净 SSH 会话的日志并打印"""
    global is_node_running
    while is_node_running:
        try:
            if channel_main and channel_main.recv_ready():
                data = channel_main.recv(1024)
                if data:
                    sys.stdout.write(data.decode('utf-8', errors='ignore'))
                    sys.stdout.flush()

            if channel_kb and channel_kb.recv_ready():
                data = channel_kb.recv(1024)
                if data:
                    sys.stdout.write(data.decode('utf-8', errors='ignore'))
                    sys.stdout.flush()
        except Exception:
            pass
        time.sleep(0.01)


def run_interactive_terminal():
    global is_node_running
    print(f"[*] 正在建立与小车 {ROBOT_IP} 的 SSH 直连通道...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=ROBOT_IP, username=SSH_USER, password=SSH_PWD, timeout=10)

        while True:
            print("\n" + "=" * 50)
            print("🚗 Wheeltec ROS2 终极极客控制台 V4 (真·全双工)")
            print("=" * 50)
            print("  [1] 打开机器人底盘 (单通道看日志)")
            print("  [3] 打开键盘控制 (单通道)")
            print("  [5] 🚀 一键遥控模式 (底层直连：告别按键乱码) - 推荐！")
            print("  [9] 🛑 紧急停止所有 ROS 进程")
            print("  [q] 退出控制台并断开连接")
            print("=" * 50)

            user_input = input("[主菜单] >>> ").strip()
            if not user_input: continue
            if user_input.lower() == 'q': break

            if user_input == '9':
                print("\n[!] 正在清理小车上的所有 ROS 进程...")
                tmp_ch = ssh.get_transport().open_session()
                tmp_ch.exec_command("pkill -f ros")
                time.sleep(1)
                tmp_ch.close()
                continue

            print(f"\n[*] 节点正在启动，请耐心等待...")
            print("[*] (按 Ctrl+C 随时中止并返回主菜单)\n")
            print("-" * 50)

            is_node_running = True

            if user_input == '5':
                # --- 核心架构重写：使用原生 exec_command 绕过 Bash 外壳 ---

                # 开启通道1 (底盘专属)
                channel_main = ssh.get_transport().open_session()
                channel_main.get_pty(term='xterm', width=100, height=40)

                # 开启通道2 (键盘专属)
                channel_kb = ssh.get_transport().open_session()
                channel_kb.get_pty(term='xterm', width=100, height=40)

                # 启动日志监听线程
                log_thread = threading.Thread(target=read_ssh_output, args=(channel_main, channel_kb))
                log_thread.daemon = True
                log_thread.start()

                print("[*] 【步骤 1/2】正在启动底盘驱动，请等待 5 秒...")
                channel_main.exec_command(
                    f"{ROS2_SETUP} && ros2 launch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch.py")

                # 必须等底盘的传感器全部上线
                time.sleep(5)

                print("[*] 【步骤 2/2】正在启动键盘控制面板...")
                channel_kb.exec_command(f"{ROS2_SETUP} && ros2 run wheeltec_robot_keyboard wheeltec_keyboard")

                # 给键盘节点 3 秒钟渲染它的界面
                time.sleep(3)

                # ⚠️ 关键修复：无情清空你在上面这 8 秒内手贱按下的所有废键！
                while msvcrt.kbhit(): msvcrt.getch()

                print("\n" + "*" * 50)
                print("✅ 【系统完美就绪】现在请直接按 u, i, o 控制！(绝对不再回显)")
                print("*" * 50 + "\n")

                while is_node_running:
                    if msvcrt.kbhit():
                        char = msvcrt.getch()
                        if char == b'\x03':  # Ctrl+C 紧急停止
                            channel_main.send(b'\x03')
                            channel_kb.send(b'\x03')
                            time.sleep(1)
                            is_node_running = False
                            break
                        else:
                            # 纯净无污染的字节，直击底盘灵魂！
                            channel_kb.send(char)
                    time.sleep(0.01)

                channel_main.close()
                channel_kb.close()

            else:
                # 处理单命令 (1 或 3)
                channel_main = ssh.get_transport().open_session()
                channel_main.get_pty(term='xterm', width=100, height=40)

                log_thread = threading.Thread(target=read_ssh_output, args=(channel_main, None))
                log_thread.daemon = True
                log_thread.start()

                cmd = ""
                if user_input == '1':
                    cmd = "ros2 launch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch.py"
                elif user_input == '3':
                    cmd = "ros2 run wheeltec_robot_keyboard wheeltec_keyboard"
                else:
                    cmd = user_input

                channel_main.exec_command(f"{ROS2_SETUP} && {cmd}")

                # 同样加上防误触清理逻辑
                time.sleep(4)
                while msvcrt.kbhit(): msvcrt.getch()

                while is_node_running:
                    if msvcrt.kbhit():
                        char = msvcrt.getch()
                        if char == b'\x03':
                            channel_main.send(b'\x03')
                            time.sleep(1)
                            is_node_running = False
                            break
                        else:
                            channel_main.send(char)
                    time.sleep(0.01)

                channel_main.close()

            log_thread.join(timeout=1)
            print("\n[*] 节点已安全停止，已返回主菜单。")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        ssh.close()
        print("👋 再见！")


if __name__ == "__main__":
    connect_wifi()
    run_interactive_terminal()
