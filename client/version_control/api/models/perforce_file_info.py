import os
import typing
from dataclasses import dataclass, field

from ayon_core.lib.log import Logger
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.settings.lib import get_project_settings

log = Logger.get_logger(__name__)

@dataclass
class PerforceFileInfo:
    """
    Represents a file in perforce.
    """
    
    depot_path: str
    revision_number: int
    workspace_path: str
    status: str
    changelist_number: int
    exists:
    
    @classmethod
    def from_p4_output(cls, output):
        lines = output.strip().split('\n')
        depot_path = lines[0].strip()
        revision_number = int(lines[1].split(' ')[1])
        workspace_path = lines[2].strip()
        status = lines[3].strip()
        changelist_number = int(lines[4].split(' ')[1])
        
        return cls(depot_path, revision_number, workspace_path, status, changelist_number)
