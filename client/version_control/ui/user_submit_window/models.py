import typing

from qtpy import QtCore, QtGui

from version_control.api.models import PerforceFileInfo


class QtPerforceFileInfoModel(QtGui.QStandardItemModel):
    FILE_PATH_ROLE = QtCore.Qt.UserRole + 100  # pyright: ignore[]
    DEPOT_PATH_ROLE = QtCore.Qt.UserRole + 101  # pyright: ignore[]
    REVISION_NUMBER_ROLE = QtCore.Qt.UserRole + 102  # pyright: ignore[]
    WORKSPACE_PATH_ROLE = QtCore.Qt.UserRole + 103  # pyright: ignore[]
    STATUS_ROLE = QtCore.Qt.UserRole + 104  # pyright: ignore[]
    CHANGE_LIST_NUMBER_ROLE = QtCore.Qt.UserRole + 105  # pyright: ignore[]
    CONNECTION_INFO_ROLE = QtCore.Qt.UserRole + 106  # pyright: ignore[]
    EXISTS_ROLE = QtCore.Qt.UserRole + 107  # pyright: ignore[]

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._source_models = None

    def add_models(self, models: typing.List[PerforceFileInfo]):
        self._source_models = models
        self._fill_items()

    def _fill_items(self) -> None:
        root_item = self.invisibleRootItem()

        if not root_item:
            raise RuntimeError("Root item unavailible")

        items = []
        if not self._source_models:
            raise ValueError(
                ("Unable to set model data self._source_models is not set.")
            )
        for model in self._source_models:
            perforce_file_item = QtGui.QStandardItem()
            items.append(perforce_file_item)

            perforce_file_item.setData(
                model.file_name,
                QtCore.Qt.DisplayRole,  # pyright: ignore[]
            )
            perforce_file_item.setData(model.file_path, self.FILE_PATH_ROLE)
            perforce_file_item.setData(model.depot_path, self.DEPOT_PATH_ROLE)
            perforce_file_item.setData(model.revision_number, self.REVISION_NUMBER_ROLE)
            perforce_file_item.setData(model.workspace_path, self.WORKSPACE_PATH_ROLE)
            perforce_file_item.setData(model.status, self.WORKSPACE_PATH_ROLE)
            perforce_file_item.setData(
                model.changelist_number, self.CHANGE_LIST_NUMBER_ROLE
            )
            perforce_file_item.setData(model.connection_info, self.CONNECTION_INFO_ROLE)
            perforce_file_item.setData(model.exists, self.EXISTS_ROLE)

        root_item.appendRows(items)
