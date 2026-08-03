# Camera rigs are in beta, take with a grain of salt!!!  

Rigs to retarget standard MMD cameras, FOV modded MMD cameras, and animated floating cameras are included here, as well as a script to bake the FOV in an Auth3D camera.

## MMD camera -> Auth3D  
- Select the MMD camera, and load your VMD to it. 
- Select all objects in the Auth3D Camera rig, and bake all transforms. 
- Optionally clean redundant keyframes on the scale. I recommend to leave the rotation and translation as-is. 
- With the camera object on the Auth3D rig selected run `Bake auth3d fov.py` from the scripting tab. 
- Export your a3da. 

## MMD FOV camera -> Auth3D
- Same process as with a standard MMD camera. 
- Please note, the MMD camera **will** look messed up in Blender. The Auth3D camera should look right. 

## Random floating camera -> Auth3D
- *Append* the action of your camera. 
- Select the floating camera, and assign your appended action to it. 
- Select all objects in the Auth3D Camera rig, and bake all transforms. 
- With the camera object on the Auth3D rig selected run `Bake auth3d fov.py` from the scripting tab.
- Export your a3da. 

## Dolly camera rig -> Auth3D
#### Intended for cameras made with the addon "Add Camera Rigs"
- *Append* the action of your camera rig. 
- Select the camera rig, and assign your appended action to it. 
- You can make the **interest** Auth3D object follow the dolly *aim* or directly the camera, depending in your animation one might give a better result than the other.  
- Select all objects in the Auth3D Camera rig, and bake all transforms. 
- With the camera object on the Auth3D rig selected run `Bake auth3d fov.py` from the scripting tab. 
- Export your a3da. 
