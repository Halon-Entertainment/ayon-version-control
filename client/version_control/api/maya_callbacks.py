import pathlib
import re

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
    """
    Installs callbacks for managing version control during reference loading in Maya.

    This function adds a check reference callback to the Maya scene message manager,
    which triggers the `_on_load_reference` function before any reference file is loaded.
    If a reference file does not exist locally, it attempts to sync it from Perforce.
    """
    OpenMaya.MSceneMessage.addCheckReferenceCallback(
        OpenMaya.MSceneMessage.kBeforeLoadReferenceCheck, _on_load_reference
    )


def _on_load_reference(*args) -> None:
    """
    Handles the loading of reference files by attempting to sync them with Perforce if local.

    This function is called before each reference file is loaded in Maya. It checks for
    missing reference files and attempts to sync them from Perforce. If the file is not found
    on the server, it raises a RuntimeError.
    """
    try:
        references = cmds.file(q=True, r=True)
        missing_references = []
        for reference in references:
            if '{' in reference:
                reference = reference.split('{')[0]
            file_path = pathlib.Path(reference)
            log.debug(f"Reference Path {file_path}")
            if not file_path.exists():
                missing_references.append(file_path)

        if missing_references:
            QtWidgets.QMessageBox.information(
                None, "Info", (f"Found {len(missing_references)} Missing References "
                               "Attempting to Sync them from Perforce")
            )

            for file_path in missing_references:
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
