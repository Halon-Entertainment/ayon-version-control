import platform
import sys

from ayon_core import style
from ayon_core.lib import ayon_info
from ayon_core.lib.log import Logger
from ayon_core.pipeline.context_tools import install_host
from ayon_core.tools.utils.lib import get_ayon_qt_app
from ayon_core.tools.utils.projects_widget import ProjectsQtModel
from qtpy import QtCore, QtWidgets

from ayon_core.tools.utils.widgets import RefreshButton
from version_control.api.pipeline import VersionControlHost

from .controller import PerforceProjectsController

log = Logger.get_logger(__name__)


class PerforceWorkspaceWizard(QtWidgets.QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug("Starting Workspace Wizard")

        self.setWindowTitle("Perforce Workspace Setup")
        self.setStyleSheet(style.load_stylesheet())

        # Add pages to the wizard
        self.addPage(self._create_introduction_page())
        self.addPage(self._project_selection_page())
        self.addPage(self._create_workspace_selection_page())

    def _create_introduction_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Introduction")

        label = QtWidgets.QLabel(
            "Welcome to the Perforce Workspace Setup Wizard. Please follow the steps to configure your workspace.",
            page,
        )

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(label)

        return page

    def _project_selection_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Project Selection")
        projects_model = ProjectsQtModel(PerforceProjectsController())
        projects_model.refresh()
        projects_view = QtWidgets.QListView()
        projects_view.setModel(projects_model)
        refresh_button = RefreshButton()

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(projects_view)
        layout.addWidget(projects_view)
        layout.addWidget(refresh_button)

        refresh_button.clicked.connect(projects_model.refresh)
        self.currentIdChanged.connect(self.on_project_selection_page_next)

        self._projects_view = projects_view
        self._projects_model = projects_model

        return page

    def on_project_selection_page_next(self, current_id):
        if current_id == 2:
            selected_index = self._projects_view.currentIndex()
            if selected_index.isValid():
                project_name = self._projects_view.model().data(
                    selected_index, role=QtCore.Qt.ItemDataRole.DisplayRole
                )
                log.info(f"{project_name}")
                self._project_name = project_name
            else:
                self.project = None
                log.warning("No project selected")

    def _create_workspace_selection_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Workspace Selection")

        workspace_label = QtWidgets.QLabel("Workspace Name:", page)
        self.workspace_line_edit = QtWidgets.QLineEdit(page)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(workspace_label)
        layout.addWidget(self.workspace_line_edit)

        return page


def main():
    host = VersionControlHost()
    install_host(host)

    app_instance = get_ayon_qt_app()
    if (
        not ayon_info.is_running_from_build()
        and platform.system().lower() == "windows"
    ):
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "trayversioncontrol"
        )

    window = PerforceWorkspaceWizard()
    window.exec()
    app_instance.exec_()
