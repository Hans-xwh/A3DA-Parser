# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. A3DA_Import.A3DA_HRC import HrcObject, HrcNode
from . Export_Core import get_transform_lines, get_channel_lines, get_channel_raw

import bpy
from io import TextIOWrapper

def sort_bones_by_hierarchy(bones: list[bpy.types.PoseBone]) -> list[bpy.types.PoseBone]: #Vivecoded func lol
    """
    Sort bones so that parents always come before their children.
    Works with Blender bones or any object with .name and .parent attributes.
    """
    sorted_bones = []
    visited = set()

    def visit(bone):
        if bone.name in visited:
            return
        # Visit parent first (if it exists and hasn't been visited)
        if bone.parent and bone.parent.name not in visited:
            visit(bone.parent)
        visited.add(bone.name)
        sorted_bones.append(bone)

    for bone in bones:
        visit(bone)

    return sorted_bones

def build_hrc(op:bpy.types.Operator, arm:bpy.types.Object) -> HrcObject:
    print("Building HRC...")
    hrc = HrcObject(Id=0, Name=arm.name)        #Check if using arm.name is the right approach
    hrc.uid_name = arm.auth3d.uid_name

    #Get anim refs
    anim_data = arm.animation_data
    if not anim_data or not anim_data.action:
        op.report({'ERROR'}, message="Armature has no anim")
        return
    
    action = anim_data.action
    action_slot = anim_data.action_slot

    channelbag = action.layers[0].strips[0].channelbag(action_slot)
    if not channelbag:
        op.report({'ERROR'}, message="Armature has no anim")
        return
    
    bone_mapping:dict[str, int] = {}
    node_id = 0

    #Read animation from Blender. Only write animation, not set parents yet
    bone:bpy.types.PoseBone
    sorted_bones = sort_bones_by_hierarchy(arm.pose.bones)
    for bone in sorted_bones:
        prefix = f'pose.bones["{bone.name}"]'
        node = HrcNode(Id=node_id, Name=bone.name)
        hrc.nodes[node_id] = node
        bone_mapping[bone.name] = node_id   #This is used later to find id per name

        ## Read anim ##
        #TODO optimize this
        # translation #
        node.translation.x.fromFCurve(channelbag.fcurves.find(f'{prefix}.location', index=0))
        node.translation.y.fromFCurve(channelbag.fcurves.find(f'{prefix}.location', index=1))
        node.translation.z.fromFCurve(channelbag.fcurves.find(f'{prefix}.location', index=2))

        # rotation #
        node.rotation.x.fromFCurve(channelbag.fcurves.find(f'{prefix}.rotation_euler', index=0))
        node.rotation.y.fromFCurve(channelbag.fcurves.find(f'{prefix}.rotation_euler', index=1))
        node.rotation.z.fromFCurve(channelbag.fcurves.find(f'{prefix}.rotation_euler', index=2))

        # scale #
        node.scale.x.fromFCurve(channelbag.fcurves.find(f'{prefix}.scale', index=0), safe=True)
        node.scale.y.fromFCurve(channelbag.fcurves.find(f'{prefix}.scale', index=1), safe=True)
        node.scale.z.fromFCurve(channelbag.fcurves.find(f'{prefix}.scale', index=2), safe=True)

        node_id += 1

    #Now that all nodes are created, set parenting & any other property required
    for bone in sorted_bones:
        node_id = bone_mapping.get(bone.name)
        if bone.parent:
            parent_id = bone_mapping.get(bone.parent.name)
        else:
            parent_id = -1

        node = hrc.nodes[node_id]
        node.parent = parent_id

    print("Finished building HRC")
    return hrc

def write_hrc(a3da:TextIOWrapper, hrcList:list[HrcObject], use_raw=True):
    for hrc in hrcList:
        hrcline = f'objhrc.{hrc.id}'
        a3da.write(f'{hrcline}.name={hrc.name}\n')
        node:HrcNode

        sortedNodes = {k: hrc.nodes[k] for k in sorted(hrc.nodes.keys(), key=str)}
        for node in sortedNodes.values():
            nodeline = f'{hrcline}.node.{node.id}'
            a3da.write(f'{nodeline}.name={node.name}\n')
            a3da.write(f'{nodeline}.parent={node.parent}\n')

            #Decide write mode: >2 keys = raw mode. Visibility always plain

            ## Write transforms ##
            a3da.write("\n".join(
                get_transform_lines(f'{nodeline}.rot', node.rotation, raw=use_raw)
            ) + "\n")
            a3da.write("\n".join(
                get_transform_lines(f'{nodeline}.scale', node.scale, safe=True, raw=use_raw)
            ) + "\n")
            a3da.write("\n".join(
                get_transform_lines(f'{nodeline}.trans', node.translation, raw=use_raw)
            ) + "\n")

            ## Write visibility ##
            #TODO actually implement this xd
            a3da.write(f'{nodeline}.visibility.type=1\n')
            a3da.write(f'{nodeline}.visibility.value=1\n')

        ## More HRC data ##
        a3da.write(f'{hrcline}.node.length={len(hrc.nodes)}\n')
        a3da.write(f'{hrcline}.uid_name={hrc.uid_name}\n')

    ## HRC end data ##
    if len(hrcList) > 0:
        a3da.write(f'objhrc.length={len(hrcList)}\n')
        for hrc in hrcList:
            a3da.write(f'objhrc_list.{hrc.id}={hrc.name}\n')
        a3da.write(f'objhrc_list.length={len(hrcList)}\n')

    return
