import typing
from dataclasses import dataclass, field

from ayon_core.settings.lib import get_project_settings
from ayon_core.lib.log import Logger

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
    workspace_name: str
    stream: str
    options: str
    allow_create_workspace: bool
    create_dirs: bool
    enable_autosync: bool
    startup_files: typing.List[str]


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
                lambda x: WorkspaceInfo(**x),
                version_control_settings["workspace_settings"],
            )
        )
        log.debug(f"Workspace {self.workspaces}")


    def get_host_workspaces(
        self, host: str, primary: bool = False
    ) -> typing.List[WorkspaceInfo]:
        if primary:
            return list(
                filter(
                    lambda x: host in x.hosts and x.primary, self.workspaces
                )
            )
        return list(filter(lambda x: host in x.hosts, self.workspaces))
