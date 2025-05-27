import typing

from ayon_applications import LaunchTypes, PreLaunchHook
from ayon_applications.exceptions import ApplicationLaunchFailed
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from version_control.api import perforce
from version_control.api.models import ServerWorkspaces


class PreLaunchCreateWorkspaces(PreLaunchHook):

    order = -8
    app_groups = []
    launch_types = {LaunchTypes.local}

    @classmethod
    def class_validation(cls, launch_context):
        """Validation of class attributes by launch context.

        Args:
            launch_context (ApplicationLaunchContext): Context of launching
                application.

        Returns:
            bool: Is launch hook valid for the context by class attributes.
        """
        if cls.platforms:
            low_platforms = tuple(
                _platform.lower()
                for _platform in cls.platforms
            )
            if platform.system().lower() not in low_platforms:
                return False

        if cls.hosts:
            if launch_context.host_name not in cls.hosts:
                return False

        if cls.app_groups:
            if launch_context.app_group.name == 'unreal':
                return False

        if cls.app_names:
            if launch_context.app_name not in cls.app_names:
                return False

        if cls.launch_types:
            if launch_context.launch_type not in cls.launch_types:
                return False

        return True

    def execute(self):
        project_name = self.data["project_name"]
        anatomy = Anatomy(project_name)

        project_name = self.data["project_name"]
        project_settings = self.data["project_settings"]
        version_control_settings = project_settings['version_control']

        if not version_control_settings["enabled"]:
            return

        server_workspaces = ServerWorkspaces(project_name)

        for workspace in server_workspaces.workspaces:
            conn_info = perforce.get_connection_info(
                project_name, configured_workspace=workspace.name
            )

            self.log.debug(f"Checking if workspace {workspace.workspace_name} exists")

            if not perforce.workspace_exists(conn_info):
                raise ApplicationLaunchFailed(f"Workspace {workspace.workspace_name} does not exist, did other hook not run?")

            self.log.debug(f"Workspace {workspace.workspace_name} exists")

            for sync_file in workspace.always_sync:
                conn_info.workspace_info.stream
                current_root = str(anatomy.roots[conn_info.workspace_info.workspace_root])
                local_file = sync_file.replace(conn_info.workspace_info.stream, current_root)
                self.log.info(f"Syncing: {local_file}")
                perforce.sync_target_to_latest(conn_info, local_file)
