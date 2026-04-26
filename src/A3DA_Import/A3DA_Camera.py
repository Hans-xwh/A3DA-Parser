# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from ..A3DA_Core import ImportConfig, A3daKeyframe, A3daChannel, A3daTransform, parseA3daKey, setA3daChannel, readRawLine, parseRawLine, ensureAction, switchAxis as CoreSwAx
from .A3DA_Objects import A3daObject, createEmpty, assignParent, createObjDriver
import bpy
from array import array
import time

#class A3daCamObj:   #Dof OBJ can be represented as one of these
#    def __init__(self):
#        self.location:A3daTransform = A3daTransform()
#        self.rotation:A3daTransform = A3daTransform()
#        self.scale:A3daTransform = A3daTransform()
#
#        self.bl_reference:bpy.types.Object | None = None

class A3daCamObj(A3daObject):   #Dof OBJ can be represented as one of these
    def __init__(self):
        self.translation:A3daTransform = A3daTransform()
        self.rotation:A3daTransform = A3daTransform()
        self.scale:A3daTransform = A3daTransform()
        self.visibility:A3daChannel = A3daChannel()

        self.bl_reference:bpy.types.Object | None = None

    def __repr__(self):
        return f'Blender obj: {self.bl_reference.name}'

class A3daCamera:
    def __init__(self, id:int=0): 
        self.id:int = id
        self.interest:A3daCamObj = A3daCamObj()
        self.view_point:A3daCamObj = A3daCamObj()

        self.roll:A3daChannel = A3daChannel()
        self.fov:A3daChannel = A3daChannel()            #DIVA in radians
        self.focal_length:A3daChannel = A3daChannel()   #MGF in mm (i think)

        #This are in inches. Why? Idk, go ask sega.
        self.aspect:float = 0.0
        self.height:float = 0.0
        self.width:float = 0.0
        #width/height = aspect

        self.bl_camera:bpy.types.Object | None = None
        self.bl_root:bpy.types.Object | None = None

    def pushKey(self, target:str, transform:str, keyframe:A3daKeyframe, keyIndex:int, axis:str=None):
        keyIndex = int(keyIndex)

        match target:
            case 'interest':
                trgt = self.interest
            case 'view_point':
                trgt = self.view_point

        match transform:
            case 'fov':
                self.fov.keys[keyIndex] = keyframe
            case 'roll':
                self.roll.keys[keyIndex] = keyframe
            case _:
                trgt.pushKey(transform, axis, keyframe, keyIndex)


def switchAxis(value):
    match value:
        #Camera
        case "roll":
            return "rotation_euler"
        case "fov":
            return "lens"
        case "focal_length":
            return "lens"
    
    #if nothing is matched
    return CoreSwAx(value)


#### Camera working functions ####
def setupCam(camera:A3daCamera=None, dof:A3daCamObj=None, prefix:str=''):
    if prefix != '':
        camName = prefix
        prefix  += ' - '

        if camera.id > 0:
            prefix = str(camera.id) + f'_{prefix}'
            camName = str(camera.id) + f'_{camName}'
    else:
        camName = 'A3DA_Camera'

    #Create objects
    camera.bl_camera = bpy.context.scene.objects.get(camName)
    if not camera.bl_camera:
        camData = bpy.data.cameras.new(prefix + 'data')
        camera.bl_camera = bpy.data.objects.new(camName, camData)
        bpy.context.scene.collection.objects.link(camera.bl_camera)

    camera.bl_root = createEmpty(prefix + 'Root')
    camera.view_point.bl_reference = createEmpty(prefix + 'ViewPoint')
    camera.interest.bl_reference = createEmpty(prefix + 'Interest')

    camera.bl_camera.auth3d_cam.subtype = 'CAM'
    camera.bl_camera.auth3d.auth3d_type = 'CAMERA'
    camera.bl_root.auth3d.auth3d_type = 'CAMERA'
    camera.bl_root.auth3d_cam.subtype = 'ROOT'
    camera.view_point.bl_reference.auth3d.auth3d_type = 'CAMERA'
    camera.view_point.bl_reference.auth3d_cam.subtype = 'VIEW'
    camera.interest.bl_reference.auth3d.auth3d_type = 'CAMERA'
    camera.interest.bl_reference.auth3d_cam.subtype = 'INTEREST'

    #set parenting
    assignParent(camera.bl_root, camera.interest.bl_reference)
    assignParent(camera.bl_root, camera.view_point.bl_reference)
    assignParent(camera.view_point.bl_reference, camera.bl_camera)

    #Set constraint
    track_to = camera.view_point.bl_reference.constraints.new(type="TRACK_TO")
    track_to.target = camera.interest.bl_reference

    #Rotate root
    camera.bl_root.rotation_euler.x = 1.570796  #90 degrees


    if dof and camera.id == 0:
        dof.bl_reference = createEmpty(prefix + 'DOF')  #I dont really know what to do with the dof object so it'll just exist there
        assignParent(camera.bl_root, dof.bl_reference)
        dof.bl_reference.auth3d.auth3d_type = 'CAMERA'
        dof.bl_reference.auth3d_cam.subtype = 'DOF'



