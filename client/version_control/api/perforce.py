import json
import os
import pathlib
import typing
from qtpy import QtWidgets

from ayon_core.lib.log import Logger
from ayon_core.pipeline.context_tools import get_current_host_name
from ayon_core.settings import get_project_settings
from ayon_core.tools.utils import qt_app_context
from qtpy import QtWidgets

from version_control.api.exceptions import LoginError
from version_control.api.models import (ConnectionInfo, ServerInfo,
                                        ServerWorkspaces, WorkspaceInfo)
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.ui.login_window import LoginWindow

log = Logger.get_logger(__name__)


class ConnectionError(Exception):
    pass


def get_connection_info(
    project_name: str,
    configured_workspace: typing.Union[str, None] = None,
    host: typing.Union[str, None] = None,
) -> ConnectionInfo:
    """
    Retrieves the connection information for a given project.

    This function fetches the current workspace settings and server information,
    updates the login credentials if necessary, and returns a ``ConnectionInfo`` object
    containing the necessary details to interact with the version control system.

    Args:
        project_name (str): The name of the project.
        configured_workspace (str, optional): Configured workspace for the project. Defaults to None.
        host (str, optional): The host that the connection will be used for.

    Returns:
        ConnectionInfo: An object containing the connection information for the specified project.
    """

    current_workspace = get_workspace(project_name, configured_workspace, host)
    servers = fetch_project_servers(project_name)
    server = current_workspace.server
    workspace_server = [x for x in servers if x.name == server]
    if not workspace_server:
        raise ValueError(f"Unable to find server {server}.")
    workspace_server = workspace_server[0]
    login = check_login(workspace_server)
    if login:
        if not login.username or not login.password:
            raise ValueError("No username and password set")
        workspace_server.username = login.username
        workspace_server.password = login.password

        connection_info = ConnectionInfo(
            workspace_info=current_workspace, workspace_server=workspace_server
        )

        return connection_info


def fetch_project_servers(project_name: str) -> typing.List[ServerInfo]:
    """
    Fetches the servers configured for a given project.

    Args:
        project_name (str): The name of the project to retrieve servers for.

    Returns:
        List[ServerInfo]: A list of `ServerInfo` objects representing the servers configured for the project.
    """
    project_settings = get_project_settings(project_name)
    version_control_settings = project_settings["version_control"]
    return list(map(lambda x: ServerInfo(**x), version_control_settings["servers"]))


def get_workspace(
    project_name: str,
    configured_workspace: typing.Union[str, None] = None,
    host: typing.Union[str, None] = None,
) -> WorkspaceInfo:
    """
    Retrieves the workspace information for a given project.

    Args:
        project_name (str): The name of the project.
        configured_workspace (str, optional): Configured workspace for the
        project. Defaults to None.
        host (str, optional): The name of the host version control in entering
        into.

    Returns:
        WorkspaceInfo: An object containing the workspace information for the specified project.
        None: if not inside a host.
    """
    log.debug(f"Project Name: {project_name}")
    server_workspaces = ServerWorkspaces(project_name)
    if configured_workspace:
        return server_workspaces.get_workspace_by_name(configured_workspace)

    current_host = host or get_current_host_name()
    current_workspace = None
    log.debug(f"Current host: {current_host}")

    if current_host:
        workspaces = server_workspaces.get_host_workspaces(current_host, primary=True)
        current_workspace = workspaces[0]

    if not current_workspace:
        raise RuntimeError(f"Unable to find workspace for {project_name}")
    return current_workspace


def handle_login(conn_info: ConnectionInfo, attempts: int = 3) -> None:
    server_info = check_login(conn_info.workspace_server)

    try:
        PerforceRestStub.login(
            host=server_info.host,
            port=server_info.port,
            username=server_info.username,
            password=server_info.password,
            workspace_dir=conn_info.workspace_info.workspace_dir,
            workspace_name=conn_info.workspace_info.workspace_name,
        )
    except Exception as e:
        build_credentials(server_info)
        if attempts > 0:
            log.error(f"Login Failed: {e}")
            QtWidgets.QMessageBox.critical(None, "Login Error", f"{e}")
            handle_login(conn_info, attempts - 1)
        else:
            msg = (
                "Login Failed: \n"
                "  - Make sure you have the right login information\n"
                "  - It could be that your password needs to be reset on the perforce server\n"
                "  - Or, Something just went wrong while connecting to perforce\n"
            )
            QtWidgets.QMessageBox.critical(None, "Login Error", msg)
            raise RuntimeError(msg)


