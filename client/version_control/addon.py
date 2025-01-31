import json
import os
import pathlib

from ayon_core.addon import (
    AYONAddon,
    IPluginPaths,
    ITrayAction,
    ITrayService,
    IHostAddon,
    click_wrap,
)
from ayon_core.pipeline.context_tools import get_current_host_name
from ayon_core.settings import get_project_settings
from ayon_core.tools.utils import qt_app_context
from qtpy import QtWidgets
from version_control.ui.login_window import LoginWindow

from .version import __version__

VERSION_CONTROL_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class LoginError(Exception):
    pass


class VersionControlAddon(AYONAddon, IHostAddon, ITrayService, IPluginPaths):
    webserver = None
    host_name = 'version_control'
    active_version_control_system = None

    @property
    def name(self) -> str:
        return "version_control"

    @property
    def label(self) -> str:
        if self.active_version_control_system:
            return f"Version Control: {self.active_version_control_system.title()}"
        return "Version Control"

    @property
    def version(self) -> str:
        return __version__

    def initialize(self, settings: dict) -> None:
        assert self.name in settings, (
            "{} not found in settings - make sure they are defined in the defaults".format(
                self.name
            )
        )

        vc_settings = settings[self.name]
        if not vc_settings["enabled"]:
            self.enabled = False
            return

        valid_hosts = vc_settings["enabled_hosts"]
        current_host = get_current_host_name()
        self.log.debug(current_host)

        enabled = vc_settings["enabled"]
        if not current_host or len(valid_hosts) == 0:
            self.enabled = enabled
        else:
            if current_host not in valid_hosts:
                self.log.debug("Version Control Disabled for %s", current_host)
                self.enabled = False

        configured_workspaces = vc_settings["workspace_settings"]
        active_version_control_system = None
        if any(
            [
                x["active_version_control_system"] == "perforce"
                for x in configured_workspaces
            ]
        ):
            active_version_control_system = "perforce"

        if active_version_control_system:
            self.active_version_control_system = active_version_control_system
            self.set_service_running_icon() if enabled else self.set_service_failed_icon()

    def get_global_environments(self):
        # return {"ACTIVE_VERSION_CONTROL_SYSTEM": self.active_version_control_system}
        return {}

    def get_connection_info(
        self, project_name, project_settings=None, configured_workspace=None
    ) -> dict:
        if not project_settings:
            project_settings = get_project_settings(project_name)

        current_workspace = self.get_workspace(
            project_settings, configured_workspace
        )
        current_workspace["workspace_dir"] = self._handle_workspace_directory(
            project_name, current_workspace
        )
        current_workspace = self._populate_settings(
            project_name, current_workspace
        )
        login = self.check_login(current_workspace["server"])
        current_workspace.update(login)
        current_workspace["host"] = list(
            filter(
                lambda x: x["name"] == current_workspace["server"],
                project_settings["version_control"]["servers"],
            )
        )[0]["host"]
        current_workspace["port"] = list(
            filter(
                lambda x: x["name"] == current_workspace["server"],
                project_settings["version_control"]["servers"],
            )
        )[0]["port"]

        return current_workspace

    def get_workspace(self, project_settings, configured_workspace=None):
        version_settings = project_settings["version_control"]
        workspaces = version_settings["workspace_settings"]
        current_host = get_current_host_name()

        self.log.debug(current_host)
        self.log.debug(workspaces)

        if current_host:
            workspaces = [
                workspace
                for workspace in workspaces
                if current_host in workspace["hosts"]
            ]
        if workspaces:
            if not configured_workspace:
                current_workspace = [
                    workspace
                    for workspace in workspaces
                    if workspace["primary"]
                ][0]
            else:
                current_workspace = [
                    workspace
                    for workspace in workspaces
                    if workspace["name"] == configured_workspace
                ][0]
        else:
            raise ValueError("No configured workspaces found.")

        return current_workspace

    def _merge_hierarchical_settings(self, settings_models, settings):
        for settings_model in settings_models:
            for field in settings_model:
                if field in settings and settings[field]:
                    continue
                settings[field] = settings_model[field]
        return settings

    def check_login(self, server_name):
        perforce_connection_config = (
            pathlib.Path(os.environ["APPDATA"]) / "perforce_servers.json"
        )
        self.log.debug(f"Perforce Config File: {perforce_connection_config}")
        if not perforce_connection_config.exists():
            with perforce_connection_config.open("w") as config_file:
                config_file.write(json.dumps([]))

        with perforce_connection_config.open("r") as config_file:
            config = json.load(config_file)

        self.log.debug(
            f"Config Items: {[item.get('server_name') for item in config]}"
        )
        if server_name not in [item.get("server_name") for item in config]:
            with qt_app_context():
                login_window = LoginWindow(server_name)
                result = login_window.exec_()

                if result == QtWidgets.QDialog.Accepted:
                    username, password = login_window.get_credentials()

                    config.append(
                        {
                            "server_name": server_name,
                            "username": username,
                            "password": password,
                        }
                    )

                    with perforce_connection_config.open("w") as config_file:
                        json.dump(config, config_file, indent=4)

                    return {
                        "server_name": server_name,
                        "username": username,
                        "password": password,
                    }

                else:
                    self.log.info("Login was cancelled")
                    return {}
        else:
            # If credentials are already available, use them
            return list(
                filter(lambda x: x["server_name"] == server_name, config)
            )[0]

    def _populate_settings(self, project_name, settings):
        import socket

        from ayon_core.pipeline.anatomy import Anatomy
        from ayon_core.pipeline.template_data import (
            get_template_data_with_names,
        )

        anatomy = Anatomy(project_name=project_name)
        template_data = get_template_data_with_names(project_name)
        template_data["computername"] = socket.gethostname()
        template_data["root"] = anatomy.roots
        template_data.update(anatomy.roots)

        formated_dict = {}
        for key, value in settings.items():
            if isinstance(value, str):
                formated_dict[key] = value.format(**template_data)
            else:
                formated_dict[key] = value
        return formated_dict

    def _handle_workspace_directory(self, project_name, workspace_settings):
        from ayon_core.pipeline.anatomy import Anatomy

        anatomy = Anatomy(project_name=project_name)
        workspace_dir = str(
            anatomy.roots[workspace_settings["workspace_root"]]
        )
        self.log.debug(workspace_dir)
        create_dirs = workspace_settings.get("create_dirs", False)

        if create_dirs:
            os.makedirs(workspace_dir, exist_ok=True)
        return os.path.normpath(workspace_dir)

    def workspace_exists(self, conn_info):
        from version_control.rest.perforce.rest_stub import PerforceRestStub

        PerforceRestStub.login(
            host=conn_info["host"],
            port=conn_info["port"],
            username=conn_info["username"],
            password=conn_info["password"],
            workspace_dir=conn_info["workspace_dir"],
            workspace_name=conn_info["workspace_name"],
        )

        return PerforceRestStub.workspace_exists(
            conn_info["workspace_name"],
        )

    def create_workspace(self, conn_info):
        from version_control.rest.perforce.rest_stub import (
            PerforceRestStub,
        )

        self.log.debug(conn_info["username"])
        PerforceRestStub.login(
            host=conn_info["host"],
            port=conn_info["port"],
            username=conn_info["username"],
            password=conn_info["password"],
            workspace_dir=conn_info["workspace_dir"],
            workspace_name=conn_info["workspace_name"],
        )

        PerforceRestStub.create_workspace(
            conn_info["workspace_dir"],
            conn_info["workspace_name"],
            conn_info["stream"],
            conn_info["options"],
        )

    def sync_to_latest(self, conn_info):
        from version_control.rest.perforce.rest_stub import PerforceRestStub

        PerforceRestStub.login(
            host=conn_info["host"],
            port=conn_info["port"],
            username=conn_info["username"],
            password=conn_info["password"],
            workspace_dir=conn_info["workspace_dir"],
            workspace_name=conn_info["workspace_name"],
        )
        PerforceRestStub.sync_latest_version(conn_info["workspace_dir"])
        return

    def sync_to_version(self, conn_info, change_id):
        from version_control.rest.perforce.rest_stub import PerforceRestStub

        PerforceRestStub.login(
            host=conn_info["host"],
            port=conn_info["port"],
            username=conn_info["username"],
            password=conn_info["password"],
            workspace_dir=conn_info["workspace_dir"],
            workspace_name=conn_info["workspace_name"],
        )

        PerforceRestStub.sync_to_version(
            f"{conn_info['workspace_dir']}/...", change_id
        )
        return

    def tray_exit(self):
        if (
            self.enabled
            and self.webserver
            and self.webserver.server_is_running
        ):
            self.webserver.stop()

    def tray_init(self):
        return

    def tray_start(self):
        if self.enabled:
            from version_control.rest.communication_server import WebServer

            self.webserver = WebServer()
            self.webserver.start()

    def get_plugin_paths(self):
        return {}

    def get_create_plugin_paths(self, host_name):
        if host_name != "unreal":
            return []
        return ["{}/plugins/create/unreal".format(VERSION_CONTROL_ADDON_DIR)]

    def get_publish_plugin_paths(self, host_name):
        return [os.path.join(VERSION_CONTROL_ADDON_DIR, "plugins", "publish")]

    def get_launch_hook_paths(self, _app):
        """Implementation for applications launch hooks.

        Returns:
            (str): full absolute path to directory with hooks for the module
        """
        self.log.debug(__file__)
        self.log.debug(
            f"Version Control Addon Var: {VERSION_CONTROL_ADDON_DIR}"
        )
        self.log.debug(self.active_version_control_system)

        return os.path.join(
            VERSION_CONTROL_ADDON_DIR,
            "launch_hooks",
            self.active_version_control_system,
        )
