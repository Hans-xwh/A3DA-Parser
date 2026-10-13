from ..A3DA_Core import ImportConfig
from ..DIVA_DSC.DSC_Core import A3daFolder, build_OpCodes, DscToFrame
from . import A3DA_Camera

import bpy
import time
import struct
import re
from pathlib import Path

def splitCamRead(a3da_path:str, dsc_path:str, config:ImportConfig):
    def natural_key(filename: str):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', filename)]     #I uhh googled this one
    
    print("Deez nuts!")
    start_time = time.time()

    folder = Path(a3da_path)
    dsc = Path(dsc_path)
    if folder.is_file():
        folder = folder.parent

    ## Folder ##
    a3da_folder = A3daFolder()
    a3da_folder.populate(folder)
    a3da_list:list[str] = sorted(a3da_folder.files.keys(), key=natural_key)

    #### DSC Read ####
    ## Build OpCodes ##
    opcodes = build_OpCodes(config.game)

    ## Define read config ##
    if config.endian == "BIG":
        endiannes = ">"
    elif config.endian == "LITTLE":
        endiannes = "<"
    else:
        if config.game in ('FT', 'F', 'MGF'):
            endiannes = "<"
        elif config.game == 'F2':
            endiannes = ">"

    if config.game in ('FT', 'F'):
        header_size = 4
    elif config.game == 'F2':
        header_size = 72
    elif config.game == 'MGF':
        header_size = 72

    with dsc.open('rb') as f:
        current_time = 0
        current_branch = 0
        target_branch = 2 if config.use_pv_branch else 1

        print("--- Reading DSC ---")
        header = f.read(header_size)

        while True:
            data = f.read(4)

            if not data or data == b"EOFC": break

            opcode = struct.unpack(f'{endiannes}i', data)[0]
            length, name = opcodes.get(opcode)

            params = []
            if length > 0:
                data = f.read(4*length)
                params = struct.unpack(f'{endiannes}{length}i', data)

            ## OPCODES ##
            if opcode == 1: #TIME - L:1
                current_time = params[0]

            elif opcode == 65: #PV_BRANCH_MODE - L:1
                current_branch = params[0]

            elif opcode == 13: #DATA_CAMERA - L:2
                mode, id = params
                filename = a3da_list[id-1]

                if not a3da_folder.imported[filename] and current_branch in (target_branch, 0):
                    A3DA_Camera.startReadingCam(
                        a3da_path=a3da_folder.files[filename],
                        frameOffset= DscToFrame(current_time),
                        config= config
                    )
                    
                    if config.place_markers: bpy.context.scene.timeline_markers.new(name=filename, frame=DscToFrame(current_time))

                    a3da_folder.imported[filename] = True

    print(f'\n[splitCamRead] Total import time: {round(time.time() - start_time, 4)} seconds.')





            

    pass
