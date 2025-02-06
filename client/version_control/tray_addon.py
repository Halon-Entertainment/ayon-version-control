import traceback
from ayon_core.addon import (
    AYONAddon,
    ITrayAction,
    click_wrap,
)

from ayon_core.addon import AddonsManager
from ayon_core.lib.execute import run_detached_process
from ayon_core.lib import get_ayon_launcher_args
from .version import __version__

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

    def tray_init(self):
        return super().tray_init()

    def on_action_trigger(self) -> None:
        self.log.debug('Version Control Tiggered')

        return self.run_version_control()

    def run_version_control(self) -> None:
        self.log.debug('Running Version Control')
        try:
            launch()
        # run_detached_process(args)
        except Exception:
            self.log.error(traceback.format_exc())


    # def cli(self, click_group):
    #     click_group.add_command(cli_main.to_click_obj())


@click_wrap.group(
    VersionControlTray.name,
    help="Version Control related commands.")
def cli_main():
    pass


# @cli_main.command()
def launch():
    """Launch TrayPublish tool UI."""
    from version_control.ui.workspace_wizard import main
    manager = AddonsManager()
    main(manager)

