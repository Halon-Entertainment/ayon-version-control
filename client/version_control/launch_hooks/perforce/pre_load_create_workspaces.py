import typing

from ayon_applications import LaunchTypes, PreLaunchHook
from ayon_core.addon import AddonsManager
from version_control.addon import VersionControlAddon
from version_control.api import perforce
from version_control.api.models import ServerWorkspaces


class PreLaunchCreateWorkspaces(PreLaunchHook):
    """Show dialog for artist to sync to specific change list.

    It is triggered before Unreal launch as syncing inside would likely
    lead to locks.
    It is called before `pre_workfile_preparation` which is using
    self.data["last_workfile_path"].

    It is expected that workspace would be created, connected
    and first version of project would be synced before.
    """

    order = -10
    app_groups = []
    launch_types = {LaunchTypes.local}

    def _get_enabled_version_control_addon(
        self,
    ) -> typing.Union[VersionControlAddon, None]:
        manager = AddonsManager()
        version_control_addon = manager.get("version_control")
        if version_control_addon and version_control_addon.enabled:
            return version_control_addon
        return None

    def execute(self):
        project_name = self.data["project_name"]
        server_workspaces = ServerWorkspaces(project_name)

        for workspace in server_workspaces.workspaces:
            conn_info = perforce.get_connection_info(
                project_name, configured_workspace=workspace.name
            )

            if not perforce.workspace_exists(conn_info):
                self.log.debug("Workspace %s Does not exist", workspace.workspace_name)
                perforce.create_workspace(conn_info)
