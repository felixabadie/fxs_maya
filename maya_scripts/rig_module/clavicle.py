import json
from maya_scripts import control
import pymel.core as pm
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.utilities import (
    create_guide, 
    create_groups,
    create_fourByFourMatrix, 
    remove_main_scale, 
    create_pom, 
    TextFieldHelper,
    CompoundFieldSlot
)

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
right_fk_color = [1, 0, 0]
left_ik_color = [0, 0.85, 0.83]
left_fk_color = [0, 0, 1]
right_ik_color = [1, 0.6, 0]

class ClavivleManager:
    def __init__(self):
        self.win_id = "fxs_clavicle_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Clavicle Riggig Module") as win:
            with pm.columnLayout(adj=True):
                self.name = TextFieldHelper("Clavivle / Leg-start name: ")
                self.limb_side = TextFieldHelper("Limb side ('L' or 'R'): ")
                self.parent_output = TextFieldHelper("Parent Output Group: ")
                self.parent_outputGuide = TextFieldHelper("Parent Output Guide: ")
                self.start_guide_pos = CompoundFieldSlot("Start position: ")
                self.end_guide_pos = CompoundFieldSlot("End position: ")
                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)
    
    def execute(self, *args):
        
        name = str(self.name)
        limb_side = str(self.limb_side)
        parent_output = str(self.parent_output)
        parent_outputGuide = str(self.parent_outputGuide)

        if limb_side == "L":
            clavicle_ctrl_color = left_fk_color
        elif limb_side == "R":
            clavicle_ctrl_color = right_fk_color
        else:
            print("Problem with clavicle limb side")

        guide_positions = {
            "start_guide_pos": self.start_guide_pos,
            "end_guide_pos": self.end_guide_pos
        }

        resolved_positions = {}

        for attr_name, slot in guide_positions.items():
            values = slot.get_values()
            if all(v is not None and v != 0.0 for v in values):
                resolved_positions[attr_name] = values
            else:
                pm.warning(f"{attr_name} contains nonvalid values")
                resolved_positions[attr_name] = None

        kwargs = {"limb_type": name, "limb_side": limb_side, "clavicle_ctrl_color": clavicle_ctrl_color}
        for attr_name, value in resolved_positions.items():
            if value is not None:
                kwargs[attr_name] = value
        
        self.module = ClavicleModule(**kwargs)

        try:
            pm.connectAttr(f"{parent_output}.offsetParentMatrix", f"{self.module.out_parent_input}.offsetParentMatrix")
            pm.connectAttr(f"{parent_outputGuide}.offsetParentMatrix", f"{self.module.out_parentGuide_input}.offsetParentMatrix")
        except:
            print("Parent Module connection not possible, manual connection requiered")


