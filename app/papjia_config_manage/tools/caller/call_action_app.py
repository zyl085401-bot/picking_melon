import sys
import time
import importlib
from rosidl_runtime_py.utilities import get_action
from rclpy.node import Node
from rclpy.action import ActionClient
import rclpy

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QLabel,
)
from PyQt5.QtCore import QTimer


class ROS2ActionNode(Node):
    def __init__(self):
        super().__init__("qt_action_client_node")
        self._action_client = None
        self._action_goal_msg = None

    def discover_actions(self):
        """Discover available ROS2 actions with type information"""
        return [
            (
                name.split("_action/send_goal")[0][:-1],  # Action name
                types[0].replace("_SendGoal", "").replace("/action/", ".action.")  # Action type
            )
            for name, types in self.get_service_names_and_types()
            if "_action/send_goal" in name
        ]

    def get_goal_msg(self, action_type):
        """Initialize and return a new goal message instance"""
        module_name, _, cls_name = action_type.rpartition(".")
        module = importlib.import_module(module_name)
        self._action_goal_msg = getattr(module, cls_name).Goal()
        return self._action_goal_msg

    def create_action_client(self, action_name, action_type):
        """Initialize ActionClient for specified action"""
        ActionType = get_action(action_type.replace(".", "/"))
        self._action_client = ActionClient(self, ActionType, action_name)
        time.sleep(1.0)  # Allow time for server discovery

    def send_goal(self, goal_msg, feedback_callback=None):
        """Send goal to action server with optional feedback callback"""
        if self._action_client and self._action_client.wait_for_server(timeout_sec=1.0):
            return self._action_client.send_goal_async(goal_msg, feedback_callback=feedback_callback)
        return None