def build_credentials(server_info_to_remove: ServerInfo = None):
    perforce_connection_config = (
        pathlib.Path(os.environ["APPDATA"]) / "halon" / "perforce_servers.json"
    )
    perforce_connection_config.parent.mkdir(parents=True, exist_ok=True)

    if not perforce_connection_config.exists():
        with perforce_connection_config.open("w") as config_file:
            config_file.write(json.dumps([]))
    else:
        log.debug(f"Perforce Config File: {perforce_connection_config}")
        if server_info_to_remove:
            with perforce_connection_config.open("r") as config_file:
                config = json.load(config_file)

            servers = [ServerInfo(**x) for x in config]
            if server_info_to_remove in servers:
                servers.remove(server_info_to_remove)
                with perforce_connection_config.open("w") as config_file:
                    json.dump(
                        list(map(lambda x: x.__dict__, servers)),
                        config_file,
                        indent=4,
                    )

    return perforce_connection_config


def check_login(server_info: ServerInfo) -> typing.Union[ServerInfo, None]:
    log.info("Checking Login")
    perforce_connection_config = build_credentials()

    with perforce_connection_config.open("r") as config_file:
        config = json.load(config_file)

    servers = [ServerInfo(**x) for x in config]
    if server_info not in servers:
        with qt_app_context():
            login_window = LoginWindow(server_info.name)
            result = login_window.exec_()  # pyright: ignore[]

            if result == QtWidgets.QDialog.Accepted:  # pyright: ignore[]
                username, password = login_window.get_credentials()
                server_info.username = username
                server_info.password = password

                servers.append(server_info)

                with perforce_connection_config.open("w") as config_file:
                    json.dump(
                        list(map(lambda x: x.__dict__, servers)),
                        config_file,
                        indent=4,
                    )

                return server_info
            else:
                log.info("Login was cancelled")
                return None
    else:
        current_server = list(filter(lambda x: server_info == x, servers))[0]
        server_info.username = current_server.username
        server_info.password = current_server.password
        log.debug(f"Server Settings: {server_info}")
        return server_info


def workspace_exists(conn_info: ConnectionInfo) -> bool:
    handle_login(conn_info)

    return PerforceRestStub.workspace_exists(
        conn_info.workspace_info.workspace_name,
    )


def create_workspace(conn_info: ConnectionInfo) -> None:
    handle_login(conn_info)

    log.info(f"Creating workspace directory at {conn_info.workspace_info.workspace_dir}")
    workspace_dir = conn_info.workspace_info.workspace_dir
    if workspace_dir:
        workspace_path = pathlib.Path(workspace_dir)
        workspace_path.mkdir(parents=True, exist_ok=True)

    PerforceRestStub.create_workspace(
        conn_info.workspace_info.workspace_dir,
        conn_info.workspace_info.workspace_name,
        conn_info.workspace_info.stream,
        conn_info.workspace_info.options,
    )
    startup_files = conn_info.workspace_info.startup_files

    if startup_files:
        for current_path in startup_files:
            workspace_root = conn_info.workspace_info.workspace_root
            if workspace_root:
                current_path = (pathlib.Path(workspace_root) / current_path).as_posix()
                PerforceRestStub.sync_latest_version(current_path)


def sync_to_latest(conn_info: ConnectionInfo) -> None:
    if not conn_info.workspace_server.username or conn_info.workspace_server.password:
        raise ConnectionError(
            "Invaild ConnectionInfo object. Must contain username and password"
        )

    handle_login(conn_info)
    PerforceRestStub.sync_latest_version(conn_info.workspace_info.workspace_dir)


def sync_target_to_latest(conn_info: ConnectionInfo, target: str) -> None:
    handle_login(conn_info)
    PerforceRestStub.sync_latest_version(pathlib.Path(target).parent.as_posix())


def sync_to_version(conn_info: ConnectionInfo, change_id: int) -> None:
    handle_login(conn_info)
    PerforceRestStub.sync_to_version(
        f"{conn_info.workspace_info.workspace_dir}/...", change_id
    )
