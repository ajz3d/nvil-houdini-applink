# coding=utf8

# ===== nvil_houdini.py
#
# Copyright (c) 2017-2022 Artur J. Żarek (ajz3d)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hou
import getpass
import platform
import tempfile
from pathlib import Path, PurePath, PureWindowsPath


CURRENT_USER = getpass.getuser()
NVIL_APPDATA = Path(hou.getenv('NVIL_APPDATA'))
TMP_PATH = Path(tempfile.gettempdir(), 'houdini-nvil')
FILE_PREFIX = 'clipboard'
MSG_FILENAME = 'NVil Message_In.txt'


def houdini_export_linux(format: str = 'obj'):
    """Merges and exports selected SOPs to Windows' temporary path."""
    # Do a simple check of the $NVIL_WINEPREFIX envvar.
    # See if it is a directory and if it contains drive_c path.
    # Abort if something is not right.
    if NVIL_APPDATA is None \
       or not NVIL_APPDATA.is_dir():
        hou.ui.setStatusMessage(
            'Invalid $NVIL_WINEPREFIX.',
            severity=hou.severityType.Error
        )
        return

    sops = hou.selectedNodes()
    # Check if anything is seleted.
    if len(sops) == 0:
        hou.ui.setStatusMessage(
            'Nothing to export.',
            severity=hou.severityType.ImportantMessage)
        return

    # Abort if one of the nodes is not a SOP.
    for sop in sops:
        if type(sop) is not hou.SopNode:
            hou.ui.setStatusMessage(
                f'Wrong candidate: {type(sop)}',
                severity=hou.severityType.Error)
            return

    # All selected nodes will be merged together.
    merge = sops[0].parent().createNode('merge')
    groups_from_name = sops[0].parent().createNode('groupsfromname')

    # Start creating temporary network.
    for sop in sops:
        merge.setNextInput(sop)

    groups_from_name.setInput(0, merge)

    # Two options: FBX or OBJ.
    if format == 'fbx':
        rop = sops[0].parent().createNode('rop_fbx')
        rop.setParms({
            'exportkind': False,
            'buildfrompath': True,
            'pathattrib': 'name'
        })
    else:
        rop = sops[0].parent().createNode('rop_geometry')

    rop.setParms({
        'sopoutput': str(Path(TMP_PATH, f'{FILE_PREFIX}.{format}'))
    })
    rop.setInput(0, groups_from_name)
    rop.parm('execute').pressButton()

    rop.destroy()
    groups_from_name.destroy()
    merge.destroy()

    # Construct absolute path to the exported file.
    # By default root is z: in Wine, so we'll use that to our advantage.
    pure_win_path = PureWindowsPath('z:', TMP_PATH, f'{FILE_PREFIX}.{format}')
    # Tell NVil to import exported file.
    instructions = [
        f'TID Common Modeling Shortcut Tools >> ' \
        f'P_LoadFromFile[{str(pure_win_path)}, false, true, false]'
    ]
    write_instructions(instructions)
    write_message()

    hou.ui.setStatusMessage('Done exporting. You can now switch to NVil.')


def houdini_export_windows(format: str='obj'):
    # TODO: Implement houdini_export_windows function.
    return


def houdini_import_linux(format: str='obj'):
    # TODO: Implement houdini_import_linux function.
    pass


def houdini_import_windows(format: str='obj'):
    # TODO: Implement houdini_import_windows function.
    pass


def write_instructions(instructions: list[str]):
    """Writes NVil instructions file."""
    instructions_path = Path(NVIL_APPDATA, 'NVil Instructions.txt').resolve()
    with instructions_path.open('w', encoding='utf-8') as target_file:
        for instruction in instructions:
            target_file.write(instruction)
        target_file.write('\n')


def write_message():
    """Generates NVil message file and tells the program
    to load external instructions set."""
    message = 'Execute External Instruction File'
    message_path = Path(NVIL_APPDATA, 'NVil Message_In.txt').resolve()
    print(message_path)
    # If import dialog is open in NVil, Python will throw IOError,
    # so an exception handle is required to deal with that.
    try:
        with message_path.open('w', encoding='utf-8') as target_file:
            target_file.write(message)
    except IOError:
        hou.ui.setStatusMessage(
            'Message file locked.' \
            'Switch to NVil and check if the import dialog is closed.',
            severity=hou.severityType.Error
        )


def is_path_a_dir(path: Path) -> bool:
    """Checks if path exists and is not a file."""
    if not path.exists() or not path.is_dir():
        hou.ui.setStatusMessage(
            f'Path {path} does not exist or is a file.',
            severity=hou.severityType.Error)
        return False
    return True


def houdini_export(format: str='obj'):
    """Runs appropriate export function for the detected operating system."""
    if platform.system() == 'Linux':
        houdini_export_linux(format)
    elif platform.system() == 'Windows':
        houdini_export_windows(format)
    else:
        hou.ui.setStatusMessage(
            'Unsupported operating system.',
            severity=hou.severityType.Error
        )


def houdini_import(format: str='obj'):
    """Runs appropriate import function for the detected operating system."""
    if platform.system() == 'Linux':
        houdini_import_linux(format)
    elif platform.system() == 'Windows':
        houdini_export_windows(format)
    else:
        hou.ui.setStatusMessage(
            'Unsupported operating system.',
            severity=hou.severityType.Error
        )
