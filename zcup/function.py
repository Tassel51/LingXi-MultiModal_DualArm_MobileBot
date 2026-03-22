import numpy as np
import cv2
import pyrealsense2 as rs
import torch.utils.data

# 检测杯子同时得到杯子的颜色
def get_color_at_point(image, box):
    # 获取图像中某一点的BGR颜色值
    x_center, y_center, _, _ = box
    pixel = image[int(y_center), int(x_center)]
    pixel = cv2.cvtColor(np.uint8([[pixel]]), cv2.COLOR_BGR2HSV)[0][0]
    return int(x_center), int(y_center), pixel

def get_average_color_in_box(image, box, color_space='bgr'):
    # 计算矩形框的边界
    x_center, y_center, w, h = box
    x_start = max(int(x_center - w / 2), 0)
    y_start = max(int(y_center - h / 2), 0)
    x_end = min(int(x_center + w / 2), image.shape[1] - 1)
    y_end = min(int(y_center + h / 2), image.shape[0] - 1)

    # 初始化颜色总和和像素数量
    color_sum = np.zeros(3, dtype=np.float64)
    pixel_count = 0

    # 遍历矩形框内的所有像素
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            pixel = image[y, x]
            if color_space == 'bgr':
                pixel = cv2.cvtColor(np.uint8([[pixel]]), cv2.COLOR_BGR2HSV)[0][0]
            color_sum += pixel
            pixel_count += 1

    # 计算平均颜色
    if pixel_count > 0:
        avg_color = color_sum / pixel_count
    else:
        avg_color = np.zeros(3, dtype=np.float64)

    return  int(x_center), int(y_center), avg_color

def determine_cup_color(annotated_frame, bgr_img, box):
    # 获取一个点的颜色
    x_center, y_center, color = get_color_at_point(bgr_img, box)
    # 获取范围内的平均颜色
    # x_center, y_center, color = get_average_color_in_box(bgr_img, box)
    # print(color)
    h, s, v = color  # HSV值范围：H=0-179, S=0-255, V=0-255
    if 0 <= h <= 10 or 170 <= h <= 179:  # 红色在HSV的0°和360°（或179）
        cup_color = "Red"
        ret = 4
    elif 90 <= h <= 124:  # 蓝色在HSV的240°左右
        cup_color = "Blue"
        ret = 2
    elif 20 <= h <= 40:  # 黄色在HSV的60°左右
        cup_color = "Yellow"
        ret = 3
    else:
        cup_color = "Other"
        ret = 1
    cv2.putText(annotated_frame, cup_color, (x_center - 20, y_center - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 2)
    return annotated_frame, ret

def cup_detect(results, r, annotated_frame, rgb_img, aligned_depth_frame, depth_intrin, color=None):
    # Check if a bottle or table is detected in the results
    bottle_detected = any(r.boxes.cls == 3)
    locations = np.zeros((1, 3))
    if bottle_detected:
        class_41_indexes = torch.where(results[0].boxes.cls == 3)[0]
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