class ClavicleModule:
    def __init__(self, parent_module:str , limb_type:str, limb_side:str, start_guide_pos:tuple = (2, 24, 1), end_guide_pos:tuple = (3, 26, 0), clavicle_ctrl_color:list = [0, 0, 0]):

        """
        Creates clavicle rigging module
        
        :param self: Description
        :param parent_module: Description
        :type parent_module: str
        :param limb_type: Description
        :type limb_type: str
        :param limb_side: Description
        :type limb_side: str
        :param start_guide_pos: Description
        :type start_guide_pos: tuple
        :param end_guide_pos: Description
        :type end_guide_pos: tuple
        :param clavicle_ctrl_color: Description
        :type clavicle_ctrl_color: list
        """

        self.name = f"{limb_type}_{limb_side}"
        self.limb_type = limb_type
        self.limb_side = limb_side

        groups = create_groups(rig_module_name=self.name)
        self.groups = groups

        start_guide = create_guide(name=f"{self.name}_start_guide", position=start_guide_pos, color=guide_color)
        end_guide = create_guide(name=f"{self.name}_end_guide", position=end_guide_pos, color=guide_color)

        self.parent_input = transform(name=f"{self.name}_{parent_module}_input")
        self.parentGuide_input = transform(name=f"{self.name}_{parent_module}Guide_input")

        self.end_output = transform(name=f"{self.name}_self.end_output")
        self.endGuide_output = transform(name=f"{self.name}_self.endGuide_output")

        start_guide_orientedM = aimMatrix(name=f"{self.name}_start_guide_orientedM")
        pm.connectAttr(start_guide.worldMatrix[0], start_guide_orientedM.inputMatrix)
        pm.connectAttr(end_guide.worldMatrix[0], start_guide_orientedM.primaryTargetMatrix)
        start_guide_orientedM.secondaryMode.set(2)
        start_guide_orientedM.secondaryTargetVector.set(0, 0, -1)

        module_POM = create_pom(module_name=self.name, name="module_POM", source_matrix = end_guide.worldMatrix[0], parentGuide_input = self.parentGuide_input.worldInverseMatrix[0])

        start_POM = create_pom(module_name=self.name, name="start_POM", source_matrix = start_guide_orientedM.outputMatrix, parentGuide_input = self.parentGuide_input.worldInverseMatrix[0])

        ctrl_WM = multMatrix(name=f"{self.name}_ctrl_WM")
        pm.connectAttr(module_POM.matrixSum, ctrl_WM.matrixIn[0])
        pm.connectAttr(self.parent_input.worldMatrix[0], ctrl_WM.matrixIn[1])

        start_baseWM = multMatrix(name=f"{self.name}_start_baseWM")
        pm.connectAttr(start_POM.matrixSum, start_baseWM.matrixIn[0])
        pm.connectAttr(self.parent_input.worldMatrix[0], start_baseWM.matrixIn[1])

        ctrl = control.create(ctrl_type="fourArrows", name=f"{self.name}_ctrl", normal=(1, 0, 0), color=clavicle_ctrl_color)
        pm.connectAttr(ctrl_WM.matrixSum, ctrl.offsetParentMatrix)
        ctrl.node.addAttr(attr="lockLength", niceName="Lock Length", attributeType="float", minValue=0, maxValue=1, defaultValue=0, hidden=False, keyable=True)

        start_WM = aimMatrix(name=f"{self.name}_startWM")
        pm.connectAttr(start_baseWM.matrixSum, start_WM.inputMatrix)
        pm.connectAttr(ctrl.worldMatrix[0], start_WM.primaryTargetMatrix)

        start_WM_noMainScale = remove_main_scale(module_name=self.name, name="start_WM_noMainScale", world_matrix=start_WM.outputMatrix, main_input=self.parent_input.worldInverseMatrix[0])

        ctrl_noMainScale = remove_main_scale(module_name=self.name, name="ctrl_noMainScale", world_matrix=ctrl.worldMatrix[0], main_input=self.parent_input.worldInverseMatrix[0])

        currentLength = distanceBetween(name=f"{self.name}_currentLength")
        pm.connectAttr(start_WM_noMainScale.matrixSum, currentLength.inMatrix1)
        pm.connectAttr(ctrl_noMainScale.matrixSum, currentLength.inMatrix2)

        originalLength = distanceBetween(name=f"{self.name}_originalLength")
        pm.connectAttr(start_guide.worldMatrix[0], originalLength.inMatrix1)
        pm.connectAttr(end_guide.worldMatrix[0], originalLength.inMatrix2)

        end_localTx = blendTwoAttr(name=f"{self.name}_end_localTx")
        pm.connectAttr(ctrl.node.lockLength, end_localTx.attributesBlender)
        pm.connectAttr(currentLength.distance, end_localTx.input_[0])
        pm.connectAttr(originalLength.distance, end_localTx.input_[1])

        end_localM = create_fourByFourMatrix(
            module_name=self.name,
            name="end_localM",
            inputs=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [end_localTx.output, 0, 0, 1]]
        )

        end_WM = multMatrix(name=f"{self.name}_end_WM")
        pm.connectAttr(end_localM.output, end_WM.matrixIn[0])
        pm.connectAttr(start_WM.outputMatrix, end_WM.matrixIn[1])

        start_guide_orientedRotationM = pickMatrix(name=f"{self.name}_start_guide_orientedRotationM")
        pm.connectAttr(start_guide_orientedM.outputMatrix, start_guide_orientedRotationM.inputMatrix)
        start_guide_orientedRotationM.useTranslate.set(0)

        start_guide_posWM = create_fourByFourMatrix(
            module_name=self.name,
            name="start_guide_posWM",
            inputs=[
                [0],
                [0, 0],
                [0, 0, 0],
                [end_guide.translateX, end_guide.translateY, end_guide.translateZ]
            ]
        )

        self.endGuide_output_WM = addMatrix(name=f"{self.name}_self.endGuide_output_WM")
        pm.connectAttr(start_guide_orientedRotationM.outputMatrix, self.endGuide_output_WM.matrixIn[0])
        pm.connectAttr(start_guide_posWM.output, self.endGuide_output_WM.matrixIn[1])

        start_jnt = joint(name=f"{self.name}_start_jnt")
        pm.connectAttr(start_WM.outputMatrix, start_jnt.offsetParentMatrix)

        end_jnt = joint(name=f"{self.name}_end_jnt")
        pm.connectAttr(end_WM.matrixSum, end_jnt.offsetParentMatrix)

        pm.connectAttr(end_WM.matrixSum, self.end_output.offsetParentMatrix)
        pm.connectAttr(self.endGuide_output_WM.matrixSum, self.endGuide_output.offsetParentMatrix)

        outliner_data = {
            "inputs": [self.parent_input, self.parentGuide_input],
            "guides": [start_guide, end_guide],
            "controls": [ctrl],
            "helpers": [],
            "joints": [start_jnt, end_jnt],
            "rigNodes": [],
            "outputs": [self.end_output, self.endGuide_output]
        }

        for group_name, nodes in outliner_data.items():
            try:
                for node in nodes:
                    try:
                        pm.parent(node.node, self.groups[group_name].node)
                    except:
                        pm.parent(node, self.groups[group_name].node)
            except:
                pass

    
    @property
    def rig_module(self):
        return self.groups
    
    @property
    def module_name(self):
        return str(self.groups)
    
    @property
    def out_parent_input(self):
        return self.parent_input

    @property
    def out_parentGuide_input(self):
        return self.parentGuide_input
    
    @property
    def out_end_output(self):
        return self.end_output

    @property
    def out_endGuide_output(self):
        return self.endGuide_output