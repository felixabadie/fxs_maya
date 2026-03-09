import json
from maya_scripts import control
import pymel.core as pm
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.utilities import (
    create_guide, 
    create_groups,
    create_ik_fk_blend, 
    setup_visibility_controls, 
    setup_ribbon_system, 
    rebuild_nurbsPlane, 
    add_pin_joints, 
    extract_matrix_axes, 
    create_fourByFourMatrix, 
    remove_main_scale, 
    create_pom, 
    lock_ctrl_attrs, 
    create_ik_solver_setup
)

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]

class Clavicle:
    def __init__(self, parent_module:str , limb_type:str, limb_side:str, start_guide_pos:tuple = (0, 0, 0), end_guide_pos:tuple = (0, 0, 0), clavicle_ctrl_color:list = [0, 0, 0]):

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

        parent_input = transform(name=f"{self.name}_{parent_module}_input")
        parentGuide_input = transform(name=f"{self.name}_{parent_module}Guide_input")

        end_output = transform(name=f"{self.name}_end_output")
        endGuide_output = transform(name=f"{self.name}_endGuide_output")

        start_guide_orientedM = aimMatrix(name=f"{self.name}_start_guide_orientedM")
        pm.connectAttr(start_guide.worldMatrix[0], start_guide_orientedM.inputMatrix)
        pm.connectAttr(end_guide.worldMatrix[0], start_guide_orientedM.primaryTargetMatrix)
        start_guide_orientedM.secondaryMode.set(2)
        start_guide_orientedM.secondaryTargetVector.set(0, 0, -1)

        module_POM = create_pom(module_name=self.name, name="module_POM", source_matrix = end_guide.worldMatrix[0], parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        start_POM = create_pom(module_name=self.name, name="start_POM", source_matrix = start_guide_orientedM.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        ctrl_WM = multMatrix(name=f"{self.name}_ctrl_WM")
        pm.connectAttr(module_POM.matrixSum, ctrl_WM.matrixIn[0])
        pm.connectAttr(parent_input.worldMatrix[0], ctrl_WM.matrixIn[1])

        start_baseWM = multMatrix(name=f"{self.name}_start_baseWM")
        pm.connectAttr(start_POM.matrixSum, start_baseWM.matrixIn[0])
        pm.connectAttr(parent_input.worldMatrix[0], start_baseWM.matrixIn[1])

        ctrl = control.create(ctrl_type="fourArrows", name=f"{self.name}_ctrl", normal=(1, 0, 0), color=clavicle_ctrl_color)
        pm.connectAttr(ctrl_WM.matrixSum, ctrl.offsetParentMatrix)
        ctrl.node.addAttr(attr="lockLength", niceName="Lock Length", attributeType="float", minValue=0, maxValue=1, defaultValue=0, hidden=False, keyable=True)

        start_WM = aimMatrix(name=f"{self.name}_startWM")
        pm.connectAttr(start_baseWM.matrixSum, start_WM.inputMatrix)
        pm.connectAttr(ctrl.worldMatrix[0], start_WM.primaryTargetMatrix)

        start_WM_noMainScale = remove_main_scale(module_name=self.name, name="start_WM_noMainScale", world_matrix=start_WM.outputMatrix, main_input=parent_input.worldInverseMatrix[0])

        ctrl_noMainScale = remove_main_scale(module_name=self.name, name="ctrl_noMainScale", world_matrix=ctrl.worldMatrix[0], main_input=parent_input.worldInverseMatrix[0])

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

        endGuide_output_WM = addMatrix(name=f"{self.name}_endGuide_output_WM")
        pm.connectAttr(start_guide_orientedRotationM.outputMatrix, endGuide_output_WM.matrixIn[0])
        pm.connectAttr(start_guide_posWM.output, endGuide_output_WM.matrixIn[1])

        start_jnt = joint(name=f"{self.name}_start_jnt")
        pm.connectAttr(start_WM.outputMatrix, start_jnt.offsetParentMatrix)

        end_jnt = joint(name=f"{self.name}_end_jnt")
        pm.connectAttr(end_WM.matrixSum, end_jnt.offsetParentMatrix)

        pm.connectAttr(end_WM.matrixSum, end_output.offsetParentMatrix)
        pm.connectAttr(endGuide_output_WM.matrixSum, endGuide_output.offsetParentMatrix)

        outliner_data = {
            "inputs": [parent_input, parentGuide_input],
            "guides": [start_guide, end_guide],
            "controls": [ctrl],
            "helpers": [],
            "joints": [start_jnt, end_jnt],
            "rigNodes": [],
            "outputs": [end_output, endGuide_output]
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

#b = Clavicle(parent_module="root", limb_type="clavicle", limb_side="L", start_guide_pos=(1, 8, 0), end_guide_pos=(2, 9, 0), clavicle_ctrl_color=[0, 0, 1])