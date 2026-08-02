# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy

### Config ###
create_missing_bones = True
force_match_parenting = True


def bindArmatures(self:bpy.types.Operator) -> int:     #0:Ok, 1:Error
    print()
    main = bpy.context.active_object
    ghost = [obj for obj in bpy.context.selected_objects if obj != main and obj.type == 'ARMATURE']

    #Bone names are expected to match
    if main.type != "ARMATURE":
        print("Not an armature!")
        self.report({'ERROR'}, "Not an armature!")
        return 1
    
    if ghost:
        ghost = ghost[0]
    else:
        print("Select two armatures!!")
        self.report({'ERROR'}, "Select two armatures!!")
        return 1

    print(f"Ghost: {ghost.name}")
    print(f"Main: {main.name}")
    
    bpy.ops.object.mode_set(mode="POSE")

    for gpb in ghost.pose.bones:    #gpb = GhostPoseBone
        mpb = main.pose.bones.get(gpb.name)
        if not mpb: continue

        constraint = mpb.constraints.new(type="COPY_TRANSFORMS")
        constraint.target = ghost
        constraint.subtarget = gpb.name
        constraint.target_space = "WORLD"
        constraint.space_subtarget = "WORLD"

    bpy.ops.object.mode_set(mode="OBJECT")

    self.report({'INFO'}, f'"{main.name}" binded to "{ghost.name}"')

    return 0


#if __name__ == "__main__":
#    bindArmatures()