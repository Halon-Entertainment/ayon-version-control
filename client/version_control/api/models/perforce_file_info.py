import os
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger

from version_control.rest.perforce.rest_stub import PerforceRestStub

from . import ConnectionInfo

log = Logger.get_logger(__name__)


@dataclass
class PerforceFileInfo:
    """
    Represents a file in perforce.
    """

    file_path: str
    depot_path: str
    revision_number: int
    workspace_path: str
    status: str
    changelist_number: int
    connection_info: ConnectionInfo
    exists: bool = field(default=False)

    def __post_init__(self) -> None:
        self.exists = self._get_file_exists()

    def _get_file_exists(self) -> bool:
        PerforceRestStub.login(
            host=self.connection_info.workspace_server.host,
            port=self.connection_info.workspace_server.port,
            username=self.connection_info.workspace_server.username,
            password=self.connection_info.workspace_server.password,
            workspace_dir=self.connection_info.workspace_info.workspace_dir,
            workspace_name=self.connection_info.workspace_info.workspace_name,
        )
        reponse = PerforceRestStub.exists_on_server(self.file_path)
        return reponse["value"]
