import platform
import sys

import qtawesome
from ayon_core import style
from ayon_core.lib import ayon_info
from ayon_core.lib.local_settings import AYONSettingsRegistry
from ayon_core.lib.log import Logger
from ayon_core.pipeline.context_tools import install_host
from ayon_core.settings.lib import get_project_settings
from ayon_core.tools.utils.lib import get_ayon_qt_app
from ayon_core.tools.utils.projects_widget import (
    ProjectSortFilterProxy,
    ProjectsQtModel,
)
from ayon_core.tools.utils.widgets import PlaceholderLineEdit, RefreshButton
from qtpy import QtCore, QtWidgets
from typing_extensions import override

from version_control.addon import VersionControlAddon
from version_control.api.pipeline import VersionControlHost
from version_control.ui.workspace_wizzard.delegates import WorkspaceIconDelegate
from version_control.ui.workspace_wizzard.models import QtWorkspaceInfo

from .controller import PerforceProjectsController

log = Logger.get_logger(__name__)


class PerforceWorkspaceRegistry(AYONSettingsRegistry):
    def __init__(self):
        super().__init__("perforceworkspace")


class PerforceWorkspaces(QtWidgets.QWizard):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        log.debug("Starting Workspace Wizard")
        self._manager = manager
        self._version_control: VersionControlAddon = manager.get('version_control')
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

        refresh_button = RefreshButton()

        projects_model = ProjectsQtModel(PerforceProjectsController())
        projects_proxy = ProjectSortFilterProxy()
        projects_proxy.setSourceModel(projects_model)
        projects_proxy.setFilterKeyColumn(0)

        projects_view = QtWidgets.QListView()
        projects_view.setObjectName("ChooseProjectView")
        projects_view.setModel(projects_proxy)
        projects_view.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )

        txt_filter = PlaceholderLineEdit()
        txt_filter.setPlaceholderText("Quick fliter projects..")
        txt_filter.setClearButtonEnabled(True)
        txt_filter.addAction(
            qtawesome.icon("fa.filter", color="gray"),
            QtWidgets.QLineEdit.LeadingPosition,
        )

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(txt_filter)
        layout.addWidget(projects_view)
        layout.addWidget(refresh_button)

        refresh_button.clicked.connect(projects_model.refresh)
        txt_filter.textChanged.connect(self._on_text_changed)
        self.currentIdChanged.connect(self.on_project_selection_page_next)

        self._projects_view = projects_view
        self._projects_model = projects_model
        self._projects_proxy = projects_proxy
        self._txt_filter = txt_filter

        return page

    def _on_text_changed(self):
        self._projects_proxy.setFilterRegularExpression(
            self._txt_filter.text())

    def on_project_selection_page_next(self, current_id):
        if current_id == 2:
            selected_index = self._projects_view.currentIndex()
            if selected_index.isValid():
                project_name = self._projects_view.model().data(
                    selected_index, role=QtCore.Qt.ItemDataRole.DisplayRole
                )
                log.info(f"{project_name}")
                project_settings = get_project_settings(project_name)
                version_control_settings = project_settings["version_control"]
                workspace_names = list(map(
                    lambda x: (x["name"], x["server"]), version_control_settings["workspace_settings"]
                ))
                log.debug(f"{workspace_names}")
                self._project_name = project_name
                self._workspace_model.set_project(project_name)
            else:
                self.project = None
                log.warning("No project selected")

    @override
    def showEvent(self, event):
        self._projects_model.refresh()

        setting_registry = PerforceWorkspaceRegistry()
        try:
            project_name = setting_registry.get_item("project_name")
        except ValueError:
            project_name = None

        if project_name:
            src_index = self._projects_model.get_index_by_project_name(
                project_name
            )

    def _create_workspace_selection_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Workspace Selection")

        workspace_label = QtWidgets.QLabel("Workspace Name:", page)
        workspace_model = QtWorkspaceInfo()
        workspace_view = QtWidgets.QListView(page)
        workspace_view.setItemDelegate(WorkspaceIconDelegate())
        workspace_view.setModel(workspace_model)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(workspace_label)
        layout.addWidget(workspace_view)

        self._workspace_view = workspace_view
        self._workspace_model = workspace_model
        return page


def main(manager):
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

    window = PerforceWorkspaces(manager)
    window.exec()
    app_instance.exec_()
