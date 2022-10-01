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
    if format == 'obj':
        load_from_obj(pure_win_path)
    else:
        load_from_fbx(pure_win_path)

    set_msg('Done exporting. You can now switch to NVil.')


def houdini_export_windows(format: str='obj'):
    # TODO: Implement houdini_export_windows function.
    return


def houdini_import_linux(format: str='obj'):
    """Imports NVil clipboard into SOP network."""
    # Check if there is anything to import.
    # For OBJ and FBX files, depending on chosen format.
    if not Path(TMP_PATH, f'{FILE_PREFIX_NVIL}.{format}').exists():
        set_msg('Nothing to import.', msg_important)
        return

    # Verify selection. Abort if first selected operator is not a SOP.
    sops = hou.selectedNodes()
    if len(sops) == 0:
        set_msg('Select at least one SOP.', msg_important)
        return

    sop = sops[0]
    if not type(sop) == hou.SopNode:
        set_msg('Selected operator is not a SOP.', msg_important)
        return

    # Create SOP network that handles the import.
    # The network is slightly different for each file format.
    parent = sop.parent()
    input = parent.createNode('file')
    input.setParms({
        'file': str(Path(TMP_PATH, f'{FILE_PREFIX_NVIL}.{format}'))
    })
    input.setInput(0, sop)
    stash = parent.createNode('stash')
    attrib_delete : hou.SopNode = None
    attrib_string_edit : hou.SopNode = None
    attrib_rename : hou.SopNode = None

    if format == 'fbx':
        # Remove unnecessary FBX attributes.
        attrib_delete = parent.createNode('attribdelete')
        attrib_delete.setParms({
            'ptdel': 'fbx*'
        })
        attrib_delete.setInput(0, input)
        stash.setInput(0, attrib_delete)
    else:
        # Remove hierarchy separators from "path" attribute.
        attrib_string_edit = parent.createNode('attribstringedit')
        attrib_string_edit.setParms({
            'primitiveattribs': 1,
            'primattriblist': 'path',
            'from0': '/*',
            'to0': '*'
        })
        # Rename the "path" attribute to "name".
        attrib_string_edit.setFirstInput(input)
        attrib_rename = parent.createNode('attribute')
        attrib_rename.setParms({
            'frompr0': 'path',
            'topr0': 'name'
        })
        attrib_rename.setFirstInput(attrib_string_edit)
        stash.setInput(0, attrib_rename)
    stash.parm('stashinput').pressButton()

    # Remove all temporary operators.
    if format == 'fbx':
        attrib_delete.destroy()
    else:
        attrib_string_edit.destroy()
        attrib_rename.destroy()
    input.destroy()

    # Tidy up the network.
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


def load_from_obj(
        path: PureWindowsPath,
        new_scene: bool=False,
        coordinates: int=1,
        scale: float=1.0,
        divide_into_obj: bool=True,
        divide_into_meshes: bool=True,
        ignore_materials: bool=True,
        replace_by_name: bool=False,
        import_into: str='',
        import_into_file_group: bool=False,
        surface_type: int=2
    ):
    """Generates instructions for NVil to load a specified OBJ file."""
    instructions = [
        f'TID Common Modeling Shortcut Tools >> ' \
        f'P_LoadFromObjFile[' \
        f'{str(path)}, ' \
        f'{new_scene}, ' \
        f'{coordinates}, ' \
        f'{scale}, ' \
        f'{divide_into_obj}, ' \
        f'{divide_into_meshes}, ' \
        f'{ignore_materials}, ' \
        f'{replace_by_name}, ' \
        f'{import_into}, ' \
        f'{import_into_file_group}, ' \
        f'{surface_type}' \
        f']'
    ]
    write_instructions(instructions)
    write_message()


def load_from_fbx(
        path: PureWindowsPath,
        new_scene: bool=False,
        coordinates: int=3,
        scale: float=1,
        divide_into_obj: bool=True,
        flip_tex_v: bool=True,
        ignore_materials: bool=True,
        map_fbx_hierarchy: bool=True,
        replace_by_name: bool=False,
        import_into: str='',
        import_into_file_group: bool=False,
        surface_type: int=2):
    """Generates instructions for NVil to load a specified FBX file."""
    instructions = [
        f'TID Common Modeling Shortcut Tools >> ' \
        f'P_LoadFromFbxFile[' \
        f'{str(path)}, ' \
        f'{new_scene}, ' \
        f'{coordinates}, ' \
        f'{scale}, ' \
        f'{divide_into_obj}, ' \
        f'{flip_tex_v}, ' \
        f'{ignore_materials}, ' \
        f'{map_fbx_hierarchy}, ' \
        f'{replace_by_name}, ' \
        f'{import_into}, ' \
        f'{import_into_file_group}, ' \
        f'{surface_type}, ' \
        f']'
    ]
    write_instructions(instructions)
    write_message()


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
