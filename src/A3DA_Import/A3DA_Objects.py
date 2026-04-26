# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import A3daTransform, A3daChannel, A3daKeyframe, ImportConfig, setA3daChannel, switchAxis, parseA3daKey
from .A3DA_TexTransform import TexTranform, TexPattern
import bpy

### Classes ###

class A3daObject:
    def __init__(self, Id=0, Name=""):
        self.id:int = Id
        self.name:str = Name
        self.uid_name:str = ""
        self.parent:str|None = None

        #self.mesh:str = ""
        self.bl_name:str= ""

        self.translation:A3daTransform = A3daTransform()
        self.rotation:A3daTransform = A3daTransform()
        self.scale:A3daTransform = A3daTransform()
        self.visibility:A3daChannel = A3daChannel()

        self.morph:A3daChannel = A3daChannel()
        self.morph_name:str = ""

        self.tex_transform:dict[int, TexTranform] = {}
        self.tex_pat:dict[int, TexPattern] = {}

    def pushKey(self, transform:str, axis:str|int, keyframe:A3daKeyframe, keyIndex:int):
        keyIndex = int(keyIndex)
        match transform:
            case 'trans':
                self.translation.push(axis, keyframe, keyIndex)
            case 'rot':
                self.rotation.push(axis, keyframe, keyIndex)
            case 'scale':
                self.scale.push(axis, keyframe, keyIndex)
            case 'visibility':
                self.visibility.keys[keyIndex] = keyframe
            case _:
                print(f'obj:{self.id} | failed to match transform: {transform}'); 

    def getTransform(self, channel:str, axis:str=None) -> A3daChannel|A3daTransform:
        transform: A3daTransform = None
        match channel:
            case "trans": transform = self.translation
            case "location": transform = self.translation
            case "rot": transform = self.rotation
            case "rotation_euler": transform = self.rotation
            case "scale": transform = self.scale
            case "visibility": return self.visibility
            case _: print(f'[getTransform] Failed to determine transform {channel}');
        
        if axis == None: return transform

        match axis:
            case "x": return transform.x
            case "y": return transform.y
            case "z": return transform.z
            case _: return transform

    def setParam(self, transform:str, axis:str=None, ep_post:int=None, ep_pre:int=None, interpolation:int=None):    #type: ignore
        #if isinstance(axis, str):
        #    axis = switchAxis(axis)
        tr = self.getTransform(transform, axis)

        if ep_post:
            tr.ep_post = int(ep_post)
        if ep_pre:
            tr.ep_pre = int(ep_pre)
        if interpolation:
            tr.interpolation = int(interpolation)

    def printAll(self):
        print(f'Translation: {self.translation.x}\n{self.translation.y}\n{self.translation.z}')
        print(f'Rotation: {self.rotation.x}\n{self.rotation.y}\n{self.rotation.z}')
        print(f'Scale: {self.scale.x}\n{self.scale.y}\n{self.scale.z}')

    def __repr__(self):
        return f'Id:{self.id} | Blender_name:{self.bl_name} | uid_name:{self.uid_name} | name:{self.name} | parent:{self.parent}\n'

class A3daCV:  #curve.x.cv stuff, used for morphs
    def __init__(self, Id=0):
        self.id:int = Id
        self.name:str = ""

        self.channel = A3daChannel()


### Functions ###
def cleanEmptiesNames() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type == "EMPTY":
            upName = obj.name.upper()

            checkObj = bpy.context.scene.objects.get(upName)    #This prevents overlaping mesh & controller names on older pvs
            if checkObj and checkObj != obj:    #And this makes sure to not rename-protect if the object is already in uppercase
                checkObj.name += '_MESH'

            obj.name = upName


