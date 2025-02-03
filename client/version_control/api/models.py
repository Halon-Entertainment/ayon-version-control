import os
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.settings.lib import get_project_settings

log = Logger.get_logger(__name__)


@dataclass
class WorkspaceInfo:
    name: str
    server: str
    primary: bool
    active_version_control_system: typing.Union[str, None]
    hosts: typing.List
    workspace_root: str
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

    def __post_init__(self):
        if self.workspace_name is not None:
            self.workspace_name = self._format_workspace_name(self.workspace_name)

    def _format_workspace_name(self, workspace_name: str):
        import socket

        log.debug(f'Workspace Name {workspace_name}')
        log.debug(f'User: {os.getlogin()}')

        data = {}
        data["computername"] = socket.gethostname()
        data["user"] = os.getlogin()
        data["project"] = {'name': self.project_name}

        return workspace_name.format(**data)


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
        project_data = {
            'project_name': project_name
        }
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
