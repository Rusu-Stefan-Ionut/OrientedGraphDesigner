from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit

class EdgeValueDialog(QDialog):
    def __init__ (self, current_flow, max_flow, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Edge Value")

        layout = QVBoxLayout()

        self.flow_input = QLineEdit(str(current_flow))
        self.max_flow = QLineEdit(str(max_flow))

        flow_layout = QHBoxLayout()
        flow_layout.addWidget(QLabel("Current Flow:"))
        flow_layout.addWidget(self.flow_input)

        max_flow_layout = QHBoxLayout()
        max_flow_layout.addWidget(QLabel("Max Flow:"))
        max_flow_layout.addWidget(self.max_flow)

        layout.addLayout(flow_layout)
        layout.addLayout(max_flow_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def getValues(self):
        return self.flow_input.text(), self.max_flow.text()

