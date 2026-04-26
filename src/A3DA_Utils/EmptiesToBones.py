# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. A3DA_Core import ensureAction, getFcurve, copyFcurve
import bpy
from bpy.types import Operator, Object, EditBone
from bpy.props import BoolProperty, StringProperty, EnumProperty
from mathutils import Matrix, Vector

class A3DA_Utils_OT_EmptiesToBones(Operator):
    bl_idname = "a3da_utils.empties_to_bones"
    bl_label = "Empties To Bones"
    bl_description = "Works on selected objects. For every empty that has at least a children mesh, creates a bone that will follow the empty, and attaches the meshes, originially parented to the empty, to the bone. Breaks for objects with negative scale."
    bl_options = {'REGISTER', 'UNDO'}


    rename : EnumProperty(  #type: ignore
        name = "Bone Naming",
        description = "How to name the created bones",
        items=[
            ('UID', "Use UID_Name", "Bones will be named after the objects' UID_Name field if it exists, otherwise fallback to object name."),
            ('OBJECT', "Use Object Names", "Bones will be named after the objects."),
            ('RENAME', "Rename", "Renames bones with a prefix."),
        ],
        default='UID'
    )

    prefix : StringProperty(  #type: ignore
        name="Name Prefix",
        description="Prefix to use when renaming bones. Underscore (_) will be added.",
        default="A3D",
    )

    at_origin : BoolProperty(   #type: ignore
        name= "Bones at origin",
        description= "Make all bones rest pose the armature's origin. This is the desired behaviour in most cases",
        default= True
    )

    scale_type : EnumProperty(  #type: ignore
        name  = "Scale Handling",
        description= "Method of handling scale animation",
        items=[
            ('BONES', "Scale Bones", "Make bones copy the scale too"),
            ('MORPHS', "Uniform Morphs", "(! Slow !) Creates a morph for the average scale of every object. Good enough for most of the cases."),
            ('NU_MORPHS', "Non-Uniform Morphs", "(!! Slower !!) Creates a scale morph for every axis of every object. Usefull for objects with non uniform scale."),
            ('NONE', "None", "Don't use scale animation.")
        ],
        default= 'BONES'
    )

    dont_scale_z_axis : BoolProperty( #type: ignore
        name = "Ignore Z Axis",
        description= "When calculating the average scale, don't take in consideration Z axis. Usefull for plain objects.",
        default= False
    )


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width= 350,
                title= "Empties to Bones",
                #confirm_text= "Ok"
                )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "at_origin")

        layout.prop(self, "scale_type")

        if self.scale_type == 'MORPHS':
            layout.prop(self, "dont_scale_z_axis")

        layout.prop(self, "rename")
        if self.rename == 'RENAME':
            layout.prop(self, "prefix")

    def execute(self, context):
        print("Empties to Bones Start")
        mappings:dict[str, str] = {}    #obj_name : bone_name
        parent_map:dict[Object, list[Object]] = {}  #Parent, [Children]
        scale_cache:dict[Object, dict[int, bpy.types.Vector]] = {}
        count = 0
        scale_factor = 5

        ### Create Armature ###
        arm_data = bpy.data.armatures.new("A3DA_ObjBake_Data")
        armature:Object = bpy.data.objects.new("A3DA_ObjBake", arm_data)
        context.collection.objects.link(armature)

        ### Build obj list ###
        objects:list[Object] = []
        for obj in context.selected_objects:
            #Check if an object is an empty controlle that has at least one mesh
            if obj.type != "EMPTY": continue
            if obj.children and obj.children[0].type == 'MESH': #Skip if child is something non-mesh
                objects.append(obj)
            elif not obj.children:
                objects.append(obj)
        #print(objects)

        ### Read objects and get max & min ###
        rest_scales = {obj: Vector((1,1,1)) for obj in objects}  #Im not 100% sure using matrices & vectors for this is the best

        if self.scale_type == 'NU_MORPHS':
            ## Build rest scales ##
            print("Reading sale matrices...")
            scale_cache = {obj: {} for obj in objects}
            scene = context.scene
            scene.frame_set(scene.frame_start)
            max_scales = {obj: obj.matrix_world.to_scale().copy() for obj in objects}

            ## Read anim data to get max & mins. Also prepares scale cache ##
            frame = scene.frame_start
            while frame <= scene.frame_end:
                #print(f'Frame = {frame}')
                scene.frame_set(frame)
                for obj in objects:
                    scale = obj.matrix_world.to_scale()

                    #Save scale to cache
                    scale_cache[obj][frame] = scale.copy()  #If i hate these in c++ IMAGINE how i hate matrices in python

                    max_scales[obj].x = max(max_scales[obj].x, scale.x)
                    max_scales[obj].y = max(max_scales[obj].y, scale.y)
                    max_scales[obj].z = max(max_scales[obj].z, scale.z)
                frame += 1

        elif self.scale_type == 'MORPHS':
            scalable_controllers = []

            #Identify objects to animate scale on
            for obj in objects:
                if not obj.children or obj.children[0].type != 'MESH': continue
                #if not obj.animation_data or not obj.animation_data.action: continue    #Skip non-mesh-controller and non animated objs

                #If object has scale on any axis
                scalable_controllers.append(obj)
                parent_map[obj] = []

                #Create shape keys & save children mapping
                for child in obj.children: 
                    if child.type == 'MESH': 
                        parent_map[obj].append(child)

                        if not child.data.shape_keys:
                            child.shape_key_add(name="Basis")
                        scale_key = child.shape_key_add(name=f"Auth3D_Scale")
                        for i, v in enumerate(scale_key.data):
                            v.co = child.data.vertices[i].co * scale_factor

                        scale_key.slider_min = -10
                        scale_key.slider_max = 10

                        #Create Fcurve
                        shapeKey_action = ensureAction(scale_key.id_data)
                        fcurve = shapeKey_action.fcurve_ensure_for_datablock(
                            scale_key.id_data,
                            f'key_blocks["Auth3D_Scale"].value'
                        )

                        fcurve.keyframe_points.add(context.scene.frame_end - context.scene.frame_start + 1)
                        #Dont update fcurve yet

            #Read animation
            print("Reading sale matrices...")
            scene = context.scene
            scene.frame_set(scene.frame_start)

            frame = scene.frame_start
            while frame <= scene.frame_end:
                #print(f"Frame: {frame}")
                scene.frame_set(frame)

                obj:bpy.types.Object
                scale = 0
                for obj in scalable_controllers:
                    if obj.parent and self.dont_scale_z_axis:
                        parent_rot = obj.parent.matrix_world.to_quaternion().to_matrix().to_4x4()   #Ok i actually don't know if this will work for every case but whatever
                        obj_matrix = parent_rot.inverted_safe() @ obj.matrix_world
                    else:
                        obj_matrix = obj.matrix_world
                    scale = obj_matrix.to_scale()     #Scale vector

                    if not self.dont_scale_z_axis:
                        avg_scale = (scale.x + scale.y + scale.z) / 3
                    else:
                        avg_scale = (scale.x + scale.y) / 2

                    for child in parent_map[obj]:
                        shapeKey:bpy.types.ShapeKey = child.data.shape_keys.key_blocks.get("Auth3D_Scale")
                        fcurve = getFcurve(shapeKey.id_data, 'key_blocks["Auth3D_Scale"].value')
                        kp:bpy.types.Keyframe = fcurve.keyframe_points[frame - scene.frame_start] #Pls just start at 0 always
                        kp.co = (frame, (avg_scale - 1) / scale_factor)

                        if frame == scene.frame_end:
                            fcurve.update()
                frame += 1

        ### Create Bones ###
        print("Creating bones...")
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = armature.data.edit_bones

        ## Create root ##
        root = edit_bones.new("Root")
        root.head = (0,0,0)
        root.tail = (0,0,1)

        for obj in objects:
            ## Get bone matrix ##
            local_matrix = armature.matrix_world.inverted() @ obj.matrix_world  #Tbh im not sure what to name these, i just played arround until it worked XD
            trans_vec = local_matrix.to_translation()
            rot_quat = local_matrix.to_quaternion()
            #scale_vec = local_matrix.to_scale()
            final_matrix = Matrix.LocRotScale(trans_vec, rot_quat, None)    #Discard scale

            ## Rename if needed ##
            if self.rename == 'RENAME':
                name = f'{self.prefix}_{count}'
            elif self.rename == 'UID':
                if obj.auth3d.auth3d_type == 'OBJECT' and obj.auth3d.uid_name not in ("", "NULL"):
                    name = obj.auth3d.uid_name
                else:
                    name = obj.name
            else:
                name = obj.name
            mappings[obj.name] = name

            ## Make Bone ##
            new_bone:EditBone = edit_bones.new(name)
            new_bone.parent = root
            new_bone.head = (0,0,0)
            #new_bone.tail = (0,0,1)
            new_bone.length = 1
            if not self.at_origin:
                new_bone.matrix = final_matrix
            else:
                new_bone.matrix = Matrix.Identity(4)

            count += 1

        ## Set constraints & parent meshes ##
        print("Setting constraints...")
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in objects:
            Bname = mappings[obj.name]
            pBone = armature.pose.bones.get(Bname)
            if not pBone:
                print(f'WARNING: Bone for obj "{obj.name}" not found!!!')
                continue

            parent_map[obj] = []

            if self.scale_type == 'BONES':
                copy_transforms = pBone.constraints.new("COPY_TRANSFORMS")
                copy_transforms.target_space = "WORLD"
                copy_transforms.target = obj
            #    copy_scale = pBone.constraints.new("COPY_SCALE")
            #    copy_scale.target_space = "WORLD"
            #    copy_scale.target = obj
            else:
                copy_loc = pBone.constraints.new("COPY_LOCATION")
                copy_loc.target_space = "WORLD"
                copy_loc.target = obj
                copy_rot = pBone.constraints.new("COPY_ROTATION")
                copy_rot.target_space = "WORLD"
                copy_rot.target = obj

            # Mesh assignment & shape key creation #
            for child in obj.children:
                if child.type != 'MESH': continue
                parent_map[obj].append(child)

                #Always apply initial scale:
                rest = rest_scales.get(obj) 

                #Decide if scale is animated
                if self.scale_type == 'NU_MORPHS':
                    max_s = max_scales[obj]
                    has_scale_anim = (max_s - rest).length > 0.001 #or (min_s - rest).length > 0.001

                    if has_scale_anim:
                        #Create shape keys (this time fr pls)
                        child.shape_key_add(name="Basis")
                        for axis in ('x', 'y', 'z'):
                            rest_val = getattr(rest, axis)
                            max_val = getattr(max_s, axis)

                            key_max:bpy.types.ShapeKey = child.shape_key_add(name=f"{Bname}_{axis}")
                            key_max.slider_min = -10
                            key_max.slider_max = 10

                            #Build shapekeys
                            for i, v in enumerate(child.data.vertices):
                                co_max = v.co.copy()
                                #co_min = v.co.copy()
                                #setattr(co_max, axis,
                                #        getattr(v.co, axis) * (max_val / rest_val) if rest_val != 0 else 0)  # max_val / rest_val = scale factor. Relative to the created shape key for max/min
                                setattr(co_max, axis,
                                        getattr(v.co, axis) * scale_factor)
                                #setattr(co_min, axis,
                                #        getattr(v.co, axis) * (min_val / rest_val) if rest_val != 0 else 0)
                                key_max.data[i].co = co_max
                                #key_min.data[i].co = co_min

                #Auto parent
                old_matrix = child.matrix_world.copy()
                child.parent = armature
                if not self.at_origin:
                    child.matrix_world = old_matrix
                else:
                    child.matrix_local = Matrix.Identity(4)
                    child.matrix_world = Matrix.Identity(4)

                #Modifier
                arm_modifier = child.modifiers.get("Armature")
                if not arm_modifier:
                    arm_modifier = child.modifiers.new(name="Armature", type="ARMATURE")
                arm_modifier.object = armature

                #Autorig
                vGroup = child.vertex_groups.get(Bname)
                if not vGroup:
                    vGroup = child.vertex_groups.new(name=Bname)
                vGroup.add(
                    range(len(child.data.vertices)),
                    weight=1,
                    type="REPLACE"
                )

                #Clear scale when scaling bones
                if self.scale_type == 'BONES':
                    child.scale = Vector((1,1,1))

        ### Animate non uniform shape keys ###
        if self.scale_type == 'NU_MORPHS':
            print("Animating shape keys...")
            frame = scene.frame_start
            while frame <= scene.frame_end:
                for obj in objects:
                    Bname = mappings[obj.name]
                    scale = scale_cache[obj][frame]
                    rest = rest_scales[obj]
                    #min_s = min_scales[obj]
                    max_s = max_scales[obj]

                    for child in parent_map[obj]:
                        if child.type != 'MESH': continue   #redundant but idk
                        if not child.data.shape_keys: continue

                        for axis in ('x', 'y', 'z'):
                            s = getattr(scale, axis)    #istg if i had learned getattr was a thing earlier...
                            r = getattr(rest, axis)
                            mx = getattr(max_s, axis)
                            #mn = getattr(min_s, axis)   

                            shapekey_max = child.data.shape_keys.key_blocks.get(f"{Bname}_{axis}")
                            #shapekey_min = child.data.shape_keys.key_blocks.get(f"{Bname}_{axis}_min")
                            if not shapekey_max: continue

                            #TODO maybe make this build fcurves instead of using insert
                            
                            #shapekey_max.value = (s - r) / (mx - r) if mx != r else 0
                            shapekey_max.value = ((s - 1) / scale_factor)

                            shapekey_max.keyframe_insert("value", frame=frame)
                frame += 1


        print(f'Empties to bones finished. Created {count} bones from objects') #Doesnt count the root
        return {"FINISHED"}
