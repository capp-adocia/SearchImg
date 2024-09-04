from PyQt5.QtWidgets import QWidget, QFileDialog, QLabel, QMessageBox, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QSettings, QTimer, QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices, QCursor
from UI.Ui_search import Ui_Search
import os
from torch import no_grad
import faiss
from torchvision.models import resnet50
from torchvision import transforms
from PIL import Image
from FeatureExtractionThread import FeatureExtractionThread
from LoadImagesThread import LoadImagesThread
from time import time
from ModelLoadingThread import ModelLoadingThread

# 搜索图片
class Search(QWidget, Ui_Search):
    def __init__(self, parent=None):
        super(Search, self).__init__(parent)
        self.setupUi(self)
        # 启用拖拽属性
        self.setAcceptDrops(True)
        self.targetImgFile = '' # 目标图片路径
        settings = QSettings('config/config.ini', QSettings.IniFormat)
        self.ImgDBPath = settings.value('image_paths', []) # 图片数据库路径列表
        self.labels = []
        self.thread = None
        self.searchButton.setEnabled(False) # 初始化搜索按钮为不可用状态
        self.progressBar.setValue(0) # 初始化进度条为0
        # 加载预训练的 ResNet50 模型
        # self.model = resnet50(pretrained=True)
        # self.model.eval()  # 设置为评估模式
        # 定义转换操作，将图片转换为模型的输入格式
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),  # 调整图片大小以匹配 ResNet50 输入
            transforms.ToTensor(),  # 将图片转换为 PyTorch 张量
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 标准化
        ])

        self.uploadButton.clicked.connect(self.openFile)
        self.searchButton.clicked.connect(self.searchImg)
        self.upgradeButton.clicked.connect(self.upgradeDB)
        self.upgradeLabels()
        # 启动模型加载线程
        self.model_loading_thread = ModelLoadingThread()
        self.model_loading_thread.finished.connect(self.on_model_loaded)
        self.model_loading_thread.start()
        # 显示等待对话框
        self.waiting_dialog = QMessageBox(self)
        self.waiting_dialog.setWindowTitle("请稍等")
        self.waiting_dialog.setText("正在初始化中，请稍等...")
        self.waiting_dialog.setStandardButtons(QMessageBox.NoButton)  # 禁用按钮
        self.waiting_dialog.setModal(True)  # 使对话框模态
        self.waiting_dialog.show()
        

    def on_model_loaded(self, model_and_transform):
        # 获取模型和转换操作
        self.model, self.transform = model_and_transform
        
        # 更新UI组件状态
        self.searchButton.setEnabled(True)
        # 关闭等待对话框
        self.waiting_dialog.setText("初始化加载完成！")
        self.waiting_dialog.setStandardButtons(QMessageBox.Ok)
        self.waiting_dialog.close()

    def upgradeLabels(self):
        self.labels = []
        settings = QSettings("config/config.ini", QSettings.IniFormat)
        image_labels_len = settings.value("ImageLabels", defaultValue=0)
        # 将长度转换为整数列表
        if image_labels_len:
            for i in range(int(image_labels_len)):
                self.labels.append(str(i))
        else:
            self.labels = []
 
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
            self.targetImgFile = url.toLocalFile()

    # 上传一个文件
    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "选择需要上传的图片", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        if fileName:
            self.targetImgFile = fileName
            self.searchButton.setEnabled(True)
            
    # 显示图片
    def showImg(self, paths):
        layout = self.scrollAreaWidgetContents.layout()
        # 清空之前的内容
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
         # 创建并启动线程
        self.drawThread = LoadImagesThread(paths)
        self.drawThread.updatePixmap.connect(self.addImageToGrid)
        self.drawThread.finished.connect(self.loadingFinished)
        self.drawThread.start()

    def addImageToGrid(self, path, row, col):
        # 创建QWidget作为容器
        container = QWidget()
        layout = QVBoxLayout(container)
        # 设置容器的样式（颜色边框）
        container.setStyleSheet("QWidget { border: 2px solid #4CAF50; }")

        # 创建并设置图片标签
        imgLabel = QLabel()
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                raise FileNotFoundError("Image file not found.")
            imgLabel.setPixmap(pixmap.scaled(200, 200, Qt.IgnoreAspectRatio))
        except FileNotFoundError as e:
            imgLabel.setText(str(e))  # 显示错误消息
            imgLabel.setAlignment(Qt.AlignCenter)  # 居中错误消息
        except Exception as e:
            imgLabel.setText("Error loading image: " + str(e))  # 显示其他错误类型的错误消息
            imgLabel.setAlignment(Qt.AlignCenter)

        imgLabel.setCursor(QCursor(Qt.PointingHandCursor))
        imgLabel.mousePressEvent = lambda event, p=path: self.openDirectory(p)
        layout.addWidget(imgLabel)

        # 创建并设置路径标签
        pathLabel = QLabel(path)
        pathLabel.setFixedWidth(200)  # 设置固定宽度为图片的宽度
        pathLabel.setWordWrap(True)   # 启用自动换行
        pathLabel.setCursor(QCursor(Qt.PointingHandCursor))  # 设置鼠标悬停为手形指针

        # 添加鼠标进入和离开事件的样式
        pathLabel.setStyleSheet("QLabel { color: black; } QLabel:hover { background-color: #D3D3D3; }")
        pathLabel.mousePressEvent = lambda event: self.copyToClipboard(path)
        layout.addWidget(pathLabel)

        # 将容器添加到滚动区域的网格布局中
        self.scrollAreaWidgetContents.layout().addWidget(container, row, col)

    def copyToClipboard(self, text):
        QApplication.clipboard().setText(text)
        QMessageBox.information(None, "复制成功", "路径已复制到剪切板！")

    def loadingFinished(self):
        QTimer.singleShot(200, lambda: QMessageBox.information(None, '提示', '图片加载完成！'))
        
    # 打开目标目录
    def openDirectory(self, path):
        if os.path.exists(path):
            # 获取文件所在的文件夹路径
            folder_path = os.path.dirname(path)
            # 使用QUrl和QDesktopServices打开文件夹
            url = QUrl.fromLocalFile(folder_path)
            QDesktopServices.openUrl(url)
        else:
            QMessageBox.warning(self, '警告', f'{path}文件不存在！')

    def searchImg(self):
        if self.targetImgFile:
            # 加载 FAISS 索引
            index = faiss.read_index("resnet50_features.index")
            # print(self.targetImgFile)
            # 加载并处理查询图片
            query_image = Image.open(self.targetImgFile).convert('RGB')
            query_image = self.transform(query_image).unsqueeze(0)

            # 提取查询图片的特征
            with no_grad():
                query_features = self.model(query_image)
            # 执行搜索
            total_images = len(self.labels)
            if total_images < 100:
                k = total_images  # 如果图片总数少于100张，则全部返回
            else:
                k = 100  # 否则返回100张最相似的图片
            distances, indices = index.search(query_features.numpy(), k)
            # 打印结果
            # print(f"Top {k} most similar images:")
            # for i in range(k):
                # print(f"Distance: {distances[0][i]}, Label: {self.labels[indices[0][i]]}")
            # 获取相似图片的路径
            similar_image_paths = list(map(lambda i: self.ImgDBPath[indices[0][i]], range(k)))
            # print("\nSimilar image paths:", similar_image_paths)
            self.showImg(similar_image_paths)

        self.searchButton.setEnabled(False)

    # 更新图片数据库
    def upgradeDB(self):
        setting = QSettings('config/config.ini', QSettings.IniFormat)
        allImgPaths = setting.value('image_paths', [])
        processedImgPaths = setting.value('processed_images', [])
    
        newImgPaths = [path for path in allImgPaths if path not in processedImgPaths]
    
        if len(newImgPaths) > 0:
            self.start_time = time()
            self.thread = FeatureExtractionThread(newImgPaths, self.model, self.transform)
            
            self.thread.finished.connect(self.on_finished)
            self.thread.progress.connect(self.update_progress)
            self.thread.time_info.connect(self.update_time_label)  # 连接更新时间标签的信号
            self.thread.start()
            self.upgradeButton.setEnabled(False)
            self.uploadButton.setEnabled(False)
            settings = QSettings('config/config.ini', QSettings.IniFormat)
            self.ImgDBPath = settings.value('image_paths', []) # 图片数据库路径列表
        else:
            QMessageBox.warning(self, '警告', '没有新图片需要处理')


    def update_time_label(self, time_info):
        self.timeLabel.setText(time_info)

    def on_finished(self):
        features, labels = self.thread.features, self.thread.labels
        d = features.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(features.numpy())
        faiss.write_index(index, "resnet50_features.index")
    
        settings = QSettings("config/config.ini", QSettings.IniFormat)
        settings.setValue("ImageLabels", len(labels))
        # 更新已处理图片列表
        allImgPaths = settings.value('image_paths', [])
        settings.setValue('processed_images', allImgPaths)
    
        # 更新操作结束，计算用时和新增图片数量
        end_time = time()  # 记录结束时间
        elapsed_time = end_time - self.start_time  # 计算用时
    
        self.searchButton.setEnabled(True)
        self.upgradeButton.setEnabled(True)
        self.uploadButton.setEnabled(True)
        self.upgradeLabels()
        QMessageBox.information(None, '提示', '数据库更新完成！')
        QMessageBox.information(self, "提示", f'更新图片数据库，共新增{len(self.thread.features)}张图片，用时{elapsed_time:.2f}秒')

    
    def update_progress(self, value):
        self.progressBar.setValue(value)