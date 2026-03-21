# 导入必要的库
from ultralytics import YOLO  # 从 Ultralytics YOLO 中导入 YOLO 类

# 加载模型
model = YOLO('yolov8n.pt')  # 替换为你的实际模型路径

# 获取类别标签
class_labels = model.names  # `model.names` 是一个字典，键是类别 ID，值是类别名称

# 打印类别标签
print("类别标签：")
for class_id, class_name in class_labels.items():
    print(f"{class_id}: {class_name}")