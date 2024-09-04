from PyQt5.QtCore import QThread, pyqtSignal
import os

class ImageLoaderThread(QThread):
    imagesLoaded = pyqtSignal(list)  # 自定义信号，用于传递图片路径列表

    def __init__(self, folderPath):
        super().__init__()
        self.folderPath = folderPath

    def run(self):
        images = []
        self._recursiveImageSearch(self.folderPath, images)
        self.imagesLoaded.emit(images)  # 发射信号，传递图片路径列表

    def _recursiveImageSearch(self, folderPath, images):
        for entry in os.scandir(folderPath):
            if entry.is_file() and entry.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                images.append(entry.path)
            elif entry.is_dir():
                self._recursiveImageSearch(entry.path, images)