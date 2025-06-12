import os.path
import copy
import shutil
import datetime
import pathlib

import pyblish.api

from ayon_core.lib import StringTemplate

from version_control.rest.perforce.rest_stub import PerforceRestStub


class IntegratePerforce(pyblish.api.InstancePlugin):
    """Integrate perforce items"""

    label = "Integrate Perforce items"
    order = pyblish.api.IntegratorOrder + 0.499
    targets = ["local"]

    families = ["version_control"]

    def process(self, instance):
        conn_info = instance.data.get("version_control", None)
        if not conn_info:
            raise ValueError("No version control data found.")
        version_template_key = conn_info.template_name
        if not version_template_key:
            raise RuntimeError(
                "Instance data missing 'version_control[template_name]'"
            )  # noqa

        if "_" in version_template_key:
            template_area, template_name = version_template_key.split("_")
        else:
            template_area = version_template_key
            template_name = "default"
        anatomy = instance.context.data["anatomy"]
        template = anatomy.templates_obj.templates[template_area][
            template_name
        ]  # noqa
        if not template:
            raise RuntimeError(
                "Anatomy is missing configuration for '{}'".format(
                    version_template_key
                )
            )

        anatomy_data = copy.deepcopy(instance.data["anatomyData"])
        anatomy_data["root"] = anatomy.roots

        for _, repre in instance.data["published_representations"].items():
            anatomy_data["ext"] = repre["anatomy_data"]["ext"]
            asset = repre["anatomy_data"]["asset"]
            family = repre["anatomy_data"]["family"]
            representation = repre["anatomy_data"]["representation"]
            user = repre["anatomy_data"]["username"]
            version = repre["anatomy_data"]["version"]
            actual_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            comment = (
                f"{asset} - {family} - {representation} "
                f"- version: {version} submitted by {user} at {actual_time}"
            )

            for source_path, version_control_path in repre["transfers"]:
                is_on_server = PerforceRestStub.exists_on_server(
                    version_control_path
                )
                if is_on_server:
                    if PerforceRestStub.is_checkouted(version_control_path):
                        raise RuntimeError(
                            "{} is checkouted by someone already, "
                            "cannot commit right now.".format(
                                version_control_path
                            )
                        )
                    if not PerforceRestStub.checkout(
                        version_control_path, comment
                    ):
                        raise ValueError(
                            "File {} not checkouted".format(
                                version_control_path
                            )
                        )

                self.log.debug(f"{source_path} -- {version_control_path}")
                if (
                    pathlib.Path(source_path)
                    != pathlib.Path(version_control_path)
                    and not pathlib.Path(version_control_path).exists()
                ):
                    shutil.copy(source_path, version_control_path)
                if not is_on_server:
                    if not PerforceRestStub.add(version_control_path, comment):
                        raise ValueError(
                            "File {} not added to changelist".format(
                                version_control_path
                            )
                        )

            if not PerforceRestStub.submit_change_list(comment):
                raise ValueError("Changelist not submitted")
