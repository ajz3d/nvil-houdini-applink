# coding=utf8

# ===== nvil_houdini_applink.py
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
import sys
import os
import time
import rpyc
from pathlib import Path, PurePath


PATH_NVIL_APPDATA = Path(hou.getenv("NVIL_APPDATA"))
PATH_CLIPBOARD = Path(PATH_NVIL_APPDATA, 'Media/Clipboard')
INSTRUCTIONS_FILE = 'NVil Instructions.txt'
MESSAGE_FILE = 'NVil Message_In.txt'
FILE_FBX = PurePath('ClipboardFbx.fbx')
FILE_OBJ = PurePath('ClipboardObj.obj')


def houdini_export(format: str = 'obj'):
    """Merges and exports selected SOPs to NVil clipboard file."""
    # Abort if something is not right with NVIL_APPDATA and CLIPBOARD paths.
    # clipboard_path = Path(nvil_appdata_path, CLIPBOARD)
    if not is_path_valid(PATH_NVIL_APPDATA):
        return

    if not is_path_valid(PATH_CLIPBOARD):
        return

    sops = hou.selectedNodes()

    # Check if anything is selected.
    if len(sops) == 0:
        hou.ui.setStatusMessage('Nothing to export',
                                severity=hou.severityType.ImportantMessage)
        return

    # Abort if one of the nodes is not a SOP.
    for sop in sops:
        if type(sop) is not hou.SopNode:
            hou.ui.setStatusMessage(f'Wrong candidate: {type(sop)}.',
                                    severity=hou.severityType.Error)
            return

    # All selected nodes will be merged together.
    merge = sops[0].parent().createNode('merge')
    groups_from_name = sops[0].parent().createNode('groupsfromname')

    # Start creating temporary network.
    for sop in sops:
       if not type(sop) == hou.SopNode:
           continue
       merge.setNextInput(sop)

    groups_from_name.setInput(0, merge)

    # Two options: FBX or OBJ.
    if format == 'fbx':
        rop = sops[0].parent().createNode('rop_fbx')
        rop.setParms({
            'sopoutput': str(Path(PATH_CLIPBOARD, 'ClipboardFbx.fbx')),
            'exportkind': False,
            'buildfrompath': True,
            'pathattrib': 'name'
        })
    else:
        rop = sops[0].parent().createNode('rop_geometry')
        rop.setParms({
            'sopoutput': str(Path(PATH_CLIPBOARD, FILE_OBJ))
        })
    rop.setInput(0, groups_from_name)
    rop.parm('execute').pressButton()

    rop.destroy()
    groups_from_name.destroy()
    merge.destroy()

    # Save instructions for NVil.
    # instructions = ['TID Object Shortcut Tools >> Create Box #']
    instructions = ['TID Common Modeling Shortcut Tools >> Clipboard Paste']
    instructions_path = Path(PATH_NVIL_APPDATA, INSTRUCTIONS_FILE)
    with instructions_path.open('w', encoding='utf-8') as target_file:
        for instruction in instructions:
            target_file.write(instruction)
        target_file.write('\n')

    # Write a message that tells NVil to load these instructions.
    message = 'Execute External Instruction File'
    message_path = Path(PATH_NVIL_APPDATA, MESSAGE_FILE)

    # If import dialog is open, this will throw IOError,
    # so an exception handle is required.
    try:
        with message_path.open('w', encoding='utf-8') as target_file:
            target_file.write(message)
    except IOError:
        hou.ui.setStatusMessage(
            'Message file locked.' \
            'Switch to NVil and check if the import dialog is closed.',
            severity=hou.severityType.Error
        )
        return

    hou.ui.setStatusMessage('Done exporting. You can switch to NVil.')


def houdini_import(format: str='obj'):
    """Imports NVil clipboard into SOP network."""
    # First check if paths exist.
    if not is_path_valid(PATH_NVIL_APPDATA):
        return

    if not is_path_valid(PATH_CLIPBOARD):
        return

    # Check if there's anything to import.
    file_missing = False

    if format == 'fbx':
        if not Path(PATH_CLIPBOARD, FILE_FBX).is_file():
            file_missing = True
    else:
        if not Path(PATH_CLIPBOARD, FILE_OBJ).is_file():
            file_missing = True

    if file_missing:
        hou.ui.setStatusMessage('Nothing to import.',
                                severity=hou.severityType.ImportantMessage)
        return

    # Verify selection.
    sops = hou.selectedNodes()

    if len(sops) == 0:
        hou.ui.setStatusMessage('Select a SOP.',
                                severity=hou.severityType.ImportantMessage)
        return

    sop = sops[0]
    parent = sop.parent()

    if not type(sop) == hou.SopNode:
        hou.ui.setStatusMessage('Selected operator is not a SOP',
                                severity=hou.severityType.ImportantMessage)
        return

    # Import cases for FBX and OBJ.
    if format == 'fbx':
        # TODO: Implement FBX import.
        return
    else:
        input = parent.createNode('file')
        input.setParms({
            'file': str(Path(PATH_CLIPBOARD, FILE_OBJ))
        })

    input.setInput(0, sop)
    stash = parent.createNode('stash')
    stash.setInput(0, input)
    stash.parm('stashinput').pressButton()
    input.destroy()
    stash.moveToGoodPosition(move_inputs=False, move_unconnected=False)

    hou.ui.setStatusMessage('Done exporting.',
                            severity=hou.severityType.Message)


