# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
from bpy.props import BoolProperty
from colorsys import rgb_to_hsv


class A3DA_Utils_OT_FixMats(bpy.types.Operator):
    bl_idname = "a3da_utils.fix_mats"
    bl_label = "Fix Materials"
    bl_description = "Edits selected objects materials to better match the Project Diva look."
    bl_options = {"REGISTER", "UNDO"}

    #Config
    fix_emission : BoolProperty(            #type: ignore
        name='Fix Emission', default=True
    )

    preserve_emission_strenght : BoolProperty(            #type: ignore
        name='Preserve Emission Strenght', default=True
    )

    fix_alpha : BoolProperty(            #type: ignore
        name='Fix Alpha', default=True
    )

    fix_metallic : BoolProperty(            #type: ignore
        name='Fix Metalic', default=True
    )

    use_alpha_blend : BoolProperty(            #type: ignore
        name='Use Alpha Blend', default=False
    )

    use_vertex_color : BoolProperty(            #type: ignore
        name='Use Vertex Color', default=True
    )

    use_alpha_dither : BoolProperty(            #type: ignore
        name='Use Alpha Dither', default=False
    )

    use_backface_culling : BoolProperty(            #type: ignore
        name='Use Backface Culling', default=True
    )

    show_backface : BoolProperty(            #type: ignore
        name='Show Backface', default=True
    )

    #Operator stuff
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width= 400,
                title= "Fix Materials",
                confirm_text= "Run!")     #This shows the popup dialog magic
    
    def draw(self, context):    #And this what is shown in the popup
        layout = self.layout
        row = layout.row()
        row.label(text="Select Fixes to Run")
        #row.operator(self.bl_idname, text="Reset", icon='FILE_REFRESH')
        #row.operator(self.bl_idname, text="Clear", icon='CANCEL')
        layout.separator()

        layout.label(text="Material Fixes")
        grid_A = layout.grid_flow(columns=2, even_columns=True, even_rows=False, align=False)
        grid_A.prop(self, 'fix_emission')

        emiRow = grid_A.row()
        emiRow.prop(self, 'preserve_emission_strenght')
        emiRow.enabled = self.fix_emission  #Only show prop when fix_emission is enabled

        grid_A.prop(self, 'fix_alpha')
        grid_A.prop(self, 'fix_metallic')
        grid_A.prop(self, 'use_vertex_color')
        layout.separator()

        grid_B = layout.grid_flow(columns=2, even_columns=True, even_rows=False, align=False)

        #Alpha blend & dither
        alphaBlend_row = grid_B.row()
        alphaDither_row = grid_B.row()
        alphaBlend_row.prop(self, 'use_alpha_blend')
        alphaDither_row.prop(self, 'use_alpha_dither')

        if self.use_alpha_blend:
            self.use_alpha_dither = False
        elif self.use_alpha_dither:
            self.use_alpha_blend = False
        alphaBlend_row.enabled = not self.use_alpha_dither
        alphaDither_row.enabled = not self.use_alpha_blend

        #Backface culling
        hideBack_row = grid_B.row()
        hideBack_row.prop(self, 'use_backface_culling')
        showBack_row = grid_B.row()
        showBack_row.prop(self, 'show_backface')

        if self.use_backface_culling:
            self.show_backface = False
        elif self.show_backface:
            self.use_backface_culling = False
        hideBack_row.enabled = not self.show_backface
        showBack_row.enabled = not self.use_backface_culling


    def execute(self, context):
        print('FixMats Start')
        selected = context.selected_objects
        processed_mats = set()   #To avoid processing the same material multiple times

        for obj in selected:
            if obj.type != 'MESH':
                continue

            #print(f'\n"{obj.name}" has {len(obj.material_slots)} material(s)')
            
            for slot in obj.material_slots:
                if not slot or not slot.material:   #So empty slots wont crash
                    continue

                ## Apply material settings ##
                material = slot.material
                if material in processed_mats:
                    continue    #Skip already processed materials
                else:
                    processed_mats.add(material)

                # Blended or Dither #
                if self.use_alpha_blend:
                    material.surface_render_method = "BLENDED"
                    material.use_transparency_overlap = True
                elif self.use_alpha_dither:
                    material.surface_render_method = "DITHERED"

                # Show/Hide Backface #
                if self.use_backface_culling:
                    material.use_backface_culling = True
                    material.use_backface_culling_shadow = True
                elif self.show_backface:
                    material.use_backface_culling = False
                    material.use_backface_culling_shadow = False


                ## Node Stuff ##
                nodeTree = material.node_tree

                prncBsdf = None
                for node in nodeTree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        prncBsdf = node
                        break
                
                #Skip material if it hasnt a BSDF_PRINCIPLED
                if not prncBsdf:
                    print("Couldn't find BSDF_PRINCIPLED")
                    continue

                #Find main image texture
                if prncBsdf.inputs["Base Color"].is_linked:
                    current = prncBsdf.inputs["Base Color"].links[0].from_node
                else:
                    current = None
                    print("Base Color is empty!")

                #Loop to find main image texture node
                while current and current.type in {'MIX', 'MIX_RGB', 'COLORRAMP'}:
                    socket = current.inputs.get("A") or current.inputs.get("Color1") or current.inputs.get("Fac")
                    if socket and socket.is_linked:
                        current = socket.links[0].from_node
                    else:
                        current = None
                        print("No linked image node found, ending search!")
                        break

                if current and current.type == "TEX_IMAGE":     #TODO Maybe update this to use bl_idname or smth
                    #print("Main image guessed!")
                    mainImg = current
                else:
                    print("Couldn't find image")
                    continue

                #### time to make changes ####

                ## Fix emission ##
                if self.fix_emission:
                    #Create link between image and bsdf
                    nodeTree.links.new(mainImg.outputs["Color"], prncBsdf.inputs["Emission Color"])

                    if self.preserve_emission_strenght:
                        #rgb values need to be normalized first
                        default_emi = prncBsdf.inputs["Emission Color"].default_value
                        norm_r = default_emi[0] / 255
                        norm_g = default_emi[1] / 255
                        norm_b = default_emi[2] / 255
                        #norm_r = default_emi[0]
                        #norm_g = default_emi[1]
                        #norm_b = default_emi[2]

                        #Now convert to hsv
                        hsv = rgb_to_hsv(norm_r, norm_g, norm_b)
                        value = hsv[2] * 255
                        #print("Strength is", value)

                        #Apply to node
                        prncBsdf.inputs["Emission Strength"].default_value = value

                ## Disconnect metalic map ##
                if self.fix_metallic:
                    for link in nodeTree.links:
                        if link.to_node == prncBsdf and link.to_socket.identifier == "Metallic":
                            nodeTree.links.remove(link)
                            break

                ## Fix alpha ##
                if self.fix_alpha:
                    #Create link imgage_alpha -> bsdf
                    nodeTree.links.new(mainImg.outputs["Alpha"], prncBsdf.inputs["Alpha"])

                ## Vertex color ###
                if self.use_vertex_color:   #This thing should always run last
                    #If a object has no vertex colors, skip
                    if len(obj.data.color_attributes) < 1:
                        #print("Object has no vertex colors, dont even try")
                        continue    #Maybe not use continue here? Can mess with other materials on the same object or with code after this

                    #If there is already an attribute node, ensure link and skip
                    attrNode = nodeTree.nodes.get("Color Attribute")
                    if attrNode:
                        print("Attribute node already exists, skipping!")
                        if self.fix_emission:   #Make sure link to emission is there anywaya
                            mixNode = attrNode.outputs["Color"].links[0].to_node
                            nodeTree.links.new(mixNode.outputs["Result"], prncBsdf.inputs["Emission Color"])
                        continue
                    else:
                        #Create attribute node
                        attrNode = nodeTree.nodes.new("ShaderNodeVertexColor")

                    #I want to make a link between att and a color mix in multiply mode. Then connect to base color and emission. In the other input of the mix node i will put the main image
                    #Create mix node
                    mixNode = nodeTree.nodes.new("ShaderNodeMix")
                    mixNode.blend_type = "MULTIPLY"
                    mixNode.data_type = "RGBA"
                    mixNode.inputs["Factor"].default_value = 1.0  #Full effect
                    mixNode.inputs["B"].default_value = (1.0, 1.0, 1.0, 1.0)  

                    #Create link between main image and mix node
                    nodeTree.links.new(mainImg.outputs["Color"], mixNode.inputs["A"])   

                    #Create link between attribute and mix node
                    nodeTree.links.new(attrNode.outputs["Color"], mixNode.inputs["B"])

                    #Create link between mix node and bsdf
                    nodeTree.links.new(mixNode.outputs["Result"], prncBsdf.inputs["Base Color"])
                    if self.fix_emission:
                        nodeTree.links.new(mixNode.outputs["Result"], prncBsdf.inputs["Emission Color"])

        print('FixMats finished')
        return {'FINISHED'}
    #Holly execute function Batman