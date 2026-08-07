# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. import A3DA_Core
from .. import A3DA_Camera
from .. import A3DA_Objects
from ..A3DA_Import import A3DA_HRC

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from mathutils import Vector, Matrix
import math 

class A3da_Edit_OT_ConvertArmature(Operator):   
    bl_idname = "a3da_edit.convert_armature"
    bl_label = "Convert Armature"
    bl_description = "Creates a new armature with the same bone structure as the selected one, but with all bones starting at the armature origin. This armature is ready to be export as A3DA"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=200,
                title="Convert armature",
                )

    def draw(self, context):
        layout = self.layout
        #layout.label(text="Modo Sexo: Activado")

    def execute(self, context):
        root = None
        for obj in context.selected_objects:
            if obj.auth3d.is_auth3d and obj.auth3d.auth3d_type == 'ROOT':
                root = obj
                break
        if not root:
            self.report({'ERROR'}, f'No Auth3D Space selected!!!')
            return {'CANCELLED'}

        print("Converting armature")
        origin_arm  = context.active_object
        new_arm_data = bpy.data.armatures.new(f'Auth3D_{origin_arm.data.name}_Data')
        new_arm:bpy.types.Object = bpy.data.objects.new(f'Auth3D_{origin_arm.name}', new_arm_data)
        context.scene.collection.objects.link(new_arm)
        context.view_layer.objects.active = new_arm

        #Copy bones
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = new_arm.data.edit_bones
        for orB in origin_arm.data.edit_bones:
            if orB.name not in edit_bones:
                bone = A3DA_HRC.createBone(new_arm, orB.name)
            else:
                bone = edit_bones[orB.name]

            if orB.parent:
                if orB.parent.name not in edit_bones:
                    A3DA_HRC.createBone(new_arm, orB.parent.name)
                bone.parent = edit_bones[orB.parent.name]

        #Set constraints
        bpy.ops.object.mode_set(mode='POSE')
        for newB in new_arm.pose.bones:
            orB:bpy.types.PoseBone = origin_arm.pose.bones.get(newB.name)
            newB.rotation_mode = 'XYZ'

            constraint = newB.constraints.new(type='COPY_TRANSFORMS')
            constraint.target = origin_arm
            constraint.subtarget = orB.name
            constraint.target_space = "WORLD"
            constraint.space_subtarget = "WORLD"

        #Finish
        bpy.ops.object.mode_set(mode="OBJECT")
        new_arm.parent = root
        new_arm.auth3d.is_auth3d = True
        new_arm.auth3d.auth3d_type = 'HRC'
        self.report({'INFO'}, f'"Created {new_arm.name}" from"{origin_arm.name}"')

        return {'FINISHED'}
    

class A3da_Edit_OT_ConvertModel(Operator):
    bl_idname = "a3da_edit.convert_model"
    bl_label = "Convert Models"
    bl_description = "Attaches empties to the selected models. Active object must be Auth3D space"
    bl_options = {"REGISTER", "UNDO"}

    transfer_mode : EnumProperty(   #type: ignore
        name="Mode",
        description="Method to transfer animation",
        items=[
            ('COPY', 'Copy FCurves', "!!! WARNING !!! This requires selected objects to be in Auth3D space (rotated 90°), or it will not work!"),
            ('BAKE', "Bake Animation", "Creates empties, then adds and bakes constraints"),
            ('NOBAKE', "Constraints Only", "Creates empies and adds constraints, but doesn't bake animation"),
            ('NONE', "None", "Creates empties, but doesn't transfer animation")
        ],
        default='BAKE'
    )

    attach_meshes : BoolProperty(  #type: ignore
        name="Attach meshes",
        description="Attaches meshes to created controllers after bake.",
        default=True
    )
    
    prefix : StringProperty(    #type: ignore
        name = "Prefix",
        description= "Prefix to use on created empties.",
        default=""
    )


    @classmethod
    def poll(cls, context): #Maybe not check for empties
        return len(context.selected_objects) > 1 and context.active_object and context.active_object.type in {'OBJECT', 'MESH', 'EMPTY'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=300,
                title="Convert model",
                )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "prefix")
        layout.prop(self, "transfer_mode")

        meshRow = layout.row()
        meshRow.prop(self, "attach_meshes")
        meshRow.enabled = self.transfer_mode != 'NOBAKE'

    def execute(self, context):
        root = None
        for obj in context.selected_objects:
            if obj.auth3d.is_auth3d and obj.auth3d.auth3d_type == 'ROOT':
                root = obj
                break
        if not root:
            self.report({'ERROR'}, f'No Auth3D Space selected!!!')
            return {'CANCELLED'}
        
        ### Conversion logic ###
        id = 0
        empties = []
        for obj in context.selected_objects:
            ## Creating empties ##
            empty = A3DA_Objects.createEmpty(f'{root.name}_{id}')
            empties.append(empty)
            empty.parent = root
            empty.auth3d.auth3d_type = 'OBJECT'
            empty.auth3d.uid_name = obj.name
            id += 1

            ## Transfer animation ##
            if self.transfer_mode == 'NONE':
                continue

            if self.transfer_mode in {'BAKE', 'NOBAKE'}:
                constraint:bpy.types.CopyTransformsConstraint = empty.constraints.new(type='COPY_TRANSFORMS')
                constraint.target = obj
                constraint.target_space = 'WORLD'
                constraint.owner_space = 'WORLD'
                constraint.remove_target_shear = True

        return {'FINISHED'}
    

