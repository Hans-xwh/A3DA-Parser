# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import ImportConfig
from .A3DA_Objects import A3daObject, A3daCV, animateObject, assignMesh, assignParent, createEmpty, cleanEmptiesNames, parseA3daObject, parseA3daCurve
from .A3DA_TexTransform import TexPattern, animateTex, animateTexPat
from .A3DA_HRC import HrcObject, M_Hrc, parseHrc, animateHrc

import bpy
from array import array
from pathlib import Path
import time
#import tracemalloc

### File reading
def readA3da(a3daFile, a3daName, stgpv=None, frameOffset=0, config:ImportConfig=None):
    startTime = time.time()
    #cleanEmptiesNames()
    print(f'\n[readA3da] Frame Offset: {frameOffset}')
    print(f'[readA3da] stgpv: {stgpv}')
    print(f'[readA3da] A3DA Prefix: {a3daName}')
    print(f'[readA3da] Reading A3DA...')

    rawBuffer:array = array('d')         #Array of doubles
    objects:dict[int, A3daObject] = {}   #Contains the objects
    objNames:dict[str, int] = {}         #Contains obj ids indexed by their names
    hrcObjects:dict[int, HrcObject] = {} #Contains HRC objects. Each one is a new armature
    m_hrcObjects:dict[int, M_Hrc] = {}    #Contains M_HRC objects.
    strandedCurves:dict[int, A3daCV] = {}   #Contains animation curves that aren't attached to an object.

    #### File reading ####
    line:str
    for line in a3daFile:
        line = line.strip()
        #print(line)

        if line.startswith(('#', '_')):
            continue
        params, data = line.split('=')
        params = params.split('.')

        ### Read object animation ###
        if params[0] == 'object' and config.use_objects:
            #0=Category(Object, camera), 1=id, 2=transform (trans, rot, scale, tex_transform)
            
            if params[1] == 'length': continue
            objId = int(params[1])

            ## Ensure object exits ##
            if objId not in objects:
                objects[objId] = A3daObject(Id=objId)
                objects[objId].bl_name = a3daName + str(objId)
                #print(f"[readA3da] Added A3DA Object #{objId}")
            obj = objects[objId]
            
            ## Object params ##
            if params[2] == 'name':
                obj.name = data
                objNames[data] = objId

            elif params[2] == 'parent_name':
                obj.parent = data

            elif params[2] == 'uid_name':
                obj.uid_name = data

            elif params[2] == 'morph' and config.use_morphs:
                obj.morph_name = data
                obj.morph = strandedCurves.get(data).channel

            elif params[2] == 'tex_pat' and config.use_tex_pat:
                if params[3] == 'length': continue

                texPatId = int(params[3])
                if texPatId not in obj.tex_pat:
                    obj.tex_pat[texPatId] = TexPattern(Id=texPatId)
                texPat = obj.tex_pat[texPatId]

                if params[4] == 'name':
                    texPat.tex_name = data
                elif params[4] == 'pat':
                    texPat.name = data
                    texPat.channel = strandedCurves.get(data).channel

            ## Object animation ##
            else:
                parseA3daObject(obj, params, data, frameOffset, config=config)
        
        ### Read "orphaned" curves ###
        elif params[0] == 'curve':
            if params[1] == 'length':
                continue

            curveId = int(params[1])
            if curveId not in strandedCurves:
                strandedCurves[curveId] = A3daCV(Id=curveId)
                print(f'[readA3da] Added stranded curve #{curveId}')

            parseA3daCurve(strandedCurves[curveId], params, data, frameOffset)
            if params[2] == 'name':
                strandedCurves[data] = strandedCurves.pop(curveId)   #Reindex by name instead of id for access later
                #All curves are declared befor any objects

        ### Read HRC animation ###
        elif params[0] in {'objhrc', 'm_objhrc'} and config.use_hrc:
             #Params: 1:HrcObjId, 3:nodeId, 4:transform/command, 5:axis, 6:"key", 7:keyId

            #Skip unused lines
            if params[1] == 'length':
                continue

            #Initialize
            HrcId = int(params[1])
            if params[0] == 'objhrc':
                if HrcId not in hrcObjects:
                    hrcObjects[HrcId] = HrcObject(Id=HrcId)
                    #hrcObjects[HrcId].bl_name = f'{a3daName}_HRC_{HrcId}'
                hrcObj = hrcObjects[HrcId]
            elif params[0] == 'm_objhrc':
                if HrcId not in m_hrcObjects:
                    m_hrcObjects[HrcId] = M_Hrc(Id=HrcId)
                hrcObj = m_hrcObjects[HrcId]
            hrcObj.bl_name = f'{a3daName}_HRC_{HrcId}'

            #Hrc params
            if params[2] == 'name':
                hrcObj.name = data

            elif params[2] == 'uid_name':
                hrcObj.uid_name = data

            #Node decoding
            elif params[2] == 'node' and params[3] != 'length':
                parseHrc(hrcObj, params, data, frameOffset, rawBuffer)

            #Instance decoding for M_HRC
            elif params[2] == 'instance' and params[3] != 'length':
                inst_id = int(params[3])
                if inst_id not in hrcObj.instances:
                    hrcObj.instances[inst_id] = A3daObject(Id=inst_id)
                    hrcObj.instances[inst_id].bl_name = f'{a3daName}{HrcId}_{inst_id}' 
                inst = hrcObj.instances[inst_id]

                if params[4] == 'name':
                    inst.name = data

                elif params[4] == 'uid_name':
                    inst.uid_name = data

                elif params[4] == 'shadow':
                    pass

                else:
                    #pass sliced params so it behaves like a regular object line
                    parseA3daObject(inst, params[2:], data, frameOffset, config=config)

                pass
        
        ### Read m_object_hrc animation ###
