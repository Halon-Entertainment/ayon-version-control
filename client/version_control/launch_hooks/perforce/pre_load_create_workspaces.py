import pathlib
from ayon_applications import (
    PreLaunchHook,
    LaunchTypes,
    ApplicationLaunchFailed
)

from ayon_core.addon import AddonsManager
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.addon import LoginError, VersionControlAddon
from ayon_core.lib import get_local_site_id
from ayon_api import get_base_url
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

        workspace_names = map(
            lambda x: x["name"], version_control_settings["workspace_settings"]
        )
        version_control_addon = self._get_enabled_version_control_addon()
        if not version_control_addon:
            raise ApplicationLaunchFailed('Unable to find version control addon.')

        for workspace in workspace_names:
            try:
                conn_info = version_control_addon.get_connection_info(
                    project_name, configured_workspace=workspace
                )
            except LoginError as error:
                    msg = ("Unable to connect to perforce, you need to update the Username "
                        "and Password in your site settings.")
                    url = f"{get_base_url()}/manageProjects/siteSettings?project={project_name}&uri=ayon+settings://version_control?project=test&site={get_local_site_id()}"

                    msg = f"{msg} <a href='{url}'>Click here to update your settings</a>"
                    raise ApplicationLaunchFailed(msg) from error

            current_workspace_settings = list(
                filter(
                    lambda x: x["name"] == workspace,
                    version_control_settings["workspace_settings"],
                )
            )[0]
            workspace_files = current_workspace_settings["startup_files"]

            if not conn_info["stream"]:
                self.log.error(
                    (
                        f"No stream set for {workspace}. The workspace will not"
                        "be created."
                    )
                )
                continue

            if not version_control_addon.workspace_exists(conn_info):
                self.log.debug("Workspace %s Does not exist", workspace)
                version_control_addon.create_workspace(conn_info)

            self.log.debug(f"Current Workspace {workspace}")
            self.log.debug(f"Workspace Files: {workspace_files}")

            if workspace_files:
                for current_path in workspace_files:
                    current_path = (
                        pathlib.Path(conn_info["workspace_dir"]) / current_path
                    ).as_posix()
                    self.log.debug(f"Syncing {current_path}")
                    PerforceRestStub.sync_latest_version(current_path)
