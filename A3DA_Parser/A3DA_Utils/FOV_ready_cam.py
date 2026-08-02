# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
import addon_utils
from bpy.props import BoolProperty
import math

from .. A3DA_Core import ensureAction, getChannelbag, getFcurve, copyFcurve


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
        #context.evaluated_depsgraph_get().update()
        
        #Insert keyframe on the 'lens' property (Focal Length)
        cam_data.keyframe_insert(data_path="lens", frame=f)

    
    cam_data.driver_remove("lens")
    print("Driver successfully removed.")
    
    scene.frame_set(current_frame)
    cam_data.update_tag()
    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get()
    
    print("Focal length baked.")

def valid_selection(context:bpy.types.Context) -> bool:
    if len(context.selected_objects) != 2: return False
    if context.active_object is None or context.active_object.type != 'CAMERA': return False

    for obj in context.selected_objects:
        if obj.type != 'CAMERA': return False

    return True

def focal_to_fov(focal:float, sensor:float, aspect:float=1, s_ratio:float=1, fit:str="") -> float:
    if fit == "HORIZONTAL":
        fov = 2 * math.atan((sensor / focal / 2) * aspect * s_ratio)

    elif fit == "AUTO":
        fov = 2 * math.atan((sensor / focal / 2) * min(s_ratio, aspect * s_ratio))  #This case i didn't know existed, learned from mmd tools.

    else:
        fov = 2 * math.atan(sensor / focal / 2)
    
    return fov

class A3DA_Utils_OT_MMDfy_camera(bpy.types.Operator):
    bl_idname = "a3da_utils.mmdfy_camera"
    bl_label = "Focal Length to FOV mod"
    bl_description = "Converts the focal length of the selected camera to FOV, and saves it into the distances of the active camera. The resulting camera will be suitable for use with float FOV modded MMD."
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

        col.label(text="Transfer the selected focal length into the distance of the active camera.")
        col.separator()

        if valid_selection(context):
            #col.label(text=f"Source camera: \"{context.active_object.name}\"", icon='CAMERA_DATA')
            col.label(text=f"Target camera: \"{context.active_object.name}\"", icon='CAMERA_DATA')
        else:
            col.label(text="Invalid selection. Please select a camera.", icon='ERROR')
        pass

        col.prop(self, "bake_lens")

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "CAMERA"

    def execute(self, context):
        if not valid_selection(context):
            self.report({'ERROR'}, "Invalid selection!")
            return {'CANCELLED'}

        print("Convert to MMD camera operator start")

        ### Logic for MMDifying camera ###
        source_cam = None
        target_cam = context.active_object

        for obj in context.selected_objects:
            if obj != target_cam and obj.type == 'CAMERA':
                source_cam = obj

        if not source_cam:
            self.report({'ERROR'}, "Invalid selection!")
            return {'CANCELLED'}
        
        ## Params ##
        render = context.scene.render
        aspect = (render.resolution_y * render.pixel_aspect_y) / (render.resolution_x * render.pixel_aspect_x) #Aren't pixel aspect y/x always 1? Dunno, seems like a weird feature
        sensor_h = source_cam.data.sensor_height
        ratio = source_cam.data.sensor_width / source_cam.data.sensor_height
        fit = source_cam.data.sensor_fit

        print(f"Aspect Ratio: {aspect}")
        print(f"Sensor Heigth: {sensor_h}")
        print(f"Sensor Ratio: {ratio}")
        print(f"Sensor Fit: {fit}")


        ## Bake driver on focal length ##
        if self.bake_lens:
            bake_camera_focal_length(context, source_cam)


        ## Get fcurves ##
        s_data_action = ensureAction(source_cam.data)
        t_channelbag = getChannelbag(target_cam, ensure=True)
        t_action = ensureAction(target_cam)
        #s_data_fcurve = s_data_channelbag.fcurves.find("lens")
        s_fcurve = s_data_action.fcurve_ensure_for_datablock(
            source_cam.data, "lens")
        #t_fcurve = t_channelbag.fcurves.find("location", index=1)
        t_fcurve = t_action.fcurve_ensure_for_datablock(
            target_cam, "location", index=1)

        #Remove Fcurve
        if t_fcurve:
            t_channelbag.fcurves.remove(t_fcurve)

        #Copy fcurve
        #copyFcurve(s_fcurve, t_fcurve)
        t_fcurve:bpy.types.FCurve = t_channelbag.fcurves.new_from_fcurve(s_fcurve, data_path="location")   #This crashes the whole Blender if s_fcurve is None xd
        t_fcurve.array_index = 1

        #Apply formula FLength to FOV
        kp:bpy.types.Keyframe
        for kp in t_fcurve.keyframe_points:

            kp.co.y = focal_to_fov(kp.co.y, sensor_h, aspect, ratio, fit) * 4.583912 #Fov magic number
            kp.handle_left.y = focal_to_fov(kp.handle_left.y, sensor_h, aspect, ratio, fit) * 4.583912     #Ok so this number is weird. It is 180 / (pi * 12.5), and 12.5 is the mmd scale factor.
            kp.handle_right.y = focal_to_fov(kp.handle_right.y, sensor_h, aspect, ratio, fit) * 4.583912   #So i guess it's necesary to compensate for the mmd scale.

        context.view_layer.update()
        return {'FINISHED'}