import os
import pathlib
import typing

from ayon_core.addon import AYONAddon, IPluginPaths, ITrayService
from ayon_core.pipeline.context_tools import get_current_host_name

from .version import __version__

VERSION_CONTROL_ADDON_DIR = pathlib.Path(__file__).parent


class LoginError(Exception):
    pass


class VersionControlAddon(AYONAddon, ITrayService, IPluginPaths):
    webserver = None
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
            (
                self.set_service_running_icon()
                if enabled
                else self.set_service_failed_icon()
            )

    def get_global_environments(self) -> typing.Dict:
        if self.active_version_control_system:
            return {
                "ACTIVE_VERSION_CONTROL_SYSTEM": self.active_version_control_system
            }
        return {}

    def _merge_hierarchical_settings(
        self, settings_models: typing.Dict, settings: typing.Dict
    ) -> typing.Dict:
        for settings_model in settings_models:
            for field in settings_model:
                if field in settings and settings[field]:
                    continue
                settings[field] = settings_model[field]
        return settings

    def tray_exit(self) -> None:
        if (
            self.enabled
            and self.webserver
            and self.webserver.server_is_running
        ):
            self.webserver.stop()

    def tray_init(self) -> None:
        return

    def tray_start(self) -> None:
        if self.enabled:
            from version_control.rest.communication_server import WebServer

            self.webserver = WebServer()
            self.webserver.start()

    def get_plugin_paths(self) -> typing.Dict:
        return {}

    def get_create_plugin_paths(self, host_name) -> typing.List[str]:
        if host_name != "unreal":
            return []
        return [
            (
                VERSION_CONTROL_ADDON_DIR / f"plugins/create/{host_name}"
            ).as_posix()
        ]

    def get_publish_plugin_paths(self, host_name: str) -> typing.List[str]:
        return [(VERSION_CONTROL_ADDON_DIR / "plugins/publish").as_posix()]

    def get_launch_hook_paths(self, _app) -> typing.Union[str, None]:
        """Implementation for applications launch hooks.

        Returns:
            (str): full absolute path to directory with hooks for the module
        """
        self.log.debug(__file__)
        self.log.debug(
            f"Version Control Addon Var: {VERSION_CONTROL_ADDON_DIR}"
        )
        self.log.debug(self.active_version_control_system)

        if self.active_version_control_system:
            return (
                VERSION_CONTROL_ADDON_DIR
                / "launch_hooks"
                / self.active_version_control_system
            ).as_posix()
