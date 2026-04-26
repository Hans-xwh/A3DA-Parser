# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
from bpy.props import PointerProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, StringProperty
from bpy.types import PropertyGroup

class auth3dProps(PropertyGroup):
    is_auth3d: BoolProperty(  #type: ignore
        name="Is Auth3D",
        description="Whether the object is Auth3D",
        default=False
    )

    auth3d_type: EnumProperty(  #type: ignore
        name="Auth3D Type",
        description="Type of Auth3D Object",
        options=set(),  #Empty set to disable default option 'ANIMATABLE'
        items=[
            ('NONE', "None", "Not an Auth3D object"),
            ('ROOT', "Auth3D Space", "Auth3D root space"),
            ('OBJECT', "Object", "Animated object"),
            ('MESH', "Mesh", "Mesh object"),
            ('MESH_C', "Mesh Controller", "Empty controller representing a mesh"),
            ('HRC', "HRC armature", "Auth3D_ready armature, all bones start at 0,0,0"),
            ('M_HRC', "M_HRC", "M_HRC"),
            ('CAMERA', "Camera", "Auth3D Camera"),
        ],
        default='NONE',
    )

    uid_name: StringProperty( #type: ignore
        name = "UID Name",
        description="Name PJD uses to match animation to model",
        default=""
    )

    visibility : IntProperty( #type:ignore
        name = "Visibility",
        description= "Show or hide an object",
        default= 1,
        min = 0,
        max = 1
    )


class auth3dCamProps(PropertyGroup):
    subtype : EnumProperty( #type: ignore
        name="Auth3D Camera Subtype",
        description="Subetype of a camera object",
        options=set(),
        items=[
            ('NONE', "None", "Not part of an Auth3D camera"),
            ('ROOT', "Camera Root", "Root object of a camera"),
            ('INTEREST', "Camera Interest", "Interest object for a viewpoint to point to"),
            ('VIEW', "Camera Viewpoint", "Viewpoint Object"),
            ('CAM', "Camera Object", "Camera Object"),
            ('DOF', "DOF Object", "DOF Object to drive Depth of Field")
        ],
        default='NONE'
    )

    fov : FloatProperty(    #type: ignore
        name= "Auth3D FOV",
        description= "Field of View of an Auth3D camera, in degrees. Internally radians.",
        subtype= 'ANGLE',
        default= 0.785398
    )

    fov_scale : FloatProperty(  #type: ignore
        name = "Fov Scale Factor",
        description= "Scale to apply to FOV. This parameter is not imported nor exported from A3DA. It's merely for previewing.",
        default= 1    
        )


classes = [
    auth3dProps,
    auth3dCamProps,
]
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.auth3d = PointerProperty(type=auth3dProps)
    bpy.types.Object.auth3d_cam = PointerProperty(type=auth3dCamProps)

def unregister():
    del bpy.types.Object.auth3d
    del bpy.types.Object.auth3d_cam

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)