class A3da_Edit_OT_ConvertCamera(Operator):
    bl_idname = "a3da_edit.convert_cam"
    bl_label = "Convert Camera"
    bl_description = "Converts selected camera to an Auth3D Camera"
    bl_options = {"REGISTER", "UNDO"}

    offset_distance : bpy.props.FloatProperty(  #type: ignore
        name="Offset Distance",
        description="Distance from the camera to the interest point",
        default=5.0,
        min=0.25,
        soft_max=100.0,
        subtype= "DISTANCE"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=200,
                title="Convert to Auth3D Camera",
                )

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True

        layout.prop(self, "offset_distance", text="Interest Distance", )
    
    def execute(self, context): #Time for matrix math fuck yeah
        def get_interest_mtrx(cam_matrix:Matrix, distance:float=5.0) -> Matrix:
            return cam_matrix @ Matrix.Translation((0, 0, -distance))  #Offsets the world matrix by distances and thats it

        def localize_world_pos(matrix:Matrix, obj:bpy.types.Object) -> Vector:
            #Returns a location vector in local space to an object
                    
            if obj.parent:
                return (obj.parent.matrix_world.inverted_safe() @ matrix).translation
            else:
                return matrix.translation             

        def apply_cam_rot(org_cam:bpy.types.Object, to_cam:bpy.types.Object):
            #Copies org_cam's resulting roll rotation onto to_cam by isolating it in view_point local space
            
            org_rot_4x4 = org_cam.matrix_world.to_quaternion().to_matrix().to_4x4().copy()
            org_pos_vec = org_cam.matrix_world.to_translation().copy()

            new_world = org_rot_4x4
            new_world.translation = org_pos_vec

            #Convert to local space
            parent_inverse = to_cam.parent.matrix_world.inverted()
            local_matrix = parent_inverse @ new_world

            #Extract rotation & apply into camera
            local_rot = local_matrix.to_quaternion().to_euler(to_cam.rotation_mode)
            to_cam.rotation_euler.z = local_rot.z

            return #Rule #1: If it works, dont touch it

        def get_fov(cam:bpy.types.Object, scene:bpy.types.Scene) -> float:
            #Returns whatever focal length the camera has as horizontal FOV

            render = scene.render
            aspect_x = render.resolution_x * render.pixel_aspect_x
            aspect_y = render.resolution_y * render.pixel_aspect_y
            sensor_fit = cam.data.sensor_fit

            if sensor_fit == 'AUTO':
                sensor_fit = 'HORIZONTAL' if aspect_x >= aspect_y else 'VERTICAL'

            if sensor_fit == 'HORIZONTAL':
                sensor = cam.data.sensor_width
            elif sensor_fit == 'VERTICAL':  #WHY IS VERTICAL EVEN A THING
                sensor = cam.data.sensor_height * (aspect_x / aspect_y)     #This converts the vertical size to it's horizontal equivalent

            return 2 * math.atan(sensor/ (2 * cam.data.lens))               #And this is just focal to fov

        ### Converter ###
        org_cam = context.active_object

        # Create auth3D rig #
        a3d_cam = A3DA_Camera.A3daCamera()
        A3DA_Camera.setupCam(a3d_cam, None, prefix=f'{org_cam.name}_A3DA')
        A3DA_Camera.setupFovDriver(a3d_cam)

        interest = a3d_cam.interest.bl_reference
        viewpoint = a3d_cam.view_point.bl_reference
        camera = a3d_cam.bl_camera

        # Bake anim #
        org_frame = context.scene.frame_current
        scene = context.scene
        scene.frame_set(context.scene.frame_start)

        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            cam_wm = org_cam.matrix_world.copy()

            # Set matrices #
            interest.location = localize_world_pos(get_interest_mtrx(cam_wm, self.offset_distance), interest)
            viewpoint.location = localize_world_pos(cam_wm, viewpoint)

            # Set values #
            camera.auth3d_cam.fov = get_fov(org_cam, scene)

            #UPDATE OBJECTS TO UPDATE TRACKTO MODIFIER
            interest.update_tag()
            viewpoint.update_tag()
            context.view_layer.depsgraph.update()

            apply_cam_rot(org_cam, camera)

            # Insert Keyframes #
            interest.keyframe_insert(data_path="location", frame=frame)
            viewpoint.keyframe_insert(data_path="location", frame=frame)
            camera.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
            camera.keyframe_insert(data_path="auth3d_cam.fov", frame=frame)


        scene.frame_set(org_frame)
        return {"FINISHED"}


classes = [
    A3da_Edit_OT_ConvertArmature,
    A3da_Edit_OT_ConvertModel,
    A3da_Edit_OT_ConvertCamera
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)