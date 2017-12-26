# coding=utf8

# ===== export_from_houdini.py
#
# Copyright (c) 2017 Artur J. Żarek
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


def main():
    selection = hou.selectedNodes()
    if len(selection) > 1:
        hou.ui.displayMessage('Only first object will be exported.', severity=hou.severityType.Warning)
    elif len(selection) == 0:
        hou.ui.displayMessage('Nothing to export!', severity=hou.severityType.Error)
        sys.exit(1)

    if not isinstance(selection[0], hou.SopNode):
        hou.ui.displayMessage('Select a single SOP node.', severity=hou.severityType.Error)
        sys.exit(2)

    # Paths and files
    appdata_path = hou.getenv('APPDATA')
    nvil_appdata = os.path.join(appdata_path, 'DigitalFossils', 'NVil')
    clipboard_file_path = os.path.join(nvil_appdata, 'Media', 'Clipboard', 'ClipboardObj.obj')
    instructions_filename = 'NVil Instructions.txt'
    message_filename = 'NVil Message_In.txt'

    # First, save the selected SOP to NVil clipboard directory.
    selection[0].geometry().saveToFile(clipboard_file_path)

    # Then, save instructions for NVil.
    instructions = ['TID Common Modeling Shortcut Tools >> Clipboard Paste']
    abs_instructions_file_path = os.path.join(nvil_appdata, instructions_filename)
    with open(abs_instructions_file_path, 'w') as out:
        for instruction in instructions:
            out.write(instruction)

    # Finally, tell NVil to import the file.
    abs_message_file_path = os.path.join(nvil_appdata, message_filename)
    try:
        with open(abs_message_file_path, 'w') as out:
            out.write('Execute External Instruction File')
    except IOError:
        hou.ui.displayMessage('Target file locked.\n Switch to NVil and check if the import dialog is closed.',
                              severity=hou.severityType.Error)
        sys.exit(3)

    hou.ui.setStatusMessage('Done. You can now switch to NVil.', severity=hou.severityType.Message)


if __name__ == '__main__':
    main()