def createEmpty(name:str, disp_type:str=None, force=False) -> bpy.types.Object:
    empty = bpy.context.scene.objects.get(name)

    if not empty or force:   #Creates an empty object with the provided name
        empty = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(empty)
        #print(f'[createObject] Empty "{name}" succesfully created.')

        if disp_type:
            empty.empty_display_type = disp_type
    else:
        #print(f'[createObject] "{name}" already exists!')
        pass

    return empty


def assignParent(parent, child, clear_transform=False):
    if isinstance(parent, str):
        #print(f'[assignParent] Looking for parent "{parent}"')
        parent = bpy.context.scene.objects.get(parent)
    if isinstance(child, str):
        #print(f'[assignParent] Looking for child "{child}"')
        child = bpy.context.scene.objects.get(child)

    if clear_transform:
        child.rotation_euler = (0,0,0)
        child.location = (0,0,0)
        child.scale = (1,1,1)

    child.parent = parent
    #print(f'[assignParent] Assigned parent "{parent.name}" to child "{child.name}"')


def createInstance(original:bpy.types.Object, name:str, independent_data=False): #-> bpy.types.Object:
    new_name = f'{original.name}_INSTANCE'
    newCtrl = createEmpty(new_name, force=True)
    #newCtrl["Has_Mesh"] = True
    newCtrl.auth3d.auth3d_type = 'MESH_C'
    print(f'[createInstance] Created instance "{new_name}"')

    #Instantiate meshes
    for child in original.children:
        if child.type != 'MESH': continue

        #Create instance
        if independent_data:
            data = child.data.copy() #This will create an independent copu
        else:
            data = child.data        #This will simply point to the same datablock.
        instance = bpy.data.objects.new(name=child.name + f"_INST", object_data=data)

        #Copy materials if needed
        if independent_data:
            for i, slot in enumerate(child.material_slots):
                if slot.material:
                    instance.data.materials[i] = slot.material.copy()


        bpy.context.scene.collection.objects.link(instance)
        instance.parent = newCtrl

    return newCtrl


def createObjDriver(source:bpy.types.Object, source_prop:str, target:bpy.types.Object, target_prop:str, target_index:int=None, source_index:int=None, var_name:str='var', expression:str=None) -> bpy.types.Driver:
    if target_index:
        fcurve = target.driver_add(target_prop, target_index)
    else:
        fcurve = target.driver_add(target_prop)

    driver = fcurve.driver

    if expression:
        driver.type = 'SCRIPTED'
        driver.expression = expression
    else:
        driver.type = 'AVERAGE'
    
    #Add variable
    #var = driver.variables.new()
    #var.name = var_name

    var = next((v for v in driver.variables if v.name == var_name), None)
    if not var:
        var = driver.variables.new()
        var.name = var_name
    var.targets[0].id = source
    var.targets[0].data_path = source_prop
    if source_index:
        var.targets[0].array_index = source_index

    return driver


def additionObjDriver(source:bpy.types.Object, source_prop:str, target:bpy.types.Object, target_prop:str, target_index:int=None, source_index:int=None, var_name:str='var', expression:str=None) -> bpy.types.Driver:
    #Find driver
    fcurve = None
    if target.animation_data:
        for fc in target.animation_data.drivers:
            if fc.data_path == target_prop:
                if not target_index or fc.array_index == target_index:
                    fcurve = fc
                    #print("[createObjDriver] Found it!")
                    break
    #Case new driver
    if fcurve is None:
        if target_index is not None:
            fcurve = target.driver_add(target_prop, target_index)
        else:
            fcurve = target.driver_add(target_prop)

    driver = fcurve.driver
    #print(f"AFTER| vars: {len(driver.variables)}, expr: '{driver.expression}', type: {driver.type}")

    #Determine if new & var count
    var_count = len(driver.variables)
    var_name = f"{var_name}_{var_count}"

    #Add variable
    var = driver.variables.new()
    var.name = var_name
    var.targets[0].id = source
    var.targets[0].data_path = source_prop
    if source_index is not None:
        var.targets[0].array_index = source_index

    #Build expression
    if expression:
        expression = f"({var_name} {expression})"
        if var_count == 0:
            driver.type = 'SCRIPTED'
            driver.expression = ''     #Clean cuz for some reason this is needed
            driver.expression = expression
        else:
            driver.expression = f'{driver.expression} + {expression}'
    else:
        driver.type = 'AVERAGE'

    #print(f"BEFORE| vars: {len(driver.variables)}, expr: '{driver.expression}', type: {driver.type}")
    return driver


