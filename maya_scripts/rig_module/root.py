import pymel.core as pm
from maya_scripts import control
from prox_node_setup.generated_nodes import *
from utilities import create_groups, create_guide, colorize, TextFieldHelper, CompoundFieldSlot

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
                self.name = pm.textField(text="Enter Name", editable=True)
                self.ctrl_size = pm.floatField(value=0.0, editable=True)
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self):
        
        module = RootModule(name=self.name, ctrl_size=self.ctrl_size)

class RootModule:
    def __init__(self, name:str, ctrl_size:int):
        
        self.name = name
        self.groups = create_groups(rig_module_name=self.name)

        root_guide = create_guide(name=f"{self.name}_guide", color=guide_color)

        root_god_ctrl = control.create_circle_ctrl(name=f"{self.name}_god_ctrl", ctrl_size=ctrl_size, color=god_color)
        root_demigod_ctrl = control.create_circle_ctrl(name=f"{self.name}_demigod_ctrl", ctrl_size=ctrl_size-1, color=demigod_color)
        root_main_ctrl = control.create_circle_ctrl(name=f"{self.name}_main_ctrl", ctrl_size=ctrl_size-2, color=main_color)

        pm.connectAttr(root_guide.worldMatrix[0], root_god_ctrl.offsetParentMatrix)
        pm.connectAttr(root_god_ctrl.worldMatrix[0], root_demigod_ctrl.offsetParentMatrix)
        pm.connectAttr(root_demigod_ctrl.worldMatrix[0], root_main_ctrl.offsetParentMatrix)

        root_main_output = transform(name=f"{self.name}_main_output")
        root_mainGuide_output = transform(name=f"{self.name}_mainGuide_ouput")

        pm.connectAttr(root_main_ctrl.worldMatrix[0], root_main_output.offsetParentMatrix)
        pm.connectAttr(root_guide.worldMatrix[0], root_mainGuide_output.offsetParentMatrix)

        outliner_data = {
            "guides": [root_guide],
            "controls": [root_god_ctrl, root_demigod_ctrl, root_main_ctrl],
            "outputs": [root_main_output, root_mainGuide_output]
        }

        for group_name, nodes in outliner_data.items():
            for node in nodes:
                try:
                    pm.parent(node.node, self.groups[group_name].name)
                except:
                    pm.parent(node, self.groups[group_name].name)
    

    @property
    def rig_module(self):
        return self.groups

    @property
    def module_name(self):
        return str(self.groups)