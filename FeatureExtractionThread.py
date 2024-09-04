from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image, UnidentifiedImageError
from torch import no_grad
from torch import cat
from time import time

def load_images_and_extract_features(image_paths, model, transform, update_progress):
    features = []
    labels = []
    total_images = len(image_paths)
    start_time = time()  # 开始时间

    for i, path in enumerate(image_paths):
        step_time = time()  # 记录每步开始的时间
        try:
            image = Image.open(path).convert('RGB')
            image = transform(image)
            image = image.unsqueeze(0)

            with no_grad():
                output = model(image)
                features.append(output)
                labels.append(i)

        except (UnidentifiedImageError, SyntaxError) as e:
            print(f"Error loading image {path}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error with image {path}: {e}")
            continue

        # 计算每步处理时间并发送更新进度的信号
        elapsed_time = time() - step_time
        update_progress((i + 1) / total_images * 100)

    # 合并特征并计算总时间
    features = cat(features, dim=0)
    total_elapsed_time = time() - start_time  # 总处理时间
    return features, labels, total_elapsed_time

def format_time(seconds):
    """
    格式化时间，将秒数转换为更直观的时间单位。
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}分钟"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.2f}小时"
    else:
        days = seconds / 86400
        return f"{days:.2f}天"

class FeatureExtractionThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    time_info = pyqtSignal(str)  # 用于更新时间标签
    total_time = pyqtSignal(str)  # 信号来传递格式化后的总时间

    def __init__(self, img_files, model, transform):
        super().__init__()
        self.img_files = img_files
        self.model = model
        self.transform = transform

    def run(self):
        self.start_time = time()
        features, labels, total_time = load_images_and_extract_features(
            self.img_files, self.model, self.transform, self.update_progress)
        self.features = features
        self.labels = labels
        self.total_time.emit(format_time(total_time))  # 发出格式化后的总时间信号
        self.finished.emit()  # 发出完成信号

    def update_progress(self, progress):
        current_time = time()
        elapsed_time = current_time - self.start_time
        estimated_total_time = elapsed_time / (progress / 100)
        remaining_time = estimated_total_time - elapsed_time
        self.progress.emit(int(progress))
        self.time_info.emit(f"剩余时间: {format_time(remaining_time)}")  # 发出格式化后的剩余时间