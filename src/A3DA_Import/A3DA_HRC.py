# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import switchAxis, parseA3daKey, setA3daChannel, readRawLine, parseRawLine, ensureAction
from .A3DA_Objects import A3daObject, findChild

import bpy
from array import array

class HrcNode(A3daObject):
    def __init__(self, Id=0, Name="", Parent:int=-1):
        super().__init__(Id, Name)

        self.parent:int = Parent

class HrcObject:
    def __init__(self, Id:int=0, Name:str=""):
        self.id:int = Id
        self.name:str = Name
        self.uid_name:str= ''
        self.bl_name:str = ''
        self.nodes:dict[int, HrcNode] = dict()

class M_Hrc(HrcObject):
    def __init__(self, Id:int=0, Name:str=""):
        super().__init__(Id, Name)
        self.instances:dict[int, A3daObject] = dict()    #M_HRC instances can be represented os objects, since they contain id, name, uid_name. Evey instances rehuses the same nodes


#### HRC Utils ####
def setBoneParent(armature:bpy.types.Object, childBone:str, parentBone:str, force:bool = True):    #If a bone has no parent, set's it
    childBone:bpy.types.Bone = armature.data.edit_bones.get(childBone)

    if childBone.parent and not force: return #If a bone already has a parent, and force=False, do nothing

    #Switch to edit mode and get edit bones
    bpy.ops.object.mode_set(mode="EDIT")
    childBone:bpy.types.EditBone = armature.data.edit_bones[childBone.name]
    parentBone:bpy.types.EditBone = armature.data.edit_bones[parentBone]

    #childBone.roll = 0
    #parentBone.roll = 0

    childBone.parent = parentBone


def createBone(armature:bpy.types.Object, newBoneName:str, preserveMode:bool=True) -> bpy.types.Bone | bpy.types.EditBone:
    #oldmode = bpy.context.active_object.mode    #Assumes armature is already active object
    #if oldmode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
    #print("[createBone] Current mode is:", bpy.context.mode)

    newBone = armature.data.edit_bones.new(newBoneName)
    #newBone.use_relative_parent = True  
    newBone.head = (0, 0, 0)
    newBone.tail = (0, 1, 0)

    #if preserveMode and oldmode=="EDIT_ARMATURE":
    #    bpy.ops.object.mode_set(mode="EDIT")
    #else:
    #    bpy.ops.object.mode_set(mode=oldmode)
    
    #print(f'[createBone] Bone "{newBoneName}" created')
    return newBone


#### HRC Functions ####
def parseHrc(hrc:HrcObject, params:list, data:list|str, frameOffset=0, rawBuffer:array=None) -> None:
    hrcId = int(params[1])  #HRC object id
    nId = int(params[3])    #HRC node id

    #Ensure node exists
    if nId not in hrc.nodes:
        hrc.nodes[nId] = HrcNode(Id=nId)
        #print(f'[parseHrc] Added Node:{nId} to Object:{hrcId}')
    node = hrc.nodes[nId]

    if params[4] == 'name':
        node.name = data
    
    elif params[4] == 'parent':
        node.parent = int(data)

    #Node visibility (Almost always 1?)
    elif params[4] == 'visibility':
        #print(f'[parseHrc] Node visibility: {data}')
        if params[5] == 'type':
            node.setParam(params[4], interpolation=data)

        elif params[5] == 'ep_type_post':
                node.setParam(params[4], ep_post=data)

        elif params[5] == 'ep_type_pre':
                node.setParam(params[4], ep_pre=data)
            
        elif params[5] == 'value':
            node.pushKey(
                transform= params[4],
                keyIndex= 0,
                axis= None,
                keyframe= parseA3daKey(data, frameOffset, not_key=True)
            )

        elif params[5] == 'key' and params[6] != 'length' and params[7] == 'data':
            node.pushKey(
                transform= params[4],
                axis= None,
                keyIndex= int(params[6]),
                keyframe= parseA3daKey(data, frameOffset)
            )

    #regular transforms
    elif params[6] == 'key' and params[7] != 'length' and params[8] == 'data':
        node.pushKey(
            transform= params[4],
            axis= params[5],
            keyIndex= int(params[7]),
            keyframe= parseA3daKey(data, frameOffset)
        )
        #print('[parseHrc] Key pushed!')

    elif params[6] == 'value':
        node.pushKey(
            transform= params[4],
            axis= params[5],
            keyIndex= 0,
            keyframe= parseA3daKey(data, frameOffset, not_key=True)
        )

    elif params[6] == 'type':
        node.setParam(
            transform= params[4],
            axis= params[5],
            interpolation= int(data)
        )

        if data == '0':   #Type 0 means a curve is always 0
            node.pushKey(
                transform= params[4],
                axis= params[5],
                keyIndex= 0,
                keyframe= parseA3daKey(data, frameOffset, not_key=True)
            )

    elif params[6] == 'raw_data' and params[7] == 'value_list':
        readRawLine(rawBuffer, data)
            
    elif params[6] == 'raw_data_key_type':  #This tells what to do whit the raw data
        channel = node.getTransform(params[4], params[5])
        parseRawLine(rawBuffer, channel, data)

