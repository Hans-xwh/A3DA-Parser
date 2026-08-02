# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from . DSC_Core import Field, A3daFolder, DscToFrame, InsertConstantKey
from . DSC_FT import ChangeField_FT
from ..A3DA_Core import ImportConfig, ensureAction
from ..A3DA_Import.A3DA_Objects import createEmpty, assignParent
from .. import Parse_A3DA

import bpy
import time
from pathlib import Path


### DSC Reading ###
def readDsc_TXT(dsc_path:Path, a3da_folder:A3daFolder, fields:dict[int, Field], config:ImportConfig):
    print("\n[readDsc_TXT] Reading DSC file in text mode...")
    dsc = dsc_path.open(mode='r')

    target_branch = 2 if config.use_pv_branch else 1    #2=failure 1=succes 0=global (globals are always read)
    #target_branch = 2
    current_branch = 0
    current_time = 0

    last_field_id = 0


    for line in dsc:
        line = line.strip()
        #print(line)

        command, data = line.split('(')
        if command in ("PV_END", "END"): continue
        data = int(data.strip(');'))

        if command == "TIME":
            current_time = data
            print(f"[readDsc_TXT] Current time: {current_time} ({DscToFrame(current_time)})")

        elif command == "PV_BRANCH_MODE":
            current_branch = data

        elif command == "CHANGE_FIELD":
            #if current_branch != 0 and current_branch != target_branch: #Skip commands not on current branch
            #    print(f'Branch "{current_branch}" skipped!')
            #    continue
            
            if data in fields:
                print(f"[readDsc_TXT] Changing fields: {last_field_id} -> {data}")
                ChangeField_FT(
                    new_field= fields[data],
                    old_field= fields[last_field_id] if last_field_id in fields else None,
                    time= current_time,
                    a3da_folder= a3da_folder,
                    config= config
                )
                last_field_id = data
            else:
                print(f"[readDsc_TXT] WARNING: Field {data} not found!!!")

        else: continue