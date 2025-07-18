from ast import Raise
import sys

from qtpy import QtWidgets, QtCore

from ayon_core import style
from ayon_core.tools.utils.lib import (
    iter_model_rows,
    qt_app_context
)
from .control import ChangesViewerController

from .widgets import ChangesDetailWidget

from ayon_applications.exceptions import ApplicationLaunchFailed

module = sys.modules[__name__]
module.window = None


class ChangesWindows(QtWidgets.QDialog):
    def __init__(self, controller=None, parent=None, launch_data=None, host_name=None):
        super(ChangesWindows, self).__init__(parent=parent)
        self.setWindowTitle("Changes Viewer")
        self.setObjectName("ChangesViewer")
        self.launch_canceled = False
        if not parent:
            self.setWindowFlags(
                self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
            )

        self.resize(780, 430)
        self._host_name = host_name

        if controller is None:
            controller = ChangesViewerController(launch_data=launch_data, host=host_name)

        self._first_show = True

        details_widget = ChangesDetailWidget(controller, self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(details_widget, stretch=1)

        self._controller = controller
        self._details_widget = details_widget
        self._details_widget.sync_canceled.connect(self._on_close)
        self._details_widget.sync_continue.connect(self.close)

    def _on_close(self):
        self.close()
        self.launch_canceled = True

    def showEvent(self, *args, **kwargs):
        super(ChangesWindows, self).showEvent(*args, **kwargs)
        if self._first_show:
            self._first_show = False
            self.setStyleSheet(style.load_stylesheet())
            self._details_widget.reset()


def show(root=None, debug=False, parent=None):
    """Display Change Viewer GUI

    Arguments:
        debug (bool, optional): Run in debug-mode,
            defaults to False
        parent (QtCore.QObject, optional): When provided parent the interface
            to this QObject.

    """

    try:
        module.window.close()
        del module.window
    except (RuntimeError, AttributeError):
        pass

    with qt_app_context():
        window = ChangesWindows(parent)
        window.show()

        module.window = window

        # Pull window to the front.
        module.window.raise_()
        module.window.activateWindow()
