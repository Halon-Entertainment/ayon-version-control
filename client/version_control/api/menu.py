from functools import partial

from ayon_core.lib.log import Logger
import pymel.all as pymel

from version_control.ui.user_submit_window import main

log = Logger.get_logger(__name__)

MENU_NAME = "version_control"

def add_menu() -> None:
    maya_window = pymel.melGlobals['gMainWindow']

    if pymel.menu(MENU_NAME, exists=True):
        return

    pymel.menu(
        MENU_NAME,
        label="Perforce",
        tearOff=True,
        parent=maya_window,
    )

    pymel.menuItem(
        "user_submit",
        label="Submit Workfiles...",
        parent=MENU_NAME,
        command=partial(main),
    )