#I aplogize to the pythonic gods for writing this absolute sh*t

class A3DA_Utils_OT_TransferDummyMorph(Operator):
    bl_idname = "a3da_utils.combine_morph"
    bl_label = "Combine Shape Keys"
    bl_description = "Transfer shape keys as dummies from selected objects to active."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Invalid selection. Active must be a mesh!")
            return {'CANCELLED'}

        #Get sources
        sources = [obj for obj in context.selected_objects
                   if obj != target and obj.type == 'MESH' and obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action]    #Dear god what is thisss
        
        if not sources:
            self.report({'ERROR'}, "Invalid selection!")
            return {'CANCELLED'}
        
        if not target.data.shape_keys:
            target.shape_key_add(name="Basis")
        
        #Ensure action & channelbag
        target_action = ensureAction(target.data.shape_keys)
        if not target_action.slots:
            t_slot = target_action.slots.new(id_type='KEY', name="Action")
        else:
            t_slot = target_action.slots[0]

        if target_action.layers:
            t_layer = target_action.layers[0]
        else:
            t_layer = target_action.layers.new(name="Layer")

        if t_layer.strips:
            t_strip = t_layer.strips[0]
        else:
            t_strip = t_layer.strips.new(type='KEYFRAME')

        t_channelbag = t_strip.channelbag(t_slot)
        if not t_channelbag:
            t_channelbag = t_strip.channelbags.new(slot=t_slot)

        # Copy fcurves #
        copied = 0
        for source in sources:
            sourceA = source.data.shape_keys.animation_data.action
            for layer in sourceA.layers:
                for strip in layer.strips:
                    for channelbag in strip.channelbags:
                        for fcurve in channelbag.fcurves:
                            if 'key_blocks' not in fcurve.data_path: continue

                            #Get shape key name from path
                            key_name = fcurve.data_path.split('"')[1]
                            target_shapekeys = target.data.shape_keys.key_blocks

                            #Create dummy shapekey
                            if not target_shapekeys.get(key_name):
                                target.shape_key_add(name=key_name)

                            #Copy fcurve
                            new_fcurve:bpy.types.FCurve = t_channelbag.fcurves.new(
                                data_path = fcurve.data_path,   #idk
                                index = fcurve.array_index
                            )

                            #Copy keyframes
                            #new_fcurve.keyframe_points.add(len(fcurve.keyframe_points))
                            #for i, kp in enumerate(fcurve.keyframe_points):
                            #    new_fcurve.keyframe_points[i].co = kp.co
                            #    new_fcurve.keyframe_points[i].interpolation = kp.interpolation

                            #new_fcurve.update()

                            copyFcurve(fcurve, new_fcurve)
                            copied += 1

        self.report({'INFO'}, f"Copied {copied} shape keys")
        print(f"Copied {copied} shape keys")
        return {'FINISHED'}
