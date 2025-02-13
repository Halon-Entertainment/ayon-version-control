import pathlib
import typing

from ayon_core.pipeline.context_tools import get_current_project_name, registered_host
from ayon_core.tools.workfiles.control import BaseWorkfileController

from version_control.api.exceptions import LoginError
from version_control.api.models.connection_info import ConnectionInfo
from version_control.api.models.perforce_file_info import PerforceFileInfo
from version_control.api.models.server_workspaces import ServerWorkspaces
from version_control.api.perforce import get_connection_info
from version_control.rest.perforce.rest_stub import PerforceRestStub


class UserSubmitController:
    """Class to handle submission of workfiles for Perforce."""

    def __init__(self):
        """Initialize the UserSubmitController.

        Raises:
            ValueError: If the host or project context is not available.
        """
        host = registered_host()
        project = get_current_project_name()
        if not host:
            raise ValueError("Unable to find host. This must run in a host context.")
        if not project:
            raise ValueError("get_files cannot be used outside of a project context.")

        self._host = host
        self._project = project

    def get_perforce_files(self) -> typing.List[PerforceFileInfo]:
        """Get the list of Perforce files for the current task.

        Returns:
            typing.List[PerforceFileInfo]: List of Perforce file information.
        """
        controller = BaseWorkfileController()
        controller.reset()
        workfiles = controller.get_workarea_file_items(
            controller.get_current_folder_id(),
            controller.get_current_task_name(),
        )

        workfile_paths = map(lambda x: pathlib.Path(x.dirpath) / x.filename, workfiles)
        connection_info = self._get_connection()
        workfiles = list(
            map(
                lambda x: PerforceFileInfo(x.as_posix(), connection_info),
                workfile_paths,
            )
        )

        return workfiles

    def submit_workfiles(
        self, workfiles: typing.List[str], comment: typing.Optional[str]
    ) -> typing.List[str]:
        """Submit the given workfiles to Perforce.

        Args:
            workfiles (typing.List[str]): List of file paths to submit.
            comment (typing.Optional[str]): Optional comment for the submission.

        Returns:
            typing.List[str]: List of submitted file paths.

        Raises:
            LoginError: If no login credentials are provided.
        """
        connection_info = self._get_connection()
        username = connection_info.workspace_server.username
        password = connection_info.workspace_server.password

        if not username or not password:
            raise LoginError("No login credentials provided.")

        PerforceRestStub.login(
            host=connection_info.workspace_server.host,
            port=str(connection_info.workspace_server.port),
            username=username,
            password=password,
            workspace_dir=connection_info.workspace_info.workspace_dir,
            workspace_name=connection_info.workspace_info.workspace_name,
        )

        for workfile in workfiles:
            PerforceRestStub.add(workfile, comment or "")

        PerforceRestStub.submit_change_list(comment or "")

        return workfiles

    def _get_connection(self) -> ConnectionInfo:
        """Get the connection information for the current project and workspace.

        Returns:
            ConnectionInfo: Connection information object.

        Raises:
            ValueError: If no workspaces are found for the host.
        """
        host = self._host
        project = self._project

        server_workspaces = ServerWorkspaces(project)
        workspaces = server_workspaces.get_host_workspaces(self._host.name, True)
        if not workspaces:
            raise ValueError(f"Unable to get workspaces for {host.name}")
        else:
            current_workspace = workspaces[0]

        connection_info = get_connection_info(
            project_name=project,
            configured_workspace=current_workspace.name,
            host=host,
        )
        return connection_info
