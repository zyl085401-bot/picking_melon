import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QTabWidget, QTextEdit,
                             QMessageBox)

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


class CodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BT节点生成工具(From msg)")
        self.setGeometry(100, 100, 1000, 800)
        
        # 保存按钮引用
        self.browse_btn = None
        self.generate_btn = None
        
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        # 主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 输入区域
        input_layout = QVBoxLayout()
        
        # 类名前缀
        self.class_prefix = QLineEdit()
        input_layout.addWidget(QLabel("类名前缀:"))
        input_layout.addWidget(self.class_prefix)
        
        # ROS2消息类型
        self.msg_type = QLineEdit()
        input_layout.addWidget(QLabel("ROS2消息类型 (格式: package::msg::Type):"))
        input_layout.addWidget(self.msg_type)
        
        # 输出目录
        self.output_dir = QLineEdit()
        self.browse_btn = QPushButton("浏览...")  # 保存为实例变量
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))
        dir_layout.addWidget(self.output_dir)
        dir_layout.addWidget(self.browse_btn)
        input_layout.addLayout(dir_layout)
        
        # 生成按钮
        self.generate_btn = QPushButton("生成代码")  # 保存为实例变量
        input_layout.addWidget(self.generate_btn)
        
        main_layout.addLayout(input_layout)
        
        # 代码预览
        self.tabs = QTabWidget()
        self.hpp_preview = QTextEdit()
        self.cpp_preview = QTextEdit()
        self.tabs.addTab(self.hpp_preview, ".hpp")
        self.tabs.addTab(self.cpp_preview, ".cpp")
        main_layout.addWidget(self.tabs)

    def setup_connections(self):
        # 直接使用保存的按钮引用
        self.browse_btn.clicked.connect(self.browse_directory)
        self.generate_btn.clicked.connect(self.generate_code)

    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir.setText(dir_path)

    def validate_inputs(self):
        if not self.class_prefix.text().strip():
            QMessageBox.critical(self, "错误", "必须填写类名前缀")
            return False
            
        msg_type = self.msg_type.text().strip()
        if not msg_type:
            QMessageBox.critical(self, "错误", "必须填写ROS2消息类型")
            return False
            
        if '::msg::' not in msg_type:
            QMessageBox.critical(self, "错误", "消息类型格式应为: package::msg::Type")
            return False
            
        return True

    def generate_hpp(self, class_name, header_path, msg_type):
        return f"""#ifndef PAPJIA_BEHAVIORS__{add_underscore_and_lowercase(class_name).upper()}_HPP
#define PAPJIA_BEHAVIORS__{add_underscore_and_lowercase(class_name).upper()}_HPP

#include <papjia_behavior_tree/async_behavior_base.hpp>
#include <behaviortree_cpp/action_node.h>
#include <papjia_behavior_tree/check_error.hpp>
#include <{header_path}>

namespace papjia::behaviors {{
class {class_name} : public papjia::behavior_tree::AsyncBehaviorBase {{
public:
    {class_name}(const std::string& name, const BT::NodeConfig& config,
               const std::shared_ptr<papjia::behavior_tree::BehaviorContext>& context);

    static BT::PortsList providedPorts();

private:
    tl::expected<bool, std::string> doWork() override;

    std::shared_future<tl::expected<bool, std::string>> &getFuture() override
    {{
            return future_;
    }}
    std::shared_future<tl::expected<bool, std::string>> future_;
}};
}} // namespace papjia::behaviors
#endif // {class_name.upper()}_HPP
"""

    def generate_cpp(self, class_name, header_name, msg_type, pkg_name):
        return f"""#include "{pkg_name}/{header_name}.hpp"

static const rclcpp::Logger LOGGER = rclcpp::get_logger("{add_underscore_and_lowercase(class_name)}");

namespace papjia::behaviors {{

{class_name}::{class_name}(const std::string& name,
                          const BT::NodeConfig& config,
                          const std::shared_ptr<papjia::behavior_tree::BehaviorContext>& context)
    : AsyncBehaviorBase(name, config, context)
{{
    RCLCPP_INFO_STREAM(LOGGER, "Initialized");
}}

BT::PortsList {class_name}::providedPorts() {{
    return {{
        BT::InputPort<std::string>("topic_name"),
        BT::InputPort<double>("timeout", 3.0, "Timeout in seconds"),
        BT::InputPort<double>("hz", 10.0, "Sampling frequency"),
        BT::OutputPort<{msg_type}>("{add_underscore_and_lowercase(msg_type.split('::')[-1])}")
    }};
}}

tl::expected<bool, std::string> {class_name}::doWork() {{
    // 获取输入参数
    auto topic_name = getInput<std::string>("topic_name");
    auto timeout = getInput<double>("timeout");
    auto hz = getInput<double>("hz");

    if (!topic_name || !timeout || !hz) {{
        return tl::make_unexpected("Missing required inputs");
    }}

    // 创建订阅器
    auto node = shared_resources_->node_;
    rclcpp::CallbackGroup::SharedPtr cb_group_not_executed = node->create_callback_group(
        rclcpp::CallbackGroupType::MutuallyExclusive, false);
    auto subscription_options = rclcpp::SubscriptionOptions();
    subscription_options.callback_group = cb_group_not_executed;
    rclcpp::QoS qos(rclcpp::KeepLast(10));
    auto not_executed_callback =
        [this]([[maybe_unused]] {msg_type}::ConstSharedPtr msg) -> void
    {{
        RCLCPP_INFO_STREAM(LOGGER, "I never heard message");
    }};
    rclcpp::Subscription<{msg_type}>::SharedPtr sub = node->create_subscription<{msg_type}>(topic_name.value(), qos, not_executed_callback, subscription_options);

    // 等待消息循环
    {msg_type} msg;
    rclcpp::MessageInfo msg_info;
    rclcpp::Rate rate(hz.value());

    while (rclcpp::ok() && timeout.value() > 0) {{
        rate.sleep();
        if (sub->take(msg, msg_info)) {{
            setOutput("{add_underscore_and_lowercase(msg_type.split('::')[-1])}", msg);
            return true;
        }}
        timeout.value() -= 1.0 / hz.value();
    }}

    return tl::make_unexpected("Timeout waiting for message");
}}

}} // namespace papjia::behaviors
"""

    def generate_code(self):
        if not self.validate_inputs():
            return
            
        try:
            # 获取输入参数
            class_prefix = self.class_prefix.text().strip()
            msg_type = self.msg_type.text().strip()
            output_dir = Path(self.output_dir.text().strip())
            pkg_name = output_dir.name
            
            # 处理消息类型
            parts = msg_type.split('::')
            pkg_parts = parts[:-2]
            msg_name = parts[-1]
            
            # 生成头文件名
            class_name = f"{class_prefix}FromTopicAction"
            header_name = f"{add_underscore_and_lowercase(class_name)}"

            
            # 获取头文件路径
            header_path = f"{'/'.join(pkg_parts)}/msg/{add_underscore_and_lowercase(msg_name)}.hpp"
            
            # 生成代码
            hpp_code = self.generate_hpp(class_name, header_path, msg_type)
            cpp_code = self.generate_cpp(class_name, header_name, msg_type, pkg_name)
            
            # 显示预览
            self.hpp_preview.setPlainText(hpp_code)
            self.cpp_preview.setPlainText(cpp_code)
            
            # 保存文件
            (output_dir / f"include/{pkg_name}/{header_name}.hpp").write_text(hpp_code)
            (output_dir / f"src/{header_name}.cpp").write_text(cpp_code)
            
            QMessageBox.information(self, "成功", f"文件已生成到:\n{output_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CodeGenerator()
    window.show()
    sys.exit(app.exec_())
