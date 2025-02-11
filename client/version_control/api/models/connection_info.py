import os
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings.lib import get_project_settings

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
