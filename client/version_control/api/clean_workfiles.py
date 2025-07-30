import pathlib
import re
import os
import shutil
import stat
import typing
from ayon_api import get_folders, get_tasks, get_project
from ayon_api._api import get_folder_by_id
from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy import Anatomy
from ayon_core.pipeline.anatomy.templates import AnatomyStringTemplate
from pprint import pformat
from ayon_core.pipeline.template_data import get_template_data
from ayon_core.settings.lib import get_project_settings
from version_control.api.models.connection_info import ConnectionInfo
from version_control.api.models.server_info import ServerInfo
from version_control.api.models.workspace_info import WorkspaceInfo
from version_control.api.perforce import handle_login
from version_control.rest.perforce.rest_stub import PerforceRestStub
from version_control.ui.workfile_cleanup.worker import CleanupSignals

log = Logger.get_logger(__name__)


def get_all_workfiles(
    project_name: str, callback: typing.Optional[CleanupSignals] = None
):
    project_entity = get_project(project_name=project_name)
    anatomy = Anatomy(project_name=project_name)
    folders = get_folders(project_name=project_name)
    folder_ids = list(map(lambda x: x["id"], folders))
    tasks = list(get_tasks(project_name=project_name, folder_ids=folder_ids))
    workfiles_by_path = []

    workfile_dir_template = anatomy.get_template_item(
        "work", "default", "directory"
    )
    if not isinstance(workfile_dir_template, AnatomyStringTemplate):
        raise TypeError(f"Invalid Template type {type(workfile_dir_template)}")

    workfile_file_template = anatomy.get_template_item(
        "work", "default", "file"
    )
    if not isinstance(workfile_file_template, AnatomyStringTemplate):
        raise TypeError(
            f"Invalid Template type {type(workfile_file_template)}"
        )

    glob_regex = r"\{([^}]*)\}"

    if callback:
        callback.started.emit("Scanning Ayon Tasks...", len(tasks))

    for progress, task in enumerate(tasks):
        folder_entity = get_folder_by_id(
            project_name=project_name, folder_id=task["folderId"]
        )
        template_data = get_template_data(
            project_entity=project_entity,
            folder_entity=folder_entity,
            task_entity=task,
        )
        log.debug(pformat(task))
        log.debug(template_data)

        workfile_path = pathlib.Path(
            workfile_dir_template.format(template_data)
        )
        log.debug(workfile_path)
        workfile_name = workfile_file_template.format(template_data)
        workfile_glob = re.sub(glob_regex, "*", workfile_name)
        log.debug(workfile_glob)
        workfiles = list(workfile_path.glob(workfile_glob))
        log.debug(workfiles)
        workfiles_by_path.append((workfile_path.as_posix(), workfiles))

        if callback:
            callback.updated.emit(progress + 1)

    return workfiles_by_path


def versions_to_remove(
    project_name: str,
    workfile_parent: str,
    workfiles: typing.List[pathlib.Path],
    progress_callback: typing.Optional[CleanupSignals] = None,
    keep_count: int = 3,
):
    if len(workfiles) <= keep_count:
        return [[], []]
    version_regex = r"[._]v(\d*)"
    workfile_versions = []

    for workfile in workfiles:

        log.debug(f"Workfile {workfile}")
        log.debug(f"Version Regex {version_regex}")
        log.debug(f"Match {re.findall(version_regex, workfile.name)}")


        match = re.findall(version_regex, workfile.name)
        filtered_match = [x for x in match if x]

        version = int(filtered_match[0])
        workfile_versions.append((workfile, version))
    workfile_versions = sorted(
        workfile_versions, key=lambda x: x[1], reverse=True
    )
    versions_to_remove = list(map(lambda x: x[0], workfile_versions))[
        keep_count:
    ]
    perforce_filtered_versions, unsubmitted_workfiles = filter_perforce_exists(
        project_name,
        workfile_parent,
        versions_to_remove,
        progress_callback=progress_callback,
    )

    return perforce_filtered_versions, unsubmitted_workfiles


