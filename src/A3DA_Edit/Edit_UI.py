# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from . import Edit_Utils

import bpy
from bpy.types import Panel
from bpy.props import BoolProperty

class A3DA_PT_edit_panel(Panel):
    bl_label = "Auth3D Manipulation"
    bl_idname = "A3DA_PT_edit_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'A3DA'

    def draw(self, context):
        layout = self.layout
        #layout.label(text="")

class A3DA_PT_view_panel(Panel):
    bl_label = "Auth3D View Panel"
    bl_idname = "A3DA_PT_view_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "A3DA_PT_edit_panel"


    @classmethod
    def poll(cls, context):
        return context.active_object #and context.active_object.auth3d.is_auth3d  

    def draw(self, context):
        show_all = True
        layout = self.layout
        #layout.label(text="This is a dev panel!")
        col = layout.column()

        col.label(text=f"Object: {context.active_object.name}")
        
        if show_all == True:
            col.prop(context.active_object.auth3d, "auth3d_type", text="Type")
        else:
            col.label(text=f"Type: {context.active_object.auth3d.auth3d_type}")

        col.separator()

        if context.active_object.auth3d.auth3d_type != 'CAMERA':
            col.prop(context.active_object.auth3d, "uid_name", text="Uid")
            col.prop(context.active_object.auth3d, "visibility", text="Visibility")

        if context.active_object.auth3d.auth3d_type == 'CAMERA':
            draw_cam(context, layout, show_all)

class A3DA_PT_edit_utils_panel(Panel):
    bl_label = "Auth3D Manipulation Utils"
    bl_idname = "A3DA_PT_edit_utils_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "A3DA_PT_edit_panel"

    def draw(self, context):
        layout = self.layout
        #layout.label(text="Fancy buttons and stuff", icon='EXPERIMENTAL')
        col = layout.column(align=False)

        col.operator("a3da_edit.create_space", icon='EMPTY_ARROWS')
        col.operator("a3da_edit.create_cam", icon='VIEW_CAMERA')
        col.operator("a3da_edit.convert_armature", icon='CON_ARMATURE')
        col.operator("a3da_edit.convert_model", icon='MONKEY')
        col.operator("a3da_edit.convert_cam", icon='CAMERA_DATA')


def draw_cam(context:bpy.types.Context, layout:bpy.types.UILayout, show_all=False):
    if show_all:
        layout.prop(context.active_object.auth3d_cam, "subtype", text="Subtype")
    else:
        layout.label(text=f"Subtype: {context.active_object.auth3d_cam.subtype}")

    if context.active_object.auth3d_cam.subtype == 'CAM':
        layout.prop(context.active_object.auth3d_cam, "fov", text="FOV")
        layout.prop(context.active_object.auth3d_cam, "fov_scale", text="Fov Scale")

    #DOF object namings
    elif context.active_object.auth3d_cam.subtype == 'DOF':
        obj = context.active_object
        layout.prop(obj, "scale", index=0, text="Focus Range")
        layout.prop(obj, "rotation_euler", index=0, text="Fuzzing Range")   #TODO make this point to a custom property, and the custom prop to drive the rotation, or idk but this is janky
    

classes = [
    A3DA_PT_edit_panel,
    A3DA_PT_view_panel,
    A3DA_PT_edit_utils_panel,
    
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)