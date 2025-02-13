from dataclasses import dataclass

from ayon_core.lib.log import Logger

from .server_info import ServerInfo
from .workspace_info import WorkspaceInfo

log = Logger.get_logger(__name__)


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

    def can_login(self):
        return self.workspace_server.username is not None and self.workspace_server.password is not None
