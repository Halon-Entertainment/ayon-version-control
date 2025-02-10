"""Shows dialog to sync Unreal project

Requires:
    None

Provides:
    self.data["last_workfile_path"]

"""

import os

from ayon_applications import LaunchTypes, PreLaunchHook
from ayon_core.tools.utils import qt_app_context

from version_control.api import perforce
from version_control.api.models import ServerWorkspaces
from version_control.ui.changes_viewer import ChangesWindows


class SyncUnrealProject(PreLaunchHook):
    """Show dialog for artist to sync to specific change list.

    It is triggered before Unreal launch as syncing inside would likely
    lead to locks.
    It is called before `pre_workfile_preparation` which is using
    self.data["last_workfile_path"].

    It is expected that workspace would be created, connected
    and first version of project would be synced before.
    """

    order = -5
    app_groups = ["unreal"]
    launch_types = {LaunchTypes.local}

    def execute(self):
        project_name = self.data["project_name"]
        server_workspaces = ServerWorkspaces(project_name)

        if self.host_name:
            server_workspaces.get_host_workspaces(self.host_name, True)
            if server_workspaces.workspaces:
                workspace = server_workspaces.workspaces[0]
                conn_info = perforce.get_connection_info(project_name, workspace.name)
            else:
                raise ValueError(f"No workspace found for {self.host_name}")

            if not perforce.workspace_exists(conn_info):
                self.log.debug(
                    "Workspace %s Does not exist",
                    conn_info.workspace_info.workspace_name,
                )
                perforce.create_workspace(conn_info)

            with qt_app_context():
                changes_tool = ChangesWindows(launch_data=self.data)
                changes_tool.show()
                changes_tool.raise_()
                changes_tool.activateWindow()
                changes_tool.showNormal()

                changes_tool.exec_()  # pyright: ignore[]

    def _get_unreal_project_path(self):
        conn_info = perforce.get_connection_info(project_name=self.data["project_name"])
        workdir = conn_info.workspace_info.workspace_dir

        project_folder = self.data["project_settings"]["unreal"]["project_folder"]
        plugin_path = f"{workdir}/{project_folder}/Plugins/Halon/ThirdParty/Ayon"
        if os.path.exists(plugin_path):
            os.environ["AYON_BUILT_UNREAL_PLUGIN"] = plugin_path

        if not workdir:
            raise RuntimeError(
                f"{workdir} must exist or workspace settings should "
                f"be set when using version control"
            )

        project_files = self._find_uproject_files(workdir)
        if len(project_files) != 1:
            if conn_info.workspace_info.allow_create_workspace:
                return None
            raise RuntimeError(
                "Found unexpected number of projects "
                f"{project_files}.\n"
                "Expected only single Unreal project."
            )
        return project_files[0]

    def _find_uproject_files(self, start_dir):
        """
        This function searches for files with the .uproject extension recursively
        within a starting directory and its subdirectories.

        Args:
            start_dir: The starting directory from where the search begins.

        Returns:
            A list of full paths to all the found .uproject files.
        """
        uproject_files = []
        for dirpath, dirnames, filenames in os.walk(start_dir):
            for filename in filenames:
                if filename.endswith(".uproject"):
                    uproject_files.append(os.path.join(dirpath, filename))
        return uproject_files
