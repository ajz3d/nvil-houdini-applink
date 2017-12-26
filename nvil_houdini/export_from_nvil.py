# coding=utf8

# ===== export_from_nvil.py
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
import rpyc
import os
import time


def main(port=18811):
    main_module = 'nvil_houdini.export_from_nvil'
    try:
        conn = rpyc.classic.connect('localhost', port)
        conn.execute('import ' + main_module)
        conn.execute('reload(' + main_module + ')')
        conn.execute(main_module + '.load_geo()')
    except Exception:  # TODO: Too general.
        print("There were errors. Have you started Houdini's RPC server?")
        time.sleep(3)
        sys.exit(1)


def load_geo():
    selected_nodes = hou.selectedNodes()
    if len(selected_nodes) != 1:
        hou.ui.displayMessage('You need to select a single SOP node.', severity=hou.severityType.Error)
        sys.exit(2)
    selection = selected_nodes[0]

    if not isinstance(selection, hou.SopNode):
        hou.ui.displayMessage('Selected node must be a SOP.', severity=hou.severityType.Error)
        sys.exit(2)

    nvil_import = hou.node(selection.parent().path()).createNode('file')
    nvil_import.setFirstInput(selection)
    nvil_import.moveToGoodPosition()

    appdata_path = hou.getenv('APPDATA')
    nvil_appdata = os.path.join(appdata_path, 'DigitalFossils', 'NVil')
    clipboard_file_path = os.path.join(nvil_appdata, 'Media', 'Clipboard', 'ClipboardObj.obj')

    nvil_import.setParms({'file': clipboard_file_path})
    nvil_import.setDisplayFlag(True)
    selection.setRenderFlag(False)
    nvil_import.setHardLocked(True)


if __name__ == '__main__':
    main()
