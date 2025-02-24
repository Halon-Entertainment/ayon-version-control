import traceback
from time import sleep

from ayon_core.lib.log import Logger
from ayon_core.tools.utils import TreeView
from ayon_core.tools.utils.delegates import PrettyTimeDelegate
from qtpy import QtCore, QtWidgets
from typing_extensions import override

from .model import CHANGE_ROLE, ChangesModel, CustomSortProxyModel

log = Logger.get_logger(__name__)


class ChangesDetailWidget(QtWidgets.QWidget):
    """Table printing list of changes from Perforce"""

    sync_triggered = QtCore.Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)

        model = ChangesModel(controller=controller, parent=self)
        proxy = CustomSortProxyModel()
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)  # pyright: ignore[]

        changes_view = TreeView(self)
        changes_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )  # pyright: ignore[]
        changes_view.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )  # pyright: ignore[]
        changes_view.setSortingEnabled(True)
        changes_view.setAlternatingRowColors(True)
        changes_view.setModel(proxy)
        changes_view.setIndentation(0)

        changes_view.setColumnWidth(0, 70)
        changes_view.setColumnWidth(1, 430)
        changes_view.setColumnWidth(2, 100)
        changes_view.setColumnWidth(3, 120)

        time_delegate = PrettyTimeDelegate()
        changes_view.setItemDelegateForColumn(3, time_delegate)

        message_label_widget = QtWidgets.QLabel(self)

        sync_btn = QtWidgets.QPushButton("Sync to", self)

        self._block_changes = False
        self._editable = False
        self._item_id = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(changes_view, 1)
        layout.addWidget(
            message_label_widget,
            0,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,  # pyright: ignore[]
        )
        layout.addWidget(sync_btn, 0, QtCore.Qt.AlignRight)  # pyright: ignore[]

        sync_btn.clicked.connect(self._on_sync_clicked)

        self._model = model
        self._controller = controller
        self._changes_view = changes_view
        self.sync_btn = sync_btn
        self._thread = None
        self._time_delegate = time_delegate
        self._message_label_widget = message_label_widget

    def reset(self):
        self._model.refresh()

    def _on_sync_clicked(self):
        selection_model = self._changes_view.selectionModel()
        if selection_model is None:
            raise TypeError("selection_model cannot be None")

        current_index = selection_model.currentIndex()
        if not current_index.isValid():
            return

        change_id = current_index.data(CHANGE_ROLE)

        self._message_label_widget.setText(f"Syncing to {change_id}")

        self.sync_btn.setEnabled(False)
        progress_thread = ProgressThread(self._message_label_widget)
        thread = SyncThread(self._controller, change_id)
        thread.finished.connect(lambda: self._on_thread_finished(change_id))
        thread.finished.connect(progress_thread.terminate)
        thread.failed.connect(progress_thread.terminate)
        thread.failed.connect(self._on_thread_failed)
        thread.started.connect(progress_thread.start)
        thread.start()

        self._progress_tread = progress_thread
        self._thread = thread

    def _on_thread_finished(self, change_id):
        self._message_label_widget.setText(
            f"Synced to '{change_id}'. Please close Viewer to continue."
        )
        self.sync_btn.setEnabled(True)

    def _on_thread_failed(self, error: Exception, traceback: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred: {error}")
        log.critical(traceback)


class ProgressThread(QtCore.QThread):
    def __init__(self, text_widget):
        super().__init__()
        self._text_widget = text_widget
        self._original_text = text_widget.text()
        self._is_terminated = False

    def run(self):
        dot_index = 0
        while not self._is_terminated:
            self._text_widget.setText(self._original_text + "." * dot_index)

            dot_index += 1
            if dot_index > 3:
                dot_index = 0

            sleep(1)

    @override
    def terminate(self) -> None:
        self._is_terminated = True
        return super().terminate()


class SyncThread(QtCore.QThread):
    failed = QtCore.Signal(object, str)

    def __init__(self, controller, change_id):
        super().__init__()
        self._controller = controller
        self._change_id = change_id

    def run(self):
        try:
            self._controller.sync_to(self._change_id)
        except Exception as err:
            self.failed.emit(err, traceback.format_exc())
