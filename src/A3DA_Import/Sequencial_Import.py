# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

# Behold, dsc script reading & pv field reading.
from ..A3DA_Core import ImportConfig
from ..DIVA_DSC.DSC_Core import A3daFolder, Field
from ..DIVA_DSC.DSC_FT import read_dsc_FT
from ..DIVA_DSC.DSC_txt import readDsc_TXT

import bpy
import time
from pathlib import Path



### PV Field ###
def readPvField_FT(pv_field:Path, pv_num:str, fields:dict[int, Field]):
    field_file = pv_field.open(mode='r')
    pv_exists = False

    print(f'[readPvField_FT] Reading PV field file for PV_{pv_num}...')
    for line in field_file:
        line = line.strip()

        params, data = line.split('=')
        params = params.split('.')
        if params[0] == f'pv_{pv_num}':
            pv_exists = True
            if params[2] == 'length':
                continue

            if int(params[2]) not in fields:
                fields[int(params[2])] = Field()
            field = fields[int(params[2])]

            ## Read data ##
            if params[3] == 'auth_3d_list':         #Which file to load
                if params[4] != 'length':
                    field.auth_3d_lists[int(params[4])] = data

            elif params[3] == 'auth_3d_frame_list': #What frame to start the anim of that file
                if params[4] != 'length':
                    field.frame_list[int(params[4])] = int(data)

            elif params[3] == 'stage':      #Not sure what this is usefull for
                field.stage = data

            elif params[3] == 'light':      #Which light file to load
                field.light = data
            
        elif pv_exists:
            break       #If all the fields for current pv are already read, stop reading the file



    field_file.close()
    print('[readPvField_FT] All fields read')


def readPvField_F2nd(pv_field:Path, pv_num:str, fields:dict[int, Field]):
    pfl = pv_field.open(mode='rb')
    pv_exists = False

    print(f'[readPvField_F2nd] Reading PV field file for PV_{pv_num}...')
    header = pfl.read(64)

    ## Divafile handling ##
    if header[:8] == b"DIVAFILE":
        print("ERROR: Encrypted DIVAFILE can't be read. Decrypt it first!!!")
        raise Exception
        return None
    
    ## File reading ##
    while True:
        chunk = pfl.readline()
        if not chunk: break

        chunk= chunk.split(b'\x00')[0].decode("utf-8").strip()
        ## Chunk is now a pf_field line

        #Same code as in FT
        params, data = chunk.split('=')
        params = params.split('.')
        if params[0] == f'pv_{pv_num}':
            pv_exists = True
            if params[2] == 'length':
                continue

            if int(params[2]) not in fields:
                fields[int(params[2])] = Field()
            field = fields[int(params[2])]

            ## Read data ##
            if params[3] == 'auth_3d_list':         #Which file to load
                if params[4] != 'length':
                    field.auth_3d_lists[int(params[4])] = data
            elif params[3] == 'auth_3d_frame_list': #What frame to start the anim of that file
                if params[4] != 'length':
                    field.frame_list[int(params[4])] = int(data)
            elif params[3] == 'stage':      #Not sure what this is usefull for
                field.stage = data
            elif params[3] == 'light':      #Which light file to load
                field.light = data

        elif pv_exists:
            break       #If all the fields for current pv are already read, stop reading the file

    pfl.close()
    print('[readPvField_F2nd] All fields read')


### Sequencial Read Funcs ###
def sequencialRead_FT(a3da_path:str, pv_field_path:str, dsc_path:str, config:ImportConfig):
    print("\nSequencia Read start")
    startTime = time.time()

    #vars
    fields:dict[int, Field] = {}

    #get Paths
    pv_field = Path(pv_field_path)
    dsc = Path(dsc_path)

    #define folder and load all entries
    a3daFolder = A3daFolder()
    folder = Path(a3da_path)
    if folder.is_file():
        folder = folder.parent

    #print(f'[sequencialRead] folder: {folder}')
    for file in folder.iterdir():
        #print(f'[sequencialRead] Checking file: {file.name}')
        if file.is_file() and file.suffix in ('.a3da', '.A3DA'):
            a3daFolder.files[file.stem.upper()] = file
            a3daFolder.imported[file.stem.upper()] = False
            #print(f'Detected: {file.stem}')
        else: continue
    print(f'[sequencialRead] Detected {len(a3daFolder.files)} files')
    print(f'Selected game: {config.game}')

    #define pv_xxx number
    pv_num = dsc.stem.split('_')[1] #This a string
    print(f'PV_{pv_num}')

    #TODO optimize this shi

    #read pv field
    if pv_field.suffix.lower() == ".txt":
        readPvField_FT(pv_field, pv_num, fields)
    elif pv_field.suffix.lower() == ".pfl":
        readPvField_F2nd(pv_field, pv_num, fields)
    else:
        raise Exception

    #if config.game in ('FT', 'F', 'TXT'):
    #    readPvField_FT(pv_field, pv_num, fields)

    ## Read dsc file to get the order of the files to import ##
    if config.game == 'TXT':
        readDsc_TXT(dsc, a3daFolder, fields, config)

    if config.game in ('FT', 'F'):      #Diva FT and F use the same field system, dsc opcodes vary
        read_dsc_FT(dsc, a3daFolder, fields, config)

    if config.game == 'F2':
        #readPvField_FT(pv_field, pv_num, fields)
        read_dsc_FT(dsc, a3daFolder, fields, config)
        pass    

    if config.game == "MGF":
        #readPvField_FT(pv_field, pv_num, fields)
        read_dsc_FT(dsc, a3daFolder, fields, config)

    
    ## Report ##
    print()
    imported = 0
    for a3da_fileName in a3daFolder.files:
        if a3daFolder.imported[a3da_fileName]:
            print(f'-> "{a3da_fileName}"')
            imported += 1
    print(f'Imported {imported}/{len(a3daFolder.files)} files')
    print(f'\n[sequenclialRead] Total import time: {round(time.time() - startTime, 4)} seconds.')
    print('[sequencialRead] Finished!')