import sys

from qtpy import QtWidgets 
import platform

from ayon_core import style
from ayon_core.tools.utils.lib import iter_model_rows, qt_app_context
from ayon_core.lib import ayon_info
from ayon_core.tools.utils import get_ayon_qt_app,
from ayon_core.tools.utils.projects_widget import ProjectsCombobox
from ayon_core.tools.common_models import ProjectsModel
from ayon_core.tools.launcher.control import BaseLauncherController
from version_control.addon import VersionControlAddon
from ayon_core.pipeline import install_host

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

def main():
    host = VersionControlAddon()
    install_host(host)

    app_instance = get_ayon_qt_app()

    if not ayon_info.is_running_from_build() and platform.system().lower() == "windows":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            u"traypublisher"
        )

    window = ProjectViewer()
    window.show()
    app_instance.exec_()

