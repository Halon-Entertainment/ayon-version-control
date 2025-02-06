from typing import Any

from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import CurrentUser
from .settings import VersionControlSettings, DEFAULT_VALUES
from ayon_server.lib.postgres import Postgres
import json
from nxtools import logging

class VersionControlAddon(BaseServerAddon):
    settings_model = VersionControlSettings

    def initialize(self):
        logging.error("initialized VC addon")

        self.add_endpoint(
            "/set-site-data",
            self.set_site_data,
            method="POST",
        )

    async def set_site_data(self, user: CurrentUser, request):
        logging.error("ENDPOINT HIT")

        # json_data = await request.json()
        # data = json.loads(json_data)
        # site_data = data.get("site_data")
        # user_name = data.get("user_name")
        # site_id = data.get("site_id")
        # addon_version = data.get("addon_version")
        # project_name = data.get("project_name")
        #
        # if not site_data or not project_name or not user_name or not site_id or not addon_version:
        #     return self.error_response("Missing required parameters")
        #
        # site_data_json = json.dumps(site_data)
        #
        # await Postgres.execute(
        #     f"""
        #     INSERT INTO project_{project_name}.project_site_settings
        #         (addon_name, addon_version, site_id, user_name, site_data)
        #     VALUES ($1, $2, $3, $4, $5)
        #     ON CONFLICT (site_id)
        #     DO UPDATE SET site_data = EXCLUDED.site_data
        #     """,
        #     "version_control",
        #     addon_version,
        #     site_id,
        #     user_name,
        #     site_data_json,
        # )
        #
        # return self.success_response("Site data updated")


    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)
