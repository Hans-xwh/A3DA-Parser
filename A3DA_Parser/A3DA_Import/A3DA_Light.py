# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import A3daBaseObj, A3daTransform, A3daChannel, A3daKeyframe, ImportConfig, setA3daChannel, ensureAction

import bpy


### Classes ###
class A3daRGB:
    def __init__(self):
        self.a = A3daChannel()
        self.r = A3daChannel()
        self.g = A3daChannel()
        self.b = A3daChannel()

    def push(self, color:str, keyframe:A3daKeyframe, index:int):
        match color:
            case 'a':
                self.a.keys[index] = keyframe
            case 'r':
                self.r.keys[index] = keyframe
            case 'g':
                self.g.keys[index] = keyframe
            case 'b':
                self.b.keys[index] = keyframe
            case _:
                print('[A3daRGB] Unable to match color')
                #input()

    def countKeys(self) -> int:
        return len(self.a.keys) + len(self.r.keys) + len(self.g.keys) + len(self.b.keys)

    def __getitem__(self, key:int|str):
        if isinstance(key, int):
            key = ['a', 'r', 'g', 'b'][key]

        return getattr(self, key)

    def __repr__(self):
        return f"A3daRGB(A:{len(self.a.keys)}, R:{len(self.r.keys)}, G:{len(self.g.keys)}, B:{len(self.b.keys)})"

class A3daLight(A3daBaseObj):
    def __init__(self, id=0):
        super().__init__(id)

        #Name is used as shader (?) assignment 99% sure

        # !!! ID here is used differently !!!
        #Id:Name; 0:Char, 1:Stage, 2:Sun, 3:Reflect, 4:Shadow, 5:CharColor, 6:CharF, 7:Projection

        self.spot_direction = A3daBaseObj()     #No idea what is this used for

        self.diffuse = A3daRGB()
        self.specular = A3daRGB()
        self.ambient = A3daRGB()
        self.incandescence = A3daRGB()

        self.type:str = ""  #SpotLight, 

    #Polymorph methos to add new transform
    def getTransform(self, channel:str, axis:str = None) -> A3daRGB|A3daTransform|A3daChannel:
        transform: A3daRGB = None
        match channel:
            case "Diffuse":     transform = self.diffuse
            case "Specular":    transform = self.specular
            case "Ambient":     transform = self.ambient
            case "Incandescence": transform = self.incandescence
            case _: return super().getTransform(channel, axis)

        if transform and axis:
            match axis:
                case "a": return transform.a
                case "r": return transform.r
                case "g": return transform.g
                case "b": return transform.b
                case _: return transform
    

### Functions ###
def parseA3daLight(light:A3daLight, params:list[str], data:str, frameOffset=0, config:ImportConfig=None):
    if params[2] == 'position':
        light.parseTransform(params[3:], data, frameOffset=frameOffset)

    elif params[2] == 'spot_direction':
        light.spot_direction.parseTransform(params[3:], data, frameOffset)

    else:
        print(params)
        if len(params) > 3:
            channel = light.getTransform(params[2], params[3])
        elif len(params) > 2:
            channel = light.getTransform(params[2])

        if channel: channel.parseA3daLine(params[4:], data, frameOffset)

        #TODO actually make this make sense

def animA3daLight(light:A3daLight, ctrl:bpy.types.Object, config:ImportConfig=None):
    def get_bl_lamp(name:str, lamp_type:str="POINT") -> bpy.types.Object:
        lamp = bpy.context.scene.objects.get(name)
        if not lamp:
            lamp_data = bpy.data.lights.new(name, type=lamp_type)
            lamp = bpy.data.objects.new(name, lamp_data)
            bpy.context.scene.collection.objects.link(lamp)
        return lamp

    def animate_lamp(lamp:bpy.types.Object, color:A3daRGB, influence_type:str = "Diffuse"):
        if not lamp.type == 'LIGHT': return

        if influence_type != "Ambient":
            lamp.data.diffuse_factor = 0
            lamp.data.specular_factor = 0

        match influence_type:
            case "Diffuse":
                lamp.data.diffuse_factor = 1
            case "Specular":
                lamp.data.specular_factor = 1

        #Animate
        action = ensureAction(lamp)
        for axis in range(3):
            fcurve = action.fcurve_ensure_for_datablock(
                datablock = lamp,
                data_path = f'data.color',
                index = axis
            )
            setA3daChannel(fcurve, color[axis+1])
        

    ## Animate root light controller ##
    light.animate(ctrl, config=config)

    ## Animate spot direction ##
    #light.spot_direction.animate()

    ## Animate lamps ##
    if light.diffuse.countKeys() > 0:
        lamp = get_bl_lamp(ctrl.name + "_Diffuse")
        if not lamp.parent: lamp.parent = ctrl

        animate_lamp(lamp, light.diffuse, 'Diffuse')
        

    if light.specular.countKeys() > 0:
        lamp = get_bl_lamp(ctrl.name + "_Specular")
        if not lamp.parent: lamp.parent = ctrl

        animate_lamp(lamp, light.specular, 'Specular')

    if light.ambient.countKeys() > 0:
        pass

    if light.incandescence.countKeys() > 0:
        pass