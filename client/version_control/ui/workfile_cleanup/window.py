from functools import partial
import typing
from qtpy import QtCore, QtGui, QtWidgets

from ayon_core.style import load_stylesheet
from ayon_core.tools.common_models.projects import ProjectsModel
from ayon_core.tools.publisher.control_qt import QtPublisherController
from ayon_core.tools.utils.projects_widget import (
    ProjectSortFilterProxy,
    ProjectsQtModel,
)
from ayon_core.tools.utils.widgets import PlaceholderLineEdit, RefreshButton
from version_control.api.clean_workfiles import clean_workfiles_files
from version_control.ui.workfile_cleanup.controller import ProjectsController
import qtawesome

from version_control.ui.workfile_cleanup.worker import CleanUpWorker, CleanupSignals


class CleanWorkfilesConfirmation(QtWidgets.QDialog):
    def __init__(
        self, project, parent: typing.Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Cleanup Workfiles")
        self.setStyleSheet(load_stylesheet())
        self.project = project
        self.worker = None
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)

        signals = CleanupSignals()

        layout = QtWidgets.QGridLayout()
        message_box = QtWidgets.QLabel()
        message_box.setWordWrap(True)
        message_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        msg = (
            "<p><h1>IMPORTANT PLEASE READ<h1></p>"
            "<p>Deleting Old workfiles will remove older workfiles from your computer. "
            "This is reversable but, to recover the files you will need to do "
            "a force pull on the files that were removed.</p>"
            "<p>To confirm type the project name in the box below:</p>"
            f"<p><b>{self.project}</b></p>"
        )
        message_box.setText(msg)
        confirmation_line_edit = QtWidgets.QLineEdit()
        confirmation_line_edit.setPlaceholderText(self.project)
        confirmation_line_edit.textChanged.connect(
            self._on_confirmation_text_changed
        )
        confirm_button = QtWidgets.QPushButton("Confirm...")
        confirm_button.setEnabled(False)
        confirm_button.clicked.connect(self._on_accept_button_clicked)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        keep_label = QtWidgets.QLabel("# Workfiles to Keep")
        keep_spinbox = QtWidgets.QSpinBox()
        keep_spinbox.setValue(3)
        keep_spinbox.setMinimum(1)

        progress_label = QtWidgets.QLabel()
        progress_bar = QtWidgets.QProgressBar()

        signals.started.connect(self._on_progress_started)
        signals.updated.connect(progress_bar.setValue)
        signals.finished.connect(self._on_worker_finished)
        

        layout.addWidget(message_box, 0, 0, 1, 2)
        layout.addWidget(confirmation_line_edit, 1, 0, 1, 2)
        layout.addWidget(keep_label, 2, 0, 1, 1)
        layout.addWidget(keep_spinbox, 2, 1, 1, 1)
        layout.addWidget(confirm_button, 3, 0, 1, 1)
        layout.addWidget(cancel_button, 3, 1, 1, 1)
        layout.addWidget(progress_label, 4, 0, 1, 1)
        layout.addWidget(progress_bar, 5, 0, 1, 2)
        self.setLayout(layout)

        self.confirmation_line_edit = confirmation_line_edit
        self.confirm_button = confirm_button
        self.keep_spinbox = keep_spinbox
        self.progress_label = progress_label
        self.progress_bar = progress_bar
        self.signals = signals

    def _on_progress_started(self, title: str, maximum: int):
        self.progress_label.setText(title)
        self.progress_bar.setMaximum(maximum)

    def _on_accept_button_clicked(self):
        self.setEnabled(False)
        keep_count = self.keep_spinbox.value()
        self.worker = CleanUpWorker(
            clean_workfiles_files, self.project, keep_count, self.signals
        )
        self.worker.start()
        self.worker.finished.connect(partial(self.setEnabled, True))

    def _on_worker_finished(self, unsubmitted_files, file_count, file_size):
        summary = SummaryDialog(unsubmitted_files, file_count, file_size)
        summary.exec()
        self.accept()

    def _on_confirmation_text_changed(self, text):
        if text != self.project:
            self.confirm_button.setEnabled(False)
            return
        self.confirm_button.setEnabled(True)




class ProjectSelectionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: typing.Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.setStyleSheet(load_stylesheet())
        self.setWindowTitle("Select Project")
        self.selected_project = None

        refresh_button = RefreshButton()
        accept_button = QtWidgets.QPushButton("Accept")

        projects_model = ProjectsQtModel(ProjectsController())
        projects_proxy = ProjectSortFilterProxy()
        projects_proxy.setSourceModel(projects_model)
        projects_proxy.setFilterKeyColumn(0)

        layout = QtWidgets.QVBoxLayout()

        projects_view = QtWidgets.QListView()
        projects_view.setObjectName("ChooseProjectView")
        projects_view.setModel(projects_proxy)

        projects_view.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers  # pyright: ignore[]
        )

        txt_filter = PlaceholderLineEdit()
        txt_filter.setPlaceholderText("Quick fliter projects..")
        txt_filter.setClearButtonEnabled(True)
        txt_filter.addAction(
            qtawesome.icon("fa.filter", color="gray"),
            QtWidgets.QLineEdit.LeadingPosition,  # pyright: ignore[]
        )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(refresh_button)
        layout.addWidget(txt_filter)
        layout.addWidget(projects_view)
        layout.addWidget(accept_button)

        refresh_button.clicked.connect(projects_model.refresh)
        txt_filter.textChanged.connect(self._on_text_changed)

        accept_button.clicked.connect(self._on_accept)

        self._projects_view = projects_view
        self._projects_model = projects_model
        self._projects_proxy = projects_proxy
        self._txt_filter = txt_filter

        self.setLayout(layout)
        self._projects_model.refresh()

    def _on_text_changed(self):
        self._projects_proxy.setFilterRegularExpression(
            self._txt_filter.text()
        )

    def _on_accept(self):
        indexes = self._projects_view.selectedIndexes()
        self.selected_project = indexes[0].data(QtGui.Qt.DisplayRole)
        self.accept()


class SummaryDialog(QtWidgets.QDialog):
    def __init__(
        self, unsubmited_files, files_removed, storage_cleared
    ) -> None:
        super().__init__()
        self.setWindowTitle("Summary")
        self.setStyleSheet(load_stylesheet())

        layout = QtWidgets.QVBoxLayout()
        unsubmitted_count_label = QtWidgets.QLabel(
            f"Unsubmitted Files: {len(unsubmited_files)}"
        )

        model = QtGui.QStandardItemModel()
        for unsubmited_file in unsubmited_files:
            item = QtGui.QStandardItem()
            item.setData(unsubmited_file.as_posix(), QtGui.Qt.DisplayRole)
            model.appendRow(item)
        unsubmited_files_view = QtWidgets.QListView()
        unsubmited_files_view.setModel(model)

        files_removed_label = QtWidgets.QLabel(
            f"Files Removed {files_removed}"
        )
        storage_cleared_label = QtWidgets.QLabel(
            f"Drive Space Freed {self.bytes_to_human_readable(storage_cleared)}"
        )
        done_button = QtWidgets.QPushButton("Done")
        done_button.clicked.connect(self.accept)

        layout.addWidget(unsubmitted_count_label)
        layout.addWidget(unsubmited_files_view)
        layout.addWidget(files_removed_label)
        layout.addWidget(storage_cleared_label)
        layout.addWidget(done_button)

        self.setLayout(layout)

    @staticmethod
    def bytes_to_human_readable(num, suffix="B"):
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"
