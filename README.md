# NVil-Houdini AppLink
This program enables quick geometry interchange between NVil and Houdini.

## Requirements
Microsoft Windows, Houdini, NVil and some Python 2.x version installed (2.x version bound with Houdini should suffice, if you have configured system paths to it)

In your firewall, you also neeed to allow Houdini's executables (```houdini.exe```, ```hindie.exe```, etc.) to establish *localhost* TCP connections via port 18811 because AppLink uses RPC for communication with Houdini.

## Installation
To install the AppLink, clone or download the repository and extract ```nvil-houdini``` directory from the archive to ```HOUDINI_USER_PREF_DIR\python2.7libs```. For example: ```C:\Users\YourName\Documents\houdini16.5\python2.7libs```. Create the folder if it doesn't exist.

Copy ```nvil-applink``` shelf from ```/toolbar``` directory to ```HOUDINI_USER_PREF_DIR\toolbar```. Then put this shelf on your toolbar (look for *NVil AppLink*).

Open ```/composite_tools/export_to_houdini.xml``` for editing and:

- Search and replace ```pathToHoudiniFolder``` with your path to *HFS*, for example:
```C:\Program Files\Side Effects Software\Houdini 16.5```

- Search and replace ```pathToHoudiniPythonLibs``` with your path to Houdini Python libraries in your *HOUDINI_USER_PREF_DIR* folder, for example:
```C:\Users\YourName\Documents\houdini16.5\python2.7libs```

Then, start NVil and import the modified composite tool with *Composite Tools->Import Composite Tool*.

## Instructions
AppLink utilizes NVil's clipboard functionality. Geometry file exported from NVil or Houdini is stored in ```ClipboardObj.obj``` Wavefront OBJ file inside ```%APPDATA%\DigitalFossils\NVil\Media\Clipboard```. It will get overwritten on each import/export operation.

For communication with Houdini, the program uses RPC calls, so the ```hrpyc``` server must be running.

The AppLink shelf contains the following tools:

- *Start RPC Server* - starts the RPC server,
- *Export to NVil* - exports geometry from the currently selected SOP to NVil's clipboard location.

### Exporting geometry from Houdini
Select a single SOP node and click *Export to NVil* shelf button. After *"Done. You can now switch to NVil"* message appears in the status bar, you can switch to NVil and confirm the import. Your geometry will be merged with the current scene.

### Exporting geometry from NVil
In Houdini, make sure that at least one SOP node is selected. Switch to NVil, select objects that you want to export and start *"Composite Tools->Export to Houdini"* tool. Confirm export options and then switch back to Houdini. You will find a new hardlocked *file* surface operator piped to the SOP node that you have selected.