class ActionGUI(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self.current_goal_fields = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize main window UI components"""
        # self.setWindowTitle("ROS2 Action Client")
        # self.setGeometry(300, 300, 1200, 600)

        # main_widget = QWidget()
        # main_layout = QHBoxLayout(main_widget)
        main_layout = QHBoxLayout(self)  # 原为main_widget


        # Create three columns
        main_layout.addLayout(self._create_action_list_column())
        main_layout.addLayout(self._create_parameters_column())
        main_layout.addLayout(self._create_control_column())

        # self.setCentralWidget(main_widget)

    def _create_action_list_column(self):
        """Left column: Action list and refresh button"""
        column = QVBoxLayout()
        self.action_list = QListWidget()
        refresh_btn = QPushButton("Refresh Actions")
        refresh_btn.clicked.connect(self.refresh_actions)
        column.addWidget(refresh_btn)
        column.addWidget(self.action_list)
        return column

    def _create_parameters_column(self):
        """Middle column: Action parameters form"""
        column = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.form_group = QGroupBox("Action Parameters")
        self.form_group.setLayout(self.form_layout)
        column.addWidget(self.form_group)
        self.input_fields = {}
        return column

    def _create_control_column(self):
        """Right column: Goal controls and feedback/results"""
        column = QVBoxLayout()
        
        # Goal Controls
        control_group = QGroupBox("Goal Control")
        control_layout = QVBoxLayout()
        self.send_btn = QPushButton("Send Goal")
        control_layout.addWidget(self.send_btn)
        control_group.setLayout(control_layout)
        column.addWidget(control_group)

        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)

        # Feedback Display
        column.addWidget(self._create_labeled_display("Feedback:", self.feedback_display))
        column.addWidget(self._create_labeled_display("Result:", self.result_display))

        return column

    def _create_labeled_display(self, label_text, display_widget):
        """Create labeled display widget with consistent styling"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel(label_text))
        display_widget.setReadOnly(True)
        layout.addWidget(display_widget)
        return container

    def _connect_signals(self):
        """Connect UI signals to slots"""
        self.action_list.currentItemChanged.connect(self._handle_action_selection)
        self.send_btn.clicked.connect(self._send_goal)

    def refresh_actions(self):
        """Refresh list of available actions"""
        self.action_list.clear()
        for action_name, action_type in self.ros_node.discover_actions():
            self.action_list.addItem(f"{action_name} ({action_type})")

    def _handle_action_selection(self, item):
        """Handle selection change in action list"""
        if item:
            action_full = item.text().split(" (")
            self.selected_action = (action_full[0], action_full[1][:-1])
            self._create_parameter_form(self.selected_action[1])

    def _create_parameter_form(self, action_type):
        """Create input form for selected action type"""
        # Clear existing form
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.input_fields.clear()  # 清空旧有的输入字段引用

        try:
            self.action_goal_msg = self.ros_node.get_goal_msg(action_type)
            self._build_parameter_form(self.action_goal_msg, self.form_layout)
        except Exception as e:
            self._show_error(f"Form creation error: {str(e)}")

    def _build_parameter_form(self, msg, layout, prefix=""):
        """Recursively build parameter form from message structure"""
        for field_name, field_type in msg.get_fields_and_field_types().items():
            field = getattr(msg, field_name)
            full_name = f"{prefix}{field_name}" if prefix else field_name

            if hasattr(field, "__slots__"):  # Nested message
                self._add_nested_field(full_name, field, layout)
            elif isinstance(field, list):  # Array type
                self._add_array_field(full_name, field, layout)
            else:  # Primitive type
                self._add_primitive_field(full_name, layout)

    def _add_nested_field(self, name, field, layout):
        """Add form group for nested message field"""
        group = QGroupBox(name)
        sub_layout = QFormLayout()
        self._build_parameter_form(field, sub_layout, f"{name}.")
        group.setLayout(sub_layout)
        layout.addRow(group)

    def _add_array_field(self, name, field, layout):
        """Add form elements for array field"""
        edit = QLineEdit()
        edit.setObjectName(name)
        layout.addRow(name, edit)
        self.input_fields[name] = edit

    def _add_primitive_field(self, name, layout):
        """Add single-line input for primitive field"""
        edit = QLineEdit()
        edit.setObjectName(name)
        layout.addRow(name, edit)
        self.input_fields[name] = edit

    def _send_goal(self):
        """Handle goal submission"""
        try:
            self._update_goal_message()
            self.ros_node.create_action_client(*self.selected_action)
            future = self.ros_node.send_goal(self.action_goal_msg, self._handle_feedback)
            
            if future:
                future.add_done_callback(self._handle_goal_response)
            else:
                self._show_error("Action server unavailable")
        except Exception as e:
            self._show_error(f"Goal submission failed: {str(e)}")

    def _update_goal_message(self):
        """Update goal message with user input values"""
        for field_path, input_widget in self.input_fields.items():
            value = self._parse_input(input_widget.text())
            if value is not None and value != "":
                self._set_message_value(self.action_goal_msg, field_path, value)

    def _parse_input(self, value_str):
        """Parse user input to appropriate Python type"""
        try:
            if "[" in value_str and "]" in value_str:
                return [self._parse_single_value(v) for v in value_str.strip("[]").split(",")]
            return self._parse_single_value(value_str)
        except ValueError:
            return value_str

    def _parse_single_value(self, value_str):
        """Parse single value from string input"""
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"
        
        # Check for integers with optional sign
        sign_removed_int = value_str.lstrip('+-')
        num_signs_int = len(value_str) - len(sign_removed_int)
        if num_signs_int <= 1 and sign_removed_int.isdigit() and sign_removed_int:
            return int(value_str)
        
        # Check for floats with optional sign
        sign_removed_float = value_str.lstrip('+-')
        num_signs_float = len(value_str) - len(sign_removed_float)
        if num_signs_float <= 1 and sign_removed_float:
            if sign_removed_float.replace('.', '', 1).isdigit() and sign_removed_float.count('.') <= 1:
                return float(value_str)
        
        return value_str

    def _set_message_value(self, msg, field_path, value):
        """Recursively set message field value"""
        parts = field_path.split(".")
        current = msg
        for part in parts[:-1]:
            current = getattr(current, part)
        setattr(current, parts[-1], value)

    def _handle_feedback(self, feedback_msg):
        """Handle incoming feedback messages"""
        self.feedback_display.append(f"Feedback: {feedback_msg.feedback}")

    def _handle_goal_response(self, future):
        """Handle server response to goal submission"""
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self._show_error("Goal rejected by server")
                return

            self.feedback_display.append("Goal accepted!")
            goal_handle.get_result_async().add_done_callback(self._handle_result)
        except Exception as e:
            self._show_error(f"Goal handling error: {str(e)}")

    def _handle_result(self, future):
        """Handle final result from action server"""
        try:
            result = future.result().result
            self.result_display.append(f"Result: {result}")
        except Exception as e:
            self._show_error(f"Result error: {str(e)}")

    def _show_error(self, message):
        """Display error message consistently"""
        self.feedback_display.append(f"Error: {message}")


def main():
    rclpy.init()
    app = QApplication(sys.argv)
    ros_node = ROS2ActionNode()
    gui = ActionGUI(ros_node)
    gui.show()

    # ROS2 spin integration
    timer = QTimer()
    timer.timeout.connect(lambda: rclpy.spin_once(ros_node, timeout_sec=0))
    timer.start(50)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()