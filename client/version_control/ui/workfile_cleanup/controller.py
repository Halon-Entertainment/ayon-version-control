from ayon_core.tools.common_models.projects import ProjectsModel
from ayon_core.tools.publisher.control_qt import QtPublisherController


class ProjectsController(QtPublisherController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._projects_model = ProjectsModel(self)

    @property
    def host(self):
        return self._host

    def reset_hierarchy_cache(self):
        self._hierarchy_model.reset()

    def get_project_items(self, sender=None):
        return self._projects_model.get_project_items(sender)
