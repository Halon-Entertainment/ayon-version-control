from qtpy import QtWidgets, QtCore, QtGui
import typing
import os

from ayon_core.tools.utils.lib import get_ayon_qt_app

class UserSubmitWindow(QtWidgets.QDialog):
    def __init__(self, work_path: str, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._work_path = work_path

        self.setWindowTitle("Perforce Submit Window")
        layout = QtWidgets.QVBoxLayout()

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabels(["File", "Confirm"])
        self.expand_folder(self.tree_widget, self._work_path)
        layout.addWidget(self.tree_widget)

        label = QtWidgets.QLabel("Perforce Comment:")
        self.comment_edit = QtWidgets.QLineEdit()
        layout.addWidget(label)
        layout.addWidget(self.comment_edit)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def expand_folder(self, tree_widget: QtWidgets.QTreeWidget, path: str) -> None:
        for item in QtCore.QDir(path).entryList():
            full_path = QtCore.QDir.cleanPath(QtCore.QDir.fromNativeSeparators(os.path.join(path, item)))
            if QtCore.QFileInfo(full_path).isDir():
                parent_item = tree_widget.addTopLevelItem(QtWidgets.QTreeWidgetItem([f"{item}/"]))
                self.expand_folder(parent_item, full_path)
            else:
                item_text = f"{item}?"
                item_checkbox = QtWidgets.QCheckBox()
                item_widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(item_widget)
                layout.addWidget(QtWidgets.QLabel(item_text))
                layout.addWidget(item_checkbox)
                layout.setContentsMargins(0, 0, 0, 0)
                tree_item = QtWidgets.QTreeWidgetItem([item_text])
                tree_item.setCheckState(0, QtCore.Qt.Checked)
                item_layout = QtWidgets.QVBoxLayout()
                item_layout.addWidget(QtWidgets.QLabel("Status"))
                item_widget.setLayout(item_layout)
                self.tree_widget.addTopLevelItem(tree_item).setCheckState(0, QtCore.Qt.Checked)

    @property
    def selected_files(self) -> dict:
        selected_files = {}
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.type() != 1:  # Check for checkbox items
                continue
            child_count = item.childCount()
            files = []
            for j in range(child_count):
                child_item = item.child(j)
                if child_item.checkState(0) == QtCore.Qt.Checked:
                    files.append(child_item.text(0).split('?')[0])
            selected_files[item.text(0).strip('/')] = files
        return selected_files


def main(manager):
    app_instance = get_ayon_qt_app()
    window = UserSubmitWindow(manager)
    if window.exec():
        print("Selected Files:", window.selected_files)
        print("Perforce Comment:", window.comment_edit.text())
    else:
        print("Operation Cancelled")

