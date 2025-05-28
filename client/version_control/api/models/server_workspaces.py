import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.settings.lib import get_project_settings

from .workspace_info import WorkspaceInfo

log = Logger.get_logger(__name__)
@dataclass
class ServerWorkspaces:
    """
    Represents a collection of workspaces associated with a server.

    Attributes:
        workspaces (List[WorkspaceInfo]): A list of workspace information objects.

    Methods:
        __init__: Initializes the ServerWorkspaces object, optionally fetching project workspaces.
        fetch_project_workspaces(str): Fetches and populates workspaces for a specified project.
        _add_workspace_info(str, dict): Generates a WorkspaceInfo instance from given settings.
        get_host_workspaces(str, bool): Retrieves workspaces associated with a specific host and primary status.
    """

    workspaces: typing.List[WorkspaceInfo] = field(default_factory=lambda: [])

    def __init__(self, project_name: typing.Union[str, None] = None) -> None:
        """
        Initializes the ServerWorkspaces object, optionally fetching project workspaces.

        Args:
            project_name (Optional[str]): The name of the project to fetch workspaces for.
                Defaults to None, which means no initial projects are fetched.
        """

        if project_name:
            self.fetch_project_workspaces(project_name)

    def fetch_project_workspaces(self, project_name: str):
        """
        Fetches and populates workspaces for a specified project.

        Args:
            project_name (str): The name of the project to fetch workspaces for.

        Returns:
            None
        """

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
        """
        Generates a WorkspaceInfo instance from given settings.

        Args:
            project_name (str): The name of the project associated with the workspace.
            settings (dict): A dictionary containing workspace-specific settings.

        Returns:
            WorkspaceInfo: An initialized WorkspaceInfo object.
        """

        project_data = {"project_name": project_name}
        settings.update(project_data)
        return WorkspaceInfo(**settings)

    def get_host_workspaces(
        self, host: typing.Union[str, None] = None, primary: bool = False
    ) -> typing.List[WorkspaceInfo]:
        """
        Retrieves workspaces associated with a specific host and primary status.

        Args:
            host (str): The hostname to filter workspaces by.
            primary (bool): If True, retrieves only primary workspaces for the specified host.
                Defaults to False, which means all workspaces for the specified host are retrieved.

        Returns:
            List[WorkspaceInfo]: A list of WorkspaceInfo objects matching the criteria.
        """

        if not host:
            return list(filter(lambda x: x.primary, self.workspaces))

        if primary:
            return list(
                filter(lambda x: host in x.hosts and x.primary, self.workspaces)
            )
        return list(filter(lambda x: host in x.hosts, self.workspaces))

    def get_workspace_by_name(self, workspace_name: str) -> WorkspaceInfo:
        return list(filter(lambda x: x.name == workspace_name, self.workspaces))[0]
