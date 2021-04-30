# Data Owner Tools Executables
Fork of https://github.com/mitre/data-owner-tools. All python files should conform to existing command line documentation. Command line and GUI tools should be interoperable. Executables built using pyinstaller version 4.2.
## Change Log
### garble.py
- Moved majority of code into callable function
- Moved argparse code into \_\_name\_\_ == "\_\_main\_\_" check
- Added parameter for output directory
- Changed subprocess call to call cli.hash from anonlinkclient import
- Added return text for successful write
### linkidtopatid.py
- Moved majority of code into callable function
- Moved argparse code into \_\_name\_\_ == "\_\_main\_\_" check
- Function returns messages instead of printing
- No longer requires headerless PII csv file
### GarbleExecutable.py
- WxPython GUI wrapper for functions inside garble.py
- Able to be built into single executable using pyinstaller
- Currently includes Salt and Schema files inside the exe
- Runs multiprocessing.freeze_support() to enable multiprocessing in the built executable.
### Link-IDs-Executable.py
- WxPython GUI wrapper for functions inside linkidtopatid.py
- Able to be built into single executable using pyinstaller
