# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import json
import struct
from pathlib import Path
import bpy

## Internal Config ##
OpCode_DB:Path = Path(__file__).parent / "db.json" 

class Field:
    def __init__(self):
        self.light:str = None
        self.stage:str = None
        self.auth_3d_lists:dict[int, str] = dict()
        self.frame_list:dict[int, int] = dict()  #Defines the starting point. Thanks to Koren for figuring this out.
        #0/-4: start from beginning, -1/-5: continue from song frame, -2/-6: continue from auth 3d frame, -3 if first: start from beginning, -3 if cont: continue from auth 3d frame

### Sequencial Classes ###
class A3daFolder:
    def __init__(self):
        self.files:dict[str, Path] = {}
        self.imported:dict[str, bool] = {}


### DSC Core ###
def DscToFrame(dsc) -> int:  # Convert Diva Script time to Blender frames. Always integers
    framerate = bpy.context.scene.render.fps
    framerate = 60
    # (dsc / 10000) * (framerate / 10) == dsc * framerate / 100000
    return round((dsc / 10000) * (framerate / 10))


### DSC Helper ####
def InsertConstantKey(obj:bpy.types.Object, value:int, frame:int):
        if not obj:
            print(f'[InsertConstantKey] Object does not exist!!!')
            return

        obj.location.y = value
        obj.keyframe_insert(data_path='location', index=1, frame=frame)
        #fcurve = obj.animation_data.action.fcurves.find(data_path='location', index=1)
        fcurve = obj.animation_data.action.fcurve_ensure_for_datablock(datablock=obj, data_path='location', index=1)
        key = fcurve.keyframe_points[-1]
        key.interpolation = 'CONSTANT'

### DSC Main ###
def build_OpCodes(target_game:str, json_path:Path=OpCode_DB) -> dict[int, tuple]:
    match target_game:
        case 'FT':
            target_game = 'info_FT'
        case 'F':
            target_game = 'info_f'
        case 'F2':
            target_game = 'info_F2'
        case 'X':
            target_game = 'info_X'
        case 'MGF':
            target_game = 'info_F2' #idk if this is right
        case _:
            pass
        #info_A12 is most likely non-FutureTone Arcade
    
    #Build lookup table of OpCode lengths, indexed by id (opcode)
    # mappings[opcode] = (length, name)
    mappings:dict[int, tuple] = {}

    print(f"[build_OpCodes] Looking opcodes for: {target_game}")
    with json_path.open('r') as db:
        json_data = json.load(db)
        for name, contents in json_data.items():
            for version, data in contents.items():
                if version == target_game:
                    opcode = int(data["id"])
                    mappings[opcode] = (
                        data["len"],
                        name
                    )
                    #print(opcode, mappings[opcode])
    
    return dict(sorted(mappings.items()))

def read_dsc_generic(dsc_path:Path, opcodes:dict[int, tuple], to_run:callable=None, verbose=False):
    with open(dsc_path, "rb") as f:
        header = f.read(12)     #Header is always 12 bytes i think, at least for FT

        print("--- Reading DSC ---")
        while True:     #Main loop to read dsc
            #Read opcode
            data = f.read(4)

            if not data:    #Break on end of file
                break

            opcode = struct.unpack('<i', data)[0]
            length, name = opcodes.get(opcode)

            #Read params
            params = []
            if length > 0:
                data = f.read(4*length)
                params = struct.unpack(f'{length}i', data)

            #Print command
            if verbose:
                param_string = ""
                for param in params:
                    param_string += str(param)
                    if param != params[-1]:
                        param_string += ", "
                print(f'{name}({param_string});')

            #opcode: id of the command
            #name: name of the command
            #length: length of the parameters
            #params: list of parameters

            #Send command to desired function
            if to_run:
                to_run(opcode, params)
    pass