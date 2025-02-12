from qtpy import QtWidgets, QtCore, QtGui
import typing

from ayon_core.tools.utils.lib import get_ayon_qt_app

class UserSubmitWindow(QtWidgets.QDialog):
    def __init__(self, work_path: str, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._work_path = work_path

        self.setWindowTitle("Perforce Submit")
        layout = QtWidgets.QVBoxLayout()

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)

        label = QtWidgets.QLabel("Perforce Comment:")
        self.comment_edit = QtWidgets.QTextEdit()
        layout.addWidget(label)
        layout.addWidget(self.comment_edit)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_files(self, path: str) -> typing.List[str]:
        pass


def main(scene_path):
    app_instance = get_ayon_qt_app()
    window = UserSubmitWindow(scene_path)
    if window.exec():
        print("Perforce Comment:", window.comment_edit.text())
    else:
        print("Operation Cancelled")
