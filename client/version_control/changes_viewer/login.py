import sys
from qtpy import QtWidgets, QtCore
from ayon_core import style

module = sys.modules[__name__]
module.window = None


class LoginWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.setWindowTitle("Login To Perforce")
        self.setObjectName("LoginToPerforce")

        self.setStyleSheet(style.load_stylesheet())

        layout = QtWidgets.QVBoxLayout(self)

        self.username_label = QtWidgets.QLabel("Username:")
        self.username_input = QtWidgets.QLineEdit(self)

        self.password_label = QtWidgets.QLabel("Password:")
        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)

        self.submit_button = QtWidgets.QPushButton("Submit")
        self.submit_button.clicked.connect(self.accept)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit_button)

    def get_credentials(self):
        """Return the username and password entered by the user."""
        return self.username_input.text(), self.password_input.text()