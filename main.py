import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from UI.Ui_main import Ui_MainWindow
from Search import Search
from Upload import Upload

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Search Picture')
        self.search = Search(self.SearchTab)
        self.upload = Upload(self.UploadTab)
        # 获取 SearchTab 和 UploadTab 的布局
        search_tab_layout = QVBoxLayout(self.SearchTab)
        upload_tab_layout = QVBoxLayout(self.UploadTab)

        # 将 Search 和 Upload 实例添加到对应的布局中
        search_tab_layout.addWidget(self.search)  # 将 Search 实例添加到 SearchTab 布局
        upload_tab_layout.addWidget(self.upload)  # 将 Upload 实例添加到 UploadTab 布局

        # 确保更新标签页的布局
        self.SearchTab.setLayout(search_tab_layout)
        self.UploadTab.setLayout(upload_tab_layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())