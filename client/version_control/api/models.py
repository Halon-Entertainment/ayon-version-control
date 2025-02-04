import os
import pathlib
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings.lib import get_project_settings

from version_control.api.perforce import get_connection_info, workspace_exists

log = Logger.get_logger(__name__)


@dataclass
class ServerInfo:
    name: str
    host: str
    port: int
    username: str
    password: str

    @property
    def perforce_port(self) -> str:
        return f"{self.host}:{self.port}"

@dataclass
class WorkspaceInfo:
    name: str
    server: str
    primary: bool
    active_version_control_system: typing.Union[str, None]
    hosts: typing.List
    sync_from_empty: bool
    stream: str
    options: str
    allow_create_workspace: bool
    create_dirs: bool
    enable_autosync: bool
    project_name: str
    startup_files: typing.List[str]
    workspace_name: typing.Optional[str] = field(
        default=None, metadata={"formatter": None}
    )
    workspace_root: typing.Optional[str] = field(
        default=None, metadata={"formatter": None}
    )
    exists: typing.Optional[bool] = field(default=False)
    username: typing.Optional[str] = field(default=None)
    password: typing.Optional[str] = field(default=None)


    def __post_init__(self) -> None:
        if self.workspace_name is not None:
            self.workspace_name = self._format_workspace_name(self.workspace_name)
        if self.workspace_root is not None:
            self.workspace_root = self._format_workspace_root(self.workspace_root)
        self.exists = self._workspace_exists()

    def _format_workspace_name(self, workspace_name: str) -> str:
        import socket

        log.debug(f"Workspace Name {workspace_name}")
        log.debug(f"User: {os.getlogin()}")

        data = {}
        data["computername"] = socket.gethostname()
        data["user"] = os.getlogin()
        data["project"] = {"name": self.project_name}

        return workspace_name.format(**data)

    def _workspace_exists(self) -> bool:
        project_settings = get_project_settings(self.project_name)
        connection_info = get_connection_info(
            self.project_name, project_settings, self.workspace_name
        )
        return workspace_exists(connection_info)

    def _format_workspace_root(self, workspace_dir: str) -> str:
        anatomy = Anatomy(project_name=self.project_name)
        data = get_template_data_with_names(self.project_name)
        data["root"] = anatomy.roots
        data.update(anatomy.roots)

        return workspace_dir.format(**data)


@dataclass
class ServerWorkspaces:
    workspaces: typing.List[WorkspaceInfo] = field(default_factory=lambda: [])

    def __init__(self, project_name: typing.Union[str, None] = None) -> None:
        if project_name:
            self.fetch_project_workspaces(project_name)

    def fetch_project_workspaces(self, project_name: str):
        project_settings = get_project_settings(project_name)
        version_control_settings = project_settings["version_control"]
        self.workspaces = list(
            map(
                lambda x: self._add_workspace_info(project_name, x),
                version_control_settings["workspace_settings"],
            )
        )
        log.debug(f"Workspace {self.workspaces}")

    def _add_workspace_info(self, project_name, settings):
        project_data = {"project_name": project_name}
        settings.update(project_data)
        return WorkspaceInfo(**settings)

    def get_host_workspaces(
        self, host: str, primary: bool = False
    ) -> typing.List[WorkspaceInfo]:
        if primary:
            return list(
                filter(lambda x: host in x.hosts and x.primary, self.workspaces)
            )
        return list(filter(lambda x: host in x.hosts, self.workspaces))


@dataclass
class ConnectionInfo:
    workspace_info: WorkspaceInfo
    workspace_server: ServerInfo
