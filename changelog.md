# Changelog

## [Unreleased]   
- Fixed camera export crashing on cameras without every property animated 
- Fixed export always writing raw_data for *fov* & *roll* 
- Fixed exporter writing with non `a3da` file extension 
- Changed *Visibility* property from an `IntProperty` to a `FloatProperty` 
- Changed visibility driver expression  
- Added object visibility export 
- Fixed export of keyframes with constant interpolation 
- Clean up View Panel. Now properties are hidden for non-Auth3D objects 
- Fixed reading of type=0 channels for visibility 


## 1.0.24
- Fixed priority of uid_name for object export  
- Fixed raw_data.value_list_size not being calculated correctly  
- Cleaned up placeholder & leftover UI elements  
- Fixed UI typos  

## 1.0.23
- Fixed a bug with reading camera DOF animation, where channels with a single keyframe were ignored  
- Fixed a bug with transfer shape keys operator crashing  

## 1.0.20
- Fixed export of ep_type_pre & ep_type_post.  
- Added Aura's DOF visualization node.  
- Fixed display of DOF properties on the viewer Panel  
- Extended compatibility to Blender 4.5+

## 1.0.1
- Reworked auto fov cam to comply with Blender Extensions best practices  

## 1.0.0 - Initial Release
- Added support for exporting cameras  
- Added export support for Camera DOF  
- Added support for exporting converted Hermite curves  
- Reworked channel to text exporter  
- Reworked fromFCurve method of channels  
- Reworked asTxt method of a3da keyframes  
- Added support for animated camera root export  
- Made objects use API defined props  
- A lot of small corrections  
- Created simpler logic for creating scale morphs  

## Beta 0.1.4
- Added support for saving hrc visibility to the armature  
- Fixed a bug in sequential import that caused a crash if "force load first a3da" was enabled  
- When selecting a folder in single file mode, all files in the folder will be loaded with the same settings  
- Added Visibility Editor utility  
- Made objects use api props for visibility  

## Beta 0.1.3
- Changed Force load first behavior to better match Diva  
- Added support for m_objhrc instances  
- Made Parse_A3DA save uid_name and set auth3d_types correctly  
- Empties to bones can now work without models, and set names based on uid_name

## Beta 0.1.2  
- Tweaked some texts on the UI  
- Updated main a3da reader to use pathlib  
- Added function DapperDots to convert Bezier to Hermite  
- Added export file picker dialogs  
- Added auth3d camera api props  
- Updated camera importer to use api props  
- Added an option to automatically assign _GND objects  

## Beta 0.1.1
- Expanded a3da api properties  
- Added option to export A3DA Objects  
- Rewrote Empties to Bones to be a bit less of a mess and be actually useful.  
- Added new Empties to Bones with support for scale  
- Added an option for Empties to Bones to copy bone scaling  

## Beta 0.1.0  
- Added a3da API properties  
- Added a3da edit & conversion utils  
- Added export for HRC animation  
- Added support for exporting raw_data HRC  
  
## Beta 0.0.4  
- Added preliminary CONCEPTUAL support for texture patterns  
- Added basic support for animated morphs  
- Added "convert to MMD FOV mod ready camera" button.  
- Added M_Hrc class  
- Added initial reading of m_objhrc  
- Added report functions to base classes of A3DA_Core  
- Added support for HRC reading visibility  

## Beta 0.0.3  
- Ported legacy addon to extension.  
- Changed file structure.  
- Added option "Force load first A3DA"  
- Changed assume loops behavior on full PV import.  
- Fixed a bug with ColorAttribute node detection on FixMats  
- Optimized FixMats so it won't run twice on the same material  
- Improved compatibility (4.5 LTS & 5.1)  
- Updated db.json ver  

## Beta 0.0.2  
- Changed Visibility property creation logic.  
- Added support for inherited visibility.  
- Added support for MGF tex transform offsetV & offsetU.  
- Added option "Assume A3DA always loops".