from pydantic import Field
from ayon_server.settings import BaseSettingsModel


def backend_enum():
    return [
        {"label": "Perforce", "value": "perforce"}
    ]


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
    template_name: str = Field("", title="Template name",
        description="Name from Anatomy to provide path and name of "
                    "committed file"
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
        description="Configure which products should be version controlled externally."
    )  # noqa


class LocalSubmodel(BaseSettingsModel):
    """Select your local and remote site"""
    username: str = Field(
        "",
        title="Username",
        scope=["site"]
    )
    password: str = Field(
        "",
        title="Password",
        scope=["site"]
    )
    allow_create_workspace: bool = Field(
        False,
        title="Allow Workspace Creation",
        description="Allows a workspace to be create when one doesn't exist.",
        scope=["site"]
    )
    create_dirs: bool = Field(
        False,
        title="Create Workspace Directories",
        scope=["site"]
    )
    workspace_name: str = Field(
        "",
        title="Workspace Name",
        scope=["site"]
    )
    stream: str = Field(
        "",
        title="Stream",
        scope=["site"]
    )
    options: str = Field(
        "",
        title="Options",
        scope=["site"],
        desctiption = "Options for workspace creation, must be seperated by space (See perforce Docs for options)"
    )

class WorkspaceSettingsModel(BaseSettingsModel):
    workspace_root: str = Field(
        "",
        title="Workspace Root",
        description="The Anatomy root for the workspace",
    )
    sync_from_empty: bool = Field(
        False,
        title="Create New Workspace If Empty",
    )
    create_dirs: bool = Field(
        False,
        title="Create Workspace Directories",
    )
    workspace_name: str = Field(
        "",
        title="Workspace Name"
    )
    stream: str = Field(
        "",
        title="Stream",
    )
    options: str = Field(
        "",
        title="Options",
        desctiption="Options for workspace creation, must be seperated by space (See perforce Docs for options)"
    )

class VersionControlSettings(BaseSettingsModel):
    """Version Control Project Settings."""

    enabled: bool = Field(default=True)

    active_version_control_system: str = Field(
        '',
        enum_resolver=backend_enum,
        title="Backend name"
    )

    host_name: str = Field(
        "perforce",
        title="Host name"
    )

    port: int = Field(
        1666,
        title="Port"
    )

    workspace_settings: WorkspaceSettingsModel = Field(
        default_factory=WorkspaceSettingsModel,
        title="Workspace settings"
    )

    publish: PublishPluginsModel = Field(
        default_factory=PublishPluginsModel,
        title="Publish Plugins",
    )

    local_setting: LocalSubmodel = Field(
        default_factory=LocalSubmodel,
        title="Local setting",
        scope=["site"],
        description="This setting is only applicable for artist's site",
    )


DEFAULT_VALUES = {}
    