def filter_perforce_exists(
    project_name: str,
    workfile_parent: str,
    workfiles: typing.List[pathlib.Path],
    progress_callback: typing.Optional[CleanupSignals] = None,
):
    anatomy = Anatomy(project_name)
    roots = anatomy.roots
    current_root = get_root_from_path(workfiles[0], roots)

    if not workfiles:
        return [[], []]

    project_settings = get_project_settings(project_name=project_name)
    version_control_settings = project_settings["version_control"]
    workspace_settings = version_control_settings["workspace_settings"]

    file_workspace = None
    for workspace in workspace_settings:
        if workspace["workspace_root"] == current_root:
            file_workspace = workspace
            break

    if not file_workspace:
        raise ValueError(f"Unable to find workspace with root {current_root}")

    workspace_server = file_workspace["server"]
    servers = version_control_settings["servers"]

    server_config = None
    for server in servers:
        if server["name"] == workspace_server:
            server_config = server
            break

    if not server_config:
        raise ValueError(f"Server not found for {file_workspace['name']}")

    server_info = ServerInfo(**server_config)
    file_workspace["project_name"] = project_name
    workspace_info = WorkspaceInfo(**file_workspace)
    connection_info = ConnectionInfo(
        workspace_info=workspace_info, workspace_server=server_info
    )
    handle_login(connection_info)

    filtered_files = []
    unsubmitted_workfiles = []
    if progress_callback:
        progress_callback.started.emit(
            f"Searching Perforce For Workfiles in ...{workfile_parent[-30:]}",
            len(workfiles),
        )

    for i, file in enumerate(workfiles):
        perforce_exists = PerforceRestStub.exists_on_server(file.as_posix())
        if not perforce_exists:
            unsubmitted_workfiles.append(file)
            log.warning(
                f"Skipping {file.as_posix()} it doesn't exist in perforce."
            )
            continue

        filtered_files.append(file)

        if progress_callback:
            progress_callback.updated.emit(i + 1)

    return filtered_files, unsubmitted_workfiles


def get_root_from_path(path: pathlib.Path, roots: dict):
    for root in roots:
        if root in path.as_posix():
            return root
    raise ValueError(f"No root found in path {path.as_posix()}")


def remove_workfiles(
    workfile_paths: typing.List[pathlib.Path],
    progress_callback: typing.Optional[CleanupSignals] = None,
):
    space_cleared = 0
    files_removed = 0

    if progress_callback:
        progress_callback.started.emit(
            f"Deleting {len(workfile_paths)} File...", len(workfile_paths)
        )

    for i, workfile in enumerate(workfile_paths):
        if workfile.exists():
            space_cleared += workfile.stat().st_size
            files_removed += 1
            workfile.chmod(stat.S_IWRITE)
            os.remove(workfile)
        if progress_callback:
            progress_callback.updated.emit(i + 1)

    return files_removed, space_cleared


def clean_workfiles_files(
    project: str,
    keep_count: int = 3,
    progress_callback: typing.Optional[CleanupSignals] = None,
):
    if not project:
        raise RuntimeError("A project must be selected.")

    workfiles = get_all_workfiles(project, progress_callback)
    workfiles_to_delete = []
    unsubmitted_workfiles = []

    for workfile_parent, workfile_list in workfiles:
        workfile_parent = pathlib.Path(workfile_parent)
        delete_workfiles, unsubmitted_workfiles = versions_to_remove(
            project,
            workfile_parent.as_posix(),
            workfile_list,
            keep_count=keep_count,
            progress_callback=progress_callback,
        )
        workfile_paths = list(
            map(lambda x: workfile_parent.joinpath(x), delete_workfiles)
        )
        workfiles_to_delete += workfile_paths

    from pprint import pformat

    log.debug(pformat(workfiles_to_delete))
    files_removed, space_cleared = remove_workfiles(
        workfiles_to_delete, progress_callback=progress_callback
    )

    if progress_callback:
        progress_callback.finished.emit(
            unsubmitted_workfiles, files_removed, space_cleared
        )

    return files_removed, space_cleared