def animateHrc(hrc:HrcObject, frameOffset=0, use_ghost:bool=True) -> bpy.types.Armature:
    print('\n[animateHrc] Begin writing HRC to Blender')

    if use_ghost:
        hrc_name = f'{hrc.name}_GHOST'
    else:
        hrc_name = f'{hrc.bl_name}'

    ## Ensure armature ##
    if not bpy.context.scene.objects.get(hrc_name): #I changed these from uid_name -> name
        armObj = bpy.data.armatures.new(hrc_name)
        armObj = bpy.data.objects.new(hrc_name, armObj)
        bpy.context.scene.collection.objects.link(armObj)
    armObj = bpy.context.scene.objects.get(hrc_name) #TODO THIS SHOULD USE NAMINGS LIKE OBJ, NOT USE UID_NAME DIRECTLY

    while armObj.type != "ARMATURE":
        child = findChild(armObj)
        if child is armObj: #Prevents infinite lopp
            return
        else:
            armObj = child
    bpy.context.view_layer.objects.active = armObj  #Makes armature current active object

    ## Armature visibility (from node 0) ##
    action = ensureAction(armObj) #Ensure armature has action
    if hrc.nodes.get(0):    #Add check to use visibility
        fcurve = action.fcurve_ensure_for_datablock(
            datablock= armObj,
            data_path= "auth3d.visibility"
            )
        setA3daChannel(
            fcurve= fcurve,
            channel= hrc.nodes[0].visibility,
            frameOffset= frameOffset
            )


    ##Ensure armature has action
    #if not armObj.animation_data:
    #    armObj.animation_data_create()
    #if not armObj.animation_data.action:
    #    armObj.animation_data.action = bpy.data.actions.new(name=f'{node.name} Action')
    #action = armObj.animation_data.action

    ## Iterate trough nodes and make sure all exist & are parented ##
    bpy.ops.object.mode_set(mode='EDIT')
    for nId in sorted(hrc.nodes):
        node = hrc.nodes[nId]   #This reads nodes in numeric order

        #Check if bone exists
        if not armObj.data.bones.get(node.name):
            #print(f"[interpolateHrc] Bone {node.name} ({node.id}) not found!")
            createBone(armObj, node.name, preserveMode=False)

        #Set parent if not parented already
        if node.parent >= 0:
            parent = hrc.nodes[node.parent]
            if not armObj.data.edit_bones.get(parent.name):
                createBone(armObj, parent.name)         #Create bone if it doens't exist
            setBoneParent(armObj, node.name, parent.name, force=False)


    ## Iterate trough node and animate. All exist at this point ##
    bpy.ops.object.mode_set(mode="POSE")
    #action = ensureAction(armObj) #Ensure armature has action

    for nId in sorted(hrc.nodes):
        node = hrc.nodes[nId]

        bone = armObj.pose.bones.get(node.name)
        bone.rotation_mode = "XYZ"

        ### Begin writing keys ###
        for transform in ('trans', 'rot', 'scale'):
            for axis in ('x', 'y', 'z'):
                #print(f'[anaimateHrc] Writing: {node.name} | {transform} | {axis}')
                channel = node.getTransform(transform, axis)

                #Ensure fcurve exists
                fcurve = action.fcurve_ensure_for_datablock(    #THANKS FOR THIS FUNCTION
                    datablock= armObj,
                    data_path= f'pose.bones["{node.name}"].{switchAxis(transform)}',
                    index= switchAxis(axis),
                    group_name= node.name   #Disable this line to use on 4.5. This groups all fcurves for a bone by its name.
                )
                #fcurve.group = node.name   #Set group to bone name after, makes it work on 4.5

                #Write keys to Blender
                setA3daChannel(
                    fcurve = fcurve,
                    channel = channel,
                    frameOffset = frameOffset,
                    clearAfterImport = True
                )

        ### Write visibility ###
        if len(node.visibility.keys) > 0:
            channel = node.visibility
            bone["A3DA_VISIBILITY"] = 1

            fcurve = action.fcurve_ensure_for_datablock(
                datablock= armObj,
                data_path= f'pose.bones["{node.name}"].["A3DA_VISIBILITY"]',
                group_name= node.name
            )

            setA3daChannel(
                fcurve= fcurve,
                channel= channel,
                frameOffset= frameOffset,
            )


    #Finally go back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    return armObj

def animateM_Hrc(mhrc:M_Hrc, frameOffset=0, use_ghost:bool=True) -> None:   #Not needed
    pass