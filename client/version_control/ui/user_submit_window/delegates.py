import typing

from qtpy import QtCore, QtGui, QtWidgets

from ayon_core.lib.log import Logger
from version_control.ui.user_submit_window.models import (
    QtPerforceFileInfoModel,
)

log = Logger.get_logger(__name__)

class PerforceWorkfilesDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: typing.Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: typing.Optional[QtGui.QPainter],
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        file_name = index.data(QtCore.Qt.DisplayRole)  # pyright: ignore[]
        status = index.data(QtPerforceFileInfoModel.STATUS_ROLE)
        file_path = index.data(QtPerforceFileInfoModel.FILE_PATH_ROLE)
        perforce_exists = index.data(QtPerforceFileInfoModel.EXISTS_ROLE)
        log.debug(f"File Name: {file_name} - {status} - {file_path} - {perforce_exists}")

        self._painter = painter
        self._option = option
        self._index = index

        if not self._painter:
            raise ValueError(
                f"{self.__class__.__name__} cannot work with out a painter."
            )
        self._draw_background()
        self._draw_file_name(file_name)
        self._painter.save()
        self._painter.restore()

    def _draw_background(
        self,
    ) -> None:
        if self._option.state & QtWidgets.QStyle.State_Selected:
            self._painter.fillRect(self._option.rect, QtGui.QColor("#5394b7"))

    def _draw_file_name(self, file_name: str):
        if not self._painter:
            raise ValueError(
                f"{self.__class__.__name__} cannot work with out a painter."
            )

        text_rect = QtCore.QRect(
            self._option.rect.x(),
            self._option.rect.y(),
            self._option.rect.width(),
            self._option.rect.height(),
        )

        self._painter.drawText(
            text_rect,
            QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter,
            file_name,
        )

    def sizeHint(self, option, index):
        font_metrics = QtGui.QFontMetrics(option.font)
        decoration_width = 16
        return QtCore.QSize(
            decoration_width + font_metrics.horizontalAdvance(index.data()),
            option.decorationSize.height(),
        )
