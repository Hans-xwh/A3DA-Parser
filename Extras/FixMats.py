import bpy
from colorsys import rgb_to_hsv

##### Config #####
fix_emission = True
preserve_emission_strenght = True
fix_alpha = True
fix_metallic = True
use_alpha_blend = False
use_backface_culling = True
use_vertex_color = True
##################

selection = bpy.context.collection.objects

for obj in selection:
    #print(obj.type)
    if obj.type == "MESH":
        print(f'"\n{obj.name}" has {len(obj.material_slots)} material(s)')

        for material in obj.material_slots: #Select a material
            nodeTree = material.material.node_tree
            print (nodeTree)

            #Find the Principled BSDF node
            for node in nodeTree.nodes:     
                if node.type == "BSDF_PRINCIPLED":
                    prncBsdf = node
                    break
            print(prncBsdf)

            #Find main image texture
            if prncBsdf.inputs["Base Color"].is_linked:
                current = prncBsdf.inputs["Base Color"].links[0].from_node
            else:
                current = None
                print("Base Color empty, ending search!")

            #Loop to find the image texture node
            while current and current.type in {'MIX', 'MIX_RGB', 'COLORRAMP'}:
                socket = current.inputs.get("A") or current.inputs.get("Color1")
                if socket.is_linked:
                    current = socket.links[0].from_node
                else:
                    current = None
                    print("No linked image node found, ending search!")
                    break

            if current and current.type == "TEX_IMAGE":
                print("Main image deduced!")
                mainImg = current

            '''for link in nodeTree.links:
                if link.to_node == prncBsdf and link.to_socket.identifier == "Base Color":
                    if link.from_node.type == "MIX":
                        rgbMix = link.from_node
                        mainImg = rgbMix.inputs["A"].links[0].from_node  #Input 6 is Color2
                        print("Main image deduced from mix node!")
                    else:
                        print("Main image detected!")
                        mainImg = link.from_node'''

            ##### Time to make changes #####

            ## Fix emission ##
            if fix_emission:
                #Create link between image and bsdf
                
                nodeTree.links.new(mainImg.outputs["Color"], prncBsdf.inputs["Emission Color"])

                if preserve_emission_strenght:
                    #rgb values need to be normalized first
                    default_emi = prncBsdf.inputs["Emission Color"].default_value
                    norm_r = default_emi[0] / 255
                    norm_g = default_emi[1] / 255
                    norm_b = default_emi[2] / 255

                    #Now convert to hsv
                    hsv = rgb_to_hsv(norm_r, norm_g, norm_b)
                    value = hsv[2] * 255
                    print("Strength is", value)

                    #Apply to node
                    prncBsdf.inputs["Emission Strength"].default_value = value

            ## Disconnect metalic map ##
            if fix_metallic:
                for link in nodeTree.links:
                    if link.to_node == prncBsdf and link.to_socket.identifier == "Metallic":
                        nodeTree.links.remove(link)
                        break

            ## Fix alpha ##
            if fix_alpha:
                #Create link imgage_alpha -> bsdf
                nodeTree.links.new(mainImg.outputs["Alpha"], prncBsdf.inputs["Alpha"])
            
            ## Use alpha blend ##
            if use_alpha_blend:
                #Change material settings (4.0+ required)
                material.material.surface_render_method = "BLENDED"
                material.material.use_transparency_overlap = True

            ## Backface culling ##
            if use_backface_culling:
                material.material.use_backface_culling = True
                material.material.use_backface_culling_shadow = True

            ## Vertex color ##
            if use_vertex_color:
                #If a object has no vertex colors, skip
                if len(obj.data.color_attributes) < 1:
                    print("Object has no vertex colors, dont even try")
                    continue    #Maybe not use continue here? Can mess with other materials on the same object or with code after this


                #If there is already an attribute node, skip
                if nodeTree.nodes.get("Color Attribute"):
                    print("Attribute node already exists, skipping!")
                    continue

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
                if fix_emission:
                    nodeTree.links.new(mixNode.outputs["Result"], prncBsdf.inputs["Emission Color"])



print('Finished!')