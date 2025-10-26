import sys
import re
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QTextEdit,
    QLineEdit,
    QHBoxLayout,
)


class CppParser:
    @staticmethod
    def parse_ports(cpp_content):
        # 提取providedPorts函数中的端口列表部分
        ports_list_match = re.search(
            r"BT::PortsList\s+\w+::providedPorts\(\)\s*{.*?return\s+BT::PortsList\s*\(\s*{([^}]*)}\s*\);.*?}",
            cpp_content,
            re.DOTALL,
        )
        if not ports_list_match:
            print("No ports list found in the providedPorts function.")
            return [], []
        ports_content = ports_list_match.group(1)

        # 解析输入端口和输出端口
        input_ports = re.findall(
            r'BT::InputPort<((?:[^<>]+|<[^<>]*>)+)>\(\s*"([^"]+)"\s*(?:,\s*[^)]+)?\s*\)', ports_content
        )
        output_ports = re.findall(
            r'BT::OutputPort<((?:[^<>]+|<[^<>]*>)+)>\(\s*"([^"]+)"\s*(?:,\s*[^)]+)?\s*\)',
            ports_content,
        )

        return input_ports, output_ports

    @staticmethod
    def get_action_by_class_from_file(file_path, class_name):
        # 正则表达式提取类名和动作名
        pattern = r'::registerBehavior(?:NotSharedResources)?<([^>]+)>\(.*?,\s*"([^"]+)"\s*,.*?\);'

        try:
            with open(file_path, "r") as file:
                # 遍历文件中的每一行
                for line in file:
                    match = re.search(pattern, line)
                    if match:
                        registered_class_name = match.group(1)  # 提取类名
                        action_name = match.group(2)  # 提取动作名
                        if registered_class_name == class_name:
                            return action_name  # 返回对应的动作名
        except FileNotFoundError:
            return f"Error: The file '{file_path}' was not found."

        return "Action not found"  # 如果没有找到该类名的动作名


