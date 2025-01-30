import sys

from qtpy import QtWidgets 

from ayon_core import style
from ayon_core.tools.utils.lib import iter_model_rows, qt_app_context
from ayon_core.tools.utils.projects_widget import ProjectsCombobox
from ayon_core.tools.common_models import ProjectsModel
from ayon_core.tools.launcher.control import BaseLauncherController

module = sys.modules[__name__]
module.window = None

class ProjectViewer(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version Control Project Viewer")
        self.setStyleSheet(style.load_stylesheet())
        layout = QtWidgets.QVBoxLayout()

        self.choose_project_label = QtWidgets.QLabel("Select a Project")
        self.choose_project_label.setObjectName("ChooseProjectLabel")

        self.controller = BaseLauncherController()
        self.project_selector = ProjectsCombobox(self.controller, None)
        self.project_selector.refresh()

        self.confirm_button = QtWidgets.QPushButton("Confirm")

        layout.addWidget(self.choose_project_label)
        layout.addWidget(self.project_selector)
        layout.addWidget(self.confirm_button)
        self.setLayout(layout)
        self.confirm_button.clicked.connect(self.close)

    def closeEvent(self, e) -> None:
        print(self.project_selector.get_selected_project_name())
        return super().closeEvent(e)


def show(parent=None):
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
        window = ProjectViewer(parent)
        window.show()
        module.window = window

        # Pull window to the front.
        module.window.raise_()
        module.window.activateWindow()
    
