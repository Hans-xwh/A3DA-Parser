# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import ensureAction, getFcurve, getChannelbag, copyFcurve
from ..A3DA_Import.A3DA_Objects import createObjDriver, additionObjDriver

import bpy
from bpy.props import BoolProperty, EnumProperty

class A3DA_Utils_OT_VisibilityEditor(bpy.types.Operator):
    bl_idname = "a3da_utils.visibility_edit"
    bl_label = "Visibility Editor"
    bl_description = "Allows to set & remove visibility drivers."
    bl_options = {'UNDO'}   #No register so it wont appear on redo menu


    operation: EnumProperty( #type: ignore
        name="Operation",
        description="Whether to add or remove visibility drivers.",
        items=[
            ('ADD', "Create Drivers", "Add visibility drivers to the selected objects."),
            ('REMOVE', "Remove Drivers", "Remove visibility drivers from the selected objects."),
            ('MOVE', "Move Fcurve", "Switch between user defined / api properties for the selected objects."),
            ('COPY', "Copy Fcurve", "Copy visibility drivers from active object to selected objects. Note: only for API defined drivers.")
        ],
        default='ADD'
    )

    source: EnumProperty( #type: ignore
        name="Source",
        description="Where to get visibility from.",
        items=[
            ('API', "Auth3D API", "Use the visibility property from the api."),
            ('CUSTOM', "Compatibility", "Use a user defined custom property for visibility.")
        ],
        default='API'
    )

    move_type: EnumProperty( #type: ignore
        name="Move type",
        description="Direction of the move",
        items=[
            ('API', "To API", "Move drivers from user defined custom properties to api properties."),
            ('CUSTOM', "To Custom", "Move drivers from api properties to user defined custom properties.")
        ],
    )

    active_to_selected: BoolProperty( #type: ignore
        name="Active to Selected",
        description="Set visibility driver from active object to selected objects only. When disabled, it will set drivers from all parents to their children meshes.",
        default=False
    )


    @classmethod
    def poll(cls, context):
        return context.active_object and context.selected_objects and context.active_object.type in {'MESH', 'EMPTY', 'ARMATURE'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width= 250,
                title= "Visibility Editor",
                confirm_text= "Apply")

    def draw(self, context):
        layout = self.layout
        #layout.prop(self, "compatibility")
        layout.prop(self, "operation")

        if self.operation == 'ADD':
            layout.label(text="Source: ")
            layout.prop(self, "source", expand=True)
            layout.prop(self, "active_to_selected")
        elif self.operation == 'MOVE':
            layout.label(text="Move to: ")
            layout.prop(self, "move_type", expand=True)

    def execute(self, context):
        active = context.active_object
        modified: int = 0

        ### Add Drivers ###
        if self.operation == 'ADD':            
            #Select source props
            if self.source == 'API':
                data_path = "auth3d.visibility"
            elif self.source == 'CUSTOM':
                data_path = '["A3DA_VISIBILITY"]'
            
            if self.active_to_selected:
                if len(context.selected_objects) < 2:
                    self.report({'WARNING'}, "No valid objects selected. Please select at least one other object!")
                    return {'CANCELLED'}
            
                for obj in context.selected_objects:
                    if obj == active or obj.type not in {'MESH'}: continue
                    createObjDriver(active, data_path, obj,
                                    target_prop='hide_viewport',
                                    expression='(var <= 0.999)')
                    createObjDriver(active, data_path, obj,
                                    target_prop='hide_render',
                                    expression='(var <= 0.999)')
                    modified += 1
            
            else:
                for obj in context.selected_objects:
                    if obj.type not in {'EMPTY', 'ARMATURE'}: continue
                    for child in obj.children:
                        if child.type != 'MESH': continue
                        createObjDriver(obj, data_path, child,
                                        target_prop='hide_viewport',
                                        expression='(var <= 0.999)')
                        createObjDriver(obj, data_path, child,
                                        target_prop='hide_render',
                                        expression='(var <= 0.999)')
                        modified += 1
            self.report({'INFO'}, f"Added visibility drivers to {modified} objects.")

        ### Remove Drivers ###
        elif self.operation == 'REMOVE':
            for obj in context.selected_objects:
                if obj.type not in {'MESH', 'ARMATURE'}: continue

                obj.driver_remove("hide_viewport")
                obj.driver_remove("hide_render")
                modified += 1

            self.report({'INFO'}, f"Removed visibility drivers from {modified} objects")

        ### Move Fcurves from custom to api or vice versa ###
        elif self.operation == 'MOVE':
            for obj in context.selected_objects:
                if obj.type not in {'EMPTY', 'ARMATURE'}: continue
                
                if self.move_type == 'API':
                    s_fcurve = getFcurve(obj, '["A3DA_VISIBILITY"]')
                    if not s_fcurve: continue
                    action = ensureAction(obj)
                    t_fcurve = action.fcurve_ensure_for_datablock(
                        datablock= obj,
                        data_path= "auth3d.visibility",
                    )
                    del obj["A3DA_VISIBILITY"]
                    
                elif self.move_type == 'CUSTOM':
                    s_fcurve = getFcurve(obj, "auth3d.visibility")
                    if not s_fcurve: continue
                    obj["A3DA_VISIBILITY"] = 1
                    action = ensureAction(obj)
                    t_fcurve = action.fcurve_ensure_for_datablock(
                        datablock= obj,
                        data_path= '["A3DA_VISIBILITY"]',
                    )
                    obj.auth3d.property_unset("visibility")
                
                #Copy & delete
                copyFcurve(s_fcurve, t_fcurve)
                s_channelbag = getChannelbag(obj)
                s_channelbag.fcurves.remove(s_fcurve)
                modified += 1
            self.report({'INFO'}, f"Moved visibility on {modified} objects.")

        ### Copy Fcurves from active to all selected ###
        elif self.operation == 'COPY':
            for obj in context.selected_objects:
                if obj == active or obj.type not in {'MESH', 'ARMATURE'}: continue

                source_fcurve = getFcurve(active, "auth3d.visibility")
                #print(f"Source fcurve for {"auth3d.visibility"} on {active.name}: {source_fcurve}")
                if source_fcurve:
                    ensureAction(obj)
                    target_fcurve = obj.animation_data.action.fcurve_ensure_for_datablock(
                        datablock=obj,
                        data_path="auth3d.visibility",
                    )

                    copyFcurve(source_fcurve, target_fcurve)
                    modified += 1
                   
            self.report({'INFO'}, f"Copied visibility drivers on {modified} objects.")

        return{'FINISHED'}