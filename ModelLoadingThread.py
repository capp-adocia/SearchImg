from PyQt5.QtCore import QThread, pyqtSignal
from torchvision.models import resnet50
from torchvision import transforms
from torch import load

class ModelLoadingThread(QThread):
    finished = pyqtSignal(object)  # 自定义信号，用于线程完成时传递模型对象

    def run(self):
        # 加载预训练的 ResNet50 模型
        model = resnet50(pretrained=False)
        model.load_state_dict(load('model/resnet50-0676ba61.pth'))
        model.eval()  # 设置为评估模式

        # 定义转换操作，将图片转换为模型的输入格式
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # 调整图片大小以匹配 ResNet50 输入
            transforms.ToTensor(),  # 将图片转换为 PyTorch 张量
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 标准化
        ])
        
        # 发射信号，传递模型和转换操作
        self.finished.emit((model, transform))
