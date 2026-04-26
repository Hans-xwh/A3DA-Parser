# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from typing import Type

from .. A3DA_Core import A3daTransform, A3daChannel, A3daKeyframe

import bpy

def decide_kv_type(key:A3daKeyframe) -> int:    #Key Value types
    if not (key.Slope1 or key.Slope2) or (key.Slope1 == 0 and key.Slope2 == 0):
        if key.value == 0:
            return 0
        else:
            return 1
    
    elif abs(key.Slope1 - key.Slope2) < 0.00001: 
        return 2
    
    else: 
        return 3
    

def get_channel_lines(prefix:str, channel:A3daChannel) -> list[str]:
    lines:list[str] = []
    max = -1
    kv_type = 1  #Key/channel Type
    #A3DA Key Value types: (from KorenKonder)
    #Type 0 - Frame. Other are 0
    #Type 1 - Frame and Value. Other are 0
    #Type 2 - Frame, Value and Tangent (used as Tangent1 and Tangent0)
    #Type 3 - Frame, Value, Tangent1 and Tangent0

    #A3DA Key types: (from KorenKonder)
    #Type 0 - Reset value for entire Key to 0
    #Type 1 - Set value for entire Key for some value
    #Type 2 - Linear interpolation between previous and current keys
    #Type 3 - Cubic Hermite Spline between previous and current keys
    #Type 4 - Hold value of last key until it reaches another key in that Key

    if len(channel.keys) == 1:
        lines.append(f'{prefix}.type=1')
        lines.append(f'{prefix}.value={channel.keys[0].value:.9g}') #Round and trim useless 0s
    else:
        sorted_keys = {k: channel.keys[k] for k in sorted(channel.keys.keys(), key=str)}    #A3da is stupid and expects key sorted in ALPHABETICAL order
        for id, key in sorted_keys.items():
            kv_type = decide_kv_type(key)
            pA = "(" if kv_type > 0 else ""   #Parenthesis for value list if type is not 0
            pB = ")" if kv_type > 0 else ""

            lines.append(f'{prefix}.key.{id}.data={pA}{key.as_txt(kv_type)}{pB}')
            lines.append(f'{prefix}.key.{id}.type={kv_type}')       #Currently hardcoded to this shit

            if key.frame > max:
                max = int(key.frame)
        lines.append(f'{prefix}.key.length={len(sorted_keys)}')
        lines.append(f'{prefix}.max={max+1}') #added +1
        lines.append(f'{prefix}.type={channel.interpolation}')

    return lines

def get_channel_raw(prefix:str, channel:A3daChannel) -> list[str]:
    lines:list[str] = []
    max = -1

    #Decide key value type
    if channel.interpolation == 3:
        kv_type = 3
    else:
        kv_type = 1

    #build raw value list
    raw_data_list:list[str] = []
    for key in channel.keys.values():
        if key.frame > max:
            max = key.frame

        raw_data_list.append(f'{key.as_txt(kv_type)}')
    raw_data:str = ",".join(raw_data_list)

    #add lines
    lines.append(f'{prefix}.max={int(max)+1}')
    lines.append(f'{prefix}.raw_data.value_list={raw_data}')
    lines.append(f'{prefix}.raw_data.value_list_size={len(channel.keys)*2}')    #double the keys
    lines.append(f'{prefix}.raw_data.value_type=float')
    lines.append(f'{prefix}.raw_data_key_type={kv_type}')
    lines.append(f'{prefix}.type={channel.interpolation}')
        
    return lines

def get_transform_lines(prefix:str, transform:A3daTransform, safe=False, raw=False) -> list[str]:
    #target prop is rot, scale, trans, visibility, etc
    lines:list[str] = []

    
    #X
    if len(transform.x.keys) == 0:
        if safe:
            lines.append(f'{prefix}.x.type=1')
            lines.append(f'{prefix}.x.value=1')    
        else:
            lines.append(f'{prefix}.x.type=0')
    elif len(transform.x.keys) <= 2 or not raw:
        lines += get_channel_lines(
            prefix= f'{prefix}.x',
            channel= transform.x
        )
    else:   #raw_data
        lines += get_channel_raw(
            prefix= f'{prefix}.x',
            channel= transform.x
        )

    #Y
    if len(transform.y.keys) == 0:
        if safe:
            lines.append(f'{prefix}.y.type=1')
            lines.append(f'{prefix}.y.value=1')    
        else:
            lines.append(f'{prefix}.y.type=0')
    elif len(transform.y.keys) <= 2 or not raw:
        lines += get_channel_lines(
            prefix= f'{prefix}.y',
            channel= transform.y
        )
    else:   #raw_data
        lines += get_channel_raw(
            prefix= f'{prefix}.y',
            channel= transform.y
        )
        
    #Z
    if len(transform.z.keys) == 0:
        if safe:
            lines.append(f'{prefix}.z.type=1')
            lines.append(f'{prefix}.z.value=1')    
        else:
            lines.append(f'{prefix}.z.type=0')
    elif len(transform.z.keys) <= 2 or not raw:
        lines += get_channel_lines(
            prefix= f'{prefix}.z',
            channel= transform.z
        )
    else:   #raw_data
        lines += get_channel_raw(
            prefix= f'{prefix}.z',
            channel= transform.z
        )

    return lines
