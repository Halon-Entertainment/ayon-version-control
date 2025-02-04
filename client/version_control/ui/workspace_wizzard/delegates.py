import qtawesome
from qtpy import QtCore, QtGui, QtWidgets

from ayon_core.tools.utils.lib import get_qt_icon
from version_control.ui.workspace_wizzard.models import (
    STREAM_ROLE,
    WORKSPACE_NAME_ROLE,
    WORKSPACE_PRIMARY_ROLE,
    WORKSPACE_ROOT_ROLE,
    WORKSPACE_SERVER_ROLE,
)


class WorkspaceIconDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        if not painter:
            return

        item_data = index.data(QtCore.Qt.DisplayRole)
        workspace_name = index.data(WORKSPACE_NAME_ROLE)
        workspace_primary = index.data(WORKSPACE_PRIMARY_ROLE)
        workspace_server = index.data(WORKSPACE_SERVER_ROLE)
        workspace_stream = index.data(STREAM_ROLE)
        workspace_root = index.data(WORKSPACE_ROOT_ROLE)

        font_height = painter.fontMetrics().height()
        text_rect = QtCore.QRect(
            option.rect.x(),
            option.rect.height() - font_height,
            option.rect.width(),
            font_height,
        )
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, QtGui.QColor("#D15C1E10"))

        # painter.drawPixmap(icon_rect, icon)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, workspace_name)
        painter.restore()

        # self._draw_background(painter, option)
        # self._draw_workspace_name(workspace_name, painter, option)


    def _draw_background(self, painter: QtGui.QPainter, option):
        painter.drawRect(
            option.rect.x(),
            option.rect.y(),
            option.rect.width() - 10,
            20,
        )


    def _draw_workspace_name(self, workspace_name, painter, option):

        paint_text_format = option.displayAlignment
        painter.drawText(
            option.rect.adjusted(
                option.decorationSize.width(),
                0,
                -10,
                0,
            ),
            paint_text_format,
            workspace_name
        )



    def sizeHint(self, option, index):
        font_metrics = QtGui.QFontMetrics(option.font)
        decoration_width = 16
        return QtCore.QSize(
            decoration_width + font_metrics.horizontalAdvance(index.data()),
            option.decorationSize.height() + 50,
        )
