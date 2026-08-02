# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
from mathutils import Matrix #Required to conver world to local space
import time

#Im keeping this since it's faster and a bit less wacky than the new one xd

def createArmature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("A3DA_ObjBake_Data")
    arm = bpy.data.objects.new("A3DA_ObjBake", arm_data)
    bpy.context.collection.objects.link(arm)

    #Make armature active and switch to edit mode
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    
    edit = arm.data.edit_bones
    rootBone = edit.new("ROOT")
    rootBone.head = (0,0,0)
    rootBone.tail = (0,0,1)

    return arm


#Makes bones from empty controllers, efficient, but can be unnacurate. It groups meshes of the same controller under the same bone
def makeBonesObjects(armature:bpy.types.Object, pvName:str, fixNames=True):    #Expects an armature object
    #It was needed to make this into separated lopps to avoid switching modes, wich is slow AF 
    objects: list[bpy.types.Object] = list()
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    editArm = armature.data.edit_bones
    root = editArm.get("ROOT")
    counter = 0

    #Identify empties
    for obj in bpy.context.view_layer.active_layer_collection.collection.objects:
        if obj.type != "EMPTY": continue
        #if not "Has_Mesh" in obj: continue
        if not obj.auth3d.auth3d_type == 'MESH_C': continue
        objects.append(obj)

    #Bone creation
    renameCount = 0
    for obj in objects:
        #Conver obj world coordinates to the armature's space
        local_matrix = armature.matrix_world.inverted() @ obj.matrix_world
        trans_matrix = local_matrix.to_translation()
        rot_matrix = local_matrix.to_quaternion()
        #rot_matrix = local_matrix.to_euler()
        #scale_matrix = local_matrix.to_scale()
        local_matrix = Matrix.LocRotScale(trans_matrix, rot_matrix, None) #Discards scale

        if fixNames and len(obj.name) > 62:
            obj.name = f'ren_{renameCount}'
            renameCount += 1

        #Make Bone
        newBone = editArm.new(obj.name)
        newBone.parent = root
        newBone.head = (0,0,0)
        newBone.tail = (0,0,1)
        newBone.matrix = local_matrix
        #newBone.tail.z += 2

    #Constraint creation
    bpy.ops.object.mode_set(mode="POSE")
    for obj in objects:
        poseBone = armature.pose.bones.get(obj.name)
        if not poseBone: 
            print(f'WARNING: bone for obj "{obj.name}" not found!')
            continue

        obj.name = f"{pvName}_{counter}"        
        poseBone.name = f"{pvName}_{counter}"   #Rename bones so they dont exede MMD name 14 char limit

        ## Constaint ##
        copy_loc = poseBone.constraints.new("COPY_LOCATION")
        copy_loc.target_space = "WORLD"
        copy_loc.target = obj

        copy_rot = poseBone.constraints.new("COPY_ROTATION")
        copy_rot.target_space = "WORLD"
        copy_rot.target = obj

        #copy_scale = poseBone.constraints.new("COPY_SCALE")
        #copy_scale.target_space = "WORLD"
        #copy_scale.target = obj

#        copy_transforms = poseBone.constraints.new("COPY_TRANSFORMS")
#        copy_transforms.target_space = "WORLD"
#        copy_transforms.target = obj
#        copy_transforms.owner_space = "CUSTOM"
#        copy_transforms.space_object = bpy.context.scene.objects.get("STGPV732")

        ## Mesh assignment ##
        for child in obj.children:
            if child.type != "MESH": continue

            #Auto parenting
            old_matrix = child.matrix_world.copy()
            child.parent = armature
            child.matrix_world = old_matrix

            #Modifier
            arm_modifier = child.modifiers.get("Armature")
            if not arm_modifier:
                arm_modifier = child.modifiers.new(name="Armature", type="ARMATURE")
            arm_modifier.object = armature


            #Auto rig
            vertexGroup = child.vertex_groups.get(obj.name)
            if not vertexGroup:
                vertexGroup = child.vertex_groups.new(name=obj.name)
            vertexGroup.add(
                range(len(child.data.vertices)),
                weight=1,
                type="REPLACE"
            )
        counter += 1


