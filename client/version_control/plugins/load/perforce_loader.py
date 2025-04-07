import pathlib
from pprint import pformat
import os

from ayon_api._api import get_representations
from ayon_core.pipeline import load
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.context_tools import (
    get_current_host_name,
    get_current_project_name,
)
from ayon_core import style
from ayon_core.settings.lib import get_project_settings
from qtpy import QtWidgets

from version_control.api import perforce
from version_control.api.perforce import (
    get_connection_info,
    get_current_host_connection,
    handle_login,
)


class PerforcePull(load.ProductLoaderPlugin):
    """Export selected versions to folder structure from Template"""

    is_multiple_contexts_compatible = True

    representations = {"*"}
    product_types = {"*"}

    label = "Pull From Perforce"
    order = 0
    icon = "download"
    color = "#d8d8d8"

    def load(self, contexts, name=None, namespace=None, options=None):
        print(dir(self))


        for context in contexts:
            host = get_current_host_name()
            if not host:
                print(pformat(context))

                project_name = context['project']['name']
                project_settings = get_project_settings(project_name)
                project_workspaces = project_settings["version_control"][
                    "workspace_settings"
                ]
                perforce_workspace = self.show_selector(project_workspaces)
                connection_info = get_connection_info(
                    project_name, perforce_workspace
                )
                os.environ["AYON_PROJECT_NAME"] = project_name
            else:
                connection_info = get_current_host_connection()

            handle_login(connection_info)

            anatomy = Anatomy()

            version = context["version"]
            representations = list(
                get_representations(
                    anatomy.project_name, version_ids=[version["id"]]
                )
            )

            for representation in representations:
                for current_file in representation["files"]:
                    template = current_file["path"]
                    path = pathlib.Path(
                        template.format(**representation["context"])
                    )
                    if not path.exists():
                        self.log.info(
                            f"Syncing {path.as_posix()} from Perforce."
                        )
                        perforce.sync_target_to_latest(
                            connection_info, path.as_posix()
                        )

        QtWidgets.QMessageBox.information(None, "Files Synced", "Files Sync'd")

    def show_selector(self, workspaces):
        workspace_selector = WorkspaceSelectorDialog(workspaces)
        workspace_selector.exec()
        return workspace_selector.selected_workspace


class WorkspaceSelectorDialog(QtWidgets.QDialog):
    def __init__(self, workspaces, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(style.load_stylesheet())

        self.selected_workspace = None

        self.setWindowTitle("Select Workspace")
        layout = QtWidgets.QVBoxLayout()
        self.workspaces = workspaces

        self.label = QtWidgets.QLabel("Select a workspace.")
        self.workspace_combo = QtWidgets.QComboBox()

        workspace_names = map(lambda x: x["name"], self.workspaces)
        self.workspace_combo.addItems(workspace_names)

        self.accept_button = QtWidgets.QPushButton("Accept")

        layout.addWidget(self.label)
        layout.addWidget(self.workspace_combo)
        layout.addWidget(self.accept_button)
        self.setLayout(layout)

        self.accept_button.clicked.connect(self._on_accept)

    def _on_accept(self):
        self.selected_workspace = self.workspace_combo.currentText()
        self.close()
