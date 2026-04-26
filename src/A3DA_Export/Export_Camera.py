# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from pathlib import Path

from .. A3DA_Core import A3daChannel, switchAxis, getChannelbag
from .. A3DA_Import.A3DA_Camera import A3daCamera, A3daCamObj
from . Export_Core import get_transform_lines, get_channel_lines, get_channel_raw

import bpy
from io import TextIOWrapper

def build_cam(bl_cam:bpy.types.Object) -> tuple[A3daCamera, A3daCamObj, A3daCamObj]:    #Camera, DOF, Root
    print("Building Camera...")
    cam = A3daCamera()
    dof = None
    root = A3daCamObj()

    ### Get references ###
    bl_viewpoint = bl_cam.parent
    cam.view_point.bl_reference = bl_viewpoint
    cam.bl_camera = bl_cam

    if not bl_viewpoint or not bl_viewpoint.parent: return None, None, None
    bl_root = bl_viewpoint.parent
    root.bl_reference = bl_root

    for child in bl_root.children:
        match child.auth3d_cam.subtype:
            case 'INTEREST':
                cam.interest.bl_reference = child
            case 'DOF':
                dof = A3daCamObj()
                dof.bl_reference = child
 

    ### Build animation ###
    obj:A3daCamObj
    for obj in {cam.interest, cam.view_point, dof, root}:
        if obj is None: continue

        ## Get channelbag and shit ##
        channelbag = getChannelbag(obj.bl_reference)

        for transform in ('location', 'rotation_euler', 'scale'):
            for axis in ('x', 'y', 'z'):
                channel = obj.getTransform(channel=transform, axis=axis)
                channel.fromFCurve(channelbag.fcurves.find(transform, index=switchAxis(axis)),
                                   correct_rot= not obj.bl_reference.parent and (transform == 'rotation_euler' and axis == 'x'))
        
        #Camera properties
        cam_chbg = getChannelbag(cam.bl_camera)
        cam.roll.fromFCurve(cam_chbg.fcurves.find('rotation_euler', index=2))
        cam.fov.fromFCurve(cam_chbg.fcurves.find('auth3d_cam.fov'))



    return cam, root, dof


def write_cam(a3da:TextIOWrapper, a3da_cam: A3daCamera, a3da_root: A3daCamObj, a3da_dof: A3daCamObj, use_raw: bool=True):
    interest_prefix = 'camera_root.0.interest'
    viewpoint_prefix = 'camera_root.0.view_point'

    interest = a3da_cam.interest
    viewpoint = a3da_cam.view_point


    #Interest transforms
    for transform in ('rot', 'scale', 'trans'): #In this order
        a3da.write("\n".join(
            get_transform_lines(f'{interest_prefix}.{transform}', interest.getTransform(transform), raw=use_raw )
        ) + "\n")

    a3da.write(f'{interest_prefix}.visibility.type=1\n')
    a3da.write(f'{interest_prefix}.visibility.value=1\n')

    #Root transforms
    root_obj = a3da_root if a3da_root else A3daCamObj()
    for transform in ('rot', 'scale', 'trans'):
        a3da.write("\n".join(
            get_transform_lines(f'camera_root.0.{transform}', root_obj.getTransform(transform), raw=use_raw, safe=(transform == 'scale'))   #Use an empty object. Not really sure if diva can use an animated root
        ) + "\n")

    #Viewpoint stuff
    a3da.write(f'{viewpoint_prefix}.aspect=1.77778\n')    #Hardcoded :P

    #fov
    a3da.write("\n".join(
        get_channel_raw(f'{viewpoint_prefix}.fov', a3da_cam.fov) if use_raw else get_channel_lines(f'{viewpoint_prefix}.fov', a3da_cam.fov)
    ) + "\n")

    a3da.write('camera_root.0.view_point.fov_is_horizontal=1\n')

    #roll
    a3da.write("\n".join(
        get_channel_raw(f'{viewpoint_prefix}.roll', a3da_cam.roll) if use_raw else get_channel_lines(f'{viewpoint_prefix}.roll', a3da_cam.roll)
    ) + "\n")

    #Interest transforms
    for transform in ('rot', 'scale', 'trans'): #In this order
        a3da.write("\n".join(
            get_transform_lines(f'{viewpoint_prefix}.{transform}', viewpoint.getTransform(transform), raw=use_raw )
        ) + "\n")

    ##translation
    #a3da.write("\n".join(
    #    get_transform_lines(f'{viewpoint_prefix}.trans', viewpoint.translation, raw=use_raw)
    #) + "\n")

    #viewpoint visibility, tho not used
    a3da.write(f'{viewpoint_prefix}.visibility.type=1\n')
    a3da.write(f'{viewpoint_prefix}.visibility.value=1\n')

    #root visibility, tho not used again
    a3da.write(f'camera_root.0.visibility.type=1\n')
    a3da.write(f'camera_root.0.visibility.value=1\n')

    a3da.write(f'camera_root.length=1\n')

    ### DOF ###
    if a3da_dof is None: return

    a3da.write('dof.name=DOF\n')

    for transform in ('rot', 'scale', 'trans'):
        a3da.write("\n".join(
            get_transform_lines(f'dof.{transform}', a3da_dof.getTransform(transform), raw=use_raw)
        ) + "\n")

    a3da.write(f'dof.0.visibility.type=1\n')
    a3da.write(f'dof.0.visibility.value=1\n')
