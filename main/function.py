import math
import numpy as np
import cv2
import pyrealsense2 as rs
import torch.utils.data
import time

color_dist = {
    'red': {'Lower': np.array([0, 70, 70]), 'Upper': np.array([10, 255, 255])},
    'red_second_range': {'Lower': np.array([170, 43, 46]), 'Upper': np.array([179, 255, 255])},
    'blue': {'Lower': np.array([90, 200, 180]), 'Upper': np.array([120, 255, 255])},
    'yellow': {'Lower': np.array([20, 70, 100]), 'Upper': np.array([40, 255, 255])},
    'green': {'Lower': np.array([65, 180, 80]), 'Upper': np.array([89, 255, 255])},
    # 注意：绿色、紫色和橙色的范围在您给出的代码片段中没有提及，所以这里没有包括它们。
}

def color_detect(frame, depth_intrin, aligned_depth_frame, ret=1):
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

    return locations, frame


def get_color_at_point(image, box):
    # 获取图像中某一点的BGR颜色值
    x_center, y_center, _, _ = box
    pixel = image[int(y_center), int(x_center)]
    pixel = cv2.cvtColor(np.uint8([[pixel]]), cv2.COLOR_BGR2HSV)[0][0]
    return int(x_center), int(y_center), pixel


def determine_cup_color(annotated_frame, bgr_img, box):
    # 获取一个点的颜色
    x_center, y_center, color = get_color_at_point(bgr_img, box)
    # print(color)
    h, s, v = color  # HSV值范围：H=0-179, S=0-255, V=0-255
    if 0 <= h <= 10 or 170 <= h <= 179:  # 红色在HSV的0°和360°（或179）
        cup_color = "Red"
        ret = 1
    elif 90 <= h <= 124:  # 蓝色在HSV的240°左右
        cup_color = "Blue"
        ret = 2
    elif 20 <= h <= 40:  # 黄色在HSV的60°左右
        cup_color = "Yellow"
        ret = 3
    else:
        cup_color = "Other"
        ret = 4
    cv2.putText(annotated_frame, cup_color, (x_center - 20, y_center - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 2)
    return annotated_frame, ret


def cup_detect(results, r, annotated_frame, rgb_img, aligned_depth_frame, depth_intrin, color=None):
    # Check if a bottle or table is detected in the results
    bottle_detected = any(r.boxes.cls == 41)
    locations = np.zeros((1, 3))
    if bottle_detected:
        class_41_indexes = torch.where(results[0].boxes.cls == 41)[0]
        # 获取目标框的中心点坐标和高与宽
        class_41_boxes = results[0].boxes.xywh[class_41_indexes]
        class_41_boxes_np = class_41_boxes.cpu().numpy()
        for box in class_41_boxes_np:  # 检测到的被子的数量可能不止一个
            annotated_frame, ret = determine_cup_color(annotated_frame, rgb_img, box)
            cv2.circle(annotated_frame, (int(box[0]), int(box[1])), 5, (0, 0, 255), -1)  # 关注中心点的坐标
            if ret == color:
                dis = aligned_depth_frame.get_distance(box[0], box[1])  # 这里需要注意一下这个数的类型
                camera_coordinate = rs.rs2_deproject_pixel_to_point(depth_intrin, [box[0], box[1]], dis)
                locations[0, :] = [camera_coordinate[0], camera_coordinate[1], camera_coordinate[2]]

    return annotated_frame, locations


def person_detect(results, r, annotated_frame, rgb_img, aligned_depth_frame, depth_intrin):
    # Check if a bottle or table is detected in the results
    person_detected = any(r.boxes.cls == 0)
    locations = np.zeros((1, 3))
    if person_detected:
        class_0_indexes = torch.where(results[0].boxes.cls == 0)[0]
        # 获取目标框的中心点坐标和高与宽
        class_0_boxes = results[0].boxes.xywh[class_0_indexes]
        class_0_boxes_np = class_0_boxes.cpu().numpy()
        for box in class_0_boxes_np:  # 检测到的被子的数量可能不止一个
            cv2.circle(annotated_frame, (int(box[0]), int(box[1])), 5, (0, 0, 255), -1)  # 关注中心点的坐标
            dis = aligned_depth_frame.get_distance(box[0], box[1])  # 这里需要注意一下这个数的类型
            camera_coordinate = rs.rs2_deproject_pixel_to_point(depth_intrin, [box[0], box[1]], dis)
            locations[0, :] = [camera_coordinate[0], camera_coordinate[1], camera_coordinate[2]]

    return annotated_frame, locations
