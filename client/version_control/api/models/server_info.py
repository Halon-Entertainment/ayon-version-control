import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger

log = Logger.get_logger(__name__)

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
