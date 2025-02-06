import pathlib
from ayon_applications import (
    PreLaunchHook,
    LaunchTypes,
    ApplicationLaunchFailed
)

from ayon_core.addon import AddonsManager
from version_control.api.workspaces import list_workspaces
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.addon import LoginError, VersionControlAddon
from ayon_core.lib import get_local_site_id
from ayon_api import get_base_url
from version_control.api import perforce
from version_control.api import workspaces
import typing


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

    def _get_enabled_version_control_addon(self) -> typing.Union[VersionControlAddon, None]:
        manager = AddonsManager()
        version_control_addon = manager.get("version_control")
        if version_control_addon and version_control_addon.enabled:
            return version_control_addon
        return None

    def execute(self):
        project_name = self.data["project_name"]
        project_settings = self.data["project_settings"]
        version_control_settings = project_settings["version_control"]
        if not version_control_settings["enabled"]:
            return

        workspace_names = workspaces.list_workspaces(version_control_settings)

        for workspace_name, workspace_server in workspace_names:
            perforce.check_login(workspace_server)
            conn_info = perforce.get_connection_info(
                project_name, configured_workspace=workspace_name
            )
            if not conn_info.workspace_info.stream:
                self.log.error(
                    (
                        f"No stream set for {workspace_name}. The workspace will not"
                        "be created."
                    )
                )
                continue

            if not perforce.workspace_exists(conn_info):
                self.log.debug("Workspace %s Does not exist", workspace_name)
                perforce.create_workspace(conn_info)
