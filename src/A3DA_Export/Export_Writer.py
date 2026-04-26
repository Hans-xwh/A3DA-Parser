# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from .. A3DA_Import.A3DA_HRC import HrcObject
from .. A3DA_Import.A3DA_Objects import A3daObject
from .. A3DA_Import.A3DA_Camera import A3daCamera, A3daCamObj
#from . Export_Core import get_transform_lines, get_channel_lines, get_channel_raw
from . Export_HRC import write_hrc
from . Export_Objects import write_obj
from . Export_Camera import write_cam

import bpy
from pathlib import Path
from datetime import datetime

def write_a3da(path:Path, hrcList:list[HrcObject]=None, objList:list[A3daObject]=None, cam:tuple[A3daCamera, A3daCamObj,A3daCamObj:None]=None, use_raw=True) -> bool:
    print("Writing A3DA...")
    now = datetime.now()
    #path = Path(out)
    file_name = path.name
    a3da = path.open('w', newline="\n")
 
    ### Write header ###
    a3da.write(f'#A3DA__________\n')
    a3da.write(f'#{now.strftime("%a %b %d %H:%M:%S %Y")}\n') #day = str(now.day)  #now.strftime(f"#%a %b {day.rjust(2)} %H:%M:%S %Y") 
    a3da.write(f'_.converter.version={now.strftime("%Y%m%d")}\n')
    a3da.write(f'_.file_name={file_name}\n')
    #a3da.write(f'_.property.version={now.strftime("%Y%m%d")}\n')
    a3da.write(f'_.property.version=20050706\n')

    #Write camera
    if cam and cam[0] is not None:
        write_cam(a3da, cam[0], cam[1], cam[2], use_raw)    #TODO this should also export the root object

    #Write Objects
    if objList and len(objList) > 0:
        write_obj(a3da, objList, use_raw)

    #Write HRC
    if hrcList and len(hrcList) > 0:
        write_hrc(a3da, hrcList, use_raw)
    
    ## Play control ##
    a3da.writelines([
        f'play_control.begin={bpy.context.scene.frame_start}\n',
        f'play_control.fps={bpy.context.scene.render.fps}\n',
        f'play_control.size={bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1}\n'
    ])
            

    a3da.close()
    print("Finished Writing A3DA!")
    print(f"Saved to {path}")
    a3da.close()
    return True