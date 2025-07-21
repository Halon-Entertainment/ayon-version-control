import pathlib
import traceback
import typing
from ayon_core.addon import (
    AYONAddon,
    ITrayAction,
    click_wrap,
)
import pathlib

from ayon_core.addon import AddonsManager
from ayon_core.lib.execute import run_detached_process
from ayon_core.lib import get_ayon_launcher_args
from ayon_core.style import load_stylesheet
from ayon_core.tools.common_models.projects import ProjectsModel
from ayon_core.tools.publisher.control_qt import QtPublisherController
from ayon_core.tools.utils.projects_widget import ProjectsQtModel
from version_control.api.clean_workfiles import (
    get_all_workfiles,
    remove_workfiles,
    versions_to_remove,
)
from version_control.ui.workfile_cleanup.window import (
    CleanUpWorker,
    CleanWorkfilesConfirmation,
    CleanupSignals,
    ProjectSelectionDialog,
    SummaryDialog,
)
from .version import __version__
from qtpy import QtCore, QtWidgets


class VersionControlTray(AYONAddon, ITrayAction):
    @property
    def label(self):
        return "Version Control"

    @property
    def name(self):
        return "version-control-tray"

    @property
    def version(self):
        return __version__

    def tray_menu(self, tray_menu: QtWidgets.QMenu) -> None:
        version_control_menu = QtWidgets.QMenu("Version Control...")

        style = load_stylesheet()
        if style:
            custom_style = """
            #DeleteWorkfilesButton  {
                padding: 6px 25px 6px 10px;
                border: 1px solid #555555;
                background: #720700;
            }
            #DeleteWorkfilesButton::hover  {
                padding: 6px 25px 6px 10px;
                border: 1px solid #555555;
                background: red;
            }
            """
            style = style + custom_style
            version_control_menu.setStyleSheet(style)

        wizard_action = QtWidgets.QAction(
            text="Workspace Wizard", parent=version_control_menu
        )
        wizard_action.triggered.connect(self.run_version_control)
        version_control_menu.addSeparator()

        delete_workfiles_label = QtWidgets.QLabel("Cleanup Workfiles")
        delete_workfiles_label.setObjectName("DeleteWorkfilesButton")

        delete_workfiles_action = QtWidgets.QWidgetAction(version_control_menu)
        delete_workfiles_action.setDefaultWidget(delete_workfiles_label)
        delete_workfiles_action.triggered.connect(self.cleanup_workfiles)

        version_control_menu.addActions(
            [wizard_action, delete_workfiles_action]
        )
        self.action_items = [wizard_action, delete_workfiles_action]
        tray_menu.addMenu(version_control_menu)

    def tray_init(self):
        return super().tray_init()

    def on_action_trigger(self) -> None:
        self.log.debug("Version Control Tiggered")

        return self.run_version_control()

    def run_version_control(self) -> None:
        self.log.debug("Running Version Control")
        try:
            launch()
        except Exception:
            self.log.error(traceback.format_exc())

    def cleanup_workfiles(self):
        project_selection = ProjectSelectionDialog()
        result = project_selection.exec()
        if result != QtWidgets.QDialog.Accepted: # pyright: ignore[]
            return

        self.project = project_selection.selected_project

        if not self.project:
            raise ValueError("No Project Provided")

        confimation = CleanWorkfilesConfirmation(self.project)
        self.signals = CleanupSignals()

        self.signals.started.connect(confimation.progress_bar.setMaximum)
        self.signals.updated.connect(confimation.progress_bar.setValue)
        self.signals.finished.connect(confimation.accept)

        result = confimation.exec()
        self.log.debug(f"Result {result}")

        if result != QtWidgets.QDialog.Accepted:  # pyright: ignore[]
            return


    def cli(self, click_group):
        click_group.add_command(cli_main.to_click_obj())


@click_wrap.group(
    VersionControlTray.name, help="Version Control related commands."
)
def cli_main():
    pass


# @cli_main.command()
def launch():
    """Launch TrayPublish tool UI."""
    from version_control.ui.workspace_wizard import main

    manager = AddonsManager()
    main(manager)
