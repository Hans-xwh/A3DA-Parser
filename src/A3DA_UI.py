# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator
from pathlib import Path

from . import Parse_A3DA
from .A3DA_Import import A3DA_Camera
from . import A3DA_Core
from .A3DA_Import import Sequencial_Import

config = None

class ImportA3DAOperator(Operator, ImportHelper):
    """Import Project Diva A3DA animation files"""
    bl_idname = "import_scene.a3da"
    bl_label = "Import A3DA"
    bl_options = {"REGISTER", "UNDO"}

    #Filter for .a3da files
    filename_ext = ".a3da"
    filter_glob: StringProperty(default="*.a3da", options={'HIDDEN'})   #type: ignore

    ### Mode select ###
    import_mode: EnumProperty(  #type: ignore
        name="Mode",
        description="Choose the import mode",
        items=[
            ('SINGLE', "Single file", "Import a single A3DA file"),
            ('SEQUENCIAL', "Full PV import", "Import multiple A3DAs using DivaScript"),
            ("CAM", "Import Camera", "Import camera animation"),
        ],
        default='SINGLE'
    )

    #Game select
    game_sel : EnumProperty( #type: ignore
        name= "Game",
        description= "Game of origin. Required for DSC read",
        items=[
            ('FT', "Future Tone", "Project Diva Future Tone / MegaMix / Arcade Future Tone"),
            ('F', "Diva F", "Project Diva F"),
            ("F2", "Diva F2nd", "Project Diva F2nd"),
            #('X', "Diva X", "Project Diva X"),
            #('MGF', "MGF", "Miracle Girls Festival"),
            ('TXT', "Text (Legacy)", "Import dsc converted to text. (Legacy)")
        ],
        default='FT'
    )

    ### Config ###
    #Frame Offset Always visible
    frame_offset : IntProperty(     #type: ignore
        name="Frame Offset",
        description="Offset to apply to all imported keyframes. Recommended to leave at 1",
        default=0,
    )

    #Compatibility mode:
    compatibility_mode : BoolProperty(  #type: ignore
        name= "Compatibility Mode",
        description= "Uses user defined insted of api definde custom properties. When enabled, resulting animation will work even without A3DA Parser enabled, but it will not be exportable.",
        default= False
    )

    #Objects Toggle: 
    use_objects : BoolProperty(     #type: ignore
        name="Use Objects",
        description="Import animated objects",
        default=True,
    )

    #Visibility Toggle
    use_visibility : BoolProperty(  #type: ignore
        name="Use Visibility",
        description="Import visibility animations",
        default=True,
    )

    #Inherit visibility
    inherit_visibility : BoolProperty(  #type: ignore
        name="Inherit Visibility",
        description="Make visibility of a controller affect children controllers and meshes. Required for MGF",
        default=False
    )

    #Morph Toggle
    use_morphs : BoolProperty(  #type: ignore
        name="Use Morphs",
        description="Import morph animations. You'll need to manually setup the shape keys after import.",
        default=True,
    )

    #Texture Transform Toggle
    use_tex_transform : BoolProperty(   #type: ignore
        name="Use Tex Transform",
        description="Import texture UV animations",
        default=True,
    )

    #Texture Pattern Toggle
    use_tex_pat : BoolProperty(   #type: ignore
        name="Use Tex Pattern",
        description="Import texture pattern animations",
        default=False,
    )

    #Make independent instances
    independent_instances : BoolProperty(   #type: ignore
        name = "Make Independent Instances ",
        description = "When enabled, A3DA instances will have independent data blocks. Required for exporting to MMD",
        default = False
    )

    #Make A3DA always loop
    force_loops : BoolProperty( #type: ignore
        name="Force loops",
        description="(EXPERIMENTAL) When enabled, all imported A3DA animations will loop. Usefull for old stages, breakes newer. Use with caution",
        default=False
    )

    #Use HRC toggle
    use_hrc : BoolProperty(     #type: ignore
        name="Use HRC",
        description="Import HRC skeletal animation",
        default=True,
    )

    #Use HRC Ghost
    use_hrc_ghost : BoolProperty(   #type: ignore
        name="Use Ghost Armature",
        description='Create a new"ghost" armature, instead of trying to find an existing one. Recommended to leave enabled',
        default=True
    )

    #Start from file begin param toggle
    use_file_begin : BoolProperty( #type: ignore
        name="Use File Begin",
        description="Use begin frame declared in the file",
        default=True,
    )

    #Pv Branch select
    use_pv_branch : BoolProperty(   #type: ignore
        name="Use Chance Time",
        description="Use chance time effect if availyble",
        default=False
    )

    #Force load first a3da of a stage
    force_load_first : BoolProperty(   #type: ignore
        name="Force Load First A3DA",
        description="(EXPERIMENTAL) When enabled, the importer will try to load the first a3da of a stage (STGPVxxxS01_EFF_001), even if its not declared in the pv_field. This is a workaround, idk if the game does this. Use with caution",
        default=False
    )

    #Auto assign grounds
    auto_gnd : BoolProperty(    #type: ignore
        name= "Auto Parent GND",
        description= "Automatically assing objects with _GND suffix to their field controllers",
        default= True
    )

    #USe DOF togglew
    use_dof : BoolProperty( #type: ignore
        name="Use DOF",
        description="Use Depth of Field animation if available",
        default=True,
    )

    ### Hide options based on mode ###
    def draw(self, context):    
        layout = self.layout
        layout.prop(self, "import_mode")
        layout.prop(self, "frame_offset") #Always visible
        layout.prop(self, "compatibility_mode")

        layout.separator() #Nice

        #Single & Sequencial
        if self.import_mode in {'SINGLE', 'SEQUENCIAL'}:
            #Obj
            objBox = layout.box()
            objBox.label(text="Object options")
            objBox.prop(self, "use_objects")        #This outside the column, obviously

            objCol = objBox.column()
            objCol.prop(self, "use_visibility")

            vrow = objCol.row()
            vrow.separator(factor=1)
            vrow.prop(self, "inherit_visibility")
            vrow.enabled = self.use_visibility

            objCol.prop(self, "use_tex_transform")
            objCol.prop(self, "use_tex_pat")
            objCol.prop(self, "independent_instances")
            #flrow = objCol.row()
            objCol.prop(self, "force_loops")
            #flrow.enabled = self.import_mode != 'SEQUENCIAL'
            objCol.enabled = self.use_objects

            #Hrc
            hrcBox = layout.box()
            hrcBox.label(text="HRC options")
            hrcBox.prop(self, "use_hrc")

            hrcCol = hrcBox.column()
            hrcCol.prop(self, "use_hrc_ghost")
            hrcCol.enabled = self.use_hrc

        if self.import_mode == 'CAM':
            camBox = layout.box()
            camBox.label(text="Camera options")
            camBox.prop(self, "use_dof")

        #Single file loading
        if self.import_mode in ('SINGLE', 'CAM'):
            singleFBox = layout.box()
            singleFBox.label(text="File options")
            singleFBox.prop(self, "use_file_begin")

        #Sequencial
        if self.import_mode == 'SEQUENCIAL':
            seqBox = layout.box()
            seqBox.label(text="Sequencial options")
            seqBox.prop(self, "game_sel")
            seqBox.separator()
            seqBox.prop(self, "use_pv_branch")
            seqBox.prop(self, "auto_gnd")
            seqBox.prop(self, "force_load_first")




    def execute(self, context):
        #Build config
        global config
        config = A3DA_Core.ImportConfig()
        config.use_file_begin = self.use_file_begin
        config.ensure_compatibility = self.compatibility_mode
        #use_file_begin = self.use_file_begin if self.import_mode == 'SINGLE' else False,
        config.use_objects = self.use_objects
        config.use_visibility = self.use_visibility
        config.inherit_visibility = self.inherit_visibility
        config.use_morphs = self.use_morphs
        config.use_tex_transform = self.use_tex_transform
        config.use_tex_pat = self.use_tex_pat
        config.independent_instances = self.independent_instances
        config.force_loops = self.force_loops
        config.use_hrc = self.use_hrc
        config.use_hrc_ghost = self.use_hrc_ghost
        config.use_dof = self.use_dof
        config.game = self.game_sel
        config.use_pv_branch = self.use_pv_branch
        config.auto_gnd = self.auto_gnd
        config.force_load_first = self.force_load_first

        #Run import code
        try:
            if self.import_mode == 'SINGLE':
                a3da_path = Path(self.filepath)

                if a3da_path.is_file():
                    print(f"\nImporting A3DA file: {a3da_path}")
                    Parse_A3DA.startReading(
                        a3da_path,
                        frameOffset = self.frame_offset,
                        config= config
                    )
                elif a3da_path.is_dir():
                    print(f"\nImporting all A3DA files in directory: {a3da_path}")
                    for file in a3da_path.glob("*.a3da"):
                        print(f"\nImporting A3DA file: {file}")
                        Parse_A3DA.startReading(
                            a3da_path= file,    
                            frameOffset= self.frame_offset,
                            config= config
                        )


            elif self.import_mode == 'CAM':
                print(f"\nImporting A3DA file: {self.filepath}")
                A3DA_Camera.startReadingCam(
                    a3da_path= Path(self.filepath),
                    frameOffset= self.frame_offset,
                    config= config
                    #use_file_begin= self.use_file_begin,
                    #use_dof= self.use_dof
                )

            elif self.import_mode == 'SEQUENCIAL':
                config.use_file_begin = False
                #Sequencial_Import.sequencialRead(self.filepath)
                bpy.ops.a3da.pvfield_import(
                    'INVOKE_DEFAULT',
                    a3da_path= self.filepath,
                )

        except Exception as ex:
                self.report({'ERROR'}, "ERROR! Check console output for details!!! \nWindow -> Toggle console")
                raise ex
        
        return {'FINISHED'} #Only if import is successful
    
