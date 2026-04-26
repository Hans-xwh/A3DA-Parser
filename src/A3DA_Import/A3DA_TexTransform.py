# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import A3daChannel, A3daKeyframe, ImportConfig, ensureAction, setA3daChannel
import bpy

### Classes ###

class TexTranform:
    def __init__(self, Id=0, Name=""):
        self.id:int = Id
        self.name:str = Name

        self.use_repeatU:bool = False
        self.use_repeatV:bool = False
        self.use_translateU:bool = False
        self.use_translateV:bool = False
        self.use_rotate:bool = False

        self.repeatU:A3daChannel = A3daChannel()
        self.repeatV:A3daChannel = A3daChannel()
        self.translateU:A3daChannel = A3daChannel()
        self.translateV:A3daChannel = A3daChannel()
        self.rotate:A3daChannel = A3daChannel()

    def getTransform(self, transform:str) -> A3daChannel:
        match transform:
            case 'repeatU': return self.repeatU
            case 'repeatV': return self.repeatV
            case 'translateFrameU': return self.translateU
            case 'offsetU': return self.translateU          #MGF
            case 'translateFrameV': return self.translateV
            case 'offsetV': return self.translateV          #MGF
            case 'rotateFrame': return self.rotate
        
    def pushKey(self, transform:str, keyIndex:int|str, keyframe:A3daKeyframe):
        if isinstance(keyIndex, str):
            keyIndex = int(keyIndex)

        channel = self.getTransform(transform)
        channel.keys[keyIndex] = keyframe

    def setParam(self, transform:str, ep_post:int=None, ep_pre:int=None, interpolation:int=None):
        channel = self.getTransform(transform)

        if ep_post:
            channel.ep_post = int(ep_post)
        if ep_pre:
            channel.ep_pre = int(ep_pre)
        if interpolation:
            channel.interpolation = int(interpolation)

class TexPattern:
    def __init__(self, Id=0):
        self.id:int = Id
        self.name:str = ""
        self.tex_name:str = ""
        self.channel = A3daChannel() 

### Functions ###
def setupNodes(material:bpy.types.Material, imgNode:bpy.types.Node|None, imgName:str, useRot:bool, yOff:int=0):
    posX = posY = 0

    links = material.node_tree.links
    nodes = material.node_tree.nodes

    #Order of nodes: UV -> Rotate -> Mapping

    #Create required nodes
    #Frame
    frame = nodes.new('NodeFrame')
    frame.location = (posX, posY)
    frame.name = "A3DA_Tex_Transform_Nodes"
    frame.label = f'({yOff}) {imgName}'   #(tex_id) tex_name

    #UV Map
    posX += 160
    new_uvmap = nodes.new('ShaderNodeUVMap')
    new_uvmap.parent = frame
    new_uvmap.location = (posX, posY)
    
    #Rotation
    if useRot:
        posX += 150
        new_rotate = nodes.new('ShaderNodeVectorRotate')
        new_rotate.parent = frame
        new_rotate.location = (posX, posY)
        links.new(new_uvmap.outputs['UV'], new_rotate.inputs['Vector'])

        new_rotate.inputs['Center'].default_value = (0.5, 0.5, 0)

    #Mapping (Scale & Translate)
    posX += 160
    new_mapping = nodes.new('ShaderNodeMapping')
    new_mapping.parent = frame
    new_mapping.location = (posX, posY)

    if useRot:
        links.new(new_rotate.outputs['Vector'], new_mapping.inputs['Vector'])
    else:
        links.new(new_uvmap.outputs['UV'], new_mapping.inputs['Vector'])

    #Position frame & final link
    if imgNode:
        links.new(new_mapping.outputs['Vector'], imgNode.inputs['Vector'])  
        offX, offY = imgNode.location_absolute
    else:
        offX = -480
        offY = 332 + 417 * yOff

    frame.location = (offX - posX - 200, offY - posY )

    return new_mapping, new_rotate if useRot else None


#def findImageNode(materials, imgName:str) -> bpy.types.Node|None:
#    pass


