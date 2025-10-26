import sys
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QComboBox,
    QHBoxLayout, QMessageBox, QFormLayout, QGroupBox, QListWidget, QGridLayout
)


# XML解析类
class XmlParser:
    @staticmethod
    def parse_action_file(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()

        actions = []

        # Parse each action element in theXML file
        for action_elem in root.findall('action'):
            action_name = action_elem.get('name')
            class_name = action_elem.get('class')

            # Parse inputs
            inputs = []
            for input_elem in action_elem.findall('./inputs/port'):
                input_name = input_elem.get('name')
                input_type = input_elem.get('type')
                inputs.append((input_name, input_type))

            # Parse outputs
            outputs = []
            for output_elem in action_elem.findall('./outputs/port'):
                output_name = output_elem.get('name')
                output_type = output_elem.get('type')
                outputs.append((output_name, output_type))

            actions.append({
                'name': action_name,
                'class_name': class_name,
                'inputs': inputs,
                'outputs': outputs
            })

        return actions


# XML导出类
class XmlExporter:
    @staticmethod
    def export_to_xml(tree_structure, file_path):
        root = ET.Element("root")
        root.set("BTCPP_format", "4")

        # Create BehaviorTree for each BehaviorTree
        for bt in tree_structure:
            behavior_tree = ET.SubElement(root, "BehaviorTree")
            behavior_tree.set("ID", bt["name"])

            for sequence in bt["sequences"]:
                sequence_elem = ET.SubElement(behavior_tree, "Sequence")
                sequence_elem.set("name", sequence["name"])

                for action in sequence["actions"]:
                    action_elem = ET.SubElement(sequence_elem, action["name"])
                    for input_name, input_value in action["inputs"].items():
                        action_elem.set(input_name, input_value)
                    for output_name, output_value in action["outputs"].items():
                        action_elem.set(output_name, output_value)

        # 生成的XML树并格式化
        tree = ET.ElementTree(root)
        xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

        # 将格式化后的 XML 写入文件
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(pretty_xml_str)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.actions = []  # Store action definitions
        self.behavior_trees = []  # Store BehaviorTrees
        self.current_bt = None  # Currently selected BehaviorTree
        self.current_sequence = None  # Currently selected sequence
        self.action_inputs = {}  # Store dynamically created inputs from actions
        self.action_outputs = {}  # Store dynamically created outputs from actions

    def initUI(self):
        self.setWindowTitle('Behavior Tree Editor')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Reduce spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Set margins

        # Load actions button
        self.load_btn = QPushButton('Load Actions', self)
        self.load_btn.clicked.connect(self.loadActions)
        layout.addWidget(self.load_btn)

        # Add BehaviorTree section
        bt_group = QHBoxLayout()
        self.bt_name_edit = QLineEdit()
        self.bt_name_edit.setPlaceholderText("Enter BehaviorTree name")
        self.create_bt_btn = QPushButton('Add BehaviorTree', self)
        self.create_bt_btn.clicked.connect(self.createBehaviorTree)
        bt_group.addWidget(self.bt_name_edit)
        bt_group.addWidget(self.create_bt_btn)
        layout.addLayout(bt_group)

        # BehaviorTree selection
        self.bt_label = QLabel('Select BehaviorTree:')
        self.bt_combobox = QComboBox(self)
        self.bt_combobox.currentIndexChanged.connect(self.onBehaviorTreeSelected)
        layout.addWidget(self.bt_label)
        layout.addWidget(self.bt_combobox)

        # Add Sequence section
        sequence_group = QHBoxLayout()
        self.sequence_name_edit = QLineEdit()
        self.sequence_name_edit.setPlaceholderText("Enter Sequence name")
        self.create_sequence_btn = QPushButton('Add Sequence', self)
        self.create_sequence_btn.clicked.connect(self.createSequence)
        sequence_group.addWidget(self.sequence_name_edit)
        sequence_group.addWidget(self.create_sequence_btn)
        layout.addLayout(sequence_group)

        # Sequence selection
        self.sequence_label = QLabel('Select Sequence:')
        self.sequence_combobox = QComboBox(self)
        self.sequence_combobox.currentIndexChanged.connect(self.onSequenceSelected)
        layout.addWidget(self.sequence_label)
        layout.addWidget(self.sequence_combobox)

        # Action selection
        self.action_label = QLabel('Select Action:')
        self.action_combobox = QComboBox(self)
        self.action_combobox.currentIndexChanged.connect(self.onActionSelected)
        layout.addWidget(self.action_label)
        layout.addWidget(self.action_combobox)

        # Group for inputs and outputs
        self.input_group = QGroupBox("Action Inputs")
        self.input_layout = QFormLayout()
        self.input_group.setLayout(self.input_layout)
        layout.addWidget(self.input_group)

        self.output_group = QGroupBox("Action Outputs")
        self.output_layout = QFormLayout()
        self.output_group.setLayout(self.output_layout)
        layout.addWidget(self.output_group)

        # Add action to sequence button
        self.add_action_btn = QPushButton('Add Action to Sequence', self)
        self.add_action_btn.clicked.connect(self.addActionToSequence)
        layout.addWidget(self.add_action_btn)

        # Export button
        self.export_btn = QPushButton('Export Behavior Tree to XML', self)
        self.export_btn.clicked.connect(self.exportToXml)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)

    def loadActions(self):
        # File dialog to select a folder containing action files
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Action Files")
        if folder_path:
            self.actions = []  # Reset actions list

            # Loop through files in the folder
            for filename in os.listdir(folder_path):
                if filename.endswith(".xml"):
                    file_path = os.path.join(folder_path, filename)
                    actions = XmlParser.parse_action_file(file_path)
                    self.actions.extend(actions)

            # Update action list in ComboBox
            self.action_combobox.clear()
            for action in self.actions:
                self.action_combobox.addItem(f"{action['name']}")

    def createBehaviorTree(self):
        bt_name = self.bt_name_edit.text().strip()
        if not bt_name:
            QMessageBox.critical(self, "Error", "BehaviorTree name cannot be empty!")
            return

        # Check if the name already exists
        if any(bt["name"] == bt_name for bt in self.behavior_trees):
            QMessageBox.critical(self, "Error", f"BehaviorTree '{bt_name}' already exists.")
            return

        self.behavior_trees.append({
            "name": bt_name,
            "sequences": []
        })
        self.bt_combobox.addItem(bt_name)
        self.bt_combobox.setCurrentText(bt_name)  # Set the newly added BehaviorTree as selected
        QMessageBox.information(self, "Success", f"BehaviorTree '{bt_name}' added.")

    def onBehaviorTreeSelected(self):
        # Update sequences when a BehaviorTree is selected
        self.current_bt = self.bt_combobox.currentText()
        self.sequence_combobox.clear()
        if self.current_bt:
            bt = next((bt for bt in self.behavior_trees if bt["name"] == self.current_bt), None)
            if bt:
                for sequence in bt["sequences"]:
                    self.sequence_combobox.addItem(sequence["name"])

    def createSequence(self):
        if not self.current_bt:
            QMessageBox.critical(self, "Error", "Please select a BehaviorTree first.")
            return

        sequence_name = self.sequence_name_edit.text().strip()
        if not sequence_name:
            QMessageBox.critical(self, "Error", "Sequence name cannot be empty!")
            return

        # Check if the name already exists in the current BehaviorTree
        bt = next((bt for bt in self.behavior_trees if bt["name"] == self.current_bt), None)
        if bt:
            if any(seq["name"] == sequence_name for seq in bt["sequences"]):
                QMessageBox.critical(self, "Error", f"Sequence '{sequence_name}' already exists in this BehaviorTree.")
                return

            bt["sequences"].append({
                "name": sequence_name,
                "actions": []
            })
            self.sequence_combobox.addItem(sequence_name)
            self.sequence_combobox.setCurrentText(sequence_name)  # Set the newly added Sequence as selected
            QMessageBox.information(self, "Success", f"Sequence '{sequence_name}' added.")

    def onSequenceSelected(self):
        # Update actions when a sequence is selected
        self.current_sequence = self.sequence_combobox.currentText()

    def onActionSelected(self):
        # Clear previous input and output fields
        for i in reversed(range(self.input_layout.count())):
            widget = self.input_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        for i in reversed(range(self.output_layout.count())):
            widget = self.output_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Get selected action
        selected_action = self.action_combobox.currentText().split(' ')[0]  # Get the action name

        # Get action details
        action = next((action for action in self.actions if action['name'] == selected_action), None)
        if action:
            # Create input fields for inputs
            self.action_inputs = {}  # Reset inputs dictionary
            for input_name, input_type in action['inputs']:
                input_field = QLineEdit(self)
                self.action_inputs[input_name] = input_field
                self.input_layout.addRow(f"{input_name} ({input_type})", input_field)

            # Create input fields for outputs (editable)
            self.action_outputs = {}  # Reset outputs dictionary
            for output_name, output_type in action['outputs']:
                output_field = QLineEdit(self)
                self.action_outputs[output_name] = output_field
                self.output_layout.addRow(f"{output_name} ({output_type})", output_field)

    def addActionToSequence(self):
        # Add selected action to the current sequence
        if not self.current_bt or not self.current_sequence:
            QMessageBox.critical(self, "Error", "Please select a BehaviorTree and Sequence first.")
            return

        selected_action = self.action_combobox.currentText().split(' ')[0]  # Get the action name

        action = next((action for action in self.actions if action['name'] == selected_action), None)

        if action:
            # Get inputs and outputs entered by the user
            inputs = {}
            for input_name, input_field in self.action_inputs.items():
                inputs[input_name] = input_field.text()

            outputs = {}
            for output_name, output_field in self.action_outputs.items():
                outputs[output_name] = output_field.text()

            # Add to current sequence
            bt = next((bt for bt in self.behavior_trees if bt["name"] == self.current_bt), None)
            if bt:
                sequence = next((seq for seq in bt["sequences"] if seq["name"] == self.current_sequence), None)
                if sequence:
                    sequence["actions"].append({
                        "name": action["name"],
                        "inputs": inputs,
                        "outputs": outputs
                    })
                    QMessageBox.information(self, "Success", f"Added action {action['name']} to sequence {self.current_sequence}.")
        else:
            QMessageBox.critical(self, "Error", f"Action {selected_action} not found.")

    def exportToXml(self):
        if not self.behavior_trees:
            QMessageBox.critical(self, "Error", "No behavior tree to export.")
            return

        # Open file dialog to choose export location
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Behavior Tree", "", "XML Files (*.xml)")
        if file_path:
            try:
                XmlExporter.export_to_xml(self.behavior_trees, file_path)
                QMessageBox.information(self, "Success", f"Behavior Tree exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while exporting: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())