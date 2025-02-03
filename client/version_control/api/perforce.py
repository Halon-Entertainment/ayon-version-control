import json
import os
import pathlib
import socket

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy import Anatomy
from ayon_core.pipeline.context_tools import get_current_host_name
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings import get_project_settings
from ayon_core.tools.utils import qt_app_context
from qtpy import QtWidgets

from version_control.ui.login_window import LoginWindow
from version_control.rest.perforce.rest_stub import PerforceRestStub

log = Logger.get_logger(__name__)


def get_connection_info(
    project_name, project_settings=None, configured_workspace=None
) -> dict:
    if not project_settings:
        project_settings = get_project_settings(project_name)

    current_workspace = get_workspace(project_settings, configured_workspace)
    current_workspace["workspace_dir"] = handle_workspace_directory(
        project_name, current_workspace
    )
    current_workspace = populate_settings(project_name, current_workspace)
    login = check_login(current_workspace["server"])
    current_workspace.update(login)
    current_workspace["host"] = list(
        filter(
            lambda x: x["name"] == current_workspace["server"],
            project_settings["version_control"]["servers"],
        )
    )[0]["host"]
    current_workspace["port"] = list(
        filter(
            lambda x: x["name"] == current_workspace["server"],
            project_settings["version_control"]["servers"],
        )
    )[0]["port"]

    return current_workspace


def get_workspace(project_settings: dict, configured_workspace=None) -> dict:
    version_settings = project_settings["version_control"]
    workspaces = version_settings["workspace_settings"]
    current_host = get_current_host_name()

    log.debug(current_host)
    log.debug(workspaces)

    if current_host:
        workspaces = list(
            filter(lambda x: current_host in x["host"], workspaces)
        )

    if workspaces:
        if not configured_workspace:
            primary_workspaces = list(
                filter(lambda x: x["primary"], workspaces)
            )
            if primary_workspaces:
                current_workspace = primary_workspaces[0]
        else:
            configured_workspaces = list(
                filter(lambda x: x["name"] == configured_workspace, workspaces)
            )
            if configured_workspace:
                current_workspace = configured_workspaces[0]
    else:
        raise ValueError("No configured workspaces found.")

    return current_workspace


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
        return list(filter(lambda x: x["server_name"] == server_name, config))[
            0
        ]


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
    workspace_dir = pathlib.Path(
        anatomy.roots[workspace_settings["workspace_root"]]
    )

    log.debug(workspace_dir)
    create_dirs = workspace_settings.get("create_dirs", False)

    if create_dirs:
        workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir

def workspace_exists(conn_info) -> bool:

    PerforceRestStub.login(
        host=conn_info["host"],
        port=conn_info["port"],
        username=conn_info["username"],
        password=conn_info["password"],
        workspace_dir=conn_info["workspace_dir"],
        workspace_name=conn_info["workspace_name"],
    )

    return PerforceRestStub.workspace_exists(
        conn_info["workspace_name"],
    )

def create_workspace(conn_info) -> None:
    log.debug(conn_info["username"])
    PerforceRestStub.login(
        host=conn_info["host"],
        port=conn_info["port"],
        username=conn_info["username"],
        password=conn_info["password"],
        workspace_dir=conn_info["workspace_dir"],
        workspace_name=conn_info["workspace_name"],
    )

    PerforceRestStub.create_workspace(
        conn_info["workspace_dir"],
        conn_info["workspace_name"],
        conn_info["stream"],
        conn_info["options"],
    )
def sync_to_latest(conn_info) -> None:
    PerforceRestStub.login(
        host=conn_info["host"],
        port=conn_info["port"],
        username=conn_info["username"],
        password=conn_info["password"],
        workspace_dir=conn_info["workspace_dir"],
        workspace_name=conn_info["workspace_name"],
    )
    PerforceRestStub.sync_latest_version(conn_info["workspace_dir"])

def sync_to_version(conn_info, change_id) -> None:
    PerforceRestStub.login(
        host=conn_info["host"],
        port=conn_info["port"],
        username=conn_info["username"],
        password=conn_info["password"],
        workspace_dir=conn_info["workspace_dir"],
        workspace_name=conn_info["workspace_name"],
    )

    PerforceRestStub.sync_to_version(
        f"{conn_info['workspace_dir']}/...", change_id
    )
