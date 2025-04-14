import os
import shutil
from ultralytics import YOLO
from PIL import Image


class CarImageDetector:
    def __init__(self, source_dir, target_dir):
        """
        初始化汽车图片检测器
        :param source_dir: 源图片目录
        :param target_dir: 目标目录(存放汽车图片)
        """
        self.source_dir = source_dir
        self.target_dir = target_dir

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        # 加载 YOLO 模型
        self.model = YOLO('yolov8n.pt')  # 加载预训练的 YOLOv8 模型

        # 定义与汽车相关的类别名称
        self.car_related_classes = {
            'car', 'truck', 'bus', 'motorcycle'
        }

    def is_valid_image(self, file_path):
        """
        检查文件是否为有效的图片文件
        :param file_path: 图片文件路径
        :return: bool
        """
        try:
            img = Image.open(file_path)
            img.verify()
            return True
        except:
            return False

    def contains_vehicle(self, image_path):
        """
        检测图片是否包含车辆
        :param image_path: 图片路径
        :return: bool
        """
        try:
            # 使用 YOLO 进行目标检测
            results = self.model(image_path)

            # 检查检测结果中是否包含车辆
            for result in results:
                # 获取检测到的所有类别名称
                detected_classes = [self.model.names[int(cls)] for cls in result.boxes.cls]

                # 检查是否有任何一个检测到的类别是车辆相关的
                if any(cls in self.car_related_classes for cls in detected_classes):
                    return True

            return False

        except Exception as e:
            print(f"处理图片 {image_path} 时发生错误: {str(e)}")
            return False

    def process_directory(self):
        """
        处理源目录中的所有图片
        """
        # 获取所有文件
        total_files = len([f for f in os.listdir(self.source_dir) if os.path.isfile(os.path.join(self.source_dir, f))])
        processed_files = 0

        for filename in os.listdir(self.source_dir):
            file_path = os.path.join(self.source_dir, filename)
            processed_files += 1

            # 检查是否为有效的图片文件
            if not os.path.isfile(file_path) or not self.is_valid_image(file_path):
                continue

            print(f"正在处理图片: {filename} ({processed_files}/{total_files})")

            # 检测图片是否包含汽车
            if self.contains_vehicle(file_path):
                print(f"发现车辆图片: {filename}")
                # 移动到目标目录
                shutil.copy2(file_path, os.path.join(self.target_dir, filename))


def main():
    # 设置源目录和目标目录
    source_dir = "landroverDefender"  # 替换为你的源图片目录
    target_dir = "new"  # 替换为你想要保存汽车图片的目录

    # 创建检测器实例并处理图片
    detector = CarImageDetector(source_dir, target_dir)
    detector.process_directory()

    print("处理完成!")


if __name__ == "__main__":
    main()