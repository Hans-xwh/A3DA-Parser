# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
import time
from array import array


#####################
###### Classes ######
#####################

class ImportConfig:
    def __init__(self):
        #General
        self.frame_offset:int = 0
        self.use_file_begin:bool
        self.use_pv_branch:bool
        self.ensure_compatibility:bool

        #Objects
        self.use_objects:bool
        self.use_visibility:bool
        self.inherit_visibility:bool
        self.use_morphs:bool
        self.use_tex_transform:bool
        self.use_tex_pat:bool
        self.independent_instances:bool
        self.force_loops:bool

        #HRC
        self.use_hrc:bool
        self.use_hrc_ghost:bool

        #Camera
        self.use_dof:bool

        #Sequencial
        self.game = None
        self.force_load_first:bool = False
        self.auto_gnd:bool = True
        self.endian = 'AUTO'    #Endianess of dsc files (AUTO, BIG, LITTLE)


class BezierCurve:  #A bezier curve formed by its 4 points.
    def __init__(self, x1=0, y1=0, b2x=0, b2y=0, b3x=0, b3y=0, x2=0, y2=0):
            self.b1x:float = x1
            self.b1y:float = y1
            self.b2x:float = b2x
            self.b2y:float = b2y
            self.b3x:float = b3x
            self.b3y:float = b3y
            self.b4x:float = x2
            self.b4y:float = y2

    def __iter__(self):
        return iter((self.b1x, self.b1y, self.b2x, self.b2y, self.b3x, self.b3y, self.b4x, self.b4y))

    def __repr__(self):
        return (f"BezierCurve (\nB1: x={self.b1x}, y={self.b1y} \nB2: x={self.b2x}, y={self.b2y} \nB3: x={self.b3x}, y={self.b3y} \n B4: x={self.b4x}, y={self.b4y})")
    
class A3daKeyframe: #Simple a3da frame, with two slopes
    def __init__(self, frame:float=0, value:float=0, s1:float=0, s2:float=0):
        self.frame:float = frame
        self.value:float = value
        self.Slope1:float = float(s1)
        self.Slope2:float = float(s2)

    def scale(self, s:int):
        self.value *= s
        self.Slope1 *= s
        self.Slope2 *= s

    def as_txt(self, kv_type:int=1) -> str:    #Returns current key data as a string   (currently onli as linear) (Needs to take a parameter to define amount of numbers)
        #return f'{round(self.frame)},{self.value:.9g}'#,{self.Slope1:.9g},{self.Slope2:.9g})'
        txt:str = ""
        if kv_type >= 0:
            txt += f'{round(self.frame)}'
        if kv_type >= 1:
            txt += f',{self.value:.9g}'
        if kv_type >= 2:
            txt += f',{self.Slope1:.9g}'
        if kv_type >= 3:
            txt += f',{self.Slope2:.9g}'

        return txt


    def __iter__(self):
        return iter((self.frame, self.value, self.Slope1, self.Slope2))

    def __repr__(self):
        return f"(frame={self.frame}, value={self.value}, s1={self.Slope1}, s2={self.Slope2})"
    
class A3daChannel:
    def __init__(self):
        self.keys:dict[int, A3daKeyframe] = {}
        self.interpolation:int = 0  #0:NoKeys, 1:Single, 2:Linear, 3:SingleSlope, 4:DualSlope
        self.ep_post:int = 0    #0:Nothing, 1:Linear, 2:Cycle, 3:CycleOffset
        self.ep_pre:int = 0

    def scaleKeys(self, scale:int, index:int|None = None):     #scale values, keeps timing
        if not index:
            for key in self.keys.values():
                key.value *= scale
                key.Slope1 *= scale
                key.Slope2 *= scale
        else:
            key = self.keys[index]
            key.value *= scale
            key.Slope1 *= scale
            key.Slope2 *= scale

    def fromFCurve(self, fcurve:bpy.types.FCurve, safe=False, correct_rot=False):
        if not fcurve:
            if safe:
                self.interpolation = 1
                self.keys[0] = A3daKeyframe(0, 1, 0, 0)
            self.interpolation = 0
            return
        
        #Convert & save keyframe loop
        count = 0
        kp:bpy.types.Keyframe
        last_kp:bpy.types.Keyframe | None = None
        for kp in fcurve.keyframe_points:
            self.keys[count] = A3daKeyframe()
            k2x, k2y = kp.co.x, kp.co.y
            if correct_rot: 
                k2y = round(k2y - 1.570796)  #90d in radians

            if last_kp:
                k1x, k1y = last_kp.co.x, last_kp.co.y
                if correct_rot: 
                    k1y = round(k1y - 1.570796, 6)
                    
                x1, y1, s1, x2, y2, s2 = DapperDots(    #S1 Slope leaving last, S2 slope entering current
                    k1x, k1y,   #k1 = last keyframe point
                    last_kp.handle_right.x, last_kp.handle_right.y,
                    kp.handle_left.x, kp.handle_left.y,
                    k2x, k2y    #k2 = current keyframe point
                )
            else:
                x2, y2 = k2x, k2y
                s2 = s1 = 0

            #Save current keyframe
            self.keys[count].frame = x2
            self.keys[count].value = y2 
            self.keys[count].Slope1 = s2    #IDK if this is correct

            #Upadte last key
            if last_kp:
                self.keys[count-1].Slope2 = s1


            last_kp = kp
            count += 1

            #Decide interpolation type
            if kp.interpolation == 'LINEAR' and self.interpolation < 2:
                self.interpolation = 2
            elif kp.interpolation == 'BEZIER' and self.interpolation < 3:
                self.interpolation = 3

        #Cleanup interpolation type if only one key
        if count == 1:
            self.interpolation = 1

        #Set ep types
        for mod in fcurve.modifiers:
            if mod.type == 'CYCLES':
                if mod.mode_before == 'REPEAT':
                    self.ep_pre = 2
                elif mod.mode_before == 'REPEAT_OFFSET':
                    self.ep_pre = 3
                if mod.mode_after == 'REPEAT':
                    self.ep_post = 2
                elif mod.mode_after == 'REPEAT_OFFSET':
                    self.ep_post = 3


    def __repr__(self):
        return f'A3daChannel (keys={len(self.keys)}, interpolation={self.interpolation}, ep_post={self.ep_post}, ep_pre={self.ep_pre})'

