# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from . import EmptiesToBones
from . import EmptiesToBones_Legacy
from . import Bind_armatures
from . import FixMats
#from . import MMD_ready_cam_og
from . import FOV_ready_cam
from . import Visibility_Editor

import bpy

class A3DA_PT_main_panel(bpy.types.Panel):  #Main panel
    bl_label = "Auth3D Utils"
    bl_idname = "A3DA_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'A3DA'

    def draw(self, context: bpy.types.Context):
        col = self.layout.column(align=False)

        #col.label(text="Testing Testing: ", icon='INFO')
        col.operator("import_scene.a3da", icon="EMPTY_ARROWS")       #Note to self: register the panel thingy last

        col.separator(factor=2, type='SPACE')
        col.label(text="Select utility to launch", icon='FILE_SCRIPT')
        col.operator("a3da_utils.empties_to_bones_legacy", icon='BONE_DATA')
        col.operator("a3da_utils.empties_to_bones", icon='BONE_DATA')
        col.operator("a3da_utils.combine_morph", icon='SHAPEKEY_DATA')
        col.operator("a3da_utils.bind_armatures", icon='ARMATURE_DATA')
        col.operator("a3da_utils.fix_mats", icon='SHADERFX')
        col.operator("a3da_utils.visibility_edit", icon='VIS_SEL_11')
        col.operator("a3da_utils.mmdfy_camera", icon='CAMERA_DATA')
        #col.operator("a3da_utils.mmdfy_camera_og", icon='CAMERA_DATA')

class A3DA_Utils_OT_EmptiesToBonesLegacy(bpy.types.Operator):
    bl_idname = "a3da_utils.empties_to_bones_legacy"
    bl_label = "Empties To Bones (Legacy)"
    bl_description = "Converts empties containign meshes, in the current collection, into bones. Then rigs the meshes for the created bones. (LEGACY method, don't use this unless you know it works for you.)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        EmptiesToBones_Legacy.autoRun()

        return {'FINISHED'}
    
class A3DA_Utils_OT_BindArmatures(bpy.types.Operator):
    bl_idname = "a3da_utils.bind_armatures"
    bl_label = "Bind armatures"
    bl_description = "Binds the global transforms of the selected armature to the active armature using constraints. Just make sure bone names match"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = Bind_armatures.bindArmatures(self)

        if not result or result == 0:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


###########################################
classes = [
    FixMats.A3DA_Utils_OT_FixMats,
    Visibility_Editor.A3DA_Utils_OT_VisibilityEditor,
    A3DA_Utils_OT_EmptiesToBonesLegacy,
    A3DA_Utils_OT_BindArmatures,
    #MMD_ready_cam_og.A3DA_Utils_OT_MMDfy_camera_og,
    FOV_ready_cam.A3DA_Utils_OT_MMDfy_camera,
    EmptiesToBones.A3DA_Utils_OT_EmptiesToBones,
    EmptiesToBones.A3DA_Utils_OT_TransferDummyMorph,
    A3DA_PT_main_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    