def setupFovDriver(camera:A3daCamera, compatibility=False) -> tuple[str]:
    if compatibility:
        camera.bl_camera['A3DA_FOV'] = 1.0  #Ensure the custom property exists
        camera.bl_camera['FOV_Scale'] = 1.0
        fov_prop = '["A3DA_FOV"]'
        fov_scale = '["FOV_Scale"]'
    else:
        fov_prop = "auth3d_cam.fov"
        fov_scale = "auth3d_cam.fov_scale"

    #Make FOV driver, then add scale
    driver = createObjDriver(camera.bl_camera, fov_prop, camera.bl_camera.data, 'lens', var_name="FOV",
                    expression='(36 / (2* tan( FOV / 2))) * s')
    
    scaleVar = driver.variables.new()
    scaleVar.name = 's'
    scaleVar.targets[0].id = camera.bl_camera
    scaleVar.targets[0].data_path = fov_scale

    return fov_prop, fov_scale

def animateCamObj(obj:A3daCamObj):
    target = obj.bl_reference

    action = ensureAction(target)    

    #Write anim
    for transform in ('trans', 'rot', 'scale'):
        for axis in ('x', 'y', 'z'):
            channel = obj.getTransform(transform, axis)
            if len(channel.keys) == 0:
                continue

            fcurve = action.fcurve_ensure_for_datablock(
                datablock= target,
                data_path= f'{switchAxis(transform)}',
                index= switchAxis(axis)
            )

            setA3daChannel(fcurve, channel)


def animateCam(camera:A3daCamera=None, dof:A3daCamObj=None, config:ImportConfig=None):
    if dof.bl_reference:
        animateCamObj(dof)

    #Animate interes and viewpoint
    animateCamObj(camera.interest)
    animateCamObj(camera.view_point)

    #Ensure camera and write roll
    cam_action = ensureAction(camera.bl_camera)
    fcurve = cam_action.fcurve_ensure_for_datablock(
        camera.bl_camera, 'rotation_euler', index=2)
    setA3daChannel(fcurve, camera.roll)

    #Decide for or focal_length
    if len(camera.fov.keys) > 0:
        fov_prop, fov_scale = setupFovDriver(camera, config.ensure_compatibility)
        fcurve = cam_action.fcurve_ensure_for_datablock(
            camera.bl_camera, fov_prop)
        
        setA3daChannel(fcurve, camera.fov)
    else:
        if not camera.bl_camera.data.animation_data:
            camera.bl_camera.data.animation_data_create()    #Assign same action as camera obj
        camera.bl_camera.data.animation_data.action = cam_action

        fcurve = cam_action.fcurve_ensure_for_datablock(
            camera.bl_camera.data, 'lens')
        setA3daChannel(fcurve, camera.focal_length)

        camera.bl_camera.data.sensor_width = camera.width * 25.4    #Inches to mm
        camera.bl_camera.data.sensor_height = camera.height * 25.4

    #Animate DOF if availible
    if dof.bl_reference:
        animateCamObj(dof)