def assignMesh(obj:A3daObject, ctrl=None, make_independent=False, forceInstance=False):
    if not ctrl:
        ctrl = bpy.context.scene.objects.get(obj.bl_name)

    child:bpy.types.Object = bpy.context.scene.objects.get(obj.uid_name)
    if not child:
        print(f'[assignMesh] Could not find mesh "{obj.uid_name}" for controller "{obj.bl_name}"')
        return
    
    #In case a mesh has the name of the object. Case observed in Two Sided Lovers F2nd
    org_child = child
    while child.type != 'EMPTY' and child.parent:
        child = child.parent
    if child.type != 'EMPTY':
        child = org_child   #In case no empty parent is found, restore original object


    #Check if mesh is already parented. If it is, create an instance of it
    #if 'Has_Mesh' not in child and not forceInstance:
    if not child.auth3d.auth3d_type == 'MESH_C' and not forceInstance:
        assignParent(ctrl, child, clear_transform=True)
        #print(f'[assignMesh] Assigned mesh "{child.name} -> {ctrl.name}"')
        #child['Has_Mesh'] = True
        child.auth3d.auth3d_type = 'MESH_C'
    else:
        instance = createInstance(child, obj.name, make_independent)  #Not sure about using obj.name here
        assignParent(ctrl, instance, clear_transform=True)
        #instance['Has_Mesh'] = 0


def findChild(parent:str): #-> bpy.types.Object:    #Return the first child of an object. If no childre, returns the parent
    if isinstance(parent, str):
        parent:bpy.types.Object = bpy.context.scene.objects.get(parent)
    
    try:
        child = parent.children[0]
        #print(f'[findChild] Child of "{parent.name}" is "{child.name}"')
        return child
    except IndexError:
        #print('[findChild] No children found!')
        return parent
    
    
def findChildrenMesh(obj:bpy.types.Object): #-> [bpy.types.Object]:      #Returns all children meshes of an object
    children = obj.children_recursive
    return [child for child in children if child.type == 'MESH']