class XmlExporter:
    @staticmethod
    def export_to_xml(
        action_name,
        class_name,
        pkg_name,
        input_ports,
        output_ports,
        file_path,
        description="",
    ):
        # 创建根元素
        root = ET.Element("root")

        # 创建 action 元素
        action = ET.SubElement(root, "Action")
        action.set("ID", action_name)

        # 创建描述元素
        description_item = ET.SubElement(action, "description")
        description_item.text = description
        # 创建包名元素
        package = ET.SubElement(action, "package_name")
        package.text = pkg_name
        # 创建类名元素
        class_elem = ET.SubElement(action, "class_name")
        class_elem.text = class_name

        # 创建输入端口节点
        for port_type, port_name in input_ports:
            input_port = ET.SubElement(action, "input")
            input_port.set("name", port_name)  # 添加端口名称
            input_port.set("type", port_type)  # 添加端口类型

        # 创建输出端口节点
        for port_type, port_name in output_ports:
            output_port = ET.SubElement(action, "output")
            output_port.set("name", port_name)  # 添加端口名称
            output_port.set("type", port_type)  # 添加端口类型

        # 将 XML 树转换为字符串并格式化
        xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        # 使用 minidom 进行格式化
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

        # 将格式化后的 XML 写入文件
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(pretty_xml_str)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cpp_dir = None
        self.cpp_content = None
        self.class_name = None
        self.input_ports = None
        self.output_ports = None
        self.export_path = None
        self.action_name = None  # 增加一个字段来存储动作名称

    def initUI(self):
        self.setWindowTitle("C++ Parser to XML Exporter")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Select a C++ file to parse and export to XML", self)
        layout.addWidget(self.label)

        # 创建文件路径显示框（只读）
        self.file_path_display = QLineEdit(self)
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("文件路径显示")

        # 创建“Open C++ File”按钮
        self.btn_open = QPushButton("Open C++ File", self)
        self.btn_open.clicked.connect(self.openFileDialog)

        # 添加到布局中，先添加路径显示框，再添加按钮
        layout.addWidget(self.file_path_display)
        layout.addWidget(self.btn_open)

        # 添加一个文本输入框用于输入描述
        self.description_input = QLineEdit(self)
        self.description_input.setPlaceholderText("请输入描述...")
        layout.addWidget(self.description_input)

        self.btn_export = QPushButton("Export to XML", self)
        self.btn_export.clicked.connect(self.exportToXml)
        self.btn_export.setEnabled(False)  # Disabled until a file is loaded
        layout.addWidget(self.btn_export)

        # 新增区域显示输入端口和输出端口信息
        self.ports_label = QLabel("Ports Information:", self)
        layout.addWidget(self.ports_label)

        self.ports_display = QTextEdit(self)
        self.ports_display.setReadOnly(True)
        layout.addWidget(self.ports_display)

        # 新增区域显示动作名称
        # 创建水平布局容器
        h_layout = QHBoxLayout()
        # 将两个控件添加到水平布局
        self.action_label = QLabel("Action/Class Name:", self)
        self.action_display = QLabel(self)
        h_layout.addWidget(self.action_label)
        h_layout.addWidget(self.action_display)
        layout.addLayout(h_layout)

        self.setLayout(layout)

    def openFileDialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open C++ File",
            self.cpp_dir,
            "C++ Files (*.cpp);;All Files (*)",
            options=options,
        )
        self.cpp_dir = os.path.dirname(file_name)
        if file_name:
            self.file_path_display.setText(file_name)
            self.description_input.setText("")  # 清空描述
            try:
                with open(file_name, "r") as file:
                    self.cpp_content = file.read()

                class_name_match = re.search(
                    r"([A-Za-z0-9_]+)::providedPorts", self.cpp_content
                )
                if not class_name_match:
                    QMessageBox.critical(
                        self, "Error", "Could not find class name in the C++ file."
                    )
                    return

                self.class_name = class_name_match.group(1)
                self.input_ports, self.output_ports = CppParser.parse_ports(
                    self.cpp_content
                )

                if not self.input_ports and not self.output_ports:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "No input and output ports found in the C++ file.",
                    )
                    # return

                # 获取动作名称
                directory = os.path.dirname(file_name)  # 获取当前文件的目录
                register_behavior_file = os.path.join(
                    directory, "register_behavior.cpp"
                )

                # 使用函数从 register_behavior.cpp 获取动作名
                self.action_name = CppParser.get_action_by_class_from_file(
                    register_behavior_file, self.class_name
                )
                if self.action_name == "Action not found":
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Action for class '{self.class_name}' not found in register_behavior.cpp.",
                    )
                    return

                self.btn_export.setEnabled(True)  # Enable export button

                # 更新显示的端口信息
                self.update_ports_display()

                # 显示动作名称
                self.action_display.setText(f"{self.action_name}/{self.class_name}")

                QMessageBox.information(
                    self, "Success", "C++ file loaded successfully."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def update_ports_display(self):
        # 显示输入和输出端口
        ports_info = "Input Ports:\n"
        if self.input_ports:
            ports_info += "\n".join([f"  {port}" for port in self.input_ports]) + "\n\n"
        else:
            ports_info += "No input ports found.\n"

        ports_info += "Output Ports:\n"
        if self.output_ports:
            ports_info += "\n".join([f"  {port}" for port in self.output_ports]) + "\n"
        else:
            ports_info += "No output ports found.\n"

        self.ports_display.setText(ports_info)

    def exportToXml(self):
        # if not self.action_name or not self.input_ports or not self.output_ports:
        if not self.action_name:
            QMessageBox.critical(self, "Error", "No C++ file loaded or parsed.")
            return

        # 默认打开 config 文件夹进行选择
        cpp_path = Path(self.cpp_dir)
        pkg_name = cpp_path.parent.name
        config_folder_path = os.path.abspath(
            os.path.join(cpp_path.parent, "config", "action")
        )
        os.makedirs(config_folder_path, exist_ok=True)
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Export Folder", config_folder_path, options=options
        )
        description = self.description_input.text()
        if description == "":
            description = "No description provided."
        if folder_path:
            self.export_path = os.path.join(folder_path, f"{self.action_name}.xml")
            try:
                XmlExporter.export_to_xml(
                    self.action_name,
                    self.class_name,
                    pkg_name,
                    self.input_ports,
                    self.output_ports,
                    self.export_path,
                    description,
                )
                QMessageBox.information(
                    self,
                    "Success",
                    f"XML file has been successfully exported to:\n{self.export_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"An error occurred while exporting: {str(e)}"
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
