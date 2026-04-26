# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

#bl_info = {
#    "name": "A3DA Parser",
#    "author": "Hans_Xwh",
#    "version": (0, 0, 2),
#    "blender": (3, 6, 0),
#    "description": "Import Project Diva A3DA animation files",
#    "category": "Import-Export",
#    "location": "File > Import > Diva A3DA (.a3da)",
#}
#Uncomment bl_info if you want to try using this on older Blender versions as legacy addon. At your own risk, may not even work. Properties should work though.

#Fun fact: a3da stands for Auth3D Assembly, while A3DC stands for Auth3D Compiled.
if "bpy" in locals():
    import importlib
    importlib.reload(A3DA_Properties)
    importlib.reload(A3DA_Core)
    importlib.reload(A3DA_Objects)
    importlib.reload(Parse_A3DA)
    importlib.reload(A3DA_UI)
    importlib.reload(A3DA_HRC)
    importlib.reload(A3DA_Camera)

    importlib.reload(A3DA_Utils)
    importlib.reload(A3DA_Edit)
    importlib.reload(A3DA_Export)
else:
    import bpy
    from . import A3DA_Properties
    from . import A3DA_Core
    from .A3DA_Import import Parse_A3DA
    from .A3DA_Import import A3DA_Objects 
    from .A3DA_Import import A3DA_HRC
    from .A3DA_Import import A3DA_Camera

    #a3da_ui must be imported after the main import functions
    from . import A3DA_UI
    from . import A3DA_Utils
    from . import A3DA_Edit
    from . import A3DA_Export

    #Register Props 
    #Register Working stuff
    #Register UI > Utils > Edit > Everything UI else   (Tho it doesnt mather i think)

def register():
    A3DA_Properties.register()
    A3DA_UI.register()
    A3DA_Utils.register()
    A3DA_Edit.register()
    A3DA_Export.register()

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    print("\nA3DA Parser registered")

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    A3DA_Export.unregister()
    A3DA_Edit.unregister()
    A3DA_Utils.unregister()
    A3DA_UI.unregister()
    A3DA_Properties.unregister()
    print("A3DA Parser unregistered")


def menu_func_import(self, context):    #This is the main button
    self.layout.operator(A3DA_UI.ImportA3DAOperator.bl_idname, text="Diva A3DA Animation (.a3da)", icon='EMPTY_ARROWS')