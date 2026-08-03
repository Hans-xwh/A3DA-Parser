import bpy

from bpy.types import Context, Object, Camera, FCurve

def bake_a3da_fov(context:Context):
    target_cam = context.active_object
    if not target_cam or target_cam.type != 'CAMERA': 
        print ("Not a camera!!!")
        return

    if target_cam.auth3d_cam.subtype != 'CAM':
        print("Not an auth3d cam!!!")
        return

    #Get stuff
    cam_data = target_cam.data
    scene = context.scene
    start_frame = scene.frame_start
    end_frame = scene.frame_end
    

    #Bake
    print(f"Baking FOV for {target_cam.name} from frame {start_frame} to {end_frame}...")

    lastKey = 0

    scene.frame_set(start_frame)
    for f in range(start_frame, end_frame + 1):
        #Set the frame
        scene.frame_set(f)

        #Force evaluate driver (Not sure if really needed)
        context.evaluated_depsgraph_get().update()

        if (target_cam.auth3d_cam.fov != lastKey):        
            #Insert keyframe on the fov
            target_cam.keyframe_insert(data_path="auth3d_cam.fov", frame=f)
        lastKey = target_cam.auth3d_cam.fov

    print("Bake finished")


#RUn this shi
if __name__ == '__main__':
    bake_a3da_fov(bpy.context)