class A3daTransform:  #Holds three axes (XYZ) to form a transformation like in Blender.
    def __init__(self):
        #self.transform:str = trans #Location, Rotation_euler, Scale
        self.x:A3daChannel = A3daChannel() #All keys indexed by their numeric id
        self.y:A3daChannel = A3daChannel()
        self.z:A3daChannel = A3daChannel()        

    def push(self, axis:int|str, keyframe:A3daKeyframe, index:int):
        if isinstance(axis, str):
            axis = switchAxis(axis)

        match axis:
            case 0:
                self.x.keys[index] = keyframe
            case 1:
                self.y.keys[index] = keyframe
            case 2:
                self.z.keys[index] = keyframe
            case _:
                print('Failed to identify an axis!')
                #input()

    def clear(self, axis:int|str):
        if isinstance(axis, str):
            axis = switchAxis(axis)
        match axis:
            case 0:
                self.x.keys.clear()
            case 1:
                self.y.keys.clear()
            case 2:
                self.z.keys.clear()

    def __repr__(self):
        return f'Keys: (X:{len(self.x.keys)}, Y:{len(self.y.keys)}, Z:{len(self.z.keys)})'

    #Returns a tuple of XYZ values on provided index
    def as_tuple(self, index=0) -> tuple:
        return (
            self.x.keys[index].value,
            self.y.keys[index].value,
            self.z.keys[index].value)
    

#######################
###### Functions ######
#######################

def SloppySlope(x1, y1, s1, x2, y2, s2) -> BezierCurve: #Converts diva Hermite to Bezier points. Requires floats as input
    deltaX = (x2 - x1)

    b2x = x1 + (deltaX / 3)
    b2y = y1 + (s1 * deltaX / 3)

    b3x = x2 - (deltaX / 3)
    b3y = y2 - (s2 * deltaX / 3)
    
    return BezierCurve(x1, y1, b2x, b2y, b3x, b3y, x2, y2)

def DapperDots(b1x, b1y, b2x, b2y, b3x, b3y, b4x, b4y) -> tuple: #Converts a Bezier curve into Diva's Cubic Hermite spline
    #b1: L_point
    #b2: L_ctrlPoint
    #b3: R_ctrlPoint
    #b4: R_point

    deltaX = b4x - b1x

    s1 = (b2y - b1y) * 3 / deltaX
    s2 = (b4y - b3y) * 3 / deltaX

    return b1x, b1y, s1, b4x, b4y, s2


def kpToA3daKey(kp_last:bpy.types.Keyframe, kp_current:bpy.types.Keyframe) -> A3daKeyframe:

    pass

def switchAxis(value) -> str | int:  #Takes an axis as string and return a number or transform for Blender.
    match value:
        #Axis
        case "x":
            return 0
        case "y":
            return 1
        case "z":
            return 2
        #Transform
        case "trans":
            return "location"
        case "rot":
            return "rotation_euler"
        
    #In case nothing is matched
    return value