def animateObject(obj:A3daObject=None, config:ImportConfig=None):
    #obj = objects[objId]

    #Make sure ctrl exits
    ctrl:bpy.types.Object = bpy.context.scene.objects.get(obj.bl_name)
    if not ctrl:
        ctrl = createEmpty(obj.bl_name)

    ### Write animation ###
    ## Ensure object anim data & action ##
    if not ctrl.animation_data:
        ctrl.animation_data_create()

    if not ctrl.animation_data.action:
        action = bpy.data.actions.new(name=ctrl.name + "_Action")
        ctrl.animation_data.action = action
    else:
        action = ctrl.animation_data.action

    ## Write transforms ##
    for transform in ('trans', 'rot', 'scale'):
        for axis in ('x', 'y', 'z'):
            #print(f'\n[animateObject] Animating obj:{obj.id} | {transform} | {axis}')
            channel = obj.getTransform(transform, axis)

            #Ensure fcurve exists
            fcurve = action.fcurve_ensure_for_datablock(    #THANKS FOR THIS FUNCTION
                datablock= ctrl,
                data_path= f'{switchAxis(transform)}',
                index= switchAxis(axis)
            )

            #Write the channel keys to Blender
            if config and config.force_loops:
                channel.ep_post = 2 #Loopy loop
            setA3daChannel(fcurve, channel)

    ## Write visibility ##
    channel = obj.getTransform('visibility')
    if len(channel.keys) > 0:   #Only write visibility if there are keys and a mesh is assigned
        #print(f'[animateObject] Animating obj:{obj.id} | visibility')

        if config.ensure_compatibility: #Im keeping the option to use user defined props for compatibility
            visibility_prop = '["A3DA_VISIBILITY"]'
            ctrl["A3DA_VISIBILITY"] = 1  #Ensure the custom property exists
        else:
            visibility_prop = "auth3d.visibility"

        fcurve = action.fcurve_ensure_for_datablock(
            datablock= ctrl,
            data_path= visibility_prop,
        )
        setA3daChannel(fcurve, channel)

        #Create drivers for all child meshes, if it has any meshes
        #if findChild(ctrl).get('Has_Mesh') and not config.inherit_visibility:   #FIXME Make this not crea useless props if not compatibility mode
        if findChild(ctrl).auth3d.auth3d_type == 'MESH_C' and not config.inherit_visibility:   #FIXME Make this not crea useless props if not compatibility mode
            for mesh in findChildrenMesh(ctrl):
                createObjDriver(
                    source= ctrl,
                    source_prop= visibility_prop,
                    target= mesh,
                    target_prop= 'hide_viewport',
                    expression= '(var <= 0.999)',
                )
                createObjDriver(
                    source= ctrl,
                    source_prop= visibility_prop,
                    target= mesh,
                    target_prop= 'hide_render',
                    expression= '(var <= 0.999)',
                )
        elif config.inherit_visibility:
            for mesh in findChildrenMesh(ctrl):
                additionObjDriver(
                    source= ctrl,
                    source_prop= visibility_prop,
                    target= mesh,
                    target_prop= 'hide_viewport',
                    expression= '<= 0.999',
                )
                additionObjDriver(
                    source= ctrl,
                    source_prop= visibility_prop,
                    target= mesh,
                    target_prop= 'hide_render',
                    expression= '<= 0.999',
                )

    ## Write morphs ##
    channel = obj.morph
    if len(channel.keys) > 0:
        #if findChild(ctrl).get('Has_Mesh'):
        if findChild(ctrl).auth3d.auth3d_type == 'MESH_C':
            for mesh in findChildrenMesh(ctrl):
                if not mesh.data.shape_keys :
                    mesh.shape_key_add(name="Basis")
                shape_keys = mesh.data.shape_keys

                #Create shape key    
                if obj.morph_name not in mesh.data.shape_keys.key_blocks:
                    SK_name = f'{obj.morph_name}_ghost'     #Shape key name
                    if SK_name in mesh.data.shape_keys.key_blocks:
                        continue    #Skip if a ghost shape key already exists, to avoid writing to instances
                else:
                    SK_name = obj.morph_name    #If the shape key IS NOT there, add _ghost
                shape_key = mesh.shape_key_add(name=SK_name)
                print(f'[animateObject] Animating morph {SK_name} on mesh: {mesh.name}')

                #Ensure action
                if not shape_keys.animation_data:
                    shape_keys.animation_data_create()

                if not shape_keys.animation_data.action:
                    action = bpy.data.actions.new(name=shape_keys.name + "_Action")
                    shape_keys.animation_data.action = action
                else:
                    action = shape_keys.animation_data.action

                #Write anim
                fcurve = action.fcurve_ensure_for_datablock(
                    datablock = mesh.data.shape_keys,
                    data_path= f'key_blocks["{SK_name}"].value',
                )
                setA3daChannel(fcurve, channel)


