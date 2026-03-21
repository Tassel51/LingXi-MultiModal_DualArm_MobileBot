import cv2
import sys
import time
from CupGraspClass import zcup

# 颜色常量定义
RED = 4
BLUE = 2
YELLOW = 3
OTHER = 1


def run_camera_test():
    # 1. 初始化视觉实体
    print("正在初始化摄像头...")
    try:
        grasp_entity = zcup()
    except Exception as e:
        print(f"摄像头初始化失败: {e}")
        return

    print("--- 进入识别模式 (按下 Ctrl+C 退出) ---")

    colors = {
        "红色": RED,
        "蓝色": BLUE,
        "黄色": YELLOW,
        "其他": OTHER
    }

    try:
        while True:
            # 轮询识别各个颜色
            for color_name, color_code in colors.items():
                camera_data = grasp_entity.get_location(color_code)

                if camera_data is not None and any(v != 0 for v in camera_data):
                    # 格式化输出坐标信息
                    # 这里的坐标转换逻辑参考了你原代码中的 offset 处理
                    print(f"[{color_name}] 识别成功! 原始数据: {camera_data}")
                else:
                    # 如果没识别到，可以打印一个简短提示
                    pass

            # 短暂休眠避免占用过多 CPU
            time.sleep(0.1)

            # 如果 zcup 类内部使用了 OpenCV 窗口，需要这行代码来刷新窗口
            # 如果你想主动关闭窗口，可以在这里检测按键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n检测到退出信号，程序结束。")
    finally:
        # 释放资源（取决于 zcup 是否有释放函数，通常是 release）
        if hasattr(grasp_entity, 'cap'):
            grasp_entity.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    run_camera_test()