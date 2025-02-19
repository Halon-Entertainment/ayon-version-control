import typing

from ayon_core.lib.log import Logger
from ayon_core.tools.utils.lib import get_ayon_qt_app
from qtpy import QtGui, QtWidgets
from typing_extensions import override

from version_control.ui.user_submit_window.control import UserSubmitController
from version_control.ui.user_submit_window.delegates import (
    PerforceWorkfilesDelegate,
)
from version_control.ui.user_submit_window.models import (
    QtPerforceFileInfoModel,
)

log = Logger.get_logger(__name__)


class UserSubmitWindow(QtWidgets.QDialog):
    def __init__(
        self, work_path: str, parent: typing.Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent=parent)

        self.setWindowTitle("Perforce Submit")
        layout = QtWidgets.QVBoxLayout()

        list_view = QtWidgets.QListView()
        model = QtPerforceFileInfoModel()
        list_view.setModel(model)
        list_view.setItemDelegate(PerforceWorkfilesDelegate())
        layout.addWidget(list_view)

        label = QtWidgets.QLabel("Perforce Comment:")
        comment_edit = QtWidgets.QTextEdit()
        comment_edit.setPlaceholderText("Add comments for Perforce...")

        layout.addWidget(label)
        layout.addWidget(comment_edit)

        ok_button = QtWidgets.QPushButton("Submit")
        cancel_button = QtWidgets.QPushButton("Cancel")

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(
            ok_button, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole
        )

        button_box.addButton(
            cancel_button, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole
        )

        button_box.accepted.connect(self._on_perforce_submit)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._model = model
        self._controller = UserSubmitController()
        self._work_path = work_path
        self._list_view = list_view
        self._comment_edit = comment_edit

        self.setLayout(layout)

    def _on_perforce_submit(self) -> None:
        file_paths = []
        for index in range(self._model.rowCount()):
            item = self._model.item(index)
            if item:
                file_path = item.data(QtPerforceFileInfoModel.FILE_PATH_ROLE)
                file_paths.append(file_path)

        comment_text = self._comment_edit.toPlainText()
        result = self._controller.submit_workfiles(file_paths, comment_text)

        if result:
            QtWidgets.QMessageBox.information(self, "Success", f"{len(file_paths)} files submitted successfully.")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to submit files.")

        self.close()


    @override
    def showEvent(self, a0: typing.Optional[QtGui.QShowEvent]) -> None:
        perforce_workfiles = self._controller.get_perforce_files()
        unsubmitted_workfiles = list(
            filter(lambda x: not x.exists, perforce_workfiles)
        )
        self._model.add_models(unsubmitted_workfiles)


def main(scene_path):
    app_instance = get_ayon_qt_app()
    window = UserSubmitWindow(scene_path)
    window.exec()  # TODO: This locked the maya ui, I need to find a better way to do this
