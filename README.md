# A3DA Parser
A Blender addon for importing and exporting Auth3D animation from the Project Diva game saga. 


### Examples
https://github.com/user-attachments/assets/d781be2a-18ee-444f-9dd8-1af4e50a5f9b

[Gaikotsu Gakudan To Riria](https://youtu.be/GbVOTZgaXsw)  

[Ghost Rule](https://youtu.be/YU3VF_tHu4g)

## Features
Import & export Auth3D Assembly files (.a3da) from Blender.  

This tool is compatible with .a3da files from all games of the Project Diva saga, however they must be in the text format.  
Also supports Miracle Girls Festival, since it's built on the same game engine as the Project Diva games.

Full PV Import supports:
- Project Diva Future Tone / MegaMix+
- Project Diva F
- Project Diva F2nd

Single file and Camera importer supports a3da from any game.  
**Just make sure the .a3da files are text, not binary.**

### Import
| Feature | Support | Details |
| --- | --- | --- |
| Full PV import | ✅ Supported | Import a whole PV by loading all a3da files, a dsc file, and pv_field / pfl. |
| Camera animation | ✅ Supported | Transformations & DOF |
| Object animation | ✅ Supported | Transformations, visibility & instances fully supported |
| Texture transformations | ✅ Supported | Transformations & patterns supported |
| Looping animations | ✅ Supported | Loops are set up as FCurve modifiers |
| Morphs | ⚠️ Partial Support | Dummy shape keys are created & animated, requires manual setup of morphs. |
| HRC skeletal animation | ⚠️ Partial Support | Transforms & visibility supported, but requires retarget to model after import. |
| Lights | ❌ Not supported | Who turned the lights off? |


### Export
The export functionality is still experimental, but the produced files will load & work on Future Tone at least.  
As a demo, I've included an a3da camera i made a while ago for Mobious-P's mocap of the song JumpUp by Deco*27. Never finished it but works as a test file lol.  

### Miscellaneous
A lot of miscellaneous tools are built in, to help with model setup, manipulation of imported animation, conversion to MMD ready assets, and creation of Auth3D animation.

## Installation
Download the zip file from Releases, then drag & drop into Blender 5.0 or newer.

## Usage
You'll find the import button in File > Import > Diva A3DA Animation (.a3da), as well as in the A3DA N-Panel.  

In the file picker window, the "Mode" dropdown switches between importing modes; Single File, Import Camera, and Full PV Import.  

If a folder is selected in Single File mode, all files in the selected folder will be imported with the same settings.  

Files from F2nd, like .pfl, are encrypted and must be decrypted first.

I hope this helps even a bit to any poor souls dealing with Sega's wicked animation format.


## Acknowledgments
This project was possible thanks to the help of the Project Diva community.  
A big thank you to the amazing people that helped along the way ;)  

**KorenKonder** - For [ReDiva](https://github.com/korenkonder/ReDIVA), and for the invaluable messages with random Diva knowledge scattered around Diva Modding 2nd lol.  

**Nastys** - For the DSC command database from [Open PD Script Editor](https://github.com/nastys/Open-PD-Script-Editor).  

**ChicoEevee** - For helping with HRC export functionality & providing files for testing.  

**Hoshi** - For explaining to me how to create scale morphs for use in MMD, and for beta testing.  

**Danii18** - For the method to convert any camera to a float FOV camera for using with modded MMD.  

**Easter Fox** - For providing amazing motions, and helping with beta testing the Full PV Import function.  

**LudoMako** - For beta testing and catching bugs in basically everywhere lol.  