#        elif params[0] == 'm_objhrc' and config.use_hrc:
#            if params[1] == 'length':
#                continue
#
#            hrcId = int(params[1])
#            if hrcId not in m_hrcObjects:
#                m_hrcObjects[hrcId] = M_Hrc(Id=hrcId)
#            
#
#
#
        ### Read play control settings ###
        elif params[0] == 'play_control':
            if params[1] == 'fps':
                bpy.context.scene.render.fps = int(data)
            
            elif params[1] == 'size':
                data = int(data)
                if bpy.context.scene.frame_end < data + frameOffset:
                    bpy.context.scene.frame_end = data + frameOffset

    
    readingTime = round(time.time() - startTime, 4)
    print("\nFinished reading A3DA file")
    print(f'Reading took: {readingTime} seconds\n')

    ###############################
    #### Write anim to Blender ####
    ###############################
    
    objTime = time.time()
    print(f'[readA3da] Animating Objects...')

    if config.use_objects:
        cleanEmptiesNames()

    ### Ensure scene & file root ###
    if stgpv and not bpy.context.scene.objects.get(stgpv):
        root = createEmpty(stgpv, 'ARROWS')
        root.auth3d.auth3d_type = 'ROOT'
    
    if not bpy.context.scene.objects.get(a3daName[:-1]):
        fRoot = createEmpty(a3daName[:-1])
        fRoot.auth3d.auth3d_type = 'OBJECT'
        root = bpy.context.scene.objects.get(stgpv)

        root.rotation_euler.x = 1.570796 #90 degrees
        fRoot.parent = root
    
    ### Animate objects ###
    for id, obj in objects.items():
        #print(f"[readA3da] Animating obj: {id}")

        #Make sure ctrl exits
        ctrl:bpy.types.Object = bpy.context.scene.objects.get(obj.bl_name)
        if not ctrl:
            ctrl = createEmpty(obj.bl_name)

        #Set parent
        if obj.parent and obj.parent != "":
            parent = objNames.get(obj.parent)
            parent = objects[parent].bl_name
            parent = createEmpty(parent)
            assignParent(parent, ctrl)
        else:
            ctrl.parent = bpy.context.scene.objects.get(a3daName[:-1])

        #Match controllers to meshes
        ctrl.auth3d.auth3d_type = 'OBJECT'
        if obj.uid_name and obj.uid_name != "NULL":
            ctrl.auth3d.uid_name = obj.uid_name
            assignMesh(obj, ctrl, make_independent=config.independent_instances)
        elif obj.uid_name:
            ctrl.auth3d.uid_name = obj.uid_name

        #Write object transform animation curves (runs even of useObjects=False)
        animateObject(obj, config)

        #Write tex_transform animation
        if config.use_tex_transform and len(obj.tex_transform) > 0:
            animateTex(obj.tex_transform, obj.uid_name, config)

        if config.use_tex_pat and len(obj.tex_pat) > 0:
            animateTexPat(obj.tex_pat, ctrl, config)
            
    
    ### Animate HRC ###
    for hrc in hrcObjects.values():
        arm = animateHrc(hrc, frameOffset, use_ghost=config.use_hrc_ghost)

        #Once armature is created and animated, assign it to it's empty
        #arm = bpy.context.scene.collection.objects.get(hrc.name)
        arm.parent = fRoot

        ### Animate MHRC ###
    for hrc in m_hrcObjects.values():
        arm = animateHrc(hrc, frameOffset, use_ghost=config.use_hrc_ghost)

        #Once armature is created and animated, assign it to it's empty
        #arm = bpy.context.scene.collection.objects.get(hrc.name)
        arm.parent = fRoot

        #Animate the instances
        obj:A3daObject
        for obj in hrc.instances.values():
            ctrl = createEmpty(obj.bl_name)
            ctrl.parent = bpy.context.scene.objects.get(a3daName[:-1])
            animateObject(obj, config)

    print(f'\n[readA3da] Finished animating objects.')
    print(f'[readA3da] Writing to Blender took: {round(time.time() - objTime, 4)} seconds.\n')


