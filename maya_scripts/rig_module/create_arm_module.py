import pymel.core as pm
import json

#from prox_node_setup.generated_nodes import *

from pymel.core.nodetypes import Transform, BlendMatrix, AimMatrix, Choice, MultMatrix
"""t:Transform = pm.createNode("transform")"""

"""c:Choice = pm.createNode("choice")
m:MultMatrix = pm.createNode("multMatrix")
a:AimMatrix = pm.createNode("aimMatrix")
a.listAttr"""


from manual_node_classes import create_guide, colorize, maya_nodes, blend_target, parent_target
import control

guide_color = [1, 1, 1]
right_fk_color = [1, 0, 0]
right_ik_color = [0, 0.85, 0.83]
left_fk_color = [0, 0, 1]
left_ik_color = [1, 0.6, 0]

identityMatrix = pm.datatypes.Matrix()

def create_parents(*parents):
    
    inputs = []
    guide_inputs = []
    return


"""
When nodes done, implementation of ik-solver (maybe let user define hand controller and ellbow)

if possible invest time in BDK (would be insanely cool)
"""


"""def blend_target(targetMatrix, useMatrix=True, weight=1.0, scaleWeight=1.0, translateWeight=1.0, rotateWeight=1.0, shearWeight=1.0):
    target = {"targetMatrix": targetMatrix, "useMatrix": useMatrix, "weight": weight, "scaleWeight": scaleWeight, "translateWeight": translateWeight, "rotateWeight": rotateWeight, "shearWeight": shearWeight}
    return target"""

