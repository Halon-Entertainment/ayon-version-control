import typing

from qtpy import QtCore, QtGui, QtWidgets

from ayon_core.tools.utils.projects_widget import ProjectsQtModel
from version_control.api.models import ServerWorkspaces

WORKSPACE_LABEL_ROLE = QtCore.Qt.UserRole + 100  # pyright: ignore[]
WORKSPACE_SERVER_ROLE = QtCore.Qt.UserRole + 101  # pyright: ignore[]
WORKSPACE_PRIMARY_ROLE = QtCore.Qt.UserRole + 102  # pyright: ignore[]
ACTIVE_VERSION_CONTROL_SYSTEM_ROLE = QtCore.Qt.UserRole + 103  # pyright: ignore[]
HOSTS_ROLE = QtCore.Qt.UserRole + 104  # pyright: ignore[]
WORKSPACE_ROOT_ROLE = QtCore.Qt.UserRole + 105  # pyright: ignore[]
SYNC_FROM_EMPTY_ROLE = QtCore.Qt.UserRole + 106  # pyright: ignore[]
STREAM_ROLE = QtCore.Qt.UserRole + 107  # pyright: ignore[]
OPTIONS_ROLE = QtCore.Qt.UserRole + 108  # pyright: ignore[]
ALLOW_CREATE_WORKSPACE_ROLE = QtCore.Qt.UserRole + 109  # pyright: ignore[]
CREATE_DIRS_ROLE = QtCore.Qt.UserRole + 110  # pyright: ignore[]
ENABLE_AUTOSYNC_ROLE = QtCore.Qt.UserRole + 111  # pyright: ignore[]
STARTUP_FILES_ROLE = QtCore.Qt.UserRole + 112  # pyright: ignore[]
WORKSPACE_NAME_ROLE = QtCore.Qt.UserRole + 113  # pyright: ignore[]


class QtWorkspaceInfo(QtGui.QStandardItemModel):
    def __init__(self, project_name: typing.Union[str, None] = None):
        super().__init__()
        self._workspace_items = {}
        self._server_workspaces = None
        if project_name:
            self.set_project(project_name)

    def set_project(self, project_name: str) -> None:
        self._server_workspaces = ServerWorkspaces(project_name)
        self._fill_items()

    def _fill_items(self):
        root_item = self.invisibleRootItem()

        if not root_item:
            raise RuntimeError("Root item unavailible")

        for row in range(root_item.rowCount()):
            root_item.takeRow(row)

        if self._server_workspaces:
            workspaces = self._server_workspaces.workspaces
            items = []
            for workspace in workspaces:
                workspace_item = QtGui.QStandardItem()
                workspace_item.setEditable(False)
                items.append(
                    workspace_item,
                )
                workspace_item.setData(workspace.name, QtCore.Qt.DisplayRole)  # pyright: ignore[]
                workspace_item.setData(workspace.name, WORKSPACE_LABEL_ROLE)
                workspace_item.setData(workspace.server, WORKSPACE_SERVER_ROLE)
                workspace_item.setData(workspace.primary, WORKSPACE_PRIMARY_ROLE)
                workspace_item.setData(workspace.active_version_control_system, ACTIVE_VERSION_CONTROL_SYSTEM_ROLE)
                workspace_item.setData(workspace.hosts, HOSTS_ROLE)
                workspace_item.setData(workspace.workspace_root, WORKSPACE_ROOT_ROLE)
                workspace_item.setData(workspace.sync_from_empty, SYNC_FROM_EMPTY_ROLE)
                workspace_item.setData(workspace.workspace_name, WORKSPACE_NAME_ROLE)
                workspace_item.setData(workspace.stream, STREAM_ROLE)
                workspace_item.setData(workspace.options, OPTIONS_ROLE)
                workspace_item.setData(workspace.allow_create_workspace, ALLOW_CREATE_WORKSPACE_ROLE)
                workspace_item.setData(workspace.create_dirs, CREATE_DIRS_ROLE)
                workspace_item.setData(workspace.enable_autosync, ENABLE_AUTOSYNC_ROLE)
                workspace_item.setData(workspace.startup_files, STARTUP_FILES_ROLE)

            root_item.appendRows(items)

