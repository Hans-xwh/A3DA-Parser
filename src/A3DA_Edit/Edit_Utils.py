# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. import A3DA_Objects
from .. import A3DA_Camera

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class A3da_Edit_OT_CreateSpace(Operator):
    bl_idname = "a3da_edit.create_space"
    bl_label = "Create Auth3D space"
    bl_description = "Creates an empty at the world origin rotated 90°. Yeh just that. Required for transforms to look good in Diva."
    bl_options = {"REGISTER", "UNDO"}

    obj_name : StringProperty(  #type: ignore
        name="Name",
        description="Name of the created empty",
        default="Auth3D_Space"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=200,
                title="Create Auth3D space",
                )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Name of the new Auth3D space:")
        layout.prop(self, "obj_name")
    
    def execute(self, context):
        space = A3DA_Objects.createEmpty(self.obj_name,disp_type='ARROWS', force=True)
        space.rotation_euler[0] = 1.5708 #90 degrees in radians
        space.auth3d.is_auth3d = True
        space.auth3d.auth3d_type = 'ROOT'
        print(f"Created Auth3D space: {self.obj_name}")
        return {'FINISHED'}


class A3da_Edit_OT_CreateCam(Operator):
    bl_idname = "a3da_edit.create_cam"
    bl_label = "Create Auth3D Camera"
    bl_description = "Creates an Auth3D Camera Rig"
    bl_options = {"REGISTER", "UNDO"}

    cam_name : StringProperty(  #type: ignore
        name="Name",
        description="Name of the created camera",
        default="Auth3D_Camera"
    )

    use_dof : BoolProperty( #type: ignore
        name="Use DOF",
        description="Create & set up a DOF object.",
        default=False
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=200,
                title="Create Auth3D Camera",
                )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "cam_name")
        layout.prop(self, "use_dof")

    def execute(self, context):
        cam = A3DA_Camera.A3daCamera()
        dof = A3DA_Camera.A3daCamObj() if self.use_dof else None

        A3DA_Camera.setupCam(cam, dof, prefix=self.cam_name)
        A3DA_Camera.setupFovDriver(cam)
        cam.interest.bl_reference.location = (0, 1, -4)
        cam.view_point.bl_reference.location = (0, 1, 0)


        return {"FINISHED"}


classes = [
    A3da_Edit_OT_CreateSpace,
    A3da_Edit_OT_CreateCam,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)