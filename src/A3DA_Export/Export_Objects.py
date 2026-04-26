# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. A3DA_Core import switchAxis
from .. A3DA_Import.A3DA_Objects import A3daObject
from . Export_Core import get_transform_lines

import bpy
from io import TextIOWrapper

def sort_obj_by_hierarchy(objects: list[bpy.types.Object]) -> list[bpy.types.Object]:
    sorted_objects: list[bpy.types.Object] = []
    visited: set[str] = set()

    def visit(obj: bpy.types.Object) -> None:
        if obj.name in visited:
            return
        if obj.parent and obj.parent.name not in visited:
            visit(obj.parent)
        visited.add(obj.name)
        sorted_objects.append(obj)

    for obj in objects:
        visit(obj)

    return sorted_objects   #TODO maybe merge this with the bones thing and make it take both

def build_obj(op:bpy.types.Operator, objects: list[bpy.types.Object], root:bpy.types.Object) -> dict[int, A3daObject]:
    auto_uid = True
    print("Building Objects...")
    a3daObjects = {}
    obj_id = 0

    for empty in objects:
        ## Filter objects & anim data ##
        if empty.type != 'EMPTY':#  or empty.auth3d.auth3d_type != 'OBJECT':
            continue
        
        #TODO replace with getchannelbag func
        anim_data = empty.animation_data
        if not anim_data or not anim_data.action:
            continue

        action = anim_data.action
        action_slot = anim_data.action_slot
        channelbag = action.layers[0].strips[0].channelbag(action_slot)
        if not channelbag:
            continue

        ## Build object ##
        obj = A3daObject(Id=obj_id, Name=empty.name)
        if empty.parent and empty.parent != root:
            obj.parent = empty.parent.name

        if auto_uid:    #TODO maybe make this run on the Blender objects instead of on the go
            if empty.children and (empty.children[0].type in 'MESH' or empty.children[0].auth3d.auth3d_type == 'MESH_C'):
                obj.uid_name = empty.children[0].name
            else:
                obj.uid_name = "NULL"
        else:
            if empty.auth3d.uid_name not in {"", None}:
                obj.uid_name = empty.auth3d.uid_name
            else:
                obj.uid_name = "NULL"

        ## Read anim from Blender ##
        for transform in ('location', 'rotation_euler', 'scale'):
            for axis in ('x', 'y', 'z'):
                channel = obj.getTransform(channel=transform, axis=axis)
                channel.fromFCurve(channelbag.fcurves.find(transform, index=switchAxis(axis)))
        
        a3daObjects[obj_id] = obj
        obj_id += 1

    print(f"Finished building ({obj_id}) objects")
    return a3daObjects

def write_obj(a3da:TextIOWrapper, objDict:dict[int, A3daObject], use_raw=True):
    objDict = {k: objDict[k] for k in sorted(objDict.keys(), key=str)}
    roots:list[A3daObject] = []

    for obj in objDict.values():
        objline = f'object.{obj.id}'
        a3da.write(f'{objline}.name={obj.name}\n')

        if obj.parent and obj.parent != "":
            a3da.write(f'{objline}.parent_name={obj.parent}\n')
        else:
            roots.append(obj)

        ## Write transforms ##
        a3da.write("\n".join(
            get_transform_lines(f'{objline}.rot', obj.rotation, raw=use_raw)
        ) + "\n")
        a3da.write("\n".join(
            get_transform_lines(f'{objline}.scale', obj.scale, safe=True, raw=use_raw)
        ) + "\n")
        a3da.write("\n".join(
            get_transform_lines(f'{objline}.trans', obj.translation, raw=use_raw)
        ) + "\n")

        ## Write uid_name ##
        a3da.write(f'{objline}.uid_name={obj.uid_name}\n')

        ## Write visibility ##
        #TODO actually implement this xd
        a3da.write(f'{objline}.visibility.type=1\n')
        a3da.write(f'{objline}.visibility.value=1\n')

    ## Write objects ending ##
    a3da.write(f'object.length={len(objDict)}\n')
    for obj in roots:
        a3da.write(f'object_list.{obj.id}={obj.name}\n')
    a3da.write(f'object_list.length={len(roots)}\n')
