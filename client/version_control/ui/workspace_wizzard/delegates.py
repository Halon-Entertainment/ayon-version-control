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

        # Draw a checkbox if the workspace is primary
        if workspace_primary:
            check_box_margin = 6
            check_box_size = option.decorationSize.width()
            check_box_x_pos = option.rect.width() + check_box_margin
            check_box_y_pos = (
                option.rect.y()
                + (option.decorationSize.height() - check_box_size) / 2
            )

            icon = get_qt_icon({"type": "awesome-font", "color": 'green',
                                "name": 'check'})
            if workspace_primary:
                checkbox_icon = icon
            else:
                checkbox_icon = None

        if checkbox_icon:
            checkbox_icon.paint(
                painter,
                QtCore.QRect(
                    check_box_x_pos,
                    check_box_y_pos,
                    check_box_size,
                    check_box_size,
                ),
            )

        # Draw the rest of the text and data
        paint_text_format = option.displayAlignment
        painter.drawText(
            option.rect.adjusted(
                check_box_margin + option.decorationSize.width(),
                0,
                -10,
                0,
            ),
            paint_text_format,
            f"{workspace_server} \n {workspace_name} \n {workspace_stream} \n {workspace_root}",
        )

    def sizeHint(self, option, index):
        font_metrics = QtGui.QFontMetrics(option.font)
        decoration_width = 16
        return QtCore.QSize(
            decoration_width + font_metrics.horizontalAdvance(index.data()),
            option.decorationSize.height() + 50,
        )
