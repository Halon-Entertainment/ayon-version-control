"""
Requires:
    none

Provides:
    context.data     -> "version_control" ({})
"""

import pyblish.api

from ayon_core.addon import AddonsManager

from ayon_core.pipeline.context_tools import get_current_host_name
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.api.perforce import get_connection_info



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

        host = get_current_host_name()
        conn_info = get_connection_info(project_name, host=host)

        conn_info.workspace_server
        conn_info.workspace_info
        context.data["version_control"] = conn_info
        self.log.debug(f"Host: {conn_info.workspace_server.host}")

        PerforceRestStub.login(conn_info.workspace_server.host,
                               conn_info.workspace_server.port,
                               conn_info.workspace_server.username,
                               conn_info.workspace_server.password,
                               conn_info.workspace_info.workspace_dir,
                               conn_info.workspace_info.workspace_name)
