# coding=utf8

# ===== nvil_houdini_applink.py
#
# Copyright (c) 2017-2019 Artur J. Żarek
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
