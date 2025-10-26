# main_app.py
import sys
import rclpy
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import QTimer
from call_action_app import ActionGUI, ROS2ActionNode
from call_service_app import ServiceGUI, ROS2ServiceNode

class CombinedClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ros_nodes()
        self._init_ui()
        self._setup_spin_timer()

    def _init_ros_nodes(self):
        """Initialize both action and service nodes"""
        self.action_node = ROS2ActionNode()
        self.service_node = ROS2ServiceNode()

    def _init_ui(self):
        """Initialize main window UI with tabs"""
        self.setWindowTitle("ROS2 Client Tool")
        self.setGeometry(100, 100, 1200, 600)
        
        tab_widget = QTabWidget()
        tab_widget.addTab(ActionGUI(self.action_node), "Action Client")
        tab_widget.addTab(ServiceGUI(self.service_node), "Service Client")
        
        self.setCentralWidget(tab_widget)

    def _setup_spin_timer(self):
        """Setup timer for ROS2 node spinning"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._spin_nodes)
        self.timer.start(50)

    def _spin_nodes(self):
        """Handle ROS2 node spinning for both nodes"""
        rclpy.spin_once(self.action_node, timeout_sec=0)
        rclpy.spin_once(self.service_node, timeout_sec=0)

def main():
    rclpy.init()
    app = QApplication(sys.argv)
    window = CombinedClient()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
