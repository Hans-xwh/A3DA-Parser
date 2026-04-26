# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .DSC_Core import Field, A3daFolder, build_OpCodes, DscToFrame, InsertConstantKey
from ..A3DA_Core import ImportConfig
from ..A3DA_Import.A3DA_Objects import createEmpty
from .. import Parse_A3DA

from pathlib import Path
import struct
import bpy

### Blender funcs ###
def ChangeField_FT(new_field:Field, old_field:Field|None, time:int, a3da_folder:A3daFolder, config:ImportConfig, branch:int=0):
    frame = DscToFrame(time) + config.frame_offset
    frame = DscToFrame(time)

    #Hide old field
    if old_field: #and len(new_field.auth_3d_lists) > 0:
        for old_a3da in old_field.auth_3d_lists.values():
            old_root = bpy.context.scene.objects.get(old_a3da)

            #action = ensureAction(old_root)
            InsertConstantKey(old_root, 10000, frame)
            #old_root.location.y = 10000
            #old_root.keyframe_insert(data_path='location', index=1, frame=frame)
            #fcurve = old_root.animation_data.action.fcurve_ensure_for_datablock(datablock= old_root, data_path='location', index=1)
            #key = fcurve.keyframe_points[-1]
            #key.interpolation = 'CONSTANT'

    #Hide static
    if old_field and old_field.stage:
        old_stage = bpy.context.scene.objects.get(old_field.stage)
        if not old_stage:
            old_stage = createEmpty(old_field.stage)
        InsertConstantKey(old_stage, 10000, frame)

    #Handle static stages
    if new_field.stage:
        new_stage = bpy.context.scene.objects.get(new_field.stage)        
        if not new_stage:
            new_stage = createEmpty(new_field.stage)
            if config.auto_gnd: #Auto assign stage gnd
                gnd = bpy.context.scene.objects.get(f'{new_field.stage}_GND')
                if gnd:
                    gnd.parent = new_stage
        #new_stage["IsStage"] = True

        #Force load first field
        if config.force_load_first or branch == 2:     #This will add the static stage to the list of objects to import, so it will be loaded. Only on branch 2
            fStageName = f'{new_field.stage}_EFF_001'   #First stage name
            if fStageName in a3da_folder.files:
                new_field.auth_3d_lists[len(new_field.auth_3d_lists)] = fStageName
                new_field.frame_list[len(new_field.auth_3d_lists)] = 0          #Changed
                print(f'[ChangeField_FT] Force loading stage static: "{fStageName}"')
        
        if old_field:   #Make sure it always starts hidden.
            InsertConstantKey(new_stage, 10000, -1)

        InsertConstantKey(new_stage, 0, frame)

    #Import and show new field
    for id, a3daName in new_field.auth_3d_lists.items():
        #Import if not already imported
        if a3daName not in a3da_folder.files:
            print(f'[ChangeField_FT] File {a3daName} requested but not found!!!')
            continue

        if a3da_folder.imported[a3daName] == False:
            if new_field.frame_list and new_field.frame_list.get(id) in (0, -4):
                startFrame = frame
            else:
                startFrame = frame      #Not sure if this is right
            
            print(f'[ChangeField_FT] Importing file: "{a3daName}" with offset {startFrame}')
            Parse_A3DA.startReading(
                a3da_path= a3da_folder.files[a3daName],
                frameOffset= startFrame,
                config= config
            )
            bpy.context.view_layer.update()
            a3da_folder.imported[a3daName] = True

        #Show new field & static stage
        new_root = bpy.context.scene.objects.get(a3daName)
        

        if old_field:
            InsertConstantKey(new_root, 10000, -1)     #Make sure obj starts hidden.
        InsertConstantKey(new_root, 0, frame)       #Show object on this frame


### Funcs ###
def read_dsc_FT(dsc_path:Path, a3da_folder:A3daFolder, fields:dict[int, Field], config:ImportConfig):
    verbose = False  

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
    

    ## Now read the file ##
    with dsc_path.open('rb') as f:
        current_time = 0
        current_branch = 0
        target_branch = 2 if config.use_pv_branch else 1
        last_field_id = 0
        last_branched_field = 0

        print("--- Reading DSC ---")
        header = f.read(header_size)     #Header is always 12 bytes for FT & F i think, 72 for F2 and MGF and maybe X
        #print(header.hex())

        while True:     #Main loop to read dsc
            #Read opcode
            data = f.read(4)
            #print(data)

            if not data or data == b"EOFC":    #Break on end of file
                break

            opcode = struct.unpack(f'{endiannes}i', data)[0]
            length, name = opcodes.get(opcode)

            #Read params
            params = []
            if length > 0:
                data = f.read(4*length)
                params = struct.unpack(f'{endiannes}{length}i', data)

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

            ### Time to change fields and stuff ###
            if opcode == 1 : #TIME - L:1
                current_time = params[0]

            elif opcode == 65: #PV_BRANCH_MODE - L:1
                current_branch = params[0]

            elif opcode == 32: #PV_END - L:0
                bpy.context.scene.frame_end = DscToFrame(current_time) #+ config.frame_offset

            elif opcode == 14: #CHANGE_FIELD - L:1
                if current_branch != 0 and current_branch != target_branch:     #Skip commands not on current branch
                    print(f'Branch {current_branch} skipped!')
                    continue

                new_field_id = params[0]
                if new_field_id in fields:
                    print(f"[readDsc_TXT] Changing fields: {last_field_id} -> {new_field_id}")
                    ChangeField_FT(
                        new_field= fields[new_field_id],
                        old_field= fields[last_field_id] if last_field_id in fields else None,
                        time= current_time,
                        a3da_folder= a3da_folder,
                        config= config,
                        branch= current_branch
                    )
                    last_field_id = new_field_id
                else:
                    print(f"[readDsc_TXT] WARNING: Field {new_field_id} not found!!!")

    pass