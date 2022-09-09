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
FILE_PREFIX_HOU = 'hou'
FILE_PREFIX_NVIL = 'nvil'
MSG_FILENAME = 'NVil Message_In.txt'

# Aliases to function and enums responsible for status messages.
set_msg = hou.ui.setStatusMessage
msg_important = hou.severityType.ImportantMessage
msg_warning = hou.severityType.Warning
msg_error = hou.severityType.Error


def houdini_export_linux(format: str = 'obj'):
    """Merges and exports selected SOPs to Windows' temporary path."""
    # Do a simple check of the $NVIL_WINEPREFIX envvar.
    # See if it is a directory and if it contains drive_c path.
    # Abort if something is not right.
    if not is_appdata_valid():
        return

    sops = hou.selectedNodes()
    # Check if anything is seleted.
    if len(sops) == 0:
        set_msg('Nothing to export.', msg_important)
        return

    # Abort if one of the nodes is not a SOP.
    for sop in sops:
        if type(sop) is not hou.SopNode:
            set_msg(f'Wrong candidate: {type(sop)}', msg_error)
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
        'sopoutput': str(Path(TMP_PATH, f'{FILE_PREFIX_HOU}.{format}'))
    })
    rop.setInput(0, groups_from_name)
    rop.parm('execute').pressButton()

    rop.destroy()
    groups_from_name.destroy()
    merge.destroy()

    # Construct absolute path to the exported file.
    # By default root is z: in Wine, so we'll use that to our advantage.
    pure_win_path = PureWindowsPath('z:', TMP_PATH, f'{FILE_PREFIX_HOU}.{format}')
    # Tell NVil to import exported file.
    instructions = [
        f'TID Common Modeling Shortcut Tools >> ' \
        f'P_LoadFromFile[{str(pure_win_path)}, false, true, false]'
    ]
    write_instructions(instructions)
    write_message()

    set_msg('Done exporting. You can now switch to NVil.')


def houdini_export_windows(format: str='obj'):
    # TODO: Implement houdini_export_windows function.
    return


def houdini_import_linux(format: str='obj'):
    """Imports NVil clipboard into SOP network."""
    # Check if there is anything to import.
    # For OBJ and FBX files, depending on chosen format.
    if not Path(TMP_PATH, f'FILE_PREFIX.{format}').exists():
        set_msg('Nothing to import.', msg_important)

    # Verify selection. Abort if first selected operator is not a SOP.
    sops = hou.selectedNodes()
    if len(sops) == 0:
        set_msg('Select at least one SOP.', msg_important)
        return

    sop = sops[0]
    if not type(sop) == hou.SopNode:
        set_msg('Selected operator is not a SOP.', msg_important)
        return

    # Import the file.
    parent = sop.parent()
    input = parent.createNode('file')
    input.setParms({
        'file': str(Path(TMP_PATH, f'{FILE_PREFIX_NVIL}.{format}'))
    })

    input.setInput(0, sop)
    stash = parent.createNode('stash')
    stash.setInput(0, input)
    stash.parm('stashinput').pressButton()
    input.destroy()
    stash.moveToGoodPosition(move_inputs=False, move_unconnected=False)
    stash.setDisplayFlag(True)
    stash.setRenderFlag(True)

    set_msg('Done importing.')


def houdini_import_windows(format: str='obj'):
    # TODO: Implement houdini_import_windows function.
    pass


def is_appdata_valid() -> bool:
    """Checks if path defined in $NVIL_APPDATA exists and is a directory."""
    if NVIL_APPDATA is None \
       or not NVIL_APPDATA.is_dir():
        set_msg('Invalid $NVIL_WINEPREFIX.', msg_error)
        return False
    else:
        return True


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
        set_msg(
            'Message file locked. ' \
            'Switch to NVil and check if the import dialog is closed.',
            msg_error
        )


def is_path_a_dir(path: Path) -> bool:
    """Checks if path exists and is not a file."""
    if not path.exists() or not path.is_dir():
        set_msg(f'Path {path} does not exist or is a file.', msg_error)
        return False
    return True


def houdini_export(format: str='obj'):
    """Runs appropriate export function for the detected operating system."""
    if platform.system() == 'Linux':
        houdini_export_linux(format)
    elif platform.system() == 'Windows':
        houdini_export_windows(format)
    else:
        set_msg('Unsupported operating system.', msg_error)


def houdini_import(format: str='obj'):
    """Runs appropriate import function for the detected operating system."""
    if platform.system() == 'Linux':
        houdini_import_linux(format)
    elif platform.system() == 'Windows':
        houdini_export_windows(format)
    else:
        set_msg('Unsupported operating system.', msg_error)