#### File reading ####
def readCam(a3daFile, a3daName, frameOffset=0, config:ImportConfig=None):
    startTime = time.time()
    print(f'[readCam] FrameOffset: {frameOffset}')
    print(f'[readCam] a3daName: {a3daName}')
    rawBuffer:array = array('d')   #Array of doubles
    cameras:dict[int, A3daCamera] = {}  #It's technically posible to have more than one camera, but i think only MGF has more than one and in some pv's only
    dof:A3daCamObj = A3daCamObj()
    has_dof = False

    #### File reading ####
    line:str
    for line in a3daFile:
        line = line.strip()
        #print(line)

        if line.startswith(('#', '_')):
            continue
        params, data = line.split('=')
        params = params.split('.')

        ### Read camera animation
        if params[0] == 'camera_root' and params[1] != 'length':
            #Params; 1:camId, 2:CamObj, 3:transform, 4:axis

            camId = int(params[1])
            camera = cameras.get(camId)
            if not camera:
                camera = A3daCamera(camId)
                cameras[camId] = camera

            if params[2] == 'interest' and params[3] != 'visibility':
                if params[5] == 'key' and params[6] != 'length' and 'data' in params:
                    camera.interest.pushKey(
                        transform=params[3],
                        axis= params[4],
                        keyIndex= params[6],
                        keyframe= parseA3daKey(data, frameOffset)
                    )
                    
                elif params[5] == 'type':
                    camera.interest.setParam(
                        transform=params[3],
                        axis= params[4],
                        interpolation= data
                    )

                elif params[5] == 'raw_data' and params[6] == 'value_list':
                    readRawLine(rawBuffer, data)

                elif params[5] == 'raw_data_key_type':
                    channel = camera.interest.getTransform(params[3], params[4])
                    parseRawLine(rawBuffer, channel, data)
                    pass

            elif params[2] == 'view_point':
                if params[3] in ('trans', 'rot', 'scale'):
                    if params[5] == 'key' and params[6] != 'length' and params[7] == 'data':
                        camera.view_point.pushKey(
                            transform= params[3],
                            axis = params[4],
                            keyIndex= params[6],
                            keyframe= parseA3daKey(data, frameOffset)
                        )
                    elif params[5] == 'type':
                        camera.view_point.setParam(
                            transform= params[3],
                            axis= params[4],
                            interpolation= data
                        )

                #TODO REFACTOR THIS HORRIBLE CODE OMG WHAT WAS I THINKING
                #It should check the case, save where to write in a var, then decide if raw or keys
                elif params[3] == 'aspect':   #Static. Idk if it's worth saving this, since for al diva pvs it's always 1.77778
                    camera.aspect = float(data)

                elif params[3] == 'fov':
                    if params[4] == 'key' and params[5] != 'length' and params[6] == 'data':
                        camera.fov.keys[int(params[5])] = parseA3daKey(data, frameOffset)
                    elif params[4] == 'type':
                        camera.fov.interpolation = int(data)

                elif params[3] == 'roll':
                    if params[4] == 'key' and params[5] != 'length' and params[6] == 'data':
                        camera.roll.keys[int(params[5])] = parseA3daKey(data, frameOffset)
                    elif params[4] == 'type':
                        camera.roll.interpolation = int(data)

                elif params[3] == 'fov_is_horizontal':  #Always 1
                    pass

                elif params[3] == 'camera_aperture_h':  #MGF    #This and W are in inches for some rason
                    camera.height = float(data)

                elif params[3] == 'camera_aperture_w':  #MGF
                    camera.width = float(data)

                elif params[3] == 'focal_length':  #MGF     #Then animate this in mm.
                    if params[4] == 'key' and params[5] != 'length' and params[6] == 'data':
                        camera.focal_length.keys[int(params[5])] = parseA3daKey(data, frameOffset)
                    elif params[4] == 'type':
                        camera.focal_length.interpolation = int(data)

        elif params[0] == 'dof' and config.use_dof:
            if params[1] in ('trans', 'rot', 'scale'):
                has_dof = True
                channel = dof.getTransform(
                    channel= params[1],
                    axis= params[2])

                if params[3] == 'key' and params[4] != 'length' and params[5] == 'data':  #Regular keys
                    keyIndex = int(params[4])
                    channel.keys[keyIndex] = parseA3daKey(data, frameOffset)

                elif params[3] == 'type':   #Interpolation mode
                    channel.interpolation = int(data)

                elif params[3] == 'raw_data' and params[4] == 'value_list':     #Raw key data buffering
                    readRawLine(rawBuffer, data)

                elif params[3] == 'raw_data_key_type':  #Raw data resolving
                    parseRawLine(rawBuffer, channel, data)
            pass

        ### Read play control settings ###
        elif params[0] == 'play_control':
            if params[1] == 'fps':
                bpy.context.scene.render.fps = int(data)
            
            elif params[1] == 'size':
                bpy.context.scene.frame_end = int(data) + frameOffset

    pass

    print("\nFinished reading A3DA file")
    print(f"Reading took {round(time.time() - startTime, 4)} seconds")

    ### Writing to Blender ###
    blTime = time.time()

    for id, camera in cameras.items():
        setupCam(camera, dof if config.use_dof else None, prefix=a3daName)

        animateCam(camera, dof, config)


    ### Finish ###
    print(f'Writing to Blender took: {round(time.time() - blTime, 4)} seconds.\n')
    print(f'Finished animating camera')


def startReadingCam(a3da_path:str='', frameOffset:int=0, config:ImportConfig=None):
    print('\nA3DA Camera Start')
    startTime = time.time()
    a3daFile = open(a3da_path, 'r')

    try:
        a3daName = None
        begin = 0
        for line in a3daFile:
            line = line.strip()
            if line.startswith(('#')):
                continue
            params, data = line.split('=')
            params = [itm for itm in params.split('.')]

            if params[1] == 'file_name':
                #a3daName = data.removesuffix('.a3da') + '_'     #This is also the field name
                a3daName = [itm for itm in data.split('_')]
                a3daName = a3daName[0]

                if not config.use_file_begin: break

            elif params[0] == 'play_control' and params[1] == 'begin':
                begin = int(data)
                break
        
        if config.use_file_begin:
            print("Begin offet:", begin)
            frameOffset += begin

        if a3daName == None:
            #a3daName = stgpv + "_EFF_"
            pass
    except UnicodeDecodeError as ex:
        print('\nFile read Error')
        print('You likely tried to load an A3DC binary file, but they are not supported by this tool!')
        print('Convert those to A3DA with PD_Tool by KorenKonder first!')
        a3daFile.close()
        raise ex
    a3daFile.seek(0)

    print('Object prefix:', a3daName)

    #### Import camera ####
    readCam(a3daFile, a3daName, frameOffset, config)

    #### Finish ####
    a3daFile.close()
    print(f'Total elapsed time: {round(time.time() - startTime, 4)} seconds.')
    print('Excecution finished')