class A3DA_FH_Drop(bpy.types.FileHandler):
    bl_idname = "A3DA_FH_DROP"
    bl_label = "A3DA Animation File Drop Handler"
    bl_file_extensions = ".a3da"
    bl_import_operator = "import_scene.a3da" 

    @classmethod
    def poll_drop(cls, context):
        #return super().poll_drop(context)
        return context.area.type == 'VIEW_3D'   #Only import in 3d view
    
class A3DA_OT_Import_PvField(Operator, ImportHelper):
    #Recursive file picker
    bl_idname = "a3da.pvfield_import"
    bl_label = "Select pv_field"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    #Filter for diva files
    filename_ext = ".txt"
    filter_glob: StringProperty(default="*.txt;*.pfl", options={'HIDDEN'})   #type: ignore #Stupid error ignore this

    #Files
    a3da_path: StringProperty(options={'HIDDEN'}) #type: ignore
    pvField_path: StringProperty(options={'HIDDEN'}) = None #type: ignore

    #config:A3DA_Core.ImportConfig = None
        

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select pv_field.txt to use")
            

    def invoke(self, context, event):
        #Select pv_field.txt

        #Call itself
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        #Select pv_field
        bpy.ops.a3da.dsc_import(
            'INVOKE_DEFAULT',
            a3da_path = self.a3da_path,  #Pass variables to new self
            pvField_path = self.filepath,   #chosen file
        )
        return {'FINISHED'}
        