#Maekes a bone for each mesh. Every mesh has it's own bone, no grouping. Only meshes inside controllers, non-a3da meshes _should_ be ignored
def makeBonesMeshes(armature:bpy.types.Object, pvName:str, fixNames=True): #Dont use, its veeery unreliable
    meshes: list[bpy.types.Object] = list()           #Contains working meshes
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    editArm = armature.data.edit_bones
    root = editArm.get("ROOT")
    counter = 0

    #Identify empties to get meshes from
    for obj in bpy.context.selected_objects:
        #if obj.type != "EMPTY" or not "Has_Mesh" in obj: continue
        if obj.type != "EMPTY" or not obj.auth3d.auth3d_type == 'MESH_C': continue
        for child in obj.children:
            if child.type != "MESH": continue
            meshes.append(child)

    #Bone creation
    renameCount = 0
    for mesh in meshes:
        #Conver obj world coordinates to the armature's space
        local_matrix = armature.matrix_world.inverted() @ mesh.matrix_world
        trans_matrix = local_matrix.to_translation()
        rot_matrix = local_matrix.to_quaternion()
        local_matrix = Matrix.LocRotScale(trans_matrix, rot_matrix, None) #Discards scale

        #Correct long names
        if fixNames and len(mesh.name) > 62:
            mesh.name = f'ren_{renameCount}'
            renameCount += 1

        #Make Bone
        newBone = editArm.new(mesh.name)
        newBone.parent = root
        newBone.head = (0,0,0)
        newBone.tail = (0,0,1)
        newBone.matrix = local_matrix

    #Constraint creation
    bpy.ops.object.mode_set(mode="POSE")
    for mesh in meshes:
        poseBone = armature.pose.bones.get(mesh.name)
        mesh.name = f"{pvName}_{counter}"        
        poseBone.name = f"{pvName}_{counter}"   #Rename bones so they dont exede MMD name 14 char limit

        ## Constaint ##
        copy_loc = poseBone.constraints.new("COPY_LOCATION")
        copy_loc.target_space = "WORLD"
        copy_loc.target = mesh

        copy_rot = poseBone.constraints.new("COPY_ROTATION")
        copy_rot.target_space = "WORLD"
        copy_rot.target = mesh

        ## Mesh assignment ##
        #old_matrix = mesh.matrix_world.copy()
        #mesh.parent = armature
        #mesh.matrix_world = old_matrix

        #Modifier
        #arm_modifier = mesh.modifiers.get("Armature")
        #if not arm_modifier:
        #    arm_modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
        #arm_modifier.object = armature

        #Auto rig
        #vertexGroup = mesh.vertex_groups.get(f"{pvName}_{counter}")
        #if not vertexGroup:
        #    vertexGroup = mesh.vertex_groups.new(name=f"{pvName}_{counter}")
        #vertexGroup.add(
        #    range(len(mesh.data.vertices)),
        #    weight=1,
        #    type="REPLACE"
        #)
        counter += 1


#Autorig for previously generated bones with MakeBonesMeshes, to be used after baking bones
def autorigBonesFromMeshes():
    armature = bpy.context.active_object
    if armature.type != "ARMATURE": print("Not an armature!"); return

    bpy.ops.object.mode_set(mode="OBJECT")
    for bone in armature.pose.bones:
        mesh = bpy.context.scene.objects.get(bone.name)
        if not mesh or mesh.type != "MESH": print(f"Skipping {bone.name}!!!"); continue

        ## Mesh assignment ##
        #old_matrix = mesh.matrix_world.copy()
        mesh.parent = armature
        mesh.matrix_parent_inverse.identity()
        mesh.matrix_local = Matrix.Identity(4) #An identity matrix means zeroed transformations

        #Modifier
        arm_modifier = mesh.modifiers.get("Armature")
        if not arm_modifier:
            arm_modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
        arm_modifier.object = armature

        #Auto rig
        vertexGroup = mesh.vertex_groups.get(bone.name)
        if not vertexGroup:
            vertexGroup = mesh.vertex_groups.new(name=bone.name)
        vertexGroup.add(
            range(len(mesh.data.vertices)),
            weight=1,
            type="REPLACE"
        )
        print(f"Bone {bone.name} assigned!")


##############################
def autoRun():
    print('\nStart')
    startTime = time.time()
    ###
    edit_bones = createArmature()
    makeBonesObjects(edit_bones, "A3D")
    #makeBonesMeshes(edit_bones, "823")
    #autorigBonesFromMeshes()
    bpy.ops.object.mode_set(mode="OBJECT")

    ###
    print(f'Elapsed time: {round(time.time() - startTime, 4)} seconds')
    print('Execution finished')