class LeftArm:
    
    def __init__(self, name, root_ctrl, *parents):
        self.name = name
        
        arm_L_main_input = pm.group(empty=True, name=f"{name}_main_input")
        arm_L_mainGuide_input = pm.group(empty=True, name=f"{name}_mainGuide_input")

        upper_guide = create_guide(name=f"{name}_upper_guide", position=(2, 4, 0), color=guide_color)
        lower_guide = create_guide(name=f"{name}_lower_guide", position=(0, 0, 0), color=guide_color)
        hand_guide = create_guide(name=f"{name}_hand_guide", position=(8, 4, 0), color=guide_color)

        elbowLocker_guide = create_guide(name=f"{name}_elbowLocker_guide", position=(5, 4, -4), color=guide_color)

        arm_L_settings_guide = create_guide(name=f"{name}_settings_guide, position", position=(2, 5, -2), color=guide_color)
        settings_ctrl:Transform = control.create("gear", "settings", size=1)

        settings_ctrl.addAttr(attr="useIK", niceName= "use IK", attributeType="float", defaultValue=0, minValue=0, maxValue=1)
        settings_ctrl.addAttr(attr="upperLenghtScaler", niceName="Upper Length Scaler", attributeType="float", defaultValue=1, minValue=0)
        settings_ctrl.addAttr(attr="lowerLengthScaler", niceName="Lower Length Scaler", attributeType="float", defaultValue=1, minValue=0)
        settings_ctrl.addAttr(attr="ellbowIkBlendpos", niceName="Ellbow IK Blendpos", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, keyable=False)
        settings_ctrl.addAttr(attr="enableIkStretch", niceName="Enable IK Stretch", attributeType="float", defaultValue=1, minValue=0, maxValue=1)
        settings_ctrl.addAttr(attr="softIkStart", niceName="Soft IK Start", attributeType="float", defaultValue=0.8, minValue=0, maxValue=1)
        settings_ctrl.addAttr(attr="enableSoftIk", niceName="Enable Soft IK", attributeType=bool, defaultValue=0)
        settings_ctrl.addAttr(attr="softIkCurve", niceName="Soft IK Curve", attributeType="enum", enumName="custom_curve:smoothstep_curve:cubic_curve", defaultValue=0)


        maya_nodes.test()


        arm_L_settings_POM = maya_nodes.multMatrix(name="arm_L_settings_POM", inputs=[arm_L_settings_guide.worldMatrix[0], arm_L_mainGuide_input.worldInverseMatrix[0]])
        arm_L_settings_WM = maya_nodes.multMatrix(name="arm_L_settings_WM", inputs=[arm_L_settings_POM.matrixSum, arm_L_main_input.worldMatrix[0]])


        pm.connectAttr(arm_L_settings_WM.matrixSum, settings_ctrl.offsetParentMatrix)
        

        upper_fk_ctrl = pm.circle(name=f"{name}_upper_fk_ctrl", radius=2, normal=(1, 0, 0))
        lower_fk_ctrl = pm.circle(name=f"{name}_lower_fk_ctrl", radius=2, normal=(1, 0, 0))
        hand_fk_ctrl = pm.circle(name=f"{name}_hand_fk_ctrl", radius=2, normal=(1, 0, 0))

        hand_ik_ctrl = control.create("box", "hand_ik_ctrl", size=1)
        colorize(hand_ik_ctrl, color=left_ik_color)

        for ctrl in (upper_fk_ctrl, lower_fk_ctrl, hand_fk_ctrl):
            colorize(ctrl, color=left_fk_color)
        

        elbow_IK_ctrl = pm.nurbsSquare(name=f"{name}_elbow_IK_ctrl", sideLength1=1, sideLength2=6, normal=(1, 0, 0))
        colorize(elbow_IK_ctrl, color=left_ik_color)

        elbowLock_IK_ctrl = control.create("box", "elbowLock_IK_ctrl", size=1)
        colorize(elbowLock_IK_ctrl, color=left_ik_color)

        arm_L_orientPlane_guide = maya_nodes.aimMatrix(
            name=f"{name}_orientPlane_guide",
            inputMatrix=upper_guide.worldMatrix[0],
            primary_targetMatrix=hand_guide.worldMatrix[0],
            secondary_targetMatrix=upper_guide.worldMatrix[0],
            secondary_aim_mode=2,
            secondary_targetVector=(0, 0, -1)
        )

        arm_L_lower_ctrl_guide_WM = maya_nodes.blendMatrix(
            name=f"{name}_lower_ctrl_guide_WM",
            inputMatrix=arm_L_orientPlane_guide.outputMatrix,
            targets = [
                blend_target(targetMatrix=hand_guide.worldMatrix[0], useMatrix=True, weight=0.5, rotateWeight=0, translateWeight=1, scaleWeight=0, shearWeight=0)
            ]
        )

        pm.connectAttr(arm_L_lower_ctrl_guide_WM.outputMatrix, lower_guide.offsetParentMatrix)

        #main = self._add_new_parent("main")

        arm_L_upper_initial_length = maya_nodes.distanceBetween(name="arm_L_upper_initial_length", inMatrix_1=upper_guide.worldMatrix[0], inMatrix_2=lower_guide.worldMatrix[0])
        arm_L_lower_initial_Length = maya_nodes.distanceBetween(name="arm_L_lower_initial_Length", inMatrix_1=lower_guide.worldMatrix[0], inMatrix_2=hand_guide.worldMatrix[0])

        arm_L_upper_length_manualScale = maya_nodes.multiply(name="arm_L_upper_length_manualScale", inputs=[arm_L_upper_initial_length.distance, settings_ctrl.upperLengthScaler])
        arm_L_lower_length_manualScale = maya_nodes.multiply(name="arm_L_lower_length_manualScale", inputs=[arm_L_lower_initial_Length.distance, settings_ctrl.lowerLengthScaler])

        arm_L_initial_length = maya_nodes.sum(name="arm_L_initial_length", inputs=[arm_L_upper_length_manualScale.output, arm_L_lower_length_manualScale.output])


        arm_L_upper_guide_outWM = maya_nodes.aimMatrix(
            name=f"{name}_upper_guide_outWM",
            inputMatrix=upper_guide.worldMatrix[0],
            primary_targetMatrix=lower_guide.worldMatrix[0],
            primary_aim_mode=1,
            secondary_targetMatrix=upper_guide.worldMatrix[0],
            secondary_aim_mode=2,
            primary_inputAxis=(1, 0, 0),
            primary_targetVector=(0, 0, 0),
            secondary_inputAxis=(0, 1, 0),
            secondary_targetVector=(0, 0, -1)
        )

        arm_L_upper_base_POM = maya_nodes.multMatrix(inputs=[arm_L_upper_guide_outWM.outputMatrix, arm_L_mainGuide_input.worldInverseMatrix[0]], name=f"{name}_upper_base_POM")
        arm_L_upper_baseWM = maya_nodes.multMatrix(inputs=[arm_L_upper_base_POM.matrixSum, arm_L_main_input.worldMatrix[0]], name=f"{name}_upper_baseWM")
        
        arm_L_upper_baseWM_noMainXformM = maya_nodes.multMatrix(inputs=[arm_L_upper_baseWM.matrixSum, arm_L_main_input.worldInverseMatrix[0]], name=f"{name}_upper_baseWM_noMainXformM")
        arm_L_upper_baseWM_noScaleM = maya_nodes.pickMatrix(matrix=arm_L_upper_baseWM_noMainXformM.matrixSum, use_scale=0, use_shear=0, name=f"{name}_upper_baseWM_noScaleM")

        arm_L_upper_WM_test = maya_nodes.multMatrix(inputs=[arm_L_upper_baseWM_noScaleM.outputMatrix, arm_L_main_input.offsetParentMatrix], name=f"{name}_upper_WM_test")
        arm_L_upper_FK_ctrl_rotWM = maya_nodes.parentMatrix(name=f"{name}_upper_FK_ctrl_rotWM",inputMatrix=arm_L_upper_WM_test.matrixSum, targets=[])
        arm_L_upper_FK_ctrl_WM = maya_nodes.blendMatrix(name=f"{name}_upper_FK_ctrl_WM", inputMatrix=arm_L_upper_FK_ctrl_rotWM.outputMatrix, targets=[blend_target(targetMatrix=arm_L_upper_WM_test.matrixSum)])

        pm.connectAttr(arm_L_upper_FK_ctrl_WM.ouputMatrix, upper_fk_ctrl[0].offsetParentMatrix)
        #pm.connectAttr(arm_L_upper_baseWM.matrixSum, upper_fk_ctrl[0].offsetParentMatrix)

        arm_L_upper_guide_outWIM = maya_nodes.inverseMatrix(name=f"{name}_upper_guide_outWIM", matrix=arm_L_upper_guide_outWM.outputMatrix)
        
        arm_L_lower_guide_outWM = maya_nodes.aimMatrix(
            name=f"{name}_lower_guide_outWM",
            inputMatrix=lower_guide.worldMatrix[0],
            primary_targetMatrix=hand_guide.worldMatrix[0],
            primary_aim_mode=1,
            secondary_targetMatrix=upper_guide.worldMatrix[0],
            secondary_aim_mode=2,
            primary_inputAxis=(1, 0, 0),
            primary_targetVector=(0, 0, 0),
            secondary_inputAxis=(0, 1, 0),
            secondary_targetVector=(0, 0, -1)
        )
        arm_L_lower_basePOM = maya_nodes.multMatrix(inputs=[arm_L_lower_guide_outWM.outputMatrix, arm_L_upper_guide_outWIM.outputMatrix], name=f"{name}_lower_basePOM")
        arm_L_lower_baseWM = maya_nodes.multMatrix(inputs=[arm_L_lower_basePOM.matrixSum, upper_fk_ctrl[0].worldMatrix[0]], name=f"{name}_lower_baseWM")
        pm.connectAttr(arm_L_lower_baseWM.matrixSum, lower_fk_ctrl[0].offsetParentMatrix)

        arm_L_lower_guide_outWIM = maya_nodes.inverseMatrix(name=f"{name}_lower_guide_outWIM", matrix=arm_L_lower_guide_outWM.outputMatrix)

        arm_L_hand_guide_outWM = maya_nodes.blendMatrix(
            name=f"{name}_hand_guide_outWM",
            inputMatrix=arm_L_lower_guide_outWM.outputMatrix,
            targets=[
                blend_target(
                    targetMatrix=hand_guide.worldMatrix[0],
                    weight=1.0,
                    scaleWeight=0,
                    translateWeight=1.0,
                    rotateWeight=0,
                    shearWeight=0
                )
            ]
        )

        arm_L_hand_base_POM = maya_nodes.multMatrix(inputs=[arm_L_hand_guide_outWM.outputMatrix, arm_L_lower_guide_outWIM.outputMatrix], name=f"{name}_hand_base_POM")
        arm_L_hand_baseWM = maya_nodes.multMatrix(inputs=[arm_L_hand_base_POM.matrixSum, lower_fk_ctrl[0].worldMatrix[0]], name=f"{name}_hand_baseWM")
        pm.connectAttr(arm_L_hand_baseWM.matrixSum, hand_fk_ctrl[0].offsetParentMatrix)


        #IK Ellbow

        arm_L_elbow_IK_guide_POM = maya_nodes.multMatrix(name="arm_L_elbow_IK_guide_POM", inputs=[arm_L_orientPlane_guide.outputMatrix, arm_L_mainGuide_input.worldInverseMatrix[0]]) #muss abgeändert werden
        arm_L_elbow_IK_clavicleSpaceWM = maya_nodes.multMatrix(name="arm_L_elbow_IK_clavicleSpaceWM", inputs=[arm_L_elbow_IK_guide_POM.matrixSum, arm_L_main_input.worldMatrix[0]]) #muss abgeädert werden
        
        arm_L_elbow_IK_baseWM = maya_nodes.parentMatrix(
            name="arm_L_elbow_IK_baseWM", 
            inputMatrix=arm_L_elbow_IK_clavicleSpaceWM.matrixSum, 
            targets=[]) #muss ergänz werden)
        
        arm_L_elbow_IK_WM = maya_nodes.blendMatrix(
            name="arm_L_elbow_IK_WM",
            inputMatrix=arm_L_elbow_IK_baseWM.outputMatrix,
            targets=[
                blend_target(
                    targetMatrix=arm_L_upper_WM_test.matrixSum
                ),
                blend_target(
                    targetMatrix=hand_ik_ctrl.worldMatrix[0],
                    weight=settings_ctrl.ellbowIkBlendpos
                )
            ]
        )
        
        pm.connectAttr(arm_L_elbow_IK_WM.outputMatrix, elbow_IK_ctrl.offsetParentMatrix)
        

        #IK Elbow Lock

        arm_L_elbowLocker_IK_ctrl_mainSpacePOM = maya_nodes.multMatrix(name="arm_L_elbowLocker_IK_ctrl_mainSpacePOM", inputs=[elbowLocker_guide.worldMatrix[0], arm_L_mainGuide_input.worldInverseMatrix[0]])
        arm_L_elbowLocker_IK_ctrl_WM = maya_nodes.multMatrix(name="arm_L_elbowLocker_IK_ctrl_WM", inputs=[arm_L_elbowLocker_IK_ctrl_mainSpacePOM.matrixSum, arm_L_main_input.worldMatrix[0]])

        pm.connectAttr(arm_L_elbowLocker_IK_ctrl_WM.matrixSum, elbowLock_IK_ctrl.offsetParentMatrix)




        #IK Prep

        arm_L_upper_baseWM_noMainScale = maya_nodes.multMatrix(name="arm_L_upper_baseWM_noMainScale", inputs=[arm_L_upper_baseWM.matrixSum, arm_L_main_input.worldInverseMatrix[0]])
        arm_L_hand_IK_ctrl_noMainScale = maya_nodes.multMatrix(name="arm_L_hand_IK_ctrl_noMainScale", inputs=[hand_ik_ctrl.worldMatrix[0], arm_L_main_input.worldInverseMatrix[0]])
        arm_L_current_length = maya_nodes.distanceBetween(name="arm_L_current_length", inMatrix_1=arm_L_upper_baseWM_noMainScale.matrixSum, inMatrix_2=arm_L_hand_IK_ctrl_noMainScale.matrixSum)

        arm_L_length_ratio = maya_nodes.divide(name="arm_L_length_ratio", in_01=arm_L_current_length.distance, in_02=arm_L_initial_length.output)
        arm_L_scaler = maya_nodes.max(name="arm_L_scaler", inputs=[arm_L_length_ratio.output, 1])
        arm_L_enable_ikStretch = maya_nodes.remapValue(name="arm_L_enable_ikStretch", input_value=settings_ctrl.ebableIkStretch, output_max=arm_L_scaler.output)

        arm_L_upper_length = maya_nodes.multiply(name="arm_L_upper_length", inputs=[arm_L_enable_ikStretch.outValue, arm_L_upper_length_manualScale.output])
        arm_L_lower_length = maya_nodes.multiply(name="arm_L_lower_length", inputs=[arm_L_enable_ikStretch.outValue, arm_L_lower_length_manualScale.output])

        arm_L_length = maya_nodes.sum(name="arm_L_length", inputs=[arm_L_upper_length.output, arm_L_lower_length.output])
        arm_L_clampedLength = maya_nodes.min(name="arm_L_clampedLength", inputs=[arm_L_length.output, arm_L_current_length.distance])
        arm_L_clampedLength_squared = maya_nodes.multiply(name="arm_L_clampedLength_sqared", inputs=[arm_L_clampedLength.output, arm_L_clampedLength.output])
        
        
        #SOFT IK

        arm_L_softIK_upper_length_squared = maya_nodes.multiply(name="arm_L_softIK_upper_length_squared", inputs=[arm_L_upper_length.output, arm_L_upper_length.output])
        arm_L_softIK_lower_length_squared = maya_nodes.multiply(name="arm_L_softIK_lower_length_squared", inputs=[arm_L_lower_length.output, arm_L_lower_length.output])
        arm_L_upper_softIK_numplus = maya_nodes.sum(name="arm_L_upper_softIK_numplus", inputs=[arm_L_softIK_upper_length_squared.output, arm_L_clampedLength_squared.output])
        arm_L_upper_softIK_denominator = maya_nodes.multiply(name="arm_L_upper_softIK_denominator", inputs=[2, arm_L_upper_length.output, arm_L_clampedLength.output])
        arm_L_upper_softIK_numenator = maya_nodes.subtract(name="arm_L_upper_softIK_numenator", in_01=arm_L_upper_softIK_numplus.output, in_02=arm_L_softIK_lower_length_squared.output)
        arm_L_upper_softIK_cosValue = maya_nodes.divide(name="arm_L_upper_softIK_cosValue", in_01=arm_L_upper_softIK_numenator.output, in_02=arm_L_upper_softIK_denominator.output)
        arm_L_upper_softIK_cosValueSquared = maya_nodes.multiply("arm_L_upper_softIK_cosValueSquared", inputs=[arm_L_upper_softIK_cosValue.output, arm_L_upper_softIK_cosValue.output])
        arm_L_upper_softIK_cubicBlendValue = maya_nodes.multiply(name="arm_L_upper_softIK_cubicBlendValue", inputs=[arm_L_upper_softIK_cosValueRemapped.outValue, arm_L_upper_softIK_cosValueRemapped.outValue, arm_L_upper_softIK_cosValueRemapped.outValue])
        arm_L_upper_softIK_cosValueRemapped = maya_nodes.remapValue(name="arm_L_upper_softIK_cosValueRemapped", input_min=settings_ctrl.softIkStart, input_value=arm_L_upper_softIK_cosValue.output)

        arm_L_mult = maya_nodes.multiply(name="arm_L_mult", inputs=[-2, arm_L_upper_softIK_cosValueRemapped.outValue])
        arm_L_sum = maya_nodes.sum(name="arm_L_sum", inputs=[arm_L_mult.output, 2])
        arm_L_power = maya_nodes.power(name="arm_L_power", input=arm_L_sum.output, exponent=3)
        arm_L_divide = maya_nodes.divide(name="arm_L_divide", in_01=arm_L_power.output, in_02=2)
        arm_L_subtract = maya_nodes.subtract("arm_L_subtract", in_01=1, in_02=arm_L_divide.output)
        arm_L_mult2 = maya_nodes.multiply(name="arm_L_mult2", inputs=[arm_L_upper_softIK_cosValueRemapped.outValue, arm_L_upper_softIK_cosValueRemapped.outValue, arm_L_upper_softIK_cosValueRemapped.outValue, 4])
        arm_L_upper_softIK_heigtSquared = maya_nodes.subtract(name="arm_L_upper_softIK_heigtSquared", in_01=arm_L_upper_softIK_cosValueSquared, in_02=1)

        arm_L_upper_softIK_smoothStepBlendBalue = maya_nodes.smoothStep(name="arm_L_upper_softIK_smoothStepBlendBalue", input=arm_L_upper_softIK_cosValueRemapped.outValue, rightEdge=1)
        arm_L_condition = maya_nodes.condition(name="arm_L_condition", first_term=arm_L_upper_softIK_cosValueRemapped.outValue, second_term=0.5, color_if_false=(arm_L_subtract.output, 0, 0), color_if_true=(arm_L_mult2.output, 0, 0))
        arm_L_upper_softIK_linearTargetHeight = maya_nodes.subtract(name="arm_L_upper_softIK_linearTargetHeight", in_01=1, in_02=arm_L_upper_softIK_cosValue.output)
        aem_L_upper_softIK_heigthSqaredClamped = maya_nodes.max(name="aem_L_upper_softIK_heigthSqaredClamped", inputs=[arm_L_upper_softIK_heigtSquared.output, 0])

        arm_L_softIK_blendcurve_selector = maya_nodes.choice(name="arm_L_softIK_blendcurve_selector", selector=settings_ctrl.softIkCurve, inputs=[arm_L_condition.outColorR, arm_L_upper_softIK_smoothStepBlendBalue.output, arm_L_upper_softIK_cubicBlendValue.output])
        arm_L_upper_softIK_quadraticTargetHeight = maya_nodes.multiply(name="arm_L_upper_softIK_quadraticTargetHeight", inputs=[arm_L_upper_softIK_linearTargetHeight.output, arm_L_upper_softIK_linearTargetHeight.output])
        arm_L_upper_softIK_height = maya_nodes.power(name="arm_L_upper_softIK_heigt", input=aem_L_upper_softIK_heigthSqaredClamped.output, exponent=0.5)
        arm_L_segment_lengthRatio = maya_nodes.divide(name="arm_L_segment_lengthRatio", in_01=arm_L_upper_length.output, in_02=arm_L_lower_length)

        arm_L_upper_softIK_blendedHeight = maya_nodes.blendTwoAttr(name="arm_L_upper_softIK_blendedHeight", attr_blender=arm_L_softIK_blendcurve_selector.output, inputs=[arm_L_upper_softIK_height.output, arm_L_upper_softIK_quadraticTargetHeight.output])
        arm_L_lower_softIK_heigt = maya_nodes.multiply(name="arm_L_lower_softIK_heigt", inputs=[arm_L_upper_softIK_height.output, arm_L_segment_lengthRatio.output])

        arm_L_upper_softIK_blendedHeightSquared = maya_nodes.multiply(name="arm_L_upper_softIK_blendedHeightSquared", inputs=[arm_L_upper_softIK_blendedHeight.output, arm_L_upper_softIK_blendedHeight.output])
        arm_L_lower_softIK_heigtSquared = maya_nodes.multiply(name="arm_L_lower_softIK_heigtSquared", inputs=[arm_L_lower_softIK_heigt.output, arm_L_lower_softIK_heigt.output])
        arm_L_lower_softIK_blendedHeight = maya_nodes.multiply(name="arm_L_lower_softIK_blendedHeight", inputs=[arm_L_upper_softIK_blendedHeight.output, arm_L_segment_lengthRatio.output])

        arm_L_upper_softIK_scalerSquared = maya_nodes.sum(name="arm_L_upper_softIK_scalerSquared", inputs=[arm_L_upper_softIK_blendedHeightSquared.output, arm_L_upper_softIK_cosValue.output])
        arm_L_lower_softIK_cosValueSquared = maya_nodes.subtract(name="arm_L_lower_softIK_cosValueSquared", in_01=1, in_02=arm_L_lower_softIK_heigtSquared.output)
        arm_L_lower_softIK_blendedHeightSquared = maya_nodes.multiply(name="arm_L_lower_softIK_blendedHeightSquared", inputs=[arm_L_lower_softIK_blendedHeight.output, arm_L_lower_softIK_blendedHeight.output])

        arm_L_upper_softIK_scaler = maya_nodes.power(name="arm_L_upper_softIK_scaler", input=arm_L_upper_softIK_scalerSquared.output, exponent=0.5)
        arm_L_lower_softIK_scalerSquared = maya_nodes.sum(name="arm_L_lower_softIK_scalerSquared", inputs=[arm_L_lower_softIK_cosValueSquared.output, arm_L_lower_softIK_blendedHeightSquared.output])

        arm_L_disable_soft_ik = maya_nodes.not_node(name="arm_L_disable_soft_ik", input=settings_ctrl.enableSoftIk)
        arm_L_lower_softIK_scaler = maya_nodes.power(name="arm_L_lower_softIK_scaler", input=arm_L_lower_softIK_scalerSquared.output, exponent=0.5)


        #----------------------------- ELBOW LOCK PART --------------------------------


        arm_L_upper_softIK_scaler_enable = maya_nodes.max(name="arm_L_upper_softIK_scaler_enable", inputs=[arm_L_disable_soft_ik.output, arm_L_upper_softIK_scaler.output])
        arm_L_elbowLock_IK_ctrl_noMainScale = maya_nodes.multMatrix(name="arm_L_elbowLock_IK_ctrl_noMainScale", inputs=[elbowLock_IK_ctrl.worldMatrix[0], arm_L_main_input.worldInverseMatrix[0]])
        arm_L_lower_softIK_scaler_enable = maya_nodes.max(name="arm_L_lower_softIK_scaler_enable", inputs=[arm_L_disable_soft_ik.input, arm_L_lower_softIK_scaler.output])

        arm_L_elbowLock_IK_upperLength = maya_nodes.distanceBetween(name="arm_L_elbowLock_IK_upperLength", inMatrix_1=arm_L_upper_baseWM_noMainScale.matrixSum, inMatrix_2=arm_L_elbowLock_IK_ctrl_noMainScale.matrixSum)
        arm_L_elbowLock_IK_lowerLength = maya_nodes.distanceBetween(name="arm_L_elbowLock_IK_lowerLength", inMatrix_1=arm_L_elbowLock_IK_ctrl_noMainScale.matrixSum, inMatrix_2=arm_L_hand_IK_ctrl_noMainScale.matrixSum)





        #IK Solver







    def _add_new_parent(self, name):
        parent = pm.group(empty=True, name=f"{self.name}_{name}_input")
        parentGuide = pm.group(empty=True, name=f"{self.name}_{name}Guide_input")

        return parent, parentGuide


