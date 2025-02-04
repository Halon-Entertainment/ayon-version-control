import json
import os
import pathlib
import socket
import typing

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy import Anatomy
from ayon_core.pipeline.context_tools import get_current_host_name
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings import get_project_settings
from ayon_core.tools.utils import qt_app_context
from qtpy import QtWidgets
from version_control.api.models import (
    ConnectionInfo,
    ServerInfo,
    ServerWorkspaces,
    WorkspaceInfo,
)
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.ui.login_window import LoginWindow

log = Logger.get_logger(__name__)


def get_connection_info(
    project_name, project_settings=None, configured_workspace=None
) -> ConnectionInfo:
    if not project_settings:
        project_settings = get_project_settings(project_name)

    current_workspace = get_workspace(project_settings, configured_workspace)
    servers = fetch_project_servers(project_name)
    server = current_workspace.server
    workspace_server = [x for x in servers if x.name == server]
    if not workspace_server:
        raise ValueError(f"Unable to find server {server}.")
    workspace_server = workspace_server[0]
    login = check_login(workspace_server)
    workspace_server.username = login["username"]
    workspace_server.password = login["password"]

    connection_info = ConnectionInfo(
        workspace_info=current_workspace, workspace_server=workspace_server
    )

    return connection_info


def fetch_project_servers(project_name: str) -> typing.List[ServerInfo]:
    project_settings = get_project_settings(project_name)
    version_control_settings = project_settings["version_control"]
    return list(map(lambda x: ServerInfo(**x), version_control_settings["servers"]))


def get_workspace(project_name, configured_workspace=None) -> WorkspaceInfo:
    project_settings = get_project_settings(project_name)
    version_settings = project_settings["version_control"]
    workspaces = list(
        map(
            lambda x: WorkspaceInfo(**x),
            version_settings["workspace_settings"],
        )
    )
    server_workspaces = ServerWorkspaces(project_name)
    current_host = get_current_host_name()

    log.debug(current_host)
    log.debug(workspaces)

    if current_host:
        workspaces = server_workspaces.get_host_workspaces(current_host, primary=True)

    return workspaces[0]


def check_login(server_name):
    perforce_connection_config = (
        pathlib.Path(os.environ["APPDATA"]) / "perforce_servers.json"
    )
    log.debug(f"Perforce Config File: {perforce_connection_config}")
    if not perforce_connection_config.exists():
        with perforce_connection_config.open("w") as config_file:
            config_file.write(json.dumps([]))

    with perforce_connection_config.open("r") as config_file:
        config = json.load(config_file)

    log.debug(f"Config Items: {[item.get('server_name') for item in config]}")
    if server_name not in [item.get("server_name") for item in config]:
        with qt_app_context():
            login_window = LoginWindow(server_name)
            result = login_window.exec_()  # pyright: ignore[]

            if result == QtWidgets.QDialog.Accepted:  # pyright: ignore[]
                username, password = login_window.get_credentials()

                config.append(
                    {
                        "server_name": server_name,
                        "username": username,
                        "password": password,
                    }
                )

                with perforce_connection_config.open("w") as config_file:
                    json.dump(config, config_file, indent=4)

                return {
                    "server_name": server_name,
                    "username": username,
                    "password": password,
                }

            else:
                log.info("Login was cancelled")
                return {}
    else:
        return list(filter(lambda x: x["server_name"] == server_name, config))[0]


def populate_settings(project_name: str, settings: dict) -> dict:
    anatomy = Anatomy(project_name=project_name)
    template_data = get_template_data_with_names(project_name)
    template_data["computername"] = socket.gethostname()
    template_data["root"] = anatomy.roots
    template_data.update(anatomy.roots)

    formated_dict = {}
    for key, value in settings.items():
        if isinstance(value, str):
            formated_dict[key] = value.format(**template_data)
        else:
            formated_dict[key] = value
    return formated_dict


def handle_workspace_directory(
    project_name: str, workspace_settings: dict
) -> pathlib.Path:
    anatomy = Anatomy(project_name=project_name)
    workspace_dir = pathlib.Path(anatomy.roots[workspace_settings["workspace_root"]])

    log.debug(workspace_dir)
    create_dirs = workspace_settings.get("create_dirs", False)

    if create_dirs:
        workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def workspace_exists(conn_info: ConnectionInfo) -> bool:
    PerforceRestStub.login(
        host=conn_info.workspace_server.host,
        port=conn_info.workspace_server.perforce_port,
        username=conn_info.workspace_server.username,
        password=conn_info.workspace_server.password,
        workspace_dir=conn_info.workspace_info.workspace_root,
        workspace_name=conn_info.workspace_info.workspace_name,
    )

    return PerforceRestStub.workspace_exists(
        conn_info.workspace_info.workspace_name,
    )


def create_workspace(conn_info: ConnectionInfo) -> None:
    log.debug(conn_info.workspace_server.username)
    PerforceRestStub.login(
        host=conn_info.workspace_server.host,
        port=conn_info.workspace_server.perforce_port,
        username=conn_info.workspace_server.username,
        password=conn_info.workspace_server.password,
        workspace_dir=conn_info.workspace_info.workspace_root,
        workspace_name=conn_info.workspace_info.workspace_name,
    )

    PerforceRestStub.create_workspace(
        conn_info.workspace_info.workspace_root,
        conn_info.workspace_info.workspace_name,
        conn_info.workspace_info.stream,
        conn_info.workspace_info.options,
    )


def sync_to_latest(conn_info: ConnectionInfo) -> None:
    PerforceRestStub.login(
        host=conn_info.workspace_server.host,
        port=conn_info.workspace_server.perforce_port,
        username=conn_info.workspace_server.username,
        password=conn_info.workspace_server.password,
        workspace_dir=conn_info.workspace_info.workspace_root,
        workspace_name=conn_info.workspace_info.workspace_name,
    )
    PerforceRestStub.sync_latest_version(conn_info.workspace_info.workspace_root)


def sync_to_version(conn_info: ConnectionInfo, change_id: int) -> None:
    PerforceRestStub.login(
        host=conn_info.workspace_server.host,
        port=conn_info.workspace_server.perforce_port,
        username=conn_info.workspace_server.username,
        password=conn_info.workspace_server.password,
        workspace_dir=conn_info.workspace_info.workspace_root,
        workspace_name=conn_info.workspace_info.workspace_name,
    )

    PerforceRestStub.sync_to_version(
        f"{conn_info.workspace_info.workspace_root}/...", change_id
    )
