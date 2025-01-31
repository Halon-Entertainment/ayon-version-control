from ayon_core.addon import (
    AYONAddon,
    ITrayAction,
    click_wrap,
)

from ayon_core.lib.execute import run_detached_process
from ayon_core.lib import get_ayon_launcher_args
from .version import __version__

class VersionControlTray(AYONAddon, ITrayAction):
    label = "Verson Control"
    name = "versioncontroltray"
    version = __version__
    host_name = "version_control"

    def tray_init(self):
        return super().tray_init()

    def on_action_trigger(self):
        self.log.debug('Version Control Tiggered')

        return self.run_version_control()

    def run_version_control(self):
        self.log.debug('Running Version Control')
        args = get_ayon_launcher_args("addon", self.name, "launch")
        launch()
        #run_detached_process(args)

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
    from version_control.ui.projects_viewer.window import show
    show()

