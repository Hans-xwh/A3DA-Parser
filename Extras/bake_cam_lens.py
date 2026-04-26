import bpy

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

#Run the function
bake_camera_focal_length(bpy.context, bpy.context.active_object)