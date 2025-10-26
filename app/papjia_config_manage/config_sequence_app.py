import sys
import json
from collections import OrderedDict
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QMessageBox


class JsonKeyMover(QWidget):
    def __init__(self):
        super().__init__()
        self.all_configs = {}
        self.config = {}
        self.key_tobe_moved = "flask"
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("JSON Key Mover")
        self.setGeometry(100, 100, 600, 400)

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧布局
        left_layout = QVBoxLayout()

        # 左侧列表
        self.left_list = QListWidget()
        left_layout.addWidget(self.left_list)

        # 加载JSON文件按钮
        self.load_button = QPushButton("Load JSON File")
        self.load_button.clicked.connect(self.load_json)
        left_layout.addWidget(self.load_button)

        # 右侧布局
        right_layout = QVBoxLayout()

        # 右侧列表
        self.right_list = QListWidget()
        right_layout.addWidget(self.right_list)

        # 导出按钮
        self.export_button = QPushButton("Export to JSON")
        self.export_button.clicked.connect(self.export_json)
        right_layout.addWidget(self.export_button)

        # 按钮布局
        button_layout = QVBoxLayout()

        # 移动到右侧按钮
        self.move_right_button = QPushButton(">")
        self.move_right_button.clicked.connect(self.move_to_right)
        button_layout.addWidget(self.move_right_button)

        # 移动到左侧按钮
        self.move_left_button = QPushButton("<")
        self.move_left_button.clicked.connect(self.move_to_left)
        button_layout.addWidget(self.move_left_button)

        # 将左侧、按钮、右侧布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(right_layout)

        # 设置主布局
        self.setLayout(main_layout)

    def load_json(self):
        # 打开文件对话框选择JSON文件
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "r") as file:
                    self.all_configs = json.load(file)
                    self.configs = self.all_configs[self.key_tobe_moved]
                    # 清空左侧列表
                    self.left_list.clear()
                    # 将JSON的key添加到左侧列表
                    for key in self.configs.keys():
                        self.left_list.addItem(key)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load JSON file: {str(e)}")

    def export_json(self):
        # 检查右侧列表是否为空
        if self.right_list.count() == 0:
            QMessageBox.warning(self, "Warning", "No keys to export!")
            return

        # 打开文件对话框选择保存路径
        file_name, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
        if file_name:
            try:
                # 创建字典
                configs = OrderedDict()
                for i in range(self.right_list.count()):
                    key = self.right_list.item(i).text()
                    configs[key] = self.configs[key]
                self.all_configs[self.key_tobe_moved] = configs
                # 写入JSON文件
                with open(file_name, "w") as file:
                    json.dump(self.all_configs, file, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Success", "JSON file exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export JSON file: {str(e)}")

    def move_to_right(self):
        # 获取选中的项
        selected_items = self.left_list.selectedItems()
        for item in selected_items:
            # 添加到右侧列表
            self.right_list.addItem(item.text())
            # 从左侧列表删除
            self.left_list.takeItem(self.left_list.row(item))

    def move_to_left(self):
        # 获取选中的项
        selected_items = self.right_list.selectedItems()
        for item in selected_items:
            # 添加到左侧列表
            self.left_list.addItem(item.text())
            # 从右侧列表删除
            self.right_list.takeItem(self.right_list.row(item))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = JsonKeyMover()
    ex.show()
    sys.exit(app.exec_())
