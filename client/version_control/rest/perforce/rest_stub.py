import os
import typing

import requests
import six

if six.PY2:
    import pathlib2 as pathlib
else:
    import pathlib

_typing = False
if _typing:
    from typing import Any, Sequence
del _typing


class PerforceRestStub:
    @staticmethod
    def _wrap_call(command, **kwargs):
        webserver_url = os.environ.get("PERFORCE_WEBSERVER_URL")

        if not webserver_url:
            raise RuntimeError("Unknown url for Perforce")

        action_url = f"{webserver_url}/perforce/{command}"

        response = requests.post(action_url, json=kwargs)
        if not response.ok:
            raise RuntimeError(response.text)
        return response.json()

    @staticmethod
    def is_in_any_workspace(path):
        response = PerforceRestStub._wrap_call("is_in_any_workspace", path=path)
        return response

    @staticmethod
    def login(
        host: str,
        port: typing.Union[str, int],
        username: str,
        password: str,
        workspace_dir: typing.Optional[str] = None,
        workspace_name: typing.Optional[str] = None,
    ):
        if isinstance(port, int):
            port = str(port)

        response = PerforceRestStub._wrap_call(
            "login",
            host=host,
            port=port,
            username=username,
            password=password,
            workspace_dir=workspace_dir,
            workspace_name=workspace_name,
        )
        return response

    @staticmethod
    def add(path, comment=""):
        # type: (pathlib.Path | str, str) -> bool
        response = PerforceRestStub._wrap_call("add", path=path, comment=comment)
        return response

    @staticmethod
    def delete(path, comment=""):
        # type: (pathlib.Path | str, str) -> bool
        response = PerforceRestStub._wrap_call("delete", path=path, comment=comment)
        return response

    @staticmethod
    def workspace_exists(workspace):
        response = PerforceRestStub._wrap_call("workspace_exists", workspace=workspace)
        print(f"Workspace Exists Stub {response}")
        return response

    @staticmethod
    def create_workspace(workspace_root, workspace_name, stream, options):
        response = PerforceRestStub._wrap_call(
            "create_workspace",
            workspace_name=workspace_name,
            workspace_root=workspace_root,
            stream=stream,
            options=options,
        )

        return response

    @staticmethod
    def sync_latest_version(path):
        response = PerforceRestStub._wrap_call("sync_latest_version", path=path)
        return response

    @staticmethod
    def sync_to_version(path, version):
        response = PerforceRestStub._wrap_call(
            "sync_to_version", path=path, version=version
        )
        return response

    @staticmethod
    def checkout(path, comment=""):
        response = PerforceRestStub._wrap_call("checkout", path=path, comment=comment)
        return response

    @staticmethod
    def is_checkouted(path):
        response = PerforceRestStub._wrap_call("is_checkouted", path=path)
        return response

    @staticmethod
    def get_last_change_list():
        # type: (None) -> dict
        response = PerforceRestStub._wrap_call("get_last_change_list")
        return response

    @staticmethod
    def get_changes(stream):
        # type: (None) -> dict
        response = PerforceRestStub._wrap_call("get_changes")
        return response

    @staticmethod
    def submit_change_list(comment):
        response = PerforceRestStub._wrap_call("submit_change_list", comment=comment)
        return response

    @staticmethod
    def exists_on_server(path):
        response = PerforceRestStub._wrap_call("exists_on_server", path=path)
        return response

    @staticmethod
    def get_stream(workspace_dir):
        response = PerforceRestStub._wrap_call(
            "get_stream", workspace_dir=workspace_dir
        )
        return response
