"""Shows dialog to sync Unreal project

Requires:
    None

Provides:
    self.data["last_workfile_path"]

"""

import os

from ayon_applications import (
    PreLaunchHook,
    ApplicationLaunchFailed,
    LaunchTypes,
)

from ayon_core.lib import get_local_site_id
from ayon_core.tools.utils import qt_app_context
from ayon_core.addon import AddonsManager
from ayon_core.pipeline import context_tools
from ayon_api import get_base_url

from version_control.changes_viewer import ChangesWindows


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
        version_control_addon = self._get_enabled_version_control_addon()
        if not version_control_addon:
            raise RuntimeError("Unable to load version control addon")

        project_name = self.data["project_name"]
        project_settings = self.data["project_settings"]
        version_control_settings = project_settings["version_control"]
        if not version_control_settings["enabled"]:
            return

        self.data["last_workfile_path"] = self._get_unreal_project_path(
            version_control_addon
        )

        current_workspace = version_control_addon.get_workspace(
            self.data["project_settings"]
        )
        project_name = context_tools.get_current_project_name()
        login_info = version_control_addon.get_login_info(
            project_name,
            current_workspace["server"],
            project_settings=self.data["project_settings"],
        )
        current_workspace.update(login_info)
        self.log.debug("Current Workspace")
        from pprint import pformat

        self.log.debug(pformat(current_workspace))
        self.log.debug("Current Workspace")
        username = login_info.get("username")
        password = login_info.get("password")
        self.log.debug("Username: %s", username)

        conn_info = {}
        project_name = self.data["project_name"]

        conn_info.update(
            version_control_addon.get_connection_info(project_name)
        )
        if not conn_info["stream"]:
            raise ApplicationLaunchFailed(
                "No stream set for the current workspace."
            )

        if not username or not password:
            msg = (
                "Unable to connect to perforce, you need to update the Username "
                "and Password in your site settings."
            )
            url = f"{get_base_url()}/manageProjects/siteSettings?project={project_name}&uri=ayon+settings://version_control?project=test&site={get_local_site_id()}"

            msg = (
                f"{msg} <a href='{url}'>Click here to update your settings</a>"
            )

            raise ApplicationLaunchFailed(msg)

        self.log.debug(conn_info)
        self.log.debug(
            "Workspace Exists %s",
            version_control_addon.workspace_exists(conn_info),
        )
        if not version_control_addon.workspace_exists(conn_info):
            self.log.debug(
                "Workspace %s Does not exist", conn_info["workspace_name"]
            )
            version_control_addon.create_workspace(conn_info)

        if not version_control_addon.get_connection_info(
            project_name=self.data["project_name"]
        )["enable_autosync"]:
            self.log.debug(f"Workspace autosync is Disabled, skipping")
            return

        with qt_app_context():
            changes_tool = ChangesWindows(launch_data=self.data)
            changes_tool.show()
            changes_tool.raise_()
            changes_tool.activateWindow()
            changes_tool.showNormal()

            changes_tool.exec_()

    def _get_unreal_project_path(self, version_control_addon):
        conn_info = version_control_addon.get_connection_info(
            project_name=self.data["project_name"]
        )
        workdir = conn_info["workspace_dir"]

        project_folder = self.data["project_settings"]["unreal"][
            "project_folder"
        ]
        plugin_path = (
            f"{workdir}/{project_folder}/Plugins/Halon/ThirdParty/Ayon"
        )
        if os.path.exists(plugin_path):
            os.environ["AYON_BUILT_UNREAL_PLUGIN"] = plugin_path

        if not workdir:
            raise RuntimeError(
                f"{workdir} must exist or workspace settings should "
                f"be set when using version control"
            )

        project_files = self._find_uproject_files(workdir)
        if len(project_files) != 1:
            if conn_info["allow_create_workspace"]:
                return None
            raise RuntimeError(
                "Found unexpected number of projects "
                f"{project_files}.\n"
                "Expected only single Unreal project."
            )
        return project_files[0]

    def _get_enabled_version_control_addon(self):
        manager = AddonsManager()
        version_control_addon = manager.get("version_control")
        if version_control_addon and version_control_addon.enabled:
            return version_control_addon
        return None

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