def parseA3daObject(obj:A3daObject, params:list[str], data:str, frameOffset=0, config:ImportConfig=None):
    #Params: 1=id, 2=transform, 3=axis, 5=KeyIndex, 6=data/type
    #Basic object transforms
    if params[2] in ('trans', 'rot', 'scale'):
        if params[4] == 'key' and params[5] != 'length' and params[6] == 'data':    #key parsing
            keyframe = parseA3daKey(data, frameOffset)
            obj.pushKey(
                transform= params[2],
                axis= params[3],
                keyframe= keyframe,
                keyIndex= int(params[5])
            )

        elif params[4] == 'value':  #Non-key value parsing
            obj.pushKey(params[2], params[3], keyIndex=0,
                keyframe= parseA3daKey(data, frameOffset, not_key=True))
        
        elif params[4] == 'type': #Interpolation mode. type=0 means the transforms is always 0
            obj.setParam(params[2], params[3], interpolation=data)
            if data == '0':
                obj.pushKey(params[2], params[3], keyIndex=0, keyframe=A3daKeyframe(frame=frameOffset))

        elif params[4] == 'ep_type_post': #Extrapolation post mode
            obj.setParam(params[2], params[3], ep_post=data)

        elif params[4] == 'ep_type_pre': #Extraolation pre mode
            obj.setParam(params[2], params[3], ep_pre=data)

    #Object Visibility
    elif params[2] == 'visibility' and config.use_visibility:
        if params[3] == 'type':
            obj.setParam(params[2], interpolation=data)

        elif params[3] == 'key' and params[4] != 'length' and params[5] == 'data':
            obj.pushKey(
                transform= params[2],
                axis= None,
                keyIndex= params[4],
                keyframe= parseA3daKey(data, frameOffset)
            )

        elif params[3] == 'value':
            obj.pushKey(transform=params[2], axis=None, keyIndex=0, 
                keyframe=parseA3daKey(data, frameOffset, not_key=True))
             
    #UV animation
    elif params[2] == 'tex_transform' and config.use_tex_transform:
        if params[3] == 'length':
            return
        
        #Chack tex transform object exists
        texId = int(params[3])
        if texId not in obj.tex_transform:
            obj.tex_transform[texId] = TexTranform(Id=texId)
        tex_t = obj.tex_transform[texId]

        #read data
        if params[4] == 'name':
            tex_t.name = data

        elif params[4] in ('repeatU', 'repeatV', 'translateFrameU', 'translateFrameV', 'rotateFrame', 'offsetV', 'offsetU'):
            if len(params) <= 5:
                return
            
            if params[5] == 'type':
                tex_t.setParam(params[4], interpolation=data)

            elif params[5] == 'ep_type_post':
                tex_t.setParam(params[4], ep_post=data)

            elif params[5] == 'ep_type_pre':
                tex_t.setParam(params[4], ep_pre=data)
            
            elif params[5] == 'value':
                tex_t.pushKey(
                    transform= params[4],
                    keyIndex= 0,
                    keyframe= parseA3daKey(data, frameOffset, not_key=True)
                )

            elif params[5] == 'key' and params[6] != 'length' and params[7] == 'data':
                key = parseA3daKey(data, frameOffset)
                if params[4] in ("offsetU", "offsetV"):     #MGF mode
                    key.scale(-1)

                tex_t.pushKey(
                    transform= params[4],
                    keyIndex= params[6],
                    keyframe= key
                )

    #Object morphs will be handled in main parser func
    #elif params[2] == 'morph'  :
    #    obj.morph_name = data


    #Tex_pat will aslo be handled in main parser func
    #elif params[2] == 'tex_pat':
    #    #Not sure what this is used for, i think for those animated image sequences
    #    pass


def parseA3daCurve(cv:A3daCV, params:list[str], data:str, frameOffset=0):
    if params[2] == 'name':
        cv.name = data

    elif params[3] == 'type':
        cv.channel.interpolation = int(data)

    elif params[3] == 'ep_type_post':
        cv.channel.ep_post = int(data)
    
    elif params[3] == 'ep_type_pre':
        cv.channel.ep_pre = int(data)

    elif params[3] == 'key' and params[4] != 'length' and params[5] == 'data':
        cv.channel.keys[int(params[4])] = parseA3daKey(data, frameOffset)

