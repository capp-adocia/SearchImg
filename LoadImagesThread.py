from PyQt5.QtCore import QThread, pyqtSignal
import os

class LoadImagesThread(QThread):
    updatePixmap = pyqtSignal(str, int, int)  # 发送 path 和位置信息
    finished = pyqtSignal()  # 加载完成的信号

    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.max_columns = 4

    def run(self):
        row = 0
        col = 0
        for path in self.paths:
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.updatePixmap.emit(path, row, col)  # 发送处理好的 QPixmap
                col += 1
                if col >= self.max_columns:
                    col = 0
                    row += 1
        self.finished.emit()