def create_right_control_module(name, parents):
    print("create right control module..........")



class CreateArmModule:
    def __init__(self):
        self.win_id = "arm_module_creator_win"

        if pm.window(self.win_id, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Arm Module Creator", widthHeight=(400, 150), bgc=(0, 0.153, 0.212)) as win:
            with pm.columnLayout(adj=True, rowSpacing=10):
                pm.text(label="This Tool will either create a left or right arm Rig module with guides and fk/ik Controllers \n based on Jean Paul Tossings Matrix Rigging",align="left")
                self.name_field = pm.textField(text="Enter Name")
                self.left_box = pm.checkBox(label="left", v=False)
                self.right_box = pm.checkBox(label="right", v=False)
                pm.text(label="Select the root module in the ouliner before starting the program", align="left")
                pm.button(label="Start", c=self.execute)
                pm.button(label="Cancel", c=self.cancel)

        pm.showWindow(win)

    def execute(self, *args):
        rig_name = self.name_field.getText()
        left = self.left_box.getValue()
        right = self.right_box.getValue()

        base_root = pm.selected()
        print(f"root name: {base_root}")

        if left:
            LeftArm(name = f"{rig_name}_L", root_ctrl=base_root)
        if right:
            create_right_control_module(name=f"{rig_name}_R", parents=base_root)

    def cancel (self, *args):
        pass

if __name__ == "__main__":
    CreateArmModule()