import pathlib
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

    Attributes:
        file_path (str): The path to the file in perforce.
        connection_info (ConnectionInfo): The connection information for accessing perforce.
        depot_path (Optional[str]): The depot path of the file. Defaults to None.
        revision_number (Optional[int]): The revision number of the file. Defaults to None.
        workspace_path (Optional[str]): The workspace path of the file. Defaults to None.
        status (Optional[str]): The status of the file in perforce. Defaults to None.
        changelist_number (Optional[int]): The changelist number associated with the file. Defaults to None.
        exists (Optional[bool]): Whether the file exists in perforce. Defaults to None.
        file_name (Optional[str]): The name of the file. Defaults to None.
    """

    file_path: str
    connection_info: ConnectionInfo
    depot_path: typing.Optional[str] = field(default=None)
    revision_number: typing.Optional[int] = field(default=None)
    workspace_path: typing.Optional[str] = field(default=None)
    status: typing.Optional[str] = field(default=None)
    changelist_number: typing.Optional[int] = field(default=None)
    exists: typing.Optional[bool] = field(default=None)
    file_name: typing.Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """
        Sets the `exists` attribute by checking if the file path exists in perforce.
        If `file_name` is not set, it is derived from `file_path`.
        """
        self.exists = self._get_file_exists()
        if self.file_name is None:
            self.file_name = pathlib.Path(self.file_path).name

    def _get_file_exists(self) -> bool:
        """
        Logs in to perforce using the provided connection information and checks
        if the file path exists on the server.

        Raises:
            ValueError: If no username or password is provided for the workspace server.
        """
        username = self.connection_info.workspace_server.username
        password = self.connection_info.workspace_server.password
        server = self.connection_info.workspace_server.name
        if not username or not password:
            raise ValueError(f"No username or password for {server}")

        PerforceRestStub.login(
            host=self.connection_info.workspace_server.host,
            port=str(self.connection_info.workspace_server.port),
            username=username,
            password=password,
            workspace_dir=self.connection_info.workspace_info.workspace_dir,
            workspace_name=self.connection_info.workspace_info.workspace_name,
        )
        log.debug(
            f"Checking {self.connection_info.workspace_server.host} for {self.file_path}"
        )
        reponse = PerforceRestStub.exists_on_server(self.file_path)
        return reponse
