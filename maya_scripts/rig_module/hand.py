import json

import pdb

import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from utilities import create_guide, colorize, create_groups, add_pins_to_ribbon, add_pins_to_ribbon_uv, create_groups_

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
right_fk_color = [1, 0, 0]
left_ik_color = [0, 0.85, 0.83]
left_fk_color = [0, 0, 1]
right_ik_color = [1, 0.6, 0]


"""
Todo:

ik solver
check hierarchy of guides
ik fk switch
result joints

"""


class Hand():

    def __init__(self, main_module:str, parent_module:str, limb_side:str, number_fingers:int, hand_base_guide_pos:tuple = (0, 0, 0)):
        pass


class Finger():

    def __init__(self, hand_name:str, finger_name:str, parent_module:str, metacarpal_guide_pos:tuple = (0, 0, 0), prox_phalange_guide_pos:tuple = (0, 0, 0), middle_phalange_guide_pos:tuple = (0, 0, 0), 
                 distal_phalange_guide_pos:tuple = (0, 0, 0), finger_end_guide_pos:tuple = (0, 0, 0), fk_color:list = [0, 0, 0], ik_color:list = [0, 0, 0]):
        
        self.name = f"{hand_name}_{finger_name}"

        parent_module_input = transform(name=f"{self.name}_{parent_module}_input")
        parent_moduleGuide_input = transform(name=f"{self.name}_{parent_module}Guide_input")

        metacarpal_guide = create_guide(name=f"{self.name}_metacarpal_guide", position=metacarpal_guide_pos, color=guide_color)
        prox_phalange_guide = create_guide(name=f"{self.name}_prox_phalange_guide", position=prox_phalange_guide_pos, color=guide_color)
        middle_phalange_guide = create_guide(name=f"{self.name}_middle_phalange_guide", position=middle_phalange_guide_pos, color=guide_color)
        distal_phalange_guide = create_guide(name=f"{self.name}_distal_phalange_guide", position=distal_phalange_guide_pos, color=guide_color)
        finger_end_guide = create_guide(name=f"{self.name}_finger_end_guide", position=finger_end_guide_pos, color=guide_color)

        metacarpal_offset = transform(name=f"{self.name}_metacarpal_offset")
        prox_phalange_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_prox_phalange_FK_ctrl", ctrl_size=1, normal=(1,0,0), color=fk_color)
        middle_phalange_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_middle_phalange_FK_ctrl", ctrl_size=1, normal=(1,0,0), color=fk_color)
        distal_phalange_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_distal_phalange_FK_ctrl", ctrl_size=1, normal=(1,0,0), color=fk_color)
        finger_end_offset = transform(name=f"{self.name}_finger_end_offset")

        finger_IK_ctrl = control.create(ctrl_type="box", degree=1, name=f"{self.name}_finger_IK_ctrl", size=[1, 1, 1], color=ik_color)
        finger_polevector_ctrl = control.create(ctrl_type="pyramid", degree=1, name=f"{self.name}_finger_polevector_ctrl", size=[0.25, 2, 0.25], color=ik_color)
        self._lock_ctrl_attrs(finger_polevector_ctrl, ["translateX", "translateY", "translateZ", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"])

        finger_orientPlane_guide = aimMatrix(name=f"{self.name}_finger_orientPlane_guide")
        pm.connectAttr(prox_phalange_guide.worldMatrix[0], finger_orientPlane_guide.inputMatrix)
        pm.connectAttr(finger_end_guide.worldMatrix[0], finger_orientPlane_guide.primaryTargetMatrix)
        pm.connectAttr(prox_phalange_guide.worldMatrix[0], finger_orientPlane_guide.secondaryTargetMatrix)
        finger_orientPlane_guide.secondaryMode.set(2)
        finger_orientPlane_guide.secondaryTargetVector.set(0, 1, 0)

        guide_WM_dict = {
            "middle_phalange_guide": {
                "WM": "middle_phalange_guide_WM",
                "inputMatrix": finger_orientPlane_guide.outputMatrix,
                "targetMatrix": finger_end_guide.worldMatrix[0],
                "weight": 0.5
            },
            "distal_phalange_guide": {
                "WM": "distal_phalange_guide_WM",
                "inputMatrix": finger_orientPlane_guide.outputMatrix,
                "targetMatrix": finger_end_guide.worldMatrix[0],
                "weight": 0.75
            },
        }

        pm.connectAttr(metacarpal_guide.worldMatrix[0], prox_phalange_guide.offsetParentMatrix)
        pm.connectAttr(prox_phalange_guide.worldMatrix[0], finger_end_guide.offsetParentMatrix)

        for key, items in guide_WM_dict.items():
            bm = blendMatrix(name=f"{self.name}_{items['WM']}")
            pm.connectAttr(items["inputMatrix"], bm.inputMatrix)
            pm.connectAttr(items["targetMatrix"], bm.target[0].targetMatrix)
            bm.target[0].weight.set(items["weight"])
            for attr in ["rotateWeight", "scaleWeight", "shearWeight"]:
                pm.setAttr(f"{bm.target[0]}.{attr}", 0)
            pm.connectAttr(bm.outputMatrix, f"{self.name}_{key}.offsetParentMatrix")

        outWM_collection = {}

        guide_outWM_dict = {
            "metacarpal_guide": {
                "name": "metacarpal_guide_FK_out",
                "inputM": metacarpal_guide.worldMatrix[0],
                "ptm": prox_phalange_guide.worldMatrix[0],
                "stm": metacarpal_guide.worldMatrix[0]
            },
            "prox_phalange_guide": {
                "name": "prox_phalange_guide_FK_out",
                "inputM": prox_phalange_guide.worldMatrix[0],
                "ptm": middle_phalange_guide.worldMatrix[0],
                "stm": metacarpal_guide.worldMatrix[0]
            },
            "middle_phalange_guide": {
                "name": "middle_phalange_guide_FK_out",
                "inputM": middle_phalange_guide.worldMatrix[0],
                "ptm": distal_phalange_guide.worldMatrix[0],
                "stm": metacarpal_guide.worldMatrix[0]
            },
            "distal_phalange_guide": {
                "name": "distal_phalange_guide_FK_out",
                "inputM": distal_phalange_guide.worldMatrix[0],
                "ptm": finger_end_guide.worldMatrix[0],
                "stm": metacarpal_guide.worldMatrix[0]
            }
        }

        for key, items in guide_outWM_dict.items():
            outWM = aimMatrix(name=f"{self.name}_{items['name']}WM")
            pm.connectAttr(items["inputM"], outWM.inputMatrix)
            pm.connectAttr(items["ptm"], outWM.primaryTargetMatrix)
            pm.connectAttr(items["stm"], outWM.secondaryTargetMatrix)
            outWM.secondaryMode.set(2)
            outWM.secondaryTargetVector.set(0, 1, 0)

            outWIM = inverseMatrix(name=f"{self.name}_{items['name']}WIM")
            pm.connectAttr(outWM.outputMatrix, outWIM.inputMatrix)

            local_dict = {
                "outWM": outWM,
                "outWIM": outWIM
            }
            outWM_collection[key] = local_dict

        finger_end_guide_FK_outWM = blendMatrix(name=f"{self.name}_finger_end_guide_FK_outWM")
        pm.connectAttr(outWM_collection["distal_phalange_guide"]["outWM"].outputMatrix, finger_end_guide_FK_outWM.inputMatrix)
        pm.connectAttr(finger_end_guide.worldMatrix[0], finger_end_guide_FK_outWM.target[0].targetMatrix)
        for attr in ["rotateWeight", "rotateWeight", "shearWeight"]:
                pm.setAttr(f"{finger_end_guide_FK_outWM.target[0]}.{attr}", 0)

        finger_hierarchies = {
            "metacarpal_hierarchy":{
                "name": "metacarpal",
                "guide": outWM_collection["metacarpal_guide"]["outWM"].outputMatrix,
                "parent": parent_module_input.worldMatrix[0],
                "parentGuide": parent_moduleGuide_input.worldInverseMatrix[0]
            },
            "prox_phalange_hierarchy": {
                "name": "prox_phalange",
                "guide": outWM_collection["prox_phalange_guide"]["outWM"].outputMatrix,
                "parent": metacarpal_offset.worldMatrix[0],
                "parentGuide": outWM_collection["metacarpal_guide"]["outWIM"].outputMatrix
            },
            "middle_phanlange_hierarchy": {
                "name": "middle_phalange",
                "guide": outWM_collection["middle_phalange_guide"]["outWM"].outputMatrix,
                "parent": prox_phalange_FK_ctrl.worldMatrix[0],
                "parentGuide": outWM_collection["prox_phalange_guide"]["outWIM"].outputMatrix
            },
            "distal_phalange_hierarchy": {
                "name": "distal_phalange",
                "guide": outWM_collection["distal_phalange_guide"]["outWM"].outputMatrix,
                "parent": middle_phalange_FK_ctrl.worldMatrix[0],
                "parentGuide": outWM_collection["middle_phalange_guide"]["outWIM"].outputMatrix
            },
            "finger_end_hierarchy": {
                "name": "finger_end",
                "guide": finger_end_guide_FK_outWM.outputMatrix,
                "parent": distal_phalange_FK_ctrl.worldMatrix[0],
                "parentGuide": outWM_collection["distal_phalange_guide"]["outWIM"].outputMatrix
            }
        }

        finger_hierarchies_collection = {}

        for key, items in finger_hierarchies.items():
            local_hierarchy = self._hierarchy_prep(name=items["name"], guide=items["guide"], parent=items["parent"], parentGuide=items["parentGuide"])
            try:
                pm.connectAttr(f"{local_hierarchy['wm'].node}.matrixSum", f"{self.name}_{items['name']}_FK_ctrl.offsetParentMatrix")    
            except:
                pm.connectAttr(f"{local_hierarchy['wm'].node}.matrixSum", f"{self.name}_{items['name']}_offset.offsetParentMatrix")

            finger_hierarchies_collection[key] = local_hierarchy
        
        finger_IK_ctrl_POM = multMatrix(name=f"{self.name}_finger_IK_ctrl_POM")
        pm.connectAttr(finger_end_guide_FK_outWM.outputMatrix, finger_IK_ctrl_POM.matrixIn[0])
        pm.connectAttr(parent_moduleGuide_input.worldInverseMatrix[0], finger_IK_ctrl_POM.matrixIn[1])

        finger_IK_ctrl_WM = multMatrix(name=f"{self.name}_finger_IK_ctrl_WM")
        pm.connectAttr(finger_IK_ctrl_POM.matrixSum, finger_IK_ctrl_WM.matrixIn[0])
        pm.connectAttr(parent_module_input.worldMatrix[0], finger_IK_ctrl_WM.matrixIn[1])

        pm.connectAttr(finger_IK_ctrl_WM.matrixSum, finger_IK_ctrl.offsetParentMatrix)

        finger_polevector_POM = multMatrix(name=f"{self.name}_finger_polevector_POM")
        pm.connectAttr(finger_orientPlane_guide.outputMatrix, finger_polevector_POM.matrixIn[0])
        pm.connectAttr(parent_moduleGuide_input.worldInverseMatrix[0], finger_polevector_POM.matrixIn[1])

        finger_polevector_baseWM = multMatrix(name=f"{self.name}_finger_polevector_POM")
        pm.connectAttr(finger_polevector_POM.matrixSum, finger_polevector_baseWM.matrixIn[0])
        pm.connectAttr(parent_module_input.worldMatrix[0], finger_polevector_baseWM.matrixIn[1])

        finger_polevector_WM = blendMatrix(name=f"{self.name}_finger_polevector_WM")
        pm.connectAttr(finger_polevector_baseWM.matrixSum, finger_polevector_WM.inputMatrix)
        pm.connectAttr(outWM_collection["prox_phalange_guide"]["outWM"].outputMatrix, finger_polevector_WM.target[0].targetMatrix)
        pm.connectAttr(finger_IK_ctrl.worldMatrix[0], finger_polevector_WM.target[1].targetMatrix)
        finger_polevector_WM.target[1].weight.set(0.5)

        pm.connectAttr(finger_polevector_WM.outputMatrix, finger_polevector_ctrl.offsetParentMatrix)


        #pdb.set_trace()


        metacarpal_IK_jnt = joint(name=f"{self.name}_metacarpal_IK_jnt")
        prox_phalange_IK_jnt = joint(name=f"{self.name}_prox_phalange_IK_jnt")
        middle_phalange_IK_jnt = joint(name=f"{self.name}_middle_phalange_IK_jnt")
        distal_phalange_IK_jnt = joint(name=f"{self.name}_distal_phalange_IK_jnt")
        finger_end_jnt = joint(name=f"{self.name}_finger_end_jnt")

        joint_list = [finger_end_jnt, distal_phalange_IK_jnt, middle_phalange_IK_jnt, prox_phalange_IK_jnt, metacarpal_IK_jnt]

        for jnt in joint_list:
            jnt.preferredAngle.set(0, 0, -10)

        for i in range(len(joint_list)):
            try:
                pm.parent(joint_list[i].node, joint_list[i+1].node)
            except:
                pass

        distance_dict = {}
        
        distance_between_dict = {
            "metacarpal": {
                "input1": metacarpal_guide.worldMatrix[0],
                "input2": prox_phalange_guide.worldMatrix[0]
            },
            "prox_phalange": {
                "input1": prox_phalange_guide.worldMatrix[0],
                "input2": middle_phalange_guide.worldMatrix[0]
            },
            "middle_phalange": {
                "input1": middle_phalange_guide.worldMatrix[0],
                "input2": distal_phalange_guide.worldMatrix[0]
            },
            "distal_phalage": {
                "input1": distal_phalange_guide.worldMatrix[0],
                "input2": finger_end_guide.worldMatrix[0]
            },
            "current_length":  {
                "input1": finger_hierarchies_collection["prox_phalange_hierarchy"]["wm"].matrixSum,
                "input2": finger_IK_ctrl.worldMatrix[0]
            }
        }

        for key, item in distance_between_dict.items():
            distance = distanceBetween(name=f"{self.name}_{key}_initialLength")
            pm.connectAttr(item["input1"], distance.inMatrix1)
            pm.connectAttr(item["input2"], distance.inMatrix2)

            distance_dict[key] = distance

        lenth_list = ['prox_phalange', 'middle_phalange', 'distal_phalage']
        
        finger_initial_length = sum_(name=f"{self.name}_finger_initial_length")
        for length in lenth_list:
            pm.connectAttr(f"{distance_dict[length].node}.distance", finger_initial_length.input_[lenth_list.index(length)])

        finger_lengthRatio = divide(name=f"{self.name}_finger_scaler")
        pm.connectAttr(distance_dict["current_length"].distance, finger_lengthRatio.input1)
        pm.connectAttr(finger_initial_length.output, finger_lengthRatio.input2)

        finger_minRatio = floatConstant(name=f"{self.name}_finger_minRatio")
        finger_minRatio.inFloat.set(1)

        finger_scaler = max_(name=f"{self.name}_finger_lengthClamped")
        pm.connectAttr(finger_lengthRatio.output, finger_scaler.input_[0])
        pm.connectAttr(finger_minRatio.outFloat, finger_scaler.input_[1])

        prox_phalange_length = multiply(name=f"{self.name}_prox_phalange_length")
        pm.connectAttr(distance_dict["prox_phalange"].distance, prox_phalange_length.input_[0])
        pm.connectAttr(finger_scaler.output, prox_phalange_length.input_[1])

        middle_phalange_length = multiply(name=f"{self.name}_middle_phalange_length")
        pm.connectAttr(distance_dict["middle_phalange"].distance, middle_phalange_length.input_[0])
        pm.connectAttr(finger_scaler.output, middle_phalange_length.input_[1])

        distal_phalange_length = multiply(name=f"{self.name}_distal_phalange_length")
        pm.connectAttr(distance_dict["distal_phalage"].distance, distal_phalange_length.input_[0])
        pm.connectAttr(finger_scaler.output, distal_phalange_length.input_[1])

        pm.connectAttr(finger_hierarchies_collection["metacarpal_hierarchy"]["wm"].matrixSum, metacarpal_IK_jnt.offsetParentMatrix)
        pm.connectAttr(distance_dict["metacarpal"].distance, prox_phalange_IK_jnt.translateX)
        pm.connectAttr(prox_phalange_length.output, middle_phalange_IK_jnt.translateX)
        pm.connectAttr(middle_phalange_length.output, distal_phalange_IK_jnt.translateX)
        pm.connectAttr(distal_phalange_length.output, finger_end_jnt.translateX)

        IK_solver, IK_effector = pm.ikHandle(
            startJoint=prox_phalange_IK_jnt.node,
            endEffector=finger_end_jnt.node,
            solver="ikRPsolver",
            name=f"{self.name}_IK_hndl"
        )
        pm.xform(IK_solver, translation=(0, 0, 0))

        finger_IK_ctrl_outWtM = pickMatrix(name=f"{self.name}_finger_IK_ctrl_outWtM")
        pm.connectAttr(finger_IK_ctrl.worldMatrix[0], finger_IK_ctrl_outWtM.inputMatrix)
        for attr in ["useRotate", "useScale", "useShear"]:
            pm.setAttr(f"{finger_IK_ctrl_outWtM.node}.{attr}", 0)

        finger_polevector_ctrl_outVector = axisFromMatrix(name=f"{self.name}_finger_polevector_ctrl_outVector")
        pm.connectAttr(finger_polevector_ctrl.worldMatrix[0], finger_polevector_ctrl_outVector.input_)
        finger_polevector_ctrl_outVector.axis.set(1)

        pm.connectAttr(finger_IK_ctrl_outWtM.outputMatrix, IK_solver.offsetParentMatrix)
        pm.connectAttr(finger_polevector_ctrl_outVector.output, IK_solver.poleVector)






    def _create_ik_fk_blend(self, name, fk_source, ik_source, blend_attr):
        blend = blendMatrix(name=f"{self.name}_{name}")
        pm.connectAttr(fk_source, blend.inputMatrix)
        pm.connectAttr(ik_source, blend.target[0].targetMatrix)
        pm.connectAttr(blend_attr, blend.target[0].weight)
        return blend

    def _create_pom(self, name:str, source_matrix, parentGuide_input):
        """Creates a multMatrix node as a Parent ofset matrix."""
        pom = multMatrix(name=f"{self.name}_{name}_POM")
        pm.connectAttr(source_matrix, pom.matrixIn[0])
        pm.connectAttr(parentGuide_input, pom.matrixIn[1])
        return pom

    def _hierarchy_prep(self, name, guide, parent, parentGuide):
        outputs = {}
        outputs["pom"] = self._create_pom(name=name, source_matrix=guide, parentGuide_input=parentGuide)
        outputs["wm"] = multMatrix(name=f"{self.name}_{name}_WM")
        outputs["pom"].matrixSum >> outputs["wm"].matrixIn[0]
        pm.connectAttr(parent, outputs["wm"].matrixIn[1])
        return outputs

    def _lock_ctrl_attrs(self, ctrl, attrs_to_lock):
        for attr in attrs_to_lock:
            pm.setAttr(f"{ctrl.node}.{attr}", lock=True)
            pm.setAttr(f"{ctrl.node}.{attr}", keyable=False)
            pm.setAttr(f"{ctrl.node}.{attr}", channelBox=False)


f = Finger(hand_name="hand_L", finger_name="index", parent_module="hand", 
           prox_phalange_guide_pos=(8, 0, 0), finger_end_guide_pos=(8, 0, 0))