class A3DA_OT_Import_DSC(Operator, ImportHelper):
    #Recursive file picker
    bl_idname = "a3da.dsc_import"
    bl_label = "Select DSC"
    bl_options = {'REGISTER', 'UNDO'}

    endian_mode: EnumProperty(      #type: ignore
        name = "Endian",
        description= "Endiannes for reading the DSC file",
        items=[
            ('AUTO', "Auto", "Automatically determine endianness based on game"),
            ('BIG', "Big endian", "Force to use big endian"),
            ('LITTLE', "Little endian", "Force to use little endian")
        ],
        default='AUTO'
    )
    
    #Filter for diva files
    filename_ext = ".dsc"
    filter_glob: StringProperty(default="*.dsc;*.txt", options={'HIDDEN'})   #type: ignore #Stupid error ignore this

    #Files
    a3da_path: StringProperty(options={'HIDDEN'}) #type: ignore
    pvField_path: StringProperty(options={'HIDDEN'}) #type: ignore
    dsc_path: StringProperty(options={'HIDDEN'}) #type: ignore

    #config: A3DA_Core.ImportConfig

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select DSC file to use")
        layout.prop(self, "endian_mode")

    def invoke(self, context, event):
        #Select pv_xxx.dsc

        #Call itself
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        global config
        config.endian = self.endian_mode
        #The real deal, all files are now availible
        self.dsc_path = self.filepath
        print("Ready for sequencial import")
        print(f"A3DA: {self.a3da_path}")
        print(f"pv_field: {self.pvField_path}")
        print(f"DSC: {self.dsc_path}")
        #print(f"Config: {config}")

        #This will run sequencial import
        Sequencial_Import.sequencialRead_FT(
            self.a3da_path,
            self.pvField_path,
            self.dsc_path,
            config
        )
        return {'FINISHED'}
    
classes = [
    A3DA_OT_Import_DSC,
    A3DA_OT_Import_PvField,
    ImportA3DAOperator,
    A3DA_FH_Drop
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
