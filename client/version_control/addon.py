import os
import json

from ayon_core.addon import AYONAddon, ITrayService, IPluginPaths
from ayon_core.settings import get_project_settings 
from ayon_core.tools.utils import qt_app_context
from ayon_core.lib  import get_local_site_id
# import ayon_api

from ayon_api import (
    post,
    get
)

from qtpy import QtWidgets

from version_control.changes_viewer import LoginWindow

_typing = False
if _typing:
    from typing import Any
del _typing

from .version import __version__


VERSION_CONTROL_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class VersionControlAddon(AYONAddon, ITrayService, IPluginPaths):
    
    label = "Version Control"
    name = "version_control"
    version = __version__
    
    # _icon_name = "mdi.jira"
    # _icon_scale = 1.3
    webserver = None
    active_version_control_system = None

    # Properties:
    @property
    def name(self):
        # type: () -> str
        return "version_control"

    @property
    def label(self):
        # type: () -> str
        return f"Version Control: {self.active_version_control_system.title()}"

    # Public Methods:
    def initialize(self, settings):
        # type: (dict[str, Any]) -> None
        assert self.name in settings, (
            "{} not found in settings - make sure they are defined in the defaults".format(self.name)
        )
        vc_settings = settings[self.name]  # type: dict[str, Any]
        enabled = vc_settings["enabled"]  # type: bool
        active_version_control_system = vc_settings["active_version_control_system"]  # type: str
        self.active_version_control_system = active_version_control_system
        self.set_service_running_icon() if enabled else self.set_service_failed_icon()
        valid_hosts = vc_settings['enabled_hosts']
        current_host = get_current_host_name()
        self.log.debug(current_host)
        if not current_host or len(valid_hosts) == 0:
            self.enabled = enabled
        else:
            if current_host not in valid_hosts:
                self.log.debug('Version Control Disabled for %s', current_host)
                self.enabled = False

        # if enabled:
        #     from .backends.perforce.communication_server import WebServer
        #     self.webserver = WebServer()

    def get_global_environments(self):
        # return {"ACTIVE_VERSION_CONTROL_SYSTEM": self.active_version_control_system}
        return {}

    def get_connection_info(self, project_name, project_settings=None):
        if not project_settings:
            project_settings = get_project_settings(project_name)

        version_settings = project_settings["version_control"]
        local_setting = version_settings["local_setting"]
        settings = {
            "host": version_settings["host_name"],
            "port": version_settings["port"],
            "username": local_setting["username"],
            "password": local_setting["password"],
        }

        workspace_settings = self._merge_hierarchical_settings([
            local_setting,
            version_settings['workspace_settings'],
        ], settings)

        workspace_settings["workspace_dir"] = self._handle_workspace_directory(project_name, workspace_settings)
        workspace_settings = self._populate_settings(project_name, workspace_settings)

        return workspace_settings

    def check_login(self, username, project_name):
        with qt_app_context():
            login_window = LoginWindow(username)
            result = login_window.exec_()

            if result == QtWidgets.QDialog.Accepted:
                username, password = login_window.get_credentials()
                self.log.info(f"Username: {username}, Password: {password}")

                settings = get_project_settings(project_name)
                local_setting = settings["version_control"]["local_setting"]
                local_setting["username"] = username
                local_setting["password"] = password

                # payload_data = {
                #     "project_name": project_name,
                #     "addon_version": self.version,
                #     "site_data": {
                #         "local_setting": local_setting
                #     },
                #     "site_id": get_local_site_id(),
                #     "user_name": os.environ.get("AYON_USERNAME")
                # }
                #
                # response = post(
                #     f"/addons/version_control/{self.version}/set-site-data",
                #     payload=payload_data
                # )

                url =  f"/addons/version_control/{self.version}/{get_local_site_id()}/{project_name}/{username}/{password}/{self.version}/set-credentials"

                print(url)

                response = get(
                   url,
                )

                print(str(response))

                return username, password
            else:
                self.log.info("Login was cancelled")
                return None, None

    def _populate_settings(self, project_name, settings):
        from ayon_core.pipeline.template_data import get_template_data_with_names
        from ayon_core.pipeline.anatomy import Anatomy
        import socket

        anatomy = Anatomy(project_name=project_name)
        template_data = get_template_data_with_names(project_name)
        template_data['computername'] = socket.gethostname()
        template_data['root'] = anatomy.roots
        template_data.update(anatomy.roots)

        formated_dict = {}
        for key, value in settings.items():
            if isinstance(value, str):
                formated_dict[key] = value.format(**template_data)
            else:
                formated_dict[key] = value
        return formated_dict

    def _merge_hierarchical_settings(self, settings_models, settings):
        for settings_model in settings_models:
            for field in settings_model:
                if field in settings and settings[field]:
                    continue
                settings[field] = settings_model[field]

        return settings

    def _handle_workspace_directory(self, project_name, workspace_settings):
        from ayon_core.pipeline.anatomy import Anatomy
        anatomy = Anatomy(project_name=project_name)
        workspace_dir = str(anatomy.roots[workspace_settings['workspace_root']])
        create_dirs = workspace_settings.get('create_dirs', False)

        if create_dirs:
            os.makedirs(workspace_dir, exist_ok=True)
        return os.path.normpath(workspace_dir)

    def workspace_exists(self, conn_info):
        from version_control.rest.perforce.rest_stub import \
            PerforceRestStub

        PerforceRestStub.login(host=conn_info["host"],
                               port=conn_info["port"],
                               username=conn_info["username"],
                               password=conn_info["password"],
                               workspace_dir=conn_info["workspace_dir"],
                               workspace_name=conn_info["workspace_name"])

        return PerforceRestStub.workspace_exists(
            conn_info['workspace_name'],
        )


    def create_workspace(self, conn_info):
        from version_control.rest.perforce.rest_stub import \
            PerforceRestStub
        self.log.debug(conn_info['username'])
        PerforceRestStub.login(host=conn_info["host"],
                               port=conn_info["port"],
                               username=conn_info["username"],
                               password=conn_info["password"],
                               workspace_dir=conn_info['workspace_dir'],
                               workspace_name=conn_info["workspace_name"])

        PerforceRestStub.create_workspace(
            conn_info['workspace_dir'],
            conn_info['workspace_name'],
            conn_info['stream'],
            conn_info['options']
        )

    def sync_to_latest(self, conn_info):
        from version_control.rest.perforce.rest_stub import \
            PerforceRestStub

        PerforceRestStub.login(host=conn_info["host"],
                               port=conn_info["port"],
                               username=conn_info["username"],
                               password=conn_info["password"],
                               workspace_dir=conn_info["workspace_dir"],
                               workspace_name=conn_info["workspace_name"])
        PerforceRestStub.sync_latest_version(conn_info["workspace_dir"])
        return

    def sync_to_version(self, conn_info, change_id):
        from version_control.rest.perforce.rest_stub import \
            PerforceRestStub

        PerforceRestStub.login(host=conn_info["host"],
                               port=conn_info["port"],
                               username=conn_info["username"],
                               password=conn_info["password"],
                               workspace_dir=conn_info["workspace_dir"],
                               workspace_name=conn_info["workspace_name"]
                               )

        PerforceRestStub.sync_to_version(
            f"{conn_info['workspace_dir']}/...", change_id)
        return

    def tray_exit(self):
        if self.enabled and \
                self.webserver and self.webserver.server_is_running:
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
        return [os.path.join(VERSION_CONTROL_ADDON_DIR,
                             "plugins", "publish")]

    def get_launch_hook_paths(self, _app):
        """Implementation for applications launch hooks.

        Returns:
            (str): full absolute path to directory with hooks for the module
        """

        return os.path.join(VERSION_CONTROL_ADDON_DIR, "launch_hooks",
                            self.active_version_control_system)
