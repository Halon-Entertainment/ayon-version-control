import typing

from qtpy import QtCore, QtGui, QtWidgets

from ayon_core.lib.log import Logger
from version_control.ui.user_submit_window.models import (
    QtPerforceFileInfoModel,
)

log = Logger.get_logger(__name__)

class PerforceWorkfilesDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: typing.Optional[QtGui.QPainter],
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        """Paint the item.

        Args:
            painter (QtGui.QPainter | None): The painter object.
            option (QtWidgets.QStyleOptionViewItem): Style options for this delegate item.
            index (QtCore.QModelIndex): Model index that points to this item in the model.

        Raises:
            ValueError: If no painter is provided.
        """
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

    def _draw_background(self) -> None:
        """Draw the background of the item."""
        if self._option.state & QtWidgets.QStyle.State_Selected: # pyright: ignore[]
            self._painter.fillRect(self._option.rect, QtGui.QColor("#5394b7")) # pyright: ignore[]

    def _draw_file_name(self, file_name: str):
        """Draw the file name.

        Args:
            file_name (str): The file name to draw.
        
        Raises:
            ValueError: If no painter is provided.
        """
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

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        """Return the preferred size for the item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex): Model index.

        Returns:
            QtCore.QSize: Preferred size of the item.
        """
        font_metrics = QtGui.QFontMetrics(option.font)
        decoration_width = 16
        return QtCore.QSize(
            decoration_width + font_metrics.horizontalAdvance(index.data()),
            option.decorationSize.height(),
        )

