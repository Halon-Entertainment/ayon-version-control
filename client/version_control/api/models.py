import os
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings.lib import get_project_settings

log = Logger.get_logger(__name__)

class ConfigurationError(Exception):
    pass


@dataclass
class ServerInfo:
    """
    Represents server information for a Perforce connection.

    Attributes:
        name (str): The name of the server.
        host (str): The hostname or IP address of the server.
        port (int): The port number on which the server is listening.
        username (str): The username used to authenticate with the server.
        password (str): The password used to authenticate with the server.

    Properties:
        perforce_port (str): Returns a formatted string representing the server's address and port.
    """

    name: str
    host: str
    port: int
    username: typing.Optional[str] = field(default=None)
    password: typing.Optional[str] = field(default=None)

    def __eq__(self, other):
        if isinstance(other, ServerInfo):
            return self.name == other.name
        else:
            raise TypeError(f"Cannot compare {type(other)} with {self.__class__.__name__}")

    @property
    def perforce_port(self) -> str:
        """
        Get a formatted string representing the server's address and port.

        Returns:
            str: The formatted server address and port.
        """
        return f"{self.host}:{self.port}"


@dataclass
class WorkspaceInfo:
    """
    Represents workspace information for a Perforce connection.

    Attributes:
        name (str): The name of the workspace.
        server (str): The name of the server associated with the workspace.
        primary (bool): Indicates whether this is the primary workspace for the server.
        active_version_control_system (Optional[str]): The version control system used by the workspace.
        hosts (List[str]): A list of hostnames where the workspace can be accessed.
        sync_from_empty (bool): If True, files will be synced from an empty directory during synchronization.
        stream (str): The stream associated with the workspace.
        options (str): Additional options for the workspace.
        allow_create_workspace (bool): If True, the workspace is allowed to be created if it does not exist.
        create_dirs (bool): If True, necessary directories will be created when setting up the workspace.
        enable_autosync (bool): If True, the workspace enables automatic synchronization with Perforce.
        project_name (str): The name of the project associated with the workspace.
        startup_files (List[str]): A list of files to start with in the workspace.
        workspace_name (Optional[str]): The workspace name formatted with placeholders for dynamic values. (default: None)
        workspace_root (Optional[str]): The root directory of the workspace formatted with placeholders for dynamic values. (default: None)
        exists (Optional[bool]): Indicates whether the workspace already exists. (default: False)
        username (Optional[str]): The workspace-specific username if different from the server's username. (default: None)
        password (Optional[str]): The workspace-specific password if different from the server's password. (default: None)

    Methods:
        __post_init__: Post-initialization method to format workspace_name and workspace_root, and check workspace existence.
        _format_workspace_name(str): Helper to populate placeholder for workspace name with dynamic data.
        _workspace_exists: Determines if the workspace exists in Perforce.
        _format_workspace_root(str): Helper to populate placeholder for workspace root directory with relevant project settings.
    """

    name: str
    server: str
    primary: bool
    active_version_control_system: typing.Union[str, None]
    hosts: typing.List
    sync_from_empty: bool
    stream: str
    options: str
    workspace_root: str
    allow_create_workspace: bool
    create_dirs: bool
    enable_autosync: bool
    project_name: str
    startup_files: typing.List[str]
    workspace_name: typing.Optional[str] = field(
        default=None, metadata={"formatter": None}
    )
    workspace_dir: typing.Optional[str] = field(
        default=None, metadata={"formatter": None}
    )

    def __post_init__(self) -> None:
        """
        Post-initialization method to format workspace_name and workspace_root, and check workspace existence.

        This method formats the `workspace_name` and `workspace_root` attributes by replacing placeholders
        with actual dynamic values as retrieved from data sources. It then checks if the workspace exists in Perforce.
        """

        if self.workspace_name is not None:
            self.workspace_name = self._format_workspace_name(self.workspace_name)
        if self.workspace_root is not None:
            self.workspace_dir = self._format_workspace_dir()

    def _format_workspace_name(self, workspace_name: str) -> str:
        """
        Helper to populate placeholder for workspace name with dynamic data.

        Args:
            workspace_name (str): The original workspace name containing placeholders.

        Returns:
            str: The formatted workspace name.
        """

        import socket

        log.debug(f"Workspace Name {workspace_name}")
        log.debug(f"User: {os.getlogin()}")

        data = {}
        data["computername"] = socket.gethostname()
        data["user"] = os.getlogin()
        data["project"] = {"name": self.project_name}

        return workspace_name.format(**data)

    def _format_workspace_dir(self) -> str:
        """
        Helper to populate placeholder for workspace root directory with relevant project settings.

        Args:
            workspace_dir (str): The original workspace root directory containing placeholders.

        Returns:
            str: The formatted workspace root directory.
        """

        anatomy = Anatomy(project_name=self.project_name)
        log.debug(anatomy.roots)
        try:
            workspace_dir = str(anatomy.roots[self.workspace_root])
        except KeyError as err:
            msg = (
                f"Unable to get the root: {self.workspace_root} "
                f"for workspace {self.name}.\n"
                f"Please contact your Administrator."
            )
            raise ConfigurationError(msg) from err
        data = get_template_data_with_names(self.project_name)
        data["root"] = anatomy.roots
        data.update(anatomy.roots)
        formatted_workspace_dir = workspace_dir.format(**data)
        log.debug(f"Workspace Dir {formatted_workspace_dir}")

        return formatted_workspace_dir


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


@dataclass
class ConnectionInfo:
    """
    Represents connection information for a Perforce workspace.

    Attributes:
        workspace_info (WorkspaceInfo): The workspace being connected to.
        workspace_server (ServerInfo): The server on which the workspace resides.

    """

    workspace_info: WorkspaceInfo
    workspace_server: ServerInfo
