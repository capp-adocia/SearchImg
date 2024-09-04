from PyQt5.QtWidgets import QLabel, QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap
from UI.Ui_upload import Ui_Upload
import os
from LoadImagesThread import LoadImagesThread
from ImageLoaderThread import ImageLoaderThread

def standardize_path(path):
    """
    标准化路径：统一斜杠方向，移除多余的斜杠
    """
    # 将路径中的反斜杠替换为正斜杠，并去除多余的斜杠
    return os.path.normpath(path).replace('\\', '/')

# 上传图片
class Upload(QWidget, Ui_Upload):
    def __init__(self, parent=None):
        super(Upload, self).__init__(parent)
        self.setupUi(self)
        self.setAcceptDrops(True) # 启用拖拽属性
        self.Images = []
        self.scrollArea.setWidgetResizable(True)
        self.progressBar.setValue(0)
        self.uploadButton.clicked.connect(self.openFile)
        self.batchUpdloadButton.clicked.connect(self.batchFile)
        self.FolderUpdloadButton.clicked.connect(self.folderFile)
        self.CheckButton.clicked.connect(self.checkUpload)
        self.CheckButton.setEnabled(False)

    def dragEnterEvent(self, event):
        # 如果拖拽的数据包含图片，我们接受它
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # 获取拖拽的数据
        mime = event.mimeData()
        if mime.hasUrls():
            # 获取图片的 URL
            url = mime.urls()[0]
            path = url.toLocalFile()
            self.showImg([path])
            self.Images = [path]

    # 上传一个文件
    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "选择需要上传的图片", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        if fileName:
            self.Images = [fileName]
            self.showImg([fileName])

    # 上传多个文件
    def batchFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileNames, _ = QFileDialog.getOpenFileNames(self, "选择需要批量上传的图片", "", "Image Files (*.png *.jpg *.jpeg *.bmp)", options=options)
        if fileNames:
            self.Images = fileNames
            self.showImg(fileNames)

    # 上传一个文件夹中多个文件
    def folderFile(self):
        options = QFileDialog.Options()
        folderPath = QFileDialog.getExistingDirectory(self, "选择包含上传图片的文件目录", "", options=options)
        if folderPath:
            # 创建并启动线程
            self.thread = ImageLoaderThread(folderPath)
            self.thread.imagesLoaded.connect(self.updateImages)  # 连接信号到槽
            self.thread.start()
    
    def updateImages(self, images):
        self.Images = images
        self.showImg(self.Images)

    # 显示图片
    def showImg(self, paths):
        layout = self.scrollAreaWidgetContents.layout()
        # 清空之前的内容
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # 限制paths列表最多只取前100个元素
        paths = paths[:100]
        # 创建并启动线程
        self.drawThread = LoadImagesThread(paths)
        self.drawThread.updatePixmap.connect(self.addImageToGrid)
        self.drawThread.finished.connect(self.loadingFinished)
        self.drawThread.start()
        self.progressBar.setRange(0, 0)

    def addImageToGrid(self, path, row, col):
        pixmap = QPixmap(path)
        label = QLabel()
        label.setPixmap(pixmap.scaled(200, 200, Qt.IgnoreAspectRatio))  # 在主线程中创建 QLabel 和设置 QPixmap
        self.scrollAreaWidgetContents.layout().addWidget(label, row, col)

    def loadingFinished(self):
        print("Loading images completed.")
        self.CheckButton.setEnabled(True)
        self.progressBar.setRange(0, 1) # 将进度条设置为完成状态
        self.progressBar.setValue(0)
        self.progressBar.setValue(1)

    def checkUpload(self):
        settings = QSettings('config/config.ini', QSettings.IniFormat)  # 创建QSettings对象
        image_paths_key = 'image_paths'
        # 读取之前保存的图片路径
        pre_img_paths = settings.value(image_paths_key, [])
        # 标准化之前保存的路径
        pre_img_paths = [standardize_path(p) for p in pre_img_paths]
        # 如果 self.Images 不是空的
        if self.Images:
            # 标准化新的图片路径
            new_img_paths = [standardize_path(p) for p in self.Images]
            # 计算总共的图片数量
            total_images = len(new_img_paths)
            # 将新的图片路径追加到之前的路径列表中
            all_img_paths = pre_img_paths + new_img_paths
            # 去重后的路径列表
            unique_img_paths = list(set(all_img_paths))
            # 计算已存在的重复路径
            existing_paths = set(pre_img_paths)
            duplicate_paths = [p for p in new_img_paths if p in existing_paths]
            num_duplicates = len(duplicate_paths)
            # 计算成功保存的图片数量
            num_saved = total_images - num_duplicates
            # 更新配置文件中的图片路径
            settings.setValue(image_paths_key, unique_img_paths)
            # 初始化进度条
            self.progressBar.setMaximum(total_images)
            self.progressBar.setValue(0)
            # 更新进度条
            for index in range(total_images):
                self.progressBar.setValue(index + 1)

            # 清空图片列表
            self.Images.clear()

            # 处理上传完成状态
            self.CheckButton.setEnabled(False)

            # 提示用户统计信息
            QMessageBox.information(None, '上传图片', 
                f'总共处理的图片数量: {total_images}\n'
                f'数据库中已有的重复图片数量: {num_duplicates}\n'
                f'成功保存的图片数量: {num_saved}'
            )
        else:
            QMessageBox.warning(self, '上传图片', '没有图片可供上传！')
            self.CheckButton.setEnabled(False)
            self.progressBar.setValue(0)