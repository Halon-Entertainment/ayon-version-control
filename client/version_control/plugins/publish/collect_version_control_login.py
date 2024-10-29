"""
Requires:
    none

Provides:
    context.data     -> "version_control" ({})
"""

import pyblish.api

from ayon_core.addon import AddonsManager

from version_control.rest.perforce.rest_stub import PerforceRestStub


class CollectVersionControlLogin(pyblish.api.ContextPlugin):
    """Collect connection info and login with it."""

    label = "Collect Version Control Connection Info"
    order = pyblish.api.CollectorOrder + 0.4990
    targets = ["local"]


    def process(self, context):
        version_control = AddonsManager().get("version_control")
        if not version_control or not version_control.enabled:
            self.log.info("No version control enabled")
            return

        project_name = context.data["projectName"]
        project_setting = context.data["project_settings"]
        if not project_setting['version_control']['publish']['CollectVersionControl']['enabled']:
            self.log.info("Version control addon disabled.")
            return
        conn_info = version_control.get_connection_info(project_name,
                                                        project_setting)

        context.data["version_control"] = conn_info
        self.log.debug(f"Host: {conn_info['host']}")

        PerforceRestStub.login(conn_info["host"], conn_info["port"],
                               conn_info["username"],
                               conn_info["password"],
                               conn_info["workspace_dir"],
                               conn_info["workspace_name"])

        stream = PerforceRestStub.get_stream(conn_info["workspace_dir"])
        context.data["version_control"]["stream"] = stream
