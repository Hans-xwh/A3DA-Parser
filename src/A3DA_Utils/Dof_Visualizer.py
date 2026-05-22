# Copyright (C) 2026 Hans_Xwh - Licensed under GPL v3.

from pathlib import Path

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

class A3DA_Utils_OT_DofNodes(Operator):
    bl_idname = "a3da_utils.dof_nodes"
    bl_label = "Add DOF Nodes"
    bl_description = "Adds Aura's DOF visualization node to the scene compositor."
    bl_options = {"REGISTER", "UNDO"}

    edit_scene: BoolProperty( #type: ignore
        name="Setup Scene",
        description="Ensures a depth render pass is enabled, and enables compositor viewer.",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and context.active_object.auth3d_cam.subtype == 'CAM'
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "edit_scene")

    def execute(self, context):
        camera = context.active_object
        dof_obj = None

        if self.edit_scene:
            context.view_layer.use_pass_z = True

        #Find dof
        if not camera.parent or not camera.parent.parent: 
            self.report({'ERROR'}, "Invalid camera rig!!!")
            return {'CANCELLED'}
        
        for child in camera.parent.parent.children:
            if child.auth3d_cam.subtype == 'DOF':
                dof_obj = child
                break
        if not dof_obj:
            self.report({'ERROR'}, "No DOF object found!!!")
            return {'CANCELLED'}

        #Nodes
        dof_node = append_dof_node(context, camera.name + " DOF")
        if dof_node is None:
            self.report({'ERROR'}, "Compositor nodes not found!!!")
            return {'CANCELLED'}

        setup_dof_nodes(dof_node)
        setup_dof_drivers(dof_node, camera, dof_obj)
        return {'FINISHED'}


def append_dof_node(context: bpy.types.Context = bpy.context, name:str = "") -> None | bpy.types.CompositorNode:
    filepath = Path(__file__).resolve().parent.parent / "Assets/dof_a3da_by_aura.blend"     #Theres gotta be a better way to to this 
    group_name = "Auth3D DOF"
    scene = context.scene

    if bpy.app.version >= (5, 0, 0):
        node_tree = scene.compositing_node_group
    else:
        node_tree = scene.node_tree if scene.use_nodes else None

    if not node_tree:
        print("Scene has no compositing node group!")
        return None
    nodes = node_tree.nodes

    #Import the node
    if not bpy.data.node_groups.get(group_name):
        with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
            data_to.node_groups.append(group_name)


    #Link data
    dof_node = bpy.data.node_groups.get(group_name)
    dof_node.use_fake_user = True
    
    #Instance the dof node
    dof_node_inst = nodes.get(name)
    if not dof_node_inst:
        dof_node_inst = nodes.new(type='CompositorNodeGroup')
        dof_node_inst.node_tree = dof_node
        dof_node_inst.location = (0, 0)
        if name != "": dof_node_inst.name = name

    return dof_node_inst


def setup_dof_nodes(dof_node:bpy.types.CompositorNode) -> bool:
    node_tree:bpy.types.NodeTree = dof_node.id_data
    nodes = node_tree.nodes
    links = node_tree.links

    ##Identify output
    output_node:bpy.types.NodeGroup = None
    for node in nodes:
        if node.bl_idname in ('NodeGroupOutput', 'CompositorNodeComposite', 'CompositorNodeViewer', 'CompositorNodeOutputFile'):
            output_node = node
            break
    if not output_node:
        return False
    
    ##Handle rerout
    out_socket = None
    if output_node.inputs[0].is_linked:
        out_link = output_node.inputs[0].links[0]
        out_socket = out_link.to_socket
        if out_link.from_node.bl_idname == 'NodeReroute':
            output_node = out_link.from_node
            out_socket = output_node.inputs[0]

    dof_node.location = (output_node.location.x - 165, output_node.location.y + 35)
    
    ##Connect dof node to output
    if not out_socket or len(out_socket.links) < 1: return False

    ## Depth -> DOF
    rndr_layers = nodes.get("Render Layers")
    if rndr_layers and rndr_layers.outputs.get("Depth"):
        links.new(rndr_layers.outputs.get("Depth"), dof_node.inputs[1])
    
    ## Source -> DOF
    source_node = out_socket.links[0].from_node
    source_socket = out_socket.links[0].from_socket

    if source_node != dof_node: #Prevents loop
        node_tree.links.remove(out_socket.links[0]) #Unlink source from output
        links.new(source_socket, dof_node.inputs[0]) #Link source to DOF

    ## DOF -> Output
    links.new(dof_node.outputs[0], out_socket)

    return True

def setup_dof_drivers(dof_node:bpy.types.CompositorNode, camera:bpy.types.Object, dof_obj:bpy.types.Object) -> None:
    def set_driver(driver:bpy.types.Driver, target_obj:bpy.types.Object, transform_type:str, transform_space:str):
        driver.type = 'AVERAGE'
        var:bpy.types.DriverVariable = driver.variables.new()
        var.name = "var"
        var.targets[0].id = target_obj
        var.type = 'TRANSFORMS'
        var.targets[0].transform_type = transform_type
        var.targets[0].transform_space = transform_space

    ##Vector drivers
    for offset, obj in ((0, camera), (1, dof_obj)):
        for i, axis in enumerate(("X", "Y", "Z")):
            dof_node.inputs[2 + offset].driver_remove("default_value", i)
            driver = dof_node.inputs[2 + offset].driver_add("default_value", i).driver   #i would be the index of the vector thingy
            set_driver(driver, obj, 'LOC_' + axis, 'WORLD_SPACE')

    # Focus > Fuzzin > Ratio > Enable
    for i, prop in enumerate(('SCALE_X', 'ROT_X', 'ROT_Y', 'ROT_Z')):
        dof_node.inputs[4 + i].driver_remove("default_value")
        driver = dof_node.inputs[4 + i].driver_add("default_value").driver
        set_driver(driver, dof_obj, prop, 'LOCAL_SPACE')
 
    #Enable is a scripted expression
    driver.type = 'SCRIPTED'
    driver.expression = "var > 0.01"

    return