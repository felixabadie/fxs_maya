import pymel.core as pm
from maya_scripts.rig_module.additional_files import registry
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.rig_module.additional_files.utilities import TextFieldHelper, CompoundFieldSlot, get_module_from_group, get_mirror_output


class AddParent:
    def __init__(self):
        self.win_id = "fxs_add_parent_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Add Parent Module") as win:
            with pm.columnLayout(adj=True):
                self.parent = TextFieldHelper("Parent: ")
                self.child = TextFieldHelper("Child: ")
                self.parent_output = TextFieldHelper("Parent output: ")
                self.parentGuide_output = TextFieldHelper("ParentGuide output: ")

                pm.text(label="Select the corresponding SETUP node")

                with pm.horizontalLayout():
                        pm.button(label="Cancel")
                        pm.button(label="OK", command=self.execute)

    def execute(self, *args):
        
        parent_module = get_module_from_group(self.parent.obj)
        child_module = get_module_from_group(self.child.obj)

        try:

            parent_name = parent_module.module_name
            parent_input_module, parentGuide_input_module = child_module.addParent(parent_name=parent_name)

            pm.connectAttr(self.parent_output.obj.offsetParentMatrix, parent_input_module.offsetParentMatrix)
            pm.connectAttr(self.parentGuide_output.obj.offsetParentMatrix, parentGuide_input_module.offsetParentMatrix)

        except Exception as e:
            import traceback
            traceback.print_exc()
            pm.error("Add Parent Error: ", e)


class Mirror:
    def __init__(self):
        self.win_id = "fxs_mirror_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Mirror Selected Module") as win:
            with pm.columnLayout(adj=True):
                self.module = TextFieldHelper("Module: ")
                self.mirror_parent = TextFieldHelper("Mirror Parent: ")
                self.mirror_parentGuide = TextFieldHelper("Mirror Parent Guide: ")
                self.mirror_name = TextFieldHelper("New Module Name: ")
                pm.text(label="Check the Axis to mirror: ")
                self.mirror_axis = pm.checkBoxGrp(numberOfCheckBoxes=3, label="X", label2="Y", label3="Z")
                pm.text("Select the corresponding SETUP node and fill out the Axis")

                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)
    
    def execute(self, *args):
        module = get_module_from_group(self.module.obj)

        mirror_name = self.mirror_name.control.getText()

        try:
            # Zuerst upstream Nodes holen und validieren
            """parent_inputs = module.out_parent_input.node.attr("offsetParentMatrix").inputs()
            parentGuide_inputs = module.out_parentGuide_input.node.attr("offsetParentMatrix").inputs()

            if not parent_inputs:
                pm.error(f"No upstream connection found on parent_input")
            if not parentGuide_inputs:
                pm.error(f"No upstream connection found on parentGuide_input")

            mirror_parent      = parent_inputs[0]
            mirror_parentGuide = parentGuide_inputs[0]"""

            mirror_value1 = pm.checkBoxGrp(self.mirror_axis, query=True, value1=True)
            mirror_value2 = pm.checkBoxGrp(self.mirror_axis, query=True, value2=True)
            mirror_value3 = pm.checkBoxGrp(self.mirror_axis, query=True, value3=True)

            # Mirror Modul erstellen
            mirror_module = module.mirror(
                    name = mirror_name,
                    axis=[
                        mirror_value1,
                        mirror_value2,
                        mirror_value3
                    ]
                )

            """if mirror_module is None:
                pm.error("mirror() returned None")"""

            # Parent verbinden
            pm.connectAttr(self.mirror_parent.obj.offsetParentMatrix, mirror_module.out_parent_input.offsetParentMatrix)
            pm.connectAttr(self.mirror_parentGuide.obj.offsetParentMatrix, mirror_module.out_parentGuide_input.offsetParentMatrix)

        except Exception as e:
            pm.error(f"Mirror Error: {e}")



class Delete:
    def __init__(self):
        self.win_id = "fxs_delete_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Delete Module") as win:
            with pm.columnLayout(adj=True):
                self.module = TextFieldHelper("Module: ")
                pm.text("Select Module to delete")

                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self, *args):
        module = get_module_from_group(self.module.obj)

        try:
            module.del_module()
        except Exception as e:
            print("Delete Module Error: ", e)


class ClearRegistry:
    def __init__(self):
        self.win_id = "fxs_clear_registry_win"

        pm.warning("Clearing Registry probably not reversable!")

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Clear Registry") as win:
            with pm.horizontalLayout():
                pm.button(label="Clear Rigging Module Registry", command=self.execute)

    def execute(self, *args):
        try:
            registry.remove_all()
        except Exception as e:
            pm.error("Clear Registry Error: ", e)


class GetRegistry:
    def __init__(self):
        self.win_id = "fxs_get_registry_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Get Current Registry") as win:
            with pm.horizontalLayout():
                pm.button(label="Get Current Rigging Module Registry", command=self.execute)

    def execute(self, *args):
        try:
            reg = registry.get_all()
            print("Current Directory: ", reg)
        except Exception as e:
            pm.error("GetRegestry Error: ", e)



"""import pymel.core as pm
from maya_scripts import registry

def get_module_from_selection():
    selection = pm.selected()
    for node in selection:
        current = node
        while current:
            if current.hasAttr("moduleRegistryKey"):
                key = current.moduleRegistryKey.get()
                return registry.get(key)
            
            
module = get_module_from_selection()

try:
    module.mirror()
except Exception as e:
    print(e)
"""
#maya_scripts.rig_module.clavicle.ClavicleModule object at 0x000001C2A14E0510

#Object <maya_scripts.prox_node_setup.generated_nodes.transform object at 0x000001C1BF14D190> is invalid