def parseA3daKey(in_data:str, frameOffset:int=0, not_key:bool=False) -> A3daKeyframe:
    in_data = in_data.strip("()")
    data:list = [item for item in in_data.split(",")]

    #type=1 FOR NON-KEY values is different, assume value 1 at frame 0
    if len(data) == 1 and not_key:
        data.append(float(data[0]))    #Copies previously frame to value
        data[0] = 0             #Makes frame 0

    while len(data) < 3:
        data.append(0)
    if len(data) < 4:
        data.append(data[-1])

    return A3daKeyframe(
        frame=float(data[0]) + frameOffset,
        value=float(data[1]),
        s1=float(data[2]),
        s2=float(data[3])
    )

def setFcurveKey(fCurve:bpy.types.FCurve, keyframe:A3daKeyframe=None, interpoType:int=0, animChannel:A3daChannel|None=None, keyIndex:int=0, writeIndex:int=0, frameOffset:int=0): #type: ignore
    #Note: interpoType is in a3da format, so it's an int
    if animChannel:
        if not keyframe:
            keyframe = animChannel.keys[keyIndex] #type: ignore
        if not interpoType:
            interpoType = animChannel.interpolation
        keys = animChannel.keys

    ### Keyframe overwrite protection ###
    #if animChannel and keyIndex < len(keys)-1  and keyframe.frame == keys[keyIndex+1].frame:
    #    keyframe.frame += -0.5
    #UNPORPER OVERWRITE PROTECTION CHANGE THIS LATER
    
    #if animChannel and keyIndex < len(keys)-1 and keyframe.frame == keys[keyIndex+1].frame: #First check if not last key, then check if frames will result in a overwritten key
    #    if keyIndex > 0 and keyframe.value == keys[keyIndex-1].value: #Check if not first key, then check if last and current will result in a continuos curve. If so, write current value to previous frame as constant.
    #        keyframe.frame = keys[keyIndex-1].frame
    #    else:   #if no previous key or values differ, we need to eihter create a frame at 0, or shift current key back by 0.5 frames
    #        if keyIndex == 0:
    #            keyframe.frame = frameOffset
    #        else:
    #            keyframe.frame += -0.5
#
    #    interpoType = 4   #Constant
    #Im not proud of this solution, but it works
              
    #Write the key
    keyPoint = fCurve.keyframe_points[writeIndex]
    keyPoint.co = (keyframe.frame, keyframe.value)

    if interpoType in (0, 1, 2):
        keyPoint.interpolation = 'LINEAR'

    if interpoType == 3: #Bezier
        keyPoint.interpolation = 'BEZIER'
        keyPoint.handle_right_type = "FREE"
        keyPoint.handle_left_type = "FREE"

        if keyIndex < len(keys) -1:     #All keys but last
            bCurveOut = SloppySlope(
                keyframe.frame,
                keyframe.value,
                keyframe.Slope2,
                keys[keyIndex+1].frame,
                keys[keyIndex+1].value,
                keys[keyIndex+1].Slope1
            )          
            keyPoint.handle_right = (bCurveOut.b2x, bCurveOut.b2y)
        #fCurve.update()

        if keyIndex > 0:    #All keys but first
            bCurveIn = SloppySlope(
                keys[keyIndex-1].frame,
                keys[keyIndex-1].value,
                keys[keyIndex-1].Slope2,
                keyframe.frame,
                keyframe.value,
                keyframe.Slope1
            )
            keyPoint.handle_left = (bCurveIn.b3x, bCurveIn.b3y)
        #fCurve.update()

    elif interpoType == 4:
        keyPoint.interpolation = 'CONSTANT'

    #fCurve.update()

def setA3daChannel(fcurve:bpy.types.FCurve, channel:A3daChannel, frameOffset:int=0, clearAfterImport:bool=False):
    writePointer = 0

    #Initialize curve by reserving memory for all keys
    fcurve.auto_smoothing = "NONE"
    fcurve.keyframe_points.add(len(channel.keys))

    #Write all keys
    index = 0
    while index < len(channel.keys):
        interpolation = channel.interpolation
        key = channel.keys[index]

        #Key Overwrite Protection
        if index < len(channel.keys) -1 and key.frame == channel.keys[index + 1].frame: #Check if key will be overwritten by next
            #if writePointer > 0 and key.value == channel.keys[index - 1].value: #Unsafe
            if writePointer > 0 and abs(key.value - fcurve.keyframe_points[writePointer - 1].co[1]) < 0.001: #Check if not first key, then check if previous and current have the same value. This means last one is a hold
                fcurve.keyframe_points[writePointer - 1].interpolation = 'CONSTANT' #Make previous key constant
                
                index += 1
                continue    #Increas only index. Skip writing current key

            elif writePointer == 0:
                key.frame = frameOffset #If this is the first key, move it to the start
                interpolation = 4       #And make it constant to preserve the hold. No key skipped

            else:   #Last resource, offset current key so it won't be overwritten
                key.frame -= 0.1

        #Write key
        setFcurveKey(
            fCurve=fcurve,
            animChannel= channel,
            keyIndex= index,
            interpoType= interpolation,
            writeIndex= writePointer,
            frameOffset= frameOffset
        )

        #Advance counters
        index += 1
        writePointer += 1

    #Cleanup unused curve spaces
    if writePointer < len(channel.keys):
        for _ in range(len(channel.keys) - writePointer):
            fcurve.keyframe_points.remove(fcurve.keyframe_points[-1]) #Delete last space in the fcurve

    #Finish by updating fcurve
    fcurve.update()

    #Add modifiers if EP
    if channel.ep_post > 0 or channel.ep_pre > 0:
        modifier:bpy.types.FModifierCycles = fcurve.modifiers.new(type='CYCLES') #type: ignore Bruh wtf is this a type error

        match channel.ep_pre:
            case 0: #No extrapolation
                modifier.mode_before = 'NONE'
            case 1: #Extrapolate with slope (i think). This doesnt exist in blender, and idk how to replicate it
                modifier.mode_before = 'NONE'    
            case 2: #Cycle repeat 
                modifier.mode_before = 'REPEAT'
            case 3: #Cycle offset 
                modifier.mode_before = 'REPEAT_OFFSET'

        match channel.ep_post:
            case 0:
                modifier.mode_after = 'NONE'
            case 1:
                modifier.mode_after = 'NONE'
            case 2:
                modifier.mode_after = 'REPEAT'
            case 3:
                modifier.mode_after = 'REPEAT_OFFSET'

    #Clear channel keys to save memory
    if clearAfterImport:
        channel.keys.clear()

def readRawLine(rawBuffer:array, rawLine:str):  #Reads and separates raw keys in a line
    data = rawLine.split(',')

    rawBuffer.extend(
        map(float, data)
    )

def parseRawLine(rawBuffer:array, channel:A3daChannel, keyType:str|int):     #Converts raw buffered data into a3da keyframes
    #Type 1: frame, value
    #Type 2: frame, value, slope
    #Type 3: frame, value, slope1, slope2

    frames = None
    values = None
    SlopeIns = None
    SlopeOuts = None

    ## Decode rawBuffer ##
    keyType = int(keyType)
    blockSize = keyType + 1

    if keyType >= 1:
        frames = rawBuffer[0 :: blockSize]
        values = rawBuffer[1 :: blockSize]
    if keyType >= 2:
        SlopeIns = rawBuffer[2 :: blockSize]

    if keyType >= 3:
        SlopeOuts = rawBuffer[3 :: blockSize]
    elif SlopeIns:
        SlopeOuts = SlopeIns
    
    del rawBuffer[:]    #Release buffer memory

    ## Convert to A3da Keyframes ##
    for i, frame in enumerate(frames):   #Use frames to iterate to everything else. Idk if there's a better way to do this
        channel.keys[i] = A3daKeyframe(
            frame= frame,
            value= values[i],
            s1= SlopeIns[i] if SlopeIns else 0,
            s2= SlopeOuts[i] if SlopeOuts else 0
        )

    del frames 
    del values 
    del SlopeIns 
    del SlopeOuts 

def ensureAction(target:bpy.types.Object) -> bpy.types.Action:
    if not target.animation_data:
        target.animation_data_create()

    if not target.animation_data.action:
        action = bpy.data.actions.new(name=f"{target.name}_Action")
        target.animation_data.action = action
    else:
        action = target.animation_data.action

    return action

def getChannelbag(target:bpy.types.ID, anim_data:bpy.types.AnimData|None=None) -> bpy.types.ActionChannelbag | None: #Should work on anything
    if anim_data is None:
        anim_data = target.animation_data
    if not anim_data: return None

    action = anim_data.action
    if not action or not action.layers or not action.layers[0].strips: return None #Idk if this can even trigger, but better safe than sorry
    
    return action.layers[0].strips[0].channelbag(anim_data.action_slot)

def getFcurve(target:bpy.types.ID, data_path:str, index:int=None) -> bpy.types.FCurve | None:
    channelbag = getChannelbag(target)
    if not channelbag: return None

    for fcurve in channelbag.fcurves:
        #print(fcurve.data_path)
        if index is not None:
             if fcurve.data_path == data_path and fcurve.array_index == index:
                return fcurve
        else:
            if fcurve.data_path == data_path:
                return fcurve

    return None

def copyFcurve(source:bpy.types.FCurve, target:bpy.types.FCurve):
    #Copy keyframe points
    target.keyframe_points.clear()
    target.keyframe_points.add(len(source.keyframe_points))
    for i, kp in enumerate(source.keyframe_points):
        t_kp = target.keyframe_points[i]
        t_kp.co = kp.co
        t_kp.handle_left = kp.handle_left
        t_kp.handle_right = kp.handle_right
        t_kp.interpolation = kp.interpolation
    target.update()



#Honor Trabajo y Justicia