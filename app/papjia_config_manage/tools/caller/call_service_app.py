import sys
import importlib
from rclpy.node import Node
import rclpy
from rosidl_runtime_py.utilities import get_service

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
    QLabel
)
from PyQt5.QtCore import QTimer


class ROS2ServiceNode(Node):
    def __init__(self):
        super().__init__("qt_service_client_node")
        self._service_client = None
        self._request_msg = None

    def discover_services(self):
        """Discover available ROS2 services with type information"""
        return [
            (name, types[0].replace('/', '.'))  # Remove leading slash from service name
            for name, types in self.get_service_names_and_types()
        ]

    def get_request_msg(self, service_type):
        """Initialize and return a new request message instance"""
        module_name, _, cls_name = service_type.rpartition(".")
        module = importlib.import_module(module_name)
        self._request_msg = getattr(module, f"{cls_name}").Request()
        return self._request_msg

    def create_service_client(self, service_name, service_type):
        """Initialize ServiceClient for specified service"""
        ServiceType = get_service(service_type.replace(".", "/"))
        self._service_client = self.create_client(ServiceType, service_name)
        
        # Wait for service to become available
        if not self._service_client.wait_for_service(timeout_sec=1.0):
            raise RuntimeError(f"Service {service_name} not available")

    def call_service(self, request_msg):
        """Call service with request message"""
        if self._service_client.service_is_ready():
            future = self._service_client.call_async(request_msg)
            return future
        return None


class ServiceGUI(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize main window UI components"""
        # self.setWindowTitle("ROS2 Service Client")
        # self.setGeometry(300, 300, 1200, 600)

        # main_widget = QWidget()
        # main_layout = QHBoxLayout(main_widget)
        main_layout = QHBoxLayout(self)  # 原为main_widget

        # Create three columns
        main_layout.addLayout(self._create_service_list_column())
        main_layout.addLayout(self._create_parameters_column())
        main_layout.addLayout(self._create_control_column())

        # self.setCentralWidget(main_widget)

    def _create_service_list_column(self):
        """Left column: Service list and refresh button"""
        column = QVBoxLayout()
        self.service_list = QListWidget()
        refresh_btn = QPushButton("Refresh Services")
        refresh_btn.clicked.connect(self.refresh_services)
        column.addWidget(refresh_btn)
        column.addWidget(self.service_list)
        return column

    def _create_parameters_column(self):
        """Middle column: Service parameters form"""
        column = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.form_group = QGroupBox("Service Parameters")
        self.form_group.setLayout(self.form_layout)
        column.addWidget(self.form_group)
        self.input_fields = {}
        return column

    def _create_control_column(self):
        """Right column: Service call controls and results"""
        column = QVBoxLayout()
        
        # Call Controls
        control_group = QGroupBox("Service Control")
        control_layout = QVBoxLayout()
        self.call_btn = QPushButton("Call Service")
        control_layout.addWidget(self.call_btn)
        control_group.setLayout(control_layout)
        column.addWidget(control_group)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)

        column.addWidget(self._create_labeled_display("Response:", self.result_display))
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
        self.service_list.currentItemChanged.connect(self._handle_service_selection)
        self.call_btn.clicked.connect(self._call_service)

    def refresh_services(self):
        """Refresh list of available services"""
        self.service_list.clear()
        for service_name, service_type in self.ros_node.discover_services():
            self.service_list.addItem(f"{service_name} ({service_type})")

    def _handle_service_selection(self, item):
        """Handle selection change in service list"""
        if item:
            service_full = item.text().split(" (")
            self.selected_service = (service_full[0], service_full[1][:-1])
            self._create_parameter_form(self.selected_service[1])

    def _create_parameter_form(self, service_type):
        """Create input form for selected service type"""
        # Clear existing form
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.input_fields.clear()

        try:
            self.service_request = self.ros_node.get_request_msg(service_type)
            self._build_parameter_form(self.service_request, self.form_layout)
        except Exception as e:
            self._show_error(f"Form creation error: {str(e)}")

    # 以下参数表单构建方法与Action版本相同，可根据需要调整
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

    def _call_service(self):
        """Handle service call submission"""
        try:
            self._update_request_message()
            self.ros_node.create_service_client(*self.selected_service)
            future = self.ros_node.call_service(self.service_request)
            
            if future:
                future.add_done_callback(self._handle_service_response)
            else:
                self._show_error("Service unavailable")
        except Exception as e:
            self._show_error(f"Service call failed: {str(e)}")

    def _update_request_message(self):
        """Update request message with user input values"""
        for field_path, input_widget in self.input_fields.items():
            value = self._parse_input(input_widget.text())
            if value is not None and value != "":
                self._set_message_value(self.service_request, field_path, value)

    # 以下数据解析方法与Action版本相同
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

    def _handle_service_response(self, future):
        """Handle service response"""
        try:
            response = future.result()
            self.result_display.append(f"Response: {response}")
        except Exception as e:
            self._show_error(f"Service response error: {str(e)}")

    def _show_error(self, message):
        """Display error message consistently"""
        self.result_display.append(f"Error: {message}")


def main():
    rclpy.init()
    app = QApplication(sys.argv)
    ros_node = ROS2ServiceNode()
    gui = ServiceGUI(ros_node)
    gui.show()

    # ROS2 spin integration
    timer = QTimer()
    timer.timeout.connect(lambda: rclpy.spin_once(ros_node, timeout_sec=0))
    timer.start(50)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
