# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from . import Export_Writer
from . import Export_HRC
from . import Export_Objects
from . import Export_Camera


import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator
from pathlib import Path

class A3DA_PT_export_panel(Panel):
    bl_label = "A3DA Export"
    bl_idname = "A3DA_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'A3DA'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Export tools")
        layout.operator('a3da_export.hrc', icon='EXPERIMENTAL')
        layout.operator('a3da_export.obj', icon='EXPERIMENTAL')
        layout.operator('a3da_export.cam', icon='EXPERIMENTAL')

class Export_BASE(Operator, ExportHelper):
    use_raw : BoolProperty(     #type: ignore
            name="Use Raw Data",
            description="Use raw data for channels with more than 2 keyframes. HUGE file size saver & performance boost.",
            default=True
        )
    
    filename_ext = ".a3da"
    filter_glob : StringProperty(default="*.a3da", options={'HIDDEN'})  #type: ignore
    filepath : StringProperty(  #type: ignore
        subtype="FILE_PATH",
        default= bpy.app.tempdir
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'use_raw')


class A3DA_OT_export_HRC(Export_BASE):
    bl_idname = "a3da_export.hrc"
    bl_label = "Export HRC"


    #filename_ext = ".a3da"
    #filter_glob : StringProperty(default="*.a3da", options={'HIDDEN'})  #type: ignore
    #filepath : StringProperty(  #type: ignore
    #    subtype="FILE_PATH",
    #    default= bpy.app.tempdir
    #)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'
    
    def draw(self, context):
        super().draw(context)

    def execute(self, context):
        #path = Path(bpy.app.tempdir) / "hrc.a3da"
        path = Path(self.filepath)
        if path.is_dir():
            path /= "hrc.a3da"

        hrc = Export_HRC.build_hrc(self, context.active_object)
        Export_Writer.write_a3da(path, hrcList=[hrc], use_raw=self.use_raw)

        self.report({'INFO'}, f"A3DA saved to: {path}")
        return {'FINISHED'}
    

class A3DA_OT_export_Obj(Export_BASE): 
    bl_idname = "a3da_export.obj"
    bl_label = "Export Objects"

    #filename_ext = ".a3da"
    #filter_glob : StringProperty(default="*.a3da", options={'HIDDEN'})  #type: ignore
    #filepath : StringProperty(  #type: ignore
    #    subtype="FILE_PATH",
    #    default= bpy.app.tempdir
    #)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in {'EMPTY'}

    def execute(self, context):
        path = Path(self.filepath)
        #path = Path(bpy.app.tempdir) / "obj.a3da"
        if path.is_dir():
            path /= "obj.a3da"

        selected = context.active_object
        objects = Export_Objects.build_obj(self, selected.children_recursive, selected)
        Export_Writer.write_a3da(path, objList=objects, use_raw=self.use_raw)

        self.report({'INFO'}, f"A3DA saved to: {path}")
        return {'FINISHED'}


class A3DA_OT_export_Cam(Export_BASE):
    bl_idname = "a3da_export.cam"
    bl_label = "Export Camera"

    #filename_ext = ".a3da"
    #filter_glob : StringProperty(default="*.a3da", options={'HIDDEN'})  #type: ignore
    #filepath : StringProperty(  #type: ignore
    #    subtype="FILE_PATH",
    #    default= bpy.app.tempdir
    #)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and context.active_object.auth3d_cam.subtype == 'CAM'
    
    def execute(self, context):
        path = Path(self.filepath)
        if path.is_dir():
            path /= "cam.a3da"

        selected = context.active_object
        a3da_cam, a3da_root, a3da_dof = Export_Camera.build_cam(selected)
        Export_Writer.write_a3da(path, cam=(a3da_cam, a3da_root, a3da_dof), use_raw=self.use_raw)

        self.report({'INFO'}, f"A3DA saved to: {path}")
        return {'FINISHED'}


classes = [
    A3DA_OT_export_HRC,
    A3DA_OT_export_Obj,
    A3DA_OT_export_Cam,
    A3DA_PT_export_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)