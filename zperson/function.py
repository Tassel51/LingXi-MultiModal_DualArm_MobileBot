import numpy as np
import cv2
import pyrealsense2 as rs
import torch.utils.data

def person_detect(results, r, annotated_frame, aligned_depth_frame, depth_intrin):
    # Check if a bottle or table is detected in the results
    person_detected = any(r.boxes.cls == 0)  # 人
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