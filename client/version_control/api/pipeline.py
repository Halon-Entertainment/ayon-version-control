from ayon_core.host.host import HostBase
import os


class VersionControlHost(HostBase):
    @property
    def name(self):
        return "trayversioncontrol"

    def install(self):
        os.environ["AYON_HOST_NAME"] = self.name