### Animate textures ###
def animateTex(texlist:dict[int, TexTranform], uid_name:str, config:ImportConfig=None):
    if not uid_name or uid_name == "NULL":
        print(f'[animateTex] Object "{uid_name}" is an empty controller!')
        return
    
    obj = bpy.context.scene.objects.get(uid_name)
    if not obj:
        print(f'[animateTex] Object "{uid_name}" does not exist!')
        return

    #Get mesh to operate on
    if obj.type != 'MESH':
        meshes = [child for child in obj.children_recursive if child.type == 'MESH']    #Only operate on first mesh
        if len(meshes) == 0:
            print(f'[animateTex] Object "{uid_name}" has no meshes!')
            return
        
        obj = meshes[0]
    else:
        meshes = [obj]  #I left this in case i want to iterate trough all meshes but idk it its needed
    
    #get materials of this mesh
    materials = [slot.material for slot in obj.material_slots if slot.material] #Man i love python for this things
    if len(materials) == 0:
        print(f'[animateTex] Mesh "{obj.name}" has no materials!')
        return
    
    #Build map. Saves in which material a texture is found.
    #[imgName, (material, imgNode)]
    images:dict[str, (bpy.types.Material, bpy.types.Node)] = {}
    for mat in materials:   
        if not mat.node_tree: continue
        
        for node in mat.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeTexImage' and node.image:
                name = node.image.name.split('.')[0]
                images[name] = (mat, node)  #This usually results in a single entry on the dict but whatever, does the job for multy mat objects
                #Tho this can potentially lead to duplicated image names, dict will overwrite...

    #Define material & nodes and write to them.
    for tex in texlist.values():
        if tex.name in images:
            material, imgNode = images[tex.name]
            #print(f'[animateTex] Texture {tex.name} found!')
        else:
            print(f'[animateTex] Texture "{tex.name}" on mesh "{obj.name}" not found, using first material!')
            material = materials[0]
            imgNode = None

        mapNode, rotNode = setupNodes(material, imgNode, tex.name,
                                useRot= len(tex.rotate.keys) > 0,
                                yOff= tex.id)
        
        ##Make all loop if config.force_loops:
        if config and config.force_loops:
            #tex.repeatU.ep_post = 2
            #tex.repeatV.ep_post = 2
            tex.translateU.ep_post = 2
            tex.translateV.ep_post = 2
            tex.rotate.ep_post = 2
        

        ### Time to animate finally ###
        action = ensureAction(material.node_tree)

        #scale U/X
        if len(tex.repeatU.keys) > 0:
            fcurve = action.fcurve_ensure_for_datablock(
                material.node_tree, 
                data_path= f'nodes["{mapNode.name}"].inputs[3].default_value', 
                index= 0
                )
            setA3daChannel(fcurve, tex.repeatU)  #FrameOffset missing
            tex.translateU.scaleKeys(-tex.repeatU.keys[0].value)   #Uhh this is potentially wrong, since scale can have more than 1 key.
        else:
            tex.translateU.scaleKeys(-1)

        #scale V/Y
        if len(tex.repeatV.keys) > 0:
            fcurve = action.fcurve_ensure_for_datablock(
                material.node_tree, 
                data_path= f'nodes["{mapNode.name}"].inputs[3].default_value', 
                index= 1
                )
            setA3daChannel(fcurve, tex.repeatV)  #FrameOffset missing
            tex.translateV.scaleKeys(tex.repeatV.keys[0].value)
        #Dont scale by -1 on V

        #location X/U
        if len(tex.translateU.keys) > 0:
            fcurve = action.fcurve_ensure_for_datablock(
                material.node_tree, 
                data_path= f'nodes["{mapNode.name}"].inputs[1].default_value', #location X
                index= 0
                )
            setA3daChannel(fcurve, tex.translateU)  #FrameOffset missing

        #location Y/V
        if len(tex.translateV.keys) > 0:
            fcurve = action.fcurve_ensure_for_datablock(
                material.node_tree, 
                data_path= f'nodes["{mapNode.name}"].inputs[1].default_value', #location y
                index= 1
                )
            setA3daChannel(fcurve, tex.translateV)  #FrameOffset missing

        #rotation
        if len(tex.rotate.keys) > 0:
            tex.rotate.scaleKeys(-1)
            fcurve = action.fcurve_ensure_for_datablock(
                material.node_tree, 
                data_path= f'nodes["{rotNode.name}"].inputs[3].default_value', #location X
            )
            setA3daChannel(fcurve, tex.rotate)  #FrameOffset missing

        #Set repeat param (Diva can choose to repeat only U or V, Blender will repeat on both always)
        #if imgNode and (len(tex.repeatU.keys) > 0 or len(tex.repeatV.keys) > 0):
        #    imgNode.extension = 'REPEAT'
        #elif imgNode:
        #    imgNode.extension = 'EXTEND'  #Or CLIP


def animateTexPat(texlist:dict[int, TexPattern], ctrl:bpy.types.Object, config:ImportConfig=None):
    #if len(ctrl.children) == 0 or 'Has_Mesh' not in ctrl.children[0]:
    if len(ctrl.children) == 0 or ctrl.children[0].auth3d.auth3d_type != 'MESH_C':
        print(f'[animateTexPat] Controller "{ctrl.name}" has no mesh child!')
        return
    mesh_ctrl = ctrl.children[0]

    meshes = [mesh for mesh in mesh_ctrl.children_recursive if mesh.type == 'MESH']
    if len(meshes) == 0:
        print(f'[animateTexPat] Controller "{mesh_ctrl.name}" has no real meshes')
        return
    
    #get materials of this mesh
    materials = []
    processed = []  #Processed materials: {origin_id, material}
    for mesh in meshes:
        for slot in mesh.material_slots:
            if slot.material and slot.material not in materials:
                materials.append(slot.material)

    images = []
    for mat in materials:
        if not mat.node_tree: continue
        
        for node in mat.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeTexImage' and node.image:
                name = node.image.name.split('.')[0]
                images.append((name, mat, node))

    
    #Main animation loop
    mat:bpy.types.Material
    for id, tex in texlist.items():
        for img_name, mat, img_node in images:
            if img_name == tex.name:
                break
        
        node = mat.node_tree.nodes.new('ShaderNodeValue')
        node.label = f'({tex.name}) {tex.tex_name}'
        node.location = (
            img_node.location[0] + 200 * (id + 1),
            img_node.location[1]
        )

        action = ensureAction(mat.node_tree)
        fcurve = action.fcurve_ensure_for_datablock(
            datablock= mat.node_tree,
            data_path= f'nodes["{node.name}"].outputs[0].default_value',
            index= 0
        )
        setA3daChannel(fcurve, tex.channel)

