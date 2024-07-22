bl_info = {
    "name": "IFC Property and Quantity Lister",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
import ifcopenshell
from blenderbim.bim.ifc import IfcStore


class PsetQsetDetailItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.StringProperty(name="Value")


class PsetQsetItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    details: bpy.props.CollectionProperty(type=PsetQsetDetailItem)  # CollectionProperty to hold details


class IFC_UL_PsetQsetList(bpy.types.UIList):
    """UIList to display property sets and quantity sets"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name)


class IFC_PT_PsetQsetListerPanel(bpy.types.Panel):
    bl_label = "IFC Property and Quantity Lister"
    bl_idname = "IFC_PT_PsetQsetListerPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IFC Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("ifc.list_psets_qsets")

        layout.label(text="Property Sets and Quantity Sets:")
        row = layout.row()
        row.template_list("IFC_UL_PsetQsetList", "PsetsQsets", scene, "pset_qset_list", scene, "pset_qset_list_index")

        layout.label(text="Details:")
        if scene.pset_qset_list_index >= 0 and scene.pset_qset_list:
            item = scene.pset_qset_list[scene.pset_qset_list_index]
            box = layout.box()
            box.label(text=item.name)

            for detail_item in item.details:
                # Display only the name part before ":"
                detail_name = detail_item.name.split(':')[0]
                row = box.row()
                row.label(text=f"{detail_name}")
                # Add a button to generate and copy the text string
                row.operator("ifc.copy_detail_string", text="Copy").detail_index = item.details.find(detail_item.name)


class IFC_OT_ListPsetsQsets(bpy.types.Operator):
    bl_idname = "ifc.list_psets_qsets"
    bl_label = "List Psets and Qsets"

    def execute(self, context):
        ifc_file_path = IfcStore.path
        if ifc_file_path:
            psets, qsets = self.list_psets_and_qsets(ifc_file_path)
            scene = context.scene
            scene.pset_qset_list.clear()

            # Clear existing detail collections
            for pset_item in scene.pset_qset_list:
                pset_item.details.clear()

            for pset, properties in psets.items():
                item = scene.pset_qset_list.add()
                item.name = pset
                # Add details to the PsetQsetItem
                for prop_name, prop_value in properties.items():
                    detail_item = item.details.add()
                    detail_item.name = prop_name
                    detail_item.value = str(prop_value)  # Ensure value is a string

            for qset in qsets:
                item = scene.pset_qset_list.add()
                item.name = qset

            self.report({'INFO'}, "Property sets and quantity sets listed.")
        else:
            self.report({'ERROR'}, "No IFC file is open in Blender.")
        return {'FINISHED'}

    def list_psets_and_qsets(self, file_path):
        ifc_file = ifcopenshell.open(file_path)
        psets = {}
        qsets = set()

        for entity in ifc_file.by_type('IfcProduct'):
            pset_attributes = ifcopenshell.util.element.get_psets(entity)
            if pset_attributes:
                for pset_name, attributes in pset_attributes.items():
                    if pset_name not in psets:
                        psets[pset_name] = {}
                    psets[pset_name].update(attributes)
            for definition in entity.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_set = definition.RelatingPropertyDefinition
                    if prop_set.is_a('IfcElementQuantity'):
                        qsets.add(prop_set.Name)

        return psets, list(qsets)


class IFC_OT_CopyDetailString(bpy.types.Operator):
    bl_idname = "ifc.copy_detail_string"
    bl_label = "Copy Detail String"
    
    detail_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        selected_item = scene.pset_qset_list[scene.pset_qset_list_index]
        if self.detail_index >= 0 and self.detail_index < len(selected_item.details):
            detail_item = selected_item.details[self.detail_index]
            # Generate text string only with the part before ':'
            detail_name = detail_item.name.split(':')[0]
            text_to_copy = f"{selected_item.name}.{detail_name}"
            bpy.context.window_manager.clipboard = text_to_copy
            self.report({'INFO'}, f"Copied to clipboard: {text_to_copy}")
        else:
            self.report({'ERROR'}, "Detail index out of range.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PsetQsetDetailItem)
    bpy.utils.register_class(PsetQsetItem)
    bpy.utils.register_class(IFC_UL_PsetQsetList)
    bpy.utils.register_class(IFC_PT_PsetQsetListerPanel)
    bpy.utils.register_class(IFC_OT_ListPsetsQsets)
    bpy.utils.register_class(IFC_OT_CopyDetailString)

    bpy.types.Scene.pset_qset_list = bpy.props.CollectionProperty(type=PsetQsetItem)
    bpy.types.Scene.pset_qset_list_index = bpy.props.IntProperty(name="Index for PsetQset List", default=0)


def unregister():
    bpy.utils.unregister_class(PsetQsetDetailItem)
    bpy.utils.unregister_class(PsetQsetItem)
    bpy.utils.unregister_class(IFC_UL_PsetQsetList)
    bpy.utils.unregister_class(IFC_PT_PsetQsetListerPanel)
    bpy.utils.unregister_class(IFC_OT_ListPsetsQsets)
    bpy.utils.unregister_class(IFC_OT_CopyDetailString)

    del bpy.types.Scene.pset_qset_list
    del bpy.types.Scene.pset_qset_list_index


if __name__ == "__main__":
    register()
