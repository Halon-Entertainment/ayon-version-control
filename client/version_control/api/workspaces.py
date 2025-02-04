import typing

from version_control.api.models import ConnectionInfo

def list_workspaces(settings: typing.Dict) -> typing.List[typing.Tuple]:
    return list(
        map(lambda x: (x["name"], x["server"]), settings["workspace_settings"])
    )

