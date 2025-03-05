import pathlib

import maya.cmds as cmds
from ayon_core.lib.log import Logger
from ayon_core.pipeline.context_tools import (get_current_host_name,
                                              get_current_project_name)
from maya import OpenMaya
from qtpy import QtWidgets

from version_control.api.models.server_workspaces import ServerWorkspaces
from version_control.api.perforce import get_connection_info, handle_login
from version_control.rest.perforce.rest_stub import PerforceRestStub

log = Logger.get_logger(__name__)


def install_version_control_callbacks() -> None:
    OpenMaya.MSceneMessage.addCheckReferenceCallback(
        OpenMaya.MSceneMessage.kBeforeLoadReferenceCheck, _on_load_reference
    )


def _on_load_reference(*args) -> None:
    try:
        references = cmds.file(q=True, r=True)
        for reference in references:
            file_path = pathlib.Path(reference)
            if not file_path.exists():
                QtWidgets.QMessageBox.information(
                    None,
                    "Info",
                    (
                        f"No File Found {file_path.name}\n"
                        "Attempting to sync with perforce"
                    ),
                )

                host = get_current_host_name()
                project = get_current_project_name()
                if not project:
                    log.error("Must be in a project context to run.")
                    return

                server_workspaces = ServerWorkspaces(project)
                workspaces = server_workspaces.get_host_workspaces(host, True)
                if not workspaces:
                    raise ValueError(f"Unable to get workspaces for {host}")
                else:
                    current_workspace = workspaces[0]

                connection_info = get_connection_info(
                    project_name=project,
                    configured_workspace=current_workspace.name,
                    host=host,
                )
                handle_login(connection_info)

                if PerforceRestStub.exists_on_server(file_path.as_posix()):
                    PerforceRestStub.sync_latest_version(file_path.as_posix())
                    log.debug(f"Reference File Path {file_path}")
                    QtWidgets.QMessageBox.information(
                        None, "Info", (f"Successfully Sync'd: {file_path.name}")
                    )
                else:
                    raise RuntimeError(
                        (
                            f"{file_path.as_posix()} not found on "
                            f"{connection_info.workspace_server.host}."
                        )
                    )
        OpenMaya.MScriptUtil.setBool(args[0], True)

    except Exception as e:
        QtWidgets.QMessageBox.critical(
            None, "Error", f"Before Load Reference Failed: {str(e)}"
        )
        OpenMaya.MScriptUtil.setBool(args[0], False)