def is_path_valid(path: Path) -> bool:
    """Checks if $NVIL_APPDATA path exists and is not a file."""
    if not path.exists() or not path.is_dir():
        hou.ui.setStatusMessage(
            f'Path {path} does not exist or is a file.',
            severity=hou.severityType.Error)
        return False
    return True


def export_from_houdini():
    selection = hou.selectedNodes()
    if len(selection) > 1:
        hou.ui.displayMessage('Only first object will be exported.',
                              severity=hou.severityType.Warning)
    elif len(selection) == 0:
        hou.ui.displayMessage('Nothing to export!',
                              severity=hou.severityType.Error)
        sys.exit(1)

    if not isinstance(selection[0], hou.SopNode):
        hou.ui.displayMessage('Select a single SOP node.',
                              severity=hou.severityType.Error)
        sys.exit(2)

    # Paths and files
    instructions_filename = 'NVil Instructions.txt'
    message_filename = 'NVil Message_In.txt'

    # First, save the selected SOP to NVil clipboard directory.
    selection[0].geometry().saveToFile(get_path()['clipboard_file_path'])

    # Then, save instructions for NVil.
    instructions = ['TID Common Modeling Shortcut Tools >> Clipboard Paste']
    abs_instructions_file_path = os.path.join(get_path()['nvil_appdata'],
                                              instructions_filename)
    with open(abs_instructions_file_path, 'w') as out:
        for instruction in instructions:
            out.write(instruction)

    # Finally, tell NVil to import the file.
    abs_message_file_path = os.path.join(get_path()['nvil_appdata'],
                                         message_filename)
    try:
        with open(abs_message_file_path, 'w') as out:
            out.write('Execute External Instruction File')
    except IOError:
        hou.ui.displayMessage('Target file locked.\n '
                    'Switch to NVil and check if the import dialog is closed.',
                    severity=hou.severityType.Error)
        sys.exit(3)

    hou.ui.setStatusMessage('Done. You can now switch to NVil.',
                            severity=hou.severityType.Message)


def export_from_nvil(port=18811):
    main_module = 'nvil_houdini_applink'
    try:
        conn = rpyc.classic.connect('localhost', port)
        conn.execute('import ' + main_module)
        conn.execute('reload(' + main_module + ')')
        conn.execute(main_module + '.load_geo()')
    except Exception:  # TODO: Too general.
        print("There were errors. Have you started Houdini's RPC server?")
        time.sleep(5)
        sys.exit(1)


def load_geo():
    """Load geometry from NVil's clipboard path."""
    path = get_current_network_editor(hou.ui.curDesktop()).pwd().path()
    # Abort if not inside an ObjNode.
    if not isinstance(hou.node(path), hou.ObjNode):
        hou.ui.displayMessage('You neet to be inside an OBJ node.',
                              severity=hou.severityType.Error)
        sys.exit(2)

    selected = hou.selectedNodes()
    if len(selected) != 0 and isinstance(selected[0], hou.SopNode):
        selected = selected[0]
    elif len(selected) == 0:
        selected = None
    elif len(selected) != 0 and not isinstance(selected[0], hou.SopNode):
        hou.ui.displayMessage('Selected node must be of hou.SopNode type.',
                              severity=hou.severityType.Error)
        sys.exit(3)

    file_sop = hou.node(path).createNode('file')
    file_sop.setParms({'file': get_path()['clipboard_file_path']})
    file_sop.setFirstInput(selected)

    file_sop.setDisplayFlag(True)
    file_sop.setHardLocked(True)
    file_sop.setSelected(True, clear_all_selected=True)
    file_sop.moveToGoodPosition()


def get_path():
    """Returns required paths."""
    # appdata_path = hou.getenv('APPDATA')
    appdata_path = hou.expandString("$WIN_APPDATA")
    nvil_appdata = os.path.join(appdata_path, 'Roaming', 'DigitalFossils', 'NVil')
    clipboard_file_path = os.path.join(nvil_appdata, 'Media', 'Clipboard',
                                       'ClipboardObj.obj')
    return {'nvil_appdata': nvil_appdata,
            'clipboard_file_path': clipboard_file_path}


def get_current_network_editor(desktop):
    """Returns the currently active Network Editor window.
    :type desktop: hou.Desktop
    :rtype: hou.NetworkEditor"""
    for pane in desktop.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
            return pane


if __name__ == '__main__':
    export_from_nvil()
