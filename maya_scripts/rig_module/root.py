import pymel.core as pm
from maya_scripts import control
from maya_scripts import registry
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.utilities import create_groups, create_guide, TextFieldHelper

guide_color = (1, 1, 1)
god_color = (1, 0, 1)
demigod_color = (0.7, 0, 0.7)
main_color = (0.4, 0, 0.4)

class RootManager:
    def __init__(self):
        
        self.win_id = "fxs_root_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Root Rigging Module") as win:
            with pm.columnLayout(adj=True):
                self.name = TextFieldHelper("Enter Name: ")
                self.ctrl_size = pm.floatFieldGrp(label="Control Size", numberOfFields=1, value1=0.0)
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self, *args):
        
        try:
            name = self.name.control.getText()
        except AttributeError:
            name = "root"
        ctrl_size = pm.floatFieldGrp(self.ctrl_size, query=True, value1=True)

        module = RootModule(name=name, ctrl_size=ctrl_size)

class RootModule:
    def __init__(self, name:str, ctrl_size:int):
        
        self.name = name
        self.groups = create_groups(rig_module_name=self.name)

        registry.register(self.name, self)
        root_node = self.groups["SETUP"].node
        if not root_node.hasAttribute("moduleRegistryKey"):
            root_node.addAttr(attr="moduleRegistryKey", dataType="string", hidden=False, keyable=True)
        root_node.moduleRegistryKey.set(self.name)

        root_guide = create_guide(name=f"{self.name}_guide", color=guide_color)

        root_god_ctrl = control.create_circle_ctrl(name=f"{self.name}_god_ctrl", ctrl_size=ctrl_size, normal=(0, 1, 0), color=god_color)
        root_demigod_ctrl = control.create_circle_ctrl(name=f"{self.name}_demigod_ctrl", ctrl_size=ctrl_size-1, normal=(0, 1, 0), color=demigod_color)
        root_main_ctrl = control.create_circle_ctrl(name=f"{self.name}_main_ctrl", ctrl_size=ctrl_size-2, normal=(0, 1, 0), color=main_color)

        pm.connectAttr(root_guide.worldMatrix[0], root_god_ctrl.offsetParentMatrix)
        pm.connectAttr(root_god_ctrl.worldMatrix[0], root_demigod_ctrl.offsetParentMatrix)
        pm.connectAttr(root_demigod_ctrl.worldMatrix[0], root_main_ctrl.offsetParentMatrix)

        self.root_main_output = transform(name=f"{self.name}_main_output")
        self.root_mainGuide_output = transform(name=f"{self.name}_mainGuide_ouput")

        pm.connectAttr(root_main_ctrl.worldMatrix[0], self.root_main_output.offsetParentMatrix)
        pm.connectAttr(root_guide.worldMatrix[0], self.root_mainGuide_output.offsetParentMatrix)

        outliner_data = {
            "guides": [root_guide],
            "controls": [root_god_ctrl, root_demigod_ctrl, root_main_ctrl],
            "outputs": [self.root_main_output, self.root_mainGuide_output]
        }

        for group_name, nodes in outliner_data.items():
            for node in nodes:
                try:
                    pm.parent(node.node, self.groups[group_name].node)
                except:
                    pm.parent(node, self.groups[group_name].node)
    
    def del_module(self):
        """Remove registry entry and delete self"""
        registry.remove_module(self.name)
        pm.delete(self.groups)

    @property
    def rig_module(self):
        return self.groups

    @property
    def module_name(self):
        return self.name
    
    @property
    def out_main_output(self):
      return self.root_main_output

    @property
    def out_mainGuide_output(self):
        return self.root_mainGuide_output