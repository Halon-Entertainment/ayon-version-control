import qtawesome
from ayon_core.tools.utils.lib import get_qt_icon
from qtpy import QtCore, QtGui, QtWidgets
from ayon_core.lib.log import Logger

from version_control.ui.workspace_wizzard.models import (
    STREAM_ROLE, WORKSPACE_DIR_ROLE, WORKSPACE_NAME_ROLE, WORKSPACE_PRIMARY_ROLE,
    WORKSPACE_ROOT_ROLE, WORKSPACE_SERVER_ROLE, WORKSPACE_STATUS_ROLE)

log = Logger.get_logger(__name__)

class WorkspaceIconDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_font_size = 14
        self.details_font_size = 10

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        if not painter:
            return

        workspace_label = index.data(QtCore.Qt.DisplayRole)
        workspace_name = index.data(WORKSPACE_NAME_ROLE)
        workspace_server = index.data(WORKSPACE_SERVER_ROLE)
        workspace_stream = index.data(STREAM_ROLE)
        workspace_dir = index.data(WORKSPACE_DIR_ROLE)
        workspace_status = index.data(WORKSPACE_STATUS_ROLE)

        # painter.drawPixmap(icon_rect, icon)
        self._draw_background(painter, option)
        log.debug(f"Workspace Dir {workspace_dir}")
        self._draw_workspace_name(workspace_label, workspace_name, painter, option)
        self._draw_details(
            workspace_server, workspace_stream, workspace_dir, painter, option
        )

        painter.save()
        painter.restore()

    def _draw_background(self, painter: QtGui.QPainter, option) -> None:
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, QtGui.QColor("#5394b7"))

    def _draw_workspace_name(
        self,
        workspace_label: str,
        workspace_name: str,
        painter: QtGui.QPainter,
        option,
    ) -> None:
        font = painter.font()
        font.setPointSize(self.title_font_size)
        painter.setFont(font)
        text_rect = QtCore.QRect(
            option.rect.x(),
            0,
            option.rect.width(),
            self.title_font_size + 10,
        )
        painter.save()
        painter.drawText(
            text_rect,
            QtCore.Qt.AlignmentFlag.AlignLeft,
            f"{workspace_label} - {workspace_name}",
        )
        painter.restore()

    def _draw_details(
        self,
        workspace_server: str,
        workspace_stream: str,
        workspace_root: str,
        painter: QtGui.QPainter,
        option,
    ) -> None:
        font = painter.font()
        font.setPointSize(self.details_font_size)
        painter.setFont(font)

        font_height = painter.fontMetrics().height()
        text_rect = QtCore.QRect(
            option.rect.x(),
            self.title_font_size + 10,
            option.rect.width(),
            font_height,
        )
        painter.save()
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignLeft, workspace_root)
        painter.restore()

    def sizeHint(self, option, index):
        font_metrics = QtGui.QFontMetrics(option.font)
        decoration_width = 16
        return QtCore.QSize(
            decoration_width + font_metrics.horizontalAdvance(index.data()),
            option.decorationSize.height() + 50,
        )