def startReading(a3da_path:Path, frameOffset, config:ImportConfig):
    ### Open A3da & set variables ###
    print('\nStart')
    #tracemalloc.start()
    startTime = time.time()
    a3daFile = open(a3da_path, 'r')

    #Define pv name
    stgpv = a3da_path.stem
    #print(stgpv)
    stgpv = stgpv.split('_')[0]
    print(stgpv)
    stgpv = stgpv.upper()
    print(stgpv)
    if stgpv.count("S") > 1:    #I have no ideaif there's a better way to do this
        stgpv = stgpv[:(stgpv.find("S", 5))]
    print('STG name:', stgpv)

    #Define file name, required to rename controllers
    try:
        a3daName = None
        begin = 0
        for line in a3daFile:
            line = line.strip()
            if line.startswith(('#')):
                continue
            params, data = line.split('=')
            params = [itm for itm in params.split('.')]

            if params[1] == 'file_name':
                a3daName = data.removesuffix('.a3da') + '_'     #This is also the field name
                if not config.use_file_begin: break

            elif params[0] == 'play_control' and params[1] == 'begin':
                begin = int(data)
                break
        
        if config.use_file_begin:
            print("Begin offet:", begin)
            frameOffset += begin

        if a3daName == None:
            a3daName = stgpv + "_EFF_"
            pass
    except UnicodeDecodeError as ex:
        print('\n!!! File read Error !!!')
        print('You likely tried to load an A3DC binary file, but they are not supported by this tool!')
        print('Convert those to A3DA with PD_Tool by KorenKonder first!\n')
        a3daFile.close()
        raise ex
    a3daFile.seek(0)

    print('Object prefix:', a3daName)

    #### Start of interesting things ####
    readA3da(a3daFile, a3daName, stgpv, frameOffset, config)

    #### Finish ####
    a3daFile.close()
    print(f'Total elapsed time: {round(time.time() - startTime, 4)} seconds.')
    print('Excecution finished')


#################################################
# When animating, call hierarchy:
# objects -> tex transform -> HRC
