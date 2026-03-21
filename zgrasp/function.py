import math
import numpy as np
import cv2
import pyrealsense2 as rs
import time

color_dist = {
    'red': {'Lower': np.array([0, 70, 70]), 'Upper': np.array([10, 255, 255])},
    'red_second_range': {'Lower': np.array([170, 43, 46]), 'Upper': np.array([179, 255, 255])},
    'blue': {'Lower': np.array([90, 200, 180]), 'Upper': np.array([120, 255, 255])},
    'yellow': {'Lower': np.array([20, 70, 100]), 'Upper': np.array([40, 255, 255])},
    'green': {'Lower': np.array([65, 150, 40]), 'Upper': np.array([89, 255, 255])},
    # 注意：绿色、紫色和橙色的范围在您给出的代码片段中没有提及，所以这里没有包括它们。
}


def detect(frame, depth_intrin, aligned_depth_frame, ret:int=1):
    print(f'ret={ret}')
    locations = np.zeros((1, 3))
    ball_color = ''
    if ret == 4:
        ball_color = 'red'
    elif ret == 2:
        ball_color = 'blue'
    elif ret == 3:
        ball_color = 'yellow'
    elif ret == 1:
        ball_color = 'green'
    if frame is not None:
        gs_frame = cv2.GaussianBlur(frame, (5, 5), 0)  # 高斯模糊
        hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)  # 转化成HSV图像
        erode_hsv = cv2.erode(hsv, None, iterations=2)  # 腐蚀
        inRange_hsv = cv2.inRange(erode_hsv, color_dist[ball_color]['Lower'], color_dist[ball_color]['Upper'])
        cnts, _ = cv2.findContours(inRange_hsv.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            center = rect[0]
            center = (int(center[0]), int(center[1]))
            cv2.drawContours(frame, [box], -1, (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            cv2.circle(frame, [320, 240], 5, (0, 0, 255), -1)

            dis = aligned_depth_frame.get_distance(center[0], center[1])  # 获取中心点距离
            camera_coordinate = rs.rs2_deproject_pixel_to_point(depth_intrin, [center[0], center[1]], dis)
            locations[0, :] = [camera_coordinate[0], camera_coordinate[1], camera_coordinate[2]]
        cv2.imshow('camera', frame)
    return locations
