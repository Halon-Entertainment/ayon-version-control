from pydantic import Field
from ayon_server.settings import BaseSettingsModel


def backend_enum():
    return [
        {"label": "Perforce", "value": "perforce"}
    ]

def workspace_type_enum():
    return ['Asset', 'Engine']


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

class WorkspaceSettingsModel(BaseSettingsModel):
    name: str = Field(
        "",
        title='Name',
        scope=['studio', 'project']
    )
    storage_type: str = Field(
        "",
        title='Storage Type',
        scope=['studio', 'project'],
        enum_resolver=workspace_type_enum

    )
    hosts: list[str] = Field(
        [],
        title='Hosts',
        scope=['studio', 'project'],
    )
    workspace_root: str = Field(
        "",
        title="Workspace Root",
        description="The Anatomy root for the workspace",
        scope=['studio', 'project']
    )
    sync_from_empty: bool = Field(
        False,
        title="Create New Workspace If Empty",
        scope=['studio', 'project']
    )
    workspace_name: str = Field(
        "",
        title="Workspace Name",
        scope=['studio', 'project']
    )
    stream: str = Field(
        "",
        title="Stream",
        scope=['project', 'site']
    )
    options: str = Field(
        "",
        title="Options",
        desctiption="Options for workspace creation, must be seperated by space (See perforce Docs for options)",
        scope=['studio', 'project', 'site']
    )
    allow_create_workspace: bool = Field(
        True,
        title="Allow Workspace Creation",
        description="Allows a workspace to be create when one doesn't exist.",
        scope=["studio", "project"]
    )
    create_dirs: bool = Field(
        True,
        title="Create Workspace Directories",
        scope=["studio", "project"]
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

    workspace_settings: list[WorkspaceSettingsModel] = Field(
        title="Workspace settings",
        default_factory=list[WorkspaceSettingsModel],
        scope=['studio', 'project', 'site'],
        description=("A list of workspaces for use in production, settings flow "
                     "studio -> project -> site"),
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
    
