# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
import addon_utils
from bpy.props import BoolProperty
import math

def check_mmd():
    is_enabled, is_loaded = addon_utils.check('bl_ext.blender_org.mmd_tools')
    return is_enabled and is_loaded


def valid_selection(context:bpy.types.Context):
    return context.active_object and context.active_object.type == "CAMERA"


def bake_camera_focal_length(context:bpy.types.Context, obj:bpy.types.Object, start_frame=None, end_frame=None):
    scene = context.scene
    
    if not obj or obj.type != 'CAMERA':
        print("Please select a Camera object.")
        return

    cam_data = obj.data
    current_frame = context.scene.frame_current
    
    #Define the range
    if start_frame is None:
        start_frame = scene.frame_start
    if end_frame is None:
        end_frame = scene.frame_end

    print(f"Baking Focal Length for {obj.name} from frame {start_frame} to {end_frame}...")

    for f in range(start_frame, end_frame + 1):
        #Set the frame
        scene.frame_set(f)

        #Force evaluate driver (Not sure if really needed)
        context.evaluated_depsgraph_get().update()
        
        #Insert keyframe on the 'lens' property (Focal Length)
        cam_data.keyframe_insert(data_path="lens", frame=f)

    
    cam_data.driver_remove("lens")
    print("Driver successfully removed.")
    
    scene.frame_set(current_frame)
    cam_data.update_tag()
    bpy.context.view_layer.update()
    
    print("Focal length baked.")


class A3DA_Utils_OT_MMDfy_camera(bpy.types.Operator):
    bl_idname = "a3da_utils.mmdfy_camera"
    bl_label = "Convert MMD FOV Camera"
    bl_description = "Converts the selected camera to MMD Fov-Mod-compatible. Requires MMD_Tools to be installed and enabled."
    bl_options = {"REGISTER", "UNDO"}

    bake_lens : BoolProperty(   #type: ignore
        name="Force Bake Lens",
        description="Foces to bake the focal length on the SOURCE camera before converting to MMD. This will modify the source camera.",
        default=False
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=400,
                title="Convert to MMD FOV Camera",
                confirm_text="Convert",)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="This will convert the selected camera to a MMD FOV mod Camera.")
        col.separator()

        if valid_selection(context):
            col.label(text=f"Selected camera: \"{context.active_object.name}\"", icon='CAMERA_DATA')
        else:
            col.label(text="Invalid selection. Please select a camera.", icon='ERROR')
        pass

        col.prop(self, "bake_lens")

    @classmethod
    def poll(cls, context):
        if not check_mmd():     #Idk if it's too much to poll for this on every call...
            cls.poll_message_set("MMD Tools addon not found!!!")
            return False
        elif not valid_selection(context):
            cls.poll_message_set("No camera selected")
            return False
        return True 

    def execute(self, context):
        print("Convert to MMD camera operator start")

        ### Logic for MMDifying camera ###
        source_cam = context.active_object

        ## Bake driver on focal length ##
        if self.bake_lens:
            bake_camera_focal_length(context, source_cam)

        try:
            bpy.ops.mmd_tools.convert_to_mmd_camera(
                'EXEC_DEFAULT', #To skip invoke and preserve parameter to bake
                bake_animation = 'ALL',
                #camera_source = 'CURRENT'
            )
        except TypeError:
            bpy.ops.mmd_tools.convert_to_mmd_camera(
                'EXEC_DEFAULT', #To skip invoke and preserve parameter to bake
                bake_animation = True,
            )
        #mmd camera is now active object
        
        mmd_cam = context.active_object
        mmd_ctrl = context.active_object.parent

        #Find FOV angle fcurve
        ctrl_action = mmd_ctrl.animation_data.action
        ctrl_slot = mmd_ctrl.animation_data.action_slot
        ctrl_channelbag = ctrl_action.layers[0].strips[0].channelbag(ctrl_slot)     #TODO build a function to find FUCKING channelbags

        angle_fcurve = ctrl_channelbag.fcurves.find("mmd_camera.angle")

        #Find target fcurve (camera y location)
        t_slot = None
        t_action = mmd_cam.animation_data.action
        for slot in t_action.slots:
            if slot.name_display == "MMD_Camera_dis":
                t_slot = slot
                break
        if not t_slot:
            t_slot = t_action.slots.new('OBJECT', "MMD_Camera_dis")
            t_slot.name_display = "MMD_Camera_dis"
        mmd_cam.animation_data.action_slot = t_slot

        #Get channelbag and remove current data
        t_channelbag = t_action.layers[0].strips[0].channelbag(t_slot, ensure=True)     #This has to be the stupidest change in modern Blender
        target_fcurve = t_channelbag.fcurves.find("location", index=1)      #I hate channelbags really
        if target_fcurve:
            t_channelbag.fcurves.remove(target_fcurve)

        #Copy fcurve
        target_fcurve:bpy.types.FCurve = t_channelbag.fcurves.new_from_fcurve(angle_fcurve, data_path="location")
        target_fcurve.array_index = 1        

        #Apply conversion
        for kp in target_fcurve.keyframe_points:
            #Convert Blender FOV to MMD FOV and scale
            kp.co.y *= 4.583912 #Fov magic number

        target_fcurve.update()
        mmd_cam.update_tag()

        context.view_layer.update()
        return {'FINISHED'}