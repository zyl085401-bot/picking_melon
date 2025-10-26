from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QComboBox, QHBoxLayout, QFileDialog
import sys
import re
from mtypes import TYPE_MAPPING

def add_underscore_and_lowercase(s):
    if not s:
        return s

    result = s[0].lower()  # 第一个字符直接转为小写
    for char in s[1:]:
        if char.isupper():
            result += "_" + char.lower()
        else:
            result += char
    return result


def get_items_text(list_widget):
    items_text = []
    for index in range(list_widget.count()):  # 遍历所有项
        item = list_widget.item(index)  # 获取 QListWidgetItem 对象
        items_text.append(item.text())  # 获取文本并添加到列表中
    return items_text


def parse_action_file(file_path):
    """
    解析 .action 文件，提取 Goal 和 Result 部分。
    """
    goal_fields = []
    result_fields = []
    with open(file_path, "r") as file:
        content = file.read()
        # 根据 --- 分隔符分割内容
        parts = content.split("---")
        if len(parts) >= 1:
            # 解析 Goal 部分
            goal_content = parts[0].strip()
            # 忽略注释，提取字段名称和类型
            goal_lines = [line.split("#")[0].strip() for line in goal_content.split("\n") if line.strip()]
            goal_fields = [re.findall(r"(\w+)\s+(\w+)", line)[0] for line in goal_lines if re.findall(r"(\w+)\s+(\w+)", line)]
        if len(parts) >= 2:
            # 解析 Result 部分
            result_content = parts[1].strip()
            # 忽略注释，提取字段名称和类型
            result_lines = [line.split("#")[0].strip() for line in result_content.split("\n") if line.strip()]
            result_fields = [re.findall(r"(\w+)\s+(\w+)", line)[0] for line in result_lines if re.findall(r"(\w+)\s+(\w+)", line)]
    return goal_fields, result_fields


class ActionClientGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.input_ports = []
        self.output_ports = []

    def initUI(self):
        layout = QVBoxLayout()

        # Action Client Name
        self.client_name_input = QLineEdit(self)
        self.client_name_input.setPlaceholderText("Enter Action Client Name")
        layout.addWidget(QLabel("Action Client Name:"))
        layout.addWidget(self.client_name_input)

        # Action Message Type
        self.action_type_input = QLineEdit(self)
        self.action_type_input.setPlaceholderText("Select Action Message Type File")
        self.action_type_button = QPushButton("Browse", self)
        self.action_type_button.clicked.connect(self.select_action_type_file)

        # Action Client Package Path
        self.pkg_path_input = QLineEdit(self)
        self.pkg_path_input.setPlaceholderText("Select Behavior Package Path")
        self.pkg_path_button = QPushButton("Browse", self)
        self.pkg_path_button.clicked.connect(self.select_behavior_pkg_dir)
        pkg_layout = QHBoxLayout()
        pkg_layout.addWidget(self.pkg_path_input)
        pkg_layout.addWidget(self.pkg_path_button)
        layout.addWidget(QLabel("Behavior Package Path:"))
        layout.addLayout(pkg_layout)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.action_type_input)
        action_layout.addWidget(self.action_type_button)
        layout.addWidget(QLabel("Action Message Type:"))
        layout.addLayout(action_layout)

        # Port Name & Type
        self.port_name_input = QLineEdit(self)
        self.port_name_input.setPlaceholderText("Enter Port Name")
        self.port_type_combo = QComboBox(self)
        self.port_type_combo.addItems(["int", "double", "string", "bool"])

        add_input_btn = QPushButton("Add Input Port", self)
        add_output_btn = QPushButton("Add Output Port", self)
        add_input_btn.clicked.connect(self.add_input_port)
        add_output_btn.clicked.connect(self.add_output_port)

        port_layout = QHBoxLayout()
        port_layout.addWidget(self.port_name_input)
        port_layout.addWidget(self.port_type_combo)
        port_layout.addWidget(add_input_btn)
        port_layout.addWidget(add_output_btn)
        layout.addLayout(port_layout)

        # Display Input & Output Ports
        self.input_list = QListWidget()
        self.output_list = QListWidget()

        # Add delete buttons for input and output ports
        delete_input_btn = QPushButton("Delete Selected Input", self)
        delete_input_btn.clicked.connect(self.delete_selected_input)
        delete_output_btn = QPushButton("Delete Selected Output", self)
        delete_output_btn.clicked.connect(self.delete_selected_output)

        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Input Ports:"))
        input_layout.addWidget(self.input_list)
        input_layout.addWidget(delete_input_btn)

        output_layout = QVBoxLayout()
        output_layout.addWidget(QLabel("Output Ports:"))
        output_layout.addWidget(self.output_list)
        output_layout.addWidget(delete_output_btn)

        layout.addLayout(input_layout)
        layout.addLayout(output_layout)

        # Export Buttons
        export_hpp_btn = QPushButton("Export HPP", self)
        export_cpp_btn = QPushButton("Export CPP", self)
        export_hpp_btn.clicked.connect(self.export_hpp)
        export_cpp_btn.clicked.connect(self.export_cpp)
        layout.addWidget(export_hpp_btn)
        layout.addWidget(export_cpp_btn)

        self.setLayout(layout)
        self.setWindowTitle("Action Client Configurator")

    def select_action_type_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Action Type File", "", "Action Files (*.action)")
        if file_path:
            self.action_type_input.setText(file_path)
            # 解析 .action 文件并填充端口
            goal_fields, result_fields = parse_action_file(file_path)
            print(goal_fields, result_fields)
            self.input_ports = []
            self.output_ports = []
            self.input_list.clear()
            self.output_list.clear()
            for field_type, field_name in goal_fields:
                field_type = TYPE_MAPPING.get(field_type)
                self.input_ports.append((field_name, field_type))
                self.input_list.addItem(f"{field_name}: {field_type}")
            for field_type, field_name in result_fields:
                field_type = TYPE_MAPPING.get(field_type)
                self.output_ports.append((field_name, field_type))
                self.output_list.addItem(f"{field_name}: {field_type}")

    def select_behavior_pkg_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Behavior Package Directory")
        if dir_path:
            self.pkg_path_input.setText(dir_path)

    def add_input_port(self):
        port_name = self.port_name_input.text()
        port_type = self.port_type_combo.currentText()
        if port_name:
            self.input_ports.append((port_name, port_type))
            self.input_list.addItem(f"{port_name}: {port_type}")
            self.port_name_input.clear()

    def add_output_port(self):
        port_name = self.port_name_input.text()
        port_type = self.port_type_combo.currentText()
        if port_name:
            self.output_ports.append((port_name, port_type))
            self.output_list.addItem(f"{port_name}: {port_type}")
            self.port_name_input.clear()

    def delete_selected_input(self):
        selected_item = self.input_list.currentRow()
        if selected_item >= 0:
            self.input_list.takeItem(selected_item)
            self.input_ports.pop(selected_item)

    def delete_selected_output(self):
        selected_item = self.output_list.currentRow()
        if selected_item >= 0:
            self.output_list.takeItem(selected_item)
            self.output_ports.pop(selected_item)

    def load_params(self):
        self.package_path = self.pkg_path_input.text()
        self.package_name = self.package_path.split("/")[-1]
        self.client_name = f"{self.client_name_input.text()}"
        self.class_name = f"{self.client_name}ActionClient"
        action_file_path = self.action_type_input.text()
        parts = action_file_path[:-7].split("/")
        self.action_type = "::".join(parts[-3:])
        self.action_type_include = parts[-3] + "/" + parts[-2] + "/" + add_underscore_and_lowercase(parts[-1])
        self.action_type_using = parts[-1]
        self.file_name = add_underscore_and_lowercase(self.client_name)
        self.file_name = f"{self.file_name}_action_client"

    def generate_port_string(self):
        strs = []
        items = get_items_text(self.input_list)
        strs.append(f'BT::InputPort<std::string>("action_name")')
        for item in items:
            port_name, port_type = item.split(": ")
            strs.append(f'BT::InputPort<{port_type}>("{port_name}")')
        strs.append(f'BT::InputPort<double>("goal_result_timeout")')
        strs.append(f'BT::InputPort<double>("wait_for_server_timeout")')
        strs.append(f'BT::InputPort<double>("goal_response_timeout")')
        strs.append(f'BT::InputPort<double>("cancel_response_timeout")')
        items = get_items_text(self.output_list)
        for item in items:
            port_name, port_type = item.split(": ")
            strs.append(f'BT::OutputPort<{port_type}>("{port_name}")')
        return ",\n                          ".join(strs)

    def generate_goal_string(self):
        strs = []
        items = get_items_text(self.input_list)
        build_str = f"        return {self.action_type_include.split('/')[0]}::build<{self.action_type_using}::Goal>()"
        for item in items:
            port_name, port_type = item.split(": ")
            strs.append(f'        const auto maybe_{port_name} = getInput<{port_type}>("{port_name}");')
            strs.append(f"        {port_type} {port_name};")
            strs.append(f"        if (const auto error = papjia::behavior_tree::maybe_error(maybe_{port_name}))")
            strs.append("        {")
            strs.append(f'            return tl::make_unexpected("input port {port_name} is not set");')
            strs.append("        }")
            strs.append("        else")
            strs.append("        {")
            strs.append(f"            {port_name} = maybe_{port_name}.value();")
            strs.append("        }")
            build_str += f".{port_name}({port_name})"
        strs.append(build_str)
        return "\n".join(strs)
    
    def generate_outport_string(self):
        strs = []
        items = get_items_text(self.output_list)
        for item in items:
            port_name, port_type = item.split(": ")
            strs.append(f'        setOutput<{port_type}>("{port_name}", result->{port_name});')
        return "\n".join(strs)

    def export_hpp(self):
        self.load_params()
        filename = f"{self.package_path}/include/{self.package_name}/{self.file_name}.hpp"
        header_guard = f"{add_underscore_and_lowercase(self.package_name).upper()}__{self.file_name.upper()}_HPP"
        with open(filename, "w") as file:
            file.write(f"#ifndef {header_guard}\n")
            file.write(f"#define {header_guard}\n\n")
            file.write("#include <string>\n")
            file.write("#include <papjia_behavior_tree/check_error.hpp>\n")
            file.write("#include <papjia_behavior_tree/papjia_behavior_tree.hpp>\n")
            file.write("#include <papjia_behavior_tree/action_client_behavior_base.hpp>\n")
            file.write(f"#include <{self.action_type_include}.hpp>\n\n")
            file.write(f"using {self.action_type_using} = {self.action_type};\n\n")
            file.write("namespace papjia::behaviors {\n")
            file.write(f"    class {self.class_name}  final : public papjia::behavior_tree::ActionClientBehaviorBase<{self.action_type_using}>\n")
            file.write("    {\n")
            file.write("    public:\n")
            file.write(
                f"        {self.class_name}(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);\n"
            )
            file.write("        static BT::PortsList providedPorts();\n")
            file.write("    private:\n")
            file.write(f"        tl::expected<{self.action_type_using}::Goal, std::string> createGoal();\n")
            file.write(f"        tl::expected<bool, std::string> processResult(const std::shared_ptr<{self.action_type_using}::Result> result);\n")
            file.write("    };\n")
            file.write("}\n\n")
            file.write("#endif\n")
        print(f"Exported {filename}")

    def export_cpp(self):
        self.load_params()
        filename = f"{self.package_path}/src/{self.file_name}.cpp"
        with open(filename, "w") as file:
            file.write(f"#include <{self.package_name}/{self.file_name}.hpp>\n\n")
            file.write("namespace papjia::behaviors {\n\n")
            file.write(
                f"    {self.class_name}::{self.class_name}(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) : papjia::behavior_tree::ActionClientBehaviorBase<{self.action_type_using}>(name, config, shared_resources) {{}}\n\n"
            )
            file.write(f"    BT::PortsList {self.class_name}::providedPorts()\n")
            file.write("    {\n")
            file.write(f"        return BT::PortsList({{{self.generate_port_string()}}});\n")
            file.write("    }\n\n")
            file.write(f"    tl::expected<{self.action_type_using}::Goal, std::string> {self.class_name}::createGoal()\n")
            file.write("    {\n")
            file.write(f"{self.generate_goal_string()};\n")
            file.write("    }\n\n")
            file.write(
                f"    tl::expected<bool, std::string> {self.class_name}::processResult(const std::shared_ptr<{self.action_type_using}::Result> result)\n"
            )
            file.write("    {\n")
            file.write(f'        if (!result) return tl::make_unexpected("Result is null");\n')
            file.write(f"{self.generate_outport_string()}\n")
            file.write(f"        return true;\n")
            file.write("    }\n\n")

            file.write("}\n")
        print(f"Exported {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ActionClientGUI()
    gui.show()
    sys.exit(app.exec_())
