import os.path
import copy
import shutil
import datetime

import pyblish.api

from openpype.lib import StringTemplate

from version_control.backends.perforce.api.rest_stub import (
    PerforceRestStub
)


class IntegratePerforce(pyblish.api.InstancePlugin):
    """Integrate perforce items
    """

    label = "Integrate Perforce items"
    order = pyblish.api.IntegratorOrder + 0.499

    families = ["version_control"]

    def process(self, instance):
        version_template_key = (
            instance.data.get("version_control_template_name"))
        if not version_template_key:
            raise RuntimeError("Instance data missing 'version_control_template_name'")   # noqa

        anatomy = instance.context.data["anatomy"]
        template = anatomy.templates_obj.templates[version_template_key]["path"]  # noqa
        if not template:
            raise RuntimeError("Anatomy is missing configuration for '{}'".
                               format(version_template_key))

        anatomy_data = copy.deepcopy(instance.data["anatomyData"])
        anatomy_data["root"] = instance.data["version_control_roots"]
        # anatomy_data["output"] = ''
        # anatomy_data["frame"] = ''
        # anatomy_data["udim"] = ''

        for repre in instance.data["representations"]:
            anatomy_data["ext"] = repre["ext"]

            version_control_path = StringTemplate.format_template(
                template, anatomy_data
            )

            source_path = repre["published_path"]

            dirname = os.path.dirname(version_control_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            file_info = PerforceRestStub.exists_on_server(version_control_path)
            actual_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            comment = os.path.basename(version_control_path) + actual_time
            if file_info:
                if PerforceRestStub.is_checkouted(version_control_path):
                    raise RuntimeError("{} is checkouted by someone already, "
                                       "cannot commit right now.".format(
                                        version_control_path))
                if not PerforceRestStub.checkout(version_control_path,
                                                 comment):
                    raise ValueError("File {} not checkouted".
                                     format(version_control_path))

            shutil.copy(source_path, version_control_path)
            if not file_info:
                if not PerforceRestStub.add(version_control_path,
                                            comment):
                    raise ValueError("File {} not added to changelist".
                                     format(version_control_path))

            if not PerforceRestStub.submit_change_list(comment):
                raise ValueError("Changelist not submitted")
