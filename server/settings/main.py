from pydantic import Field
from ayon_server.settings import BaseSettingsModel


def backend_enum():
    return [{"label": "Perforce", "value": "perforce"}]


def workspace_type_enum():
    return ["Asset", "Engine"]


class CollectVersionControlProfileModel(BaseSettingsModel):
    _layout = "expanded"
    host_names: list[str] = Field(
        default_factory=list,
        title="Host names",
    )
    product_types: list[str] = Field(
        default_factory=list,
        title="Families",
    )
    task_types: list[str] = Field(
        default_factory=list,
        title="Task types",
    )
    task_names: list[str] = Field(
        default_factory=list,
        title="Task names",
    )
    add_version_control: bool = Field(
        True,
        title="Add Version Control to representations",
    )
    template_name: str = Field(
        "",
        title="Template name",
        description="Name from Anatomy to provide path and name of "
        "committed file",
    )


class CollectVersionControlModel(BaseSettingsModel):
    _isGroup = True
    enabled: bool = True
    profiles: list[CollectVersionControlProfileModel] = Field(
        default_factory=list,
        title="Profiles to add version control",
    )


class PublishPluginsModel(BaseSettingsModel):
    CollectVersionControl: CollectVersionControlModel = Field(
        default_factory=CollectVersionControlModel,
        title="Collect Version Control",
        description="Configure which products should be version controlled externally.",
    )  # noqa


class ServerSettingsModel(BaseSettingsModel):
    name: str = Field(
        "Server", title="Name", scope=["studio", "project", "site"]
    )
    host: str = Field(
        "perforce", title="Host name", scope=["studio", "project", "site"]
    )
    port: int = Field(1666, title="Port", scope=["studio", "project", "site"])


class WorkspaceSettingsModel(BaseSettingsModel):
    name: str = Field("", title="Name", scope=["studio", "project"])
    server: str = Field("", title="Server", scope=["studio", "project"])
    sync_workfile: bool = Field(
        False,
        title="Sync Workfile",
        scope=["studio", "project"],
    )
    primary: bool = Field(
        False, title="Primary Workspace", scope=["studio", "project"]
    )
    active_version_control_system: str = Field(
        "",
        enum_resolver=backend_enum,
        title="Backend name",
        scope=["studio", "project"],
    )
    hosts: list[str] = Field(
        [],
        title="Hosts",
        scope=["studio", "project"],
    )
    workspace_root: str = Field(
        "",
        title="Workspace Template",
        description="The Anatomy root for the workspace",
        scope=["studio", "project"],
    )
    sync_from_empty: bool = Field(
        False,
        title="Create New Workspace If Empty",
        scope=["studio", "project"],
    )
    workspace_name: str = Field(
        "", title="Workspace Name", scope=["studio", "project"]
    )
    stream: str = Field("", title="Stream", scope=["project"])
    options: str = Field(
        "",
        title="Options",
        desctiption="Options for workspace creation, must be seperated by space (See perforce Docs for options)",
        scope=["studio", "project"],
    )
    allow_create_workspace: bool = Field(
        True,
        title="Allow Workspace Creation",
        description="Allows a workspace to be create when one doesn't exist.",
        scope=["studio", "project"],
    )
    create_dirs: bool = Field(
        True, title="Create Workspace Directories", scope=["studio", "project"]
    )
    enable_autosync: bool = Field(
        True,
        title="Enable Workspace Sync",
        scope=["studio", "project"],
    )
    startup_files: list[str] = Field(
        title="Start Up Files",
        default=[],
        scope=["studio", "project"],
        description="A list of file to pull down when initializing the workspace.",
    )
    always_sync: list[str] = Field(
        title="Always Sync Files",
        default=[],
        scope=["studio", "project"],
        description="A list of files that will be synced when ever an application is launched",
    )


class LocalWorkspaceSettingsModel(BaseSettingsModel):
    name: str = Field("", title="Name", scope=["site"])
    server: str = Field("", title="Server", scope=["site"])
    workspace_root: str = Field(
        "",
        title="Workspace Template",
        description="The Anatomy root for the workspace",
        scope=["site"],
    )
    workspace_name: str = Field("", title="Workspace Name", scope=["site"])
    stream: str = Field("", title="Stream", scope=["site"])


class LocalSubmodel(BaseSettingsModel):
    """Select your local and remote site"""

    workspace_settings: list[LocalWorkspaceSettingsModel] = Field(
        title="Workspace settings",
        default_factory=list[LocalWorkspaceSettingsModel],
        scope=["site"],
        description=(
            "A list of workspaces for use in production, settings flow "
            "studio -> project -> site"
        ),
    )


class VersionControlSettings(BaseSettingsModel):
    """Version Control Project Settings."""

    enabled: bool = Field(default=True)
    enabled_hosts: list[str] = Field(
        title="Enabled Hosts", default=[], scope=["studio", "project"]
    )
    servers: list[ServerSettingsModel] = Field(
        title="Servers",
        default_factory=list[ServerSettingsModel],
        scope=["studio", "project"],
        description="Server configuration",
    )

    workspace_settings: list[WorkspaceSettingsModel] = Field(
        title="Workspace settings",
        default_factory=list[WorkspaceSettingsModel],
        scope=["studio", "project"],
        description=(
            "A list of workspaces for use in production, settings flow "
            "studio -> project -> site"
        ),
    )
    local_settings: LocalSubmodel = Field(
        default_factory=LocalSubmodel,
        title="Local settings",
        scope=["site"],
        description="This setting is only applicable for artist's site",
    )

    publish: PublishPluginsModel = Field(
        default_factory=PublishPluginsModel,
        title="Publish Plugins",
    )


DEFAULT_VALUES = {}
