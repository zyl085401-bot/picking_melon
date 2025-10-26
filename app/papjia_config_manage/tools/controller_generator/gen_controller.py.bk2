from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QFormLayout, QComboBox, QTextEdit, QFileDialog
import sys


def add_underscore_and_lowercase(s):
    if not s:
        return s

    result = s[0].lower()
    for char in s[1:]:
        if char.isupper():
            result += "_" + char.lower()
        else:
            result += char
    return result


class ROS2ControllerGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.joints = {}  # Stores joints and their interfaces
        self.gpios = {}  # Stores gpios and their interfaces
        self.current_joint = None  # Currently selected joint
        self.current_joint_v2 = None  # Currently selected joint
        self.initUI()

    def initUI(self):
        # 主布局分为左右两栏
        main_layout = QHBoxLayout()

        # 左栏布局
        left_layout = QVBoxLayout()

        # 右栏布局
        right_layout = QVBoxLayout()

        # ================= 左栏内容 =================
        # 包路径选择
        pkg_group = QVBoxLayout()
        pkg_group.addWidget(QLabel("Behavior Package Path:"))
        self.pkg_path_input = QLineEdit()
        self.pkg_path_button = QPushButton("Browse")
        self.pkg_path_button.clicked.connect(self.select_behavior_pkg_dir)
        pkg_hbox = QHBoxLayout()
        pkg_hbox.addWidget(self.pkg_path_input)
        pkg_hbox.addWidget(self.pkg_path_button)
        pkg_group.addLayout(pkg_hbox)
        left_layout.addLayout(pkg_group)

        # 类名输入
        class_group = QFormLayout()
        self.class_name_input = QLineEdit()
        class_group.addRow("Class Name:", self.class_name_input)
        left_layout.addLayout(class_group)

        # 服务/动作输入
        service_action_group = QFormLayout()
        self.service_input = QLineEdit()
        self.action_input = QLineEdit()
        service_action_group.addRow("Service Type:", self.service_input)
        service_action_group.addRow("Action Type:", self.action_input)
        left_layout.addLayout(service_action_group)

        # 关节管理
        joint_management = QVBoxLayout()
        joint_management.addWidget(QLabel("Joint Management:"))

        # 添加关节部分
        joint_add_group = QHBoxLayout()
        self.joint_name_input = QLineEdit()
        self.joint_name_input.setPlaceholderText("New Joint Name")
        self.add_joint_button = QPushButton("Add Joint")
        self.add_joint_button.clicked.connect(self.add_joint)
        joint_add_group.addWidget(self.joint_name_input)
        joint_add_group.addWidget(self.add_joint_button)
        joint_management.addLayout(joint_add_group)

        # 关节选择部分
        self.joint_combo = QComboBox()
        self.joint_combo.currentTextChanged.connect(self.select_joint)
        joint_management.addWidget(QLabel("当前选择关节:"))
        joint_management.addWidget(self.joint_combo)

        # 接口添加部分
        interface_group = QFormLayout()
        self.interface_name_input = QLineEdit()
        self.interface_name_input.setPlaceholderText("position/velocity/effort/other")
        self.interface_type_combo = QComboBox()
        self.interface_type_combo.addItems(["state_interface", "command_interface"])
        self.add_interface_button = QPushButton("Add Interface")
        self.add_interface_button.clicked.connect(self.add_interface)
        interface_group.addRow("Interface Name:", self.interface_name_input)
        interface_group.addRow("Interface Type:", self.interface_type_combo)
        interface_group.addRow(self.add_interface_button)
        joint_management.addLayout(interface_group)

        left_layout.addLayout(joint_management)

        # 关节选择下拉框（放在左栏最底部）
        self.joint_combo2 = QComboBox()
        self.joint_combo2.currentTextChanged.connect(self.select_joint_v2)
        left_layout.addWidget(QLabel("当前选择关节:"))
        left_layout.addWidget(self.joint_combo2)
        left_layout.addStretch()  # 添加伸缩空间

        # ================= 右栏内容 =================
        # 生成按钮
        self.generate_button = QPushButton("Generate Controller Code")
        self.generate_button.clicked.connect(self.generate_code)
        right_layout.addWidget(self.generate_button)

        # 输出显示
        right_layout.addWidget(QLabel("代码输出:"))
        self.output_display = QTextEdit()
        self.output_display.setMinimumWidth(400)
        right_layout.addWidget(self.output_display)

        # 将左右布局加入主布局
        main_layout.addLayout(left_layout, 3)  # 左栏占3份宽度
        main_layout.addLayout(right_layout, 2)  # 右栏占2份宽度

        self.setLayout(main_layout)
        self.setWindowTitle("ROS2 Controller Generator")
        self.resize(1000, 600)

    def add_joint(self):
        joint_name = self.joint_name_input.text().strip()
        if joint_name and joint_name not in self.joints:
            self.joints[joint_name] = []
            self.joint_combo.addItem(joint_name)
            self.joint_combo2.addItem(joint_name)
            self.joint_combo.setCurrentText(joint_name)
            self.joint_name_input.clear()

    def select_joint(self, joint_name):
        self.current_joint = joint_name if joint_name else None

    def select_joint_v2(self, joint_name):
        self.current_joint_v2 = joint_name if joint_name else None

    def add_interface(self):
        if self.current_joint:
            interface_name = self.interface_name_input.text().strip()
            interface_type = self.interface_type_combo.currentText()
            if interface_name:
                self.joints[self.current_joint].append({"name": interface_name, "type": interface_type})
                self.interface_name_input.clear()

    def select_behavior_pkg_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.pkg_path_input.setText(dir_path)

    def generate_code(self):
        try:
            self.generate_controller_code()
        except Exception as e:
            print(e)

    def generate_controller_code(self):
        package_path = self.pkg_path_input.text().strip()
        package_name = package_path.split("/")[-1]
        class_name = f"{self.class_name_input.text().strip()}Controller"
        file_name = add_underscore_and_lowercase(class_name)
        service_type = self.service_input.text().strip()
        service_type_using = f'{service_type.split("::")[-1]}Service' if service_type else ""
        service_topic = f'"{add_underscore_and_lowercase(service_type_using)}"' if service_type_using else ""
        action_type = self.action_input.text().strip()
        action_type_using = f'{action_type.split("::")[-1]}Action' if action_type else ""
        action_topic = f'"{add_underscore_and_lowercase(service_type_using)}"' if service_type_using else ""

        includes = f"""
#ifndef {class_name.upper()}_CONTROLLER_HPP
#define {class_name.upper()}_CONTROLLER_HPP

#include "rclcpp_action/rclcpp_action.hpp"
#include "controller_interface/controller_interface.hpp"
#include "{package_name}/{file_name}_parameters.hpp"
"""
        if service_type:
            includes += f'\n#include "{service_type}.hpp"'
        if action_type:
            includes += f'\n#include "{action_type}.hpp"'

        service_code = ""
        if service_type:
            service_code = f"""
        // Service type
        using {service_type_using} = {service_type};
        using {service_type_using}Server = rclcpp::Service<{service_type_using}>;

        // Service server
        {service_type_using}Server::SharedPtr {add_underscore_and_lowercase(service_type_using)}_server_;

        // Service callback
        bool {add_underscore_and_lowercase(service_type_using)}_callback(const std::shared_ptr<{service_type_using}::Request> request,
            std::shared_ptr<{service_type_using}::Response> response);
        """
            service_code += "\n"

        action_code = ""
        if action_type:
            action_code = f"""
        // Action type
        using {action_type_using} = {action_type};
        using {action_type_using}Server = rclcpp_action::Server<{action_type_using}>;
        using {action_type_using}GoalHandle = rclcpp_action::ServerGoalHandle<{action_type_using}>;

        // Action server
        rclcpp_action::Server<action_type_using>::SharedPtr {add_underscore_and_lowercase(action_type_using)}_server_;

        // Action callback
        rclcpp_action::GoalResponse handle_goal(
            const rclcpp_action::GoalUUID &uuid, std::shared_ptr<const {action_type_using}::Goal> goal);
        rclcpp_action::CancelResponse handle_cancel(const std::shared_ptr<{action_type_using}GoalHandle> goal_handle);
        void handle_accepted(std::shared_ptr<{action_type_using}GoalHandle> goal_handle);
        void execute(const std::shared_ptr<{action_type_using}GoalHandle> goal_handle);
        """

        hpp_code = f"""
{includes}

namespace generated_ros2_controller {{
    class {class_name} : public controller_interface::ControllerInterface {{
    public:
        {class_name}();
        controller_interface::InterfaceConfiguration command_interface_configuration() const override;
        controller_interface::InterfaceConfiguration state_interface_configuration() const override;
        controller_interface::return_type update(const rclcpp::Time &time, const rclcpp::Duration &period) override;

        controller_interface::CallbackReturn on_init() override;
        controller_interface::CallbackReturn on_configure(const rclcpp_lifecycle::State &previous_state) override;
        controller_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State &previous_state) override;
        controller_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State &previous_state) override;
        
    private:
        std::shared_ptr<ParamListener> param_listener_;
        Params params_;
        std::map<std::string, int> interface_mapping_;

        {f'{service_code}' if service_type else ''}
        {f'{action_code}' if action_type else ''}
    }};
}}

#endif
        """

        cpp_code = f"""
#include "{file_name}.hpp"

namespace generated_ros2_controller {{

    {class_name}::{class_name}() {{}}

    controller_interface::InterfaceConfiguration {class_name}::command_interface_configuration() const {{
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        // 配置关节接口
        for (const auto &joint : params_.joints) {{
            auto name = joint["name"].as<std::string>();
            auto command_interfaces = joint["command_interfaces"].as<std::vector<std::string>>();
            for (const auto &interface : command_interfaces) 
            {{
                config.names.push_back(name + "/" + interface);
                interface_mapping_[name + "---command---" + interface] = config.names.size() - 1;
            }}
        }}
        return config;
    }}

    controller_interface::InterfaceConfiguration {class_name}::state_interface_configuration() const {{
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        // 配置关节接口
        for (const auto &joint : params_.joints) {{
            auto name = joint["name"].as<std::string>();
            auto state_interfaces = joint["state_interfaces"].as<std::vector<std::string>>();
            for (const auto &interface : state_interfaces) {{
                config.names.push_back(name + "/" + interface);
                interface_mapping_[name + "---state---" + interface] = config.names.size() - 1;
            }}
        }}
        return config;
    }}

    controller_interface::return_type {class_name}::update(const rclcpp::Time &time, const rclcpp::Duration &period) {{
        return controller_interface::return_type::OK;
    }}

    controller_interface::CallbackReturn {class_name}::on_init() {{
        try
        {{
            param_listener_ = std::make_shared<ParamListener>(get_node());
            params_ = param_listener_->get_params();
            return controller_interface::CallbackReturn::SUCCESS;
        }} catch (const std::exception &e) {{
            RCLCPP_ERROR(get_node()->get_logger(), "Initialization failed: %s", e.what());
            return controller_interface::CallbackReturn::ERROR;
        }}
    }}

    controller_interface::CallbackReturn {class_name}::on_configure(const rclcpp_lifecycle::State &) {{
        if (!param_listener_)
        {{
            RCLCPP_ERROR(get_node()->get_logger(), "Error encountered during init");
            return controller_interface::CallbackReturn::ERROR;
        }}
        else
        {{
            params_ = param_listener_->get_params();
            RCLCPP_INFO(get_node()->get_logger(), "Get params");
        }}
        return controller_interface::CallbackReturn::SUCCESS;
    }}

    controller_interface::CallbackReturn {class_name}::on_activate(const rclcpp_lifecycle::State &) {{
        {f"service_server_ = get_node()->create_service<{service_type_using}>({service_topic}, &{class_name}::handle_service, this);" if service_type else ""}
        {f"action_server_ = rclcpp_action::create_server<{action_type_using}>(get_node(), {action_topic}, std::bind(&{class_name}::handle_goal, this, _1, _2), std::bind(&{class_name}::handle_cancel, this, _1), std::bind(&{class_name}::handle_accepted, this, _1));" if action_type else ""}
        return controller_interface::CallbackReturn::SUCCESS;
    }}

    controller_interface::CallbackReturn {class_name}::on_deactivate(const rclcpp_lifecycle::State &) {{
        return controller_interface::CallbackReturn::SUCCESS;
    }}
}}
        """

        self.output_display.setText(f"HPP File:\n{hpp_code}\n\nCPP File:\n{cpp_code}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ROS2ControllerGenerator()
    window.show()
    sys.exit(app.exec_())
