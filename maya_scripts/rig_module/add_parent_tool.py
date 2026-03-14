import pymel.core as pm
from maya_scripts import registry
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.utilities import TextFieldHelper, CompoundFieldSlot, get_module_from_group


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

            parent_name = child_module.module_name
            parent_input_module, parentGuide_input_module = child_module.addParent(parent_name=parent_name)

            pm.connectAttr(self.parent_output.obj.offsetParentMatrix, parent_input_module.offsetParentMatrix)
            pm.connectAttr(self.parentGuide_output.offsetParentMatrix, parentGuide_input_module.offsetParentMatrix)

        except Exception as e:
            pm.error("Add Parent Error: ", e)


class Mirror:
    def __init__(self):
        self.win_id = "fxs_mirror_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Mirror Selected Module") as win:
            with pm.columnLayout(adj=True):
                self.module = TextFieldHelper("Module: ")
                self.mirror_axis = CompoundFieldSlot("Axis (1 for mirroring, 0 for not): ")
                pm.text("Select the corresponding SETUP node and fill out the Axis")

                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)
    
    def execute(self):
        module = get_module_from_group(self.module.obj)

        try:
            module.mirror(axis=list(self.mirror_axis))
        except Exception as e:
            pm.error("Mirror Error: ", e)


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

    def execute(self):
        module = get_module_from_group(self.module.obj)

        try:
            module.del_module()
        except Exception as e:
            pm.error("Delete Module Error: ", e)


class ClearRegistry:
    def __init__(self):
        self.win_id = "fxs_clear_registry_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Clear Registry") as win:
            with pm.horizontalLayout():
                pm.button(label="Clear Rigging Module Registry", command=self.execute)

    def execute(self):
        try:
            registry.remove_all()
        except Exception as e:
            pm.error("Clear Registry Error: ", e)

"""def get_module_from_selection():
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
    print(e)"""