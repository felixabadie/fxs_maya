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
    hierarchy_prep,
    lock_ctrl_attrs, 
    create_ik_solver_setup,
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


"""
Todo:

When everything works make roll and bank accessible via variables in the creation.
"""


class LegManager:
    def __init__(self):
        self.win_id = "fxs_leg_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Leg Rigging Module") as win:
            with pm.columnLayout(adj=True):
                self.name = TextFieldHelper("Leg name: ")
                self.limb_side = TextFieldHelper("Leg side ('L' or 'R'): ")
                self.bind_jnts = pm.intFieldGrp(label="Amount of bind joints: ", numberOfFields=1)
                self.parent_output = TextFieldHelper("Parent Output Group: ")
                self.parent_outputGuide = TextFieldHelper("Parent Output Guide: ")
                self.main_output = TextFieldHelper("Root Controller output group: ")
                self.mainGuide_output = TextFieldHelper("Root Controller output guide: ")
                self.upper_guide_pos = CompoundFieldSlot("Initial position of the upper guide: ")
                self.lower_guide_pos = CompoundFieldSlot("Initial position of the lower guide: ")
                self.ankle_guide_pos = CompoundFieldSlot("Initial position of the ankle guide: ")
                self.foot_guide_pos = CompoundFieldSlot("Initial position of the foot guide: ")
                self.foot_left_bank_guide_pos = CompoundFieldSlot("Initial position of the left bank guide: ")
                self.foot_right_bank_guide_pos = CompoundFieldSlot("Initial position of the right bank guide: ")
                self.foot_heel_guide_pos = CompoundFieldSlot("Initial position of the heel guide: ")
                self.foot_ball_guide_pos = CompoundFieldSlot("Initial position of the ball guide: ")
                self.foot_end_guide_pos = CompoundFieldSlot("Initial position of the foot_end guide: ")
                self.kneeLock_guide_pos = CompoundFieldSlot("Initial position of the kneeLock guide: ")
                
                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)
    
    def execute(self, *args):
        
        try:
            name = self.name.obj.control.getText()
            limb_side = self.limb_side.obj.control.getText()
        except AttributeError:
            pm.error("Naming Error")

        if pm.intFieldGrp(self.bind_jnts, query=True, value1=True) > 0:
            bind_jnts = pm.intFieldGrp(self.bind_jnts, query=True, value=True)
        else:
            pm.warning("Not enough bind joints (using 5 instead)")
            bind_jnts = 5
        
        if limb_side == "L":
            fk_ctrl_color = left_fk_color
            ik_ctrl_color = left_ik_color
        elif limb_side == "R":
            fk_ctrl_color = right_fk_color
            ik_ctrl_color = right_ik_color
        else:
            print("Problem with limb side")

        guide_positions = {
            "upper_guide_pos": self.upper_guide_pos,
            "lower_guide_pos": self.lower_guide_pos,
            "ankle_guide_pos": self.ankle_guide_pos,
            "foot_guide_pos": self.foot_guide_pos,
            "foot_left_bank_guide_pos": self.foot_left_bank_guide_pos,
            "foot_right_bank_guide_pos": self.foot_right_bank_guide_pos,
            "foot_heel_guide_pos": self.foot_heel_guide_pos,
            "foot_ball_guide_pos": self.foot_ball_guide_pos,
            "foot_end_guide_pos": self.foot_end_guide_pos,
            "kneeLock_guide_pos": self.kneeLock_guide_pos
        }

        resolved_positions = {}

        for attr_name, slot in guide_positions.items():
            values = slot.get_values()
            if all(v is not None and v != 0.0 for v in values):
                resolved_positions[attr_name] = values
            else:
                pm.warning(f"{attr_name} contains nonvalid values")
                resolved_positions[attr_name] = None

        kwargs = {"limb_type": name, "limb_side": limb_side, "fk_color": fk_ctrl_color, "ik_color": ik_ctrl_color, "bind_jnts": bind_jnts}
        for attr_name, value in resolved_positions.items():
            if value is not None:
                kwargs[attr_name] = value
        
        self.module = LegModule(**kwargs)

        try:
            pm.connectAttr(f"{self.parent_output.obj}.offsetParentMatrix", f"{self.module.out_parent_input}.offsetParentMatrix")
            pm.connectAttr(f"{self.parent_outputGuide.obj}.offsetParentMatrix", f"{self.module.out_parentGuide_input}.offsetParentMatrix")
            
            pm.connectAttr(f"{self.main_output.obj}.offsetParentMatrix", f"{self.module.out_main_input}.offsetParentMatrix")
            pm.connectAttr(f"{self.mainGuide_output.obj}.offsetParentMatrix", f"{self.module.out_mainGuide_input}.offsetParentMatrix")
        except:
            print("Parent Module connection not possible, manual connection requiered")



class LegModule:

    def __init__(self, main_module:str, parent_module:str , limb_type:str, limb_side:str, bind_jnts=10, upper_guide_pos:tuple = (4, 10, 0), lower_guide_pos:tuple = (0, 1, 0), 
                 ankle_guide_pos:tuple = (0, 1, 0), foot_guide_pos:tuple = (0, 0, 0), foot_left_bank_guide_pos:tuple = (1, 0, 0), foot_right_bank_guide_pos:tuple = (-1, 0, 0), 
                 foot_heel_guide_pos:tuple = (0, 0, -1), foot_end_guide_pos:tuple = (0, 0, 5), foot_ball_guide_pos:tuple = (0, 0, 3), kneeLock_guide_pos:tuple = (4, 5, 8), 
                 settings_guide_pos:tuple = (5, 13, -2), upper_guide_rot:tuple = (0, 0, 0), fk_color:list = [0, 0, 1], ik_color:list = [0, 0.85, 0.83]):
        """
        Creates a limb-rig-module based on the tutorials of Jean Paul Tossings. The module can be adapted thanks to guides and be repositioned at any time.
        The Module contains a math-based IK-Solver, an IK/FK Blend, manually scalable segments, softIK to prevent snapping and a ribbon.
        
        :param self: Description
        :param main_module: name of main controller for naming the inputs
        :type main_module: str
        :param parent_module: name of the connecting module (clavicle or leg)
        :type parent_module: str
        :param limb_type: either arm or leg, currently no additional function just for naming
        :type limb_type: str
        :param limb_side: left or right from perspective of charakter, currently no additional function just for naming
        :type limb_side: str
        :param upper_guide_pos: upper guide position as (X, Y, Z)
        :type upper_guide_pos: tuple
        :param lower_guide_pos: lower guide position as (X, Y, Z)
        :type lower_guide_pos: tuple
        :param ankle_guide_pos: ankle guide position as (X, Y, Z)
        :type ankle_guide_pos: tuple
        :param foot_guide_pos: foot guide position as (X, Y, Z)
        :type foot_guide_pos: tuple
        :param foot_left_bank_guide_pos: position that defines the left banking pivot as (X, Y, Z)
        :type foot_left_bank_guide_pos: tuple
        :param foot_right_bank_guide_pos: position that defines the right banking pivot as (X, Y, Z)
        :type foot_right_bank_guide_pos: tuple
        :param foot_heel_guide_pos: foot heel guide position, defining the pivot of the foot heel during foot roll as (X, Y, Z)
        :type foot_heel_guide_pos: tuple
        :param foot_end_guide_pos: foot end guide position, defining the pivot of the foot tip or end during foot roll as (X, Y, Z)
        :type foot_end_guide_pos: tuple
        :param foot_ball_guide_pos: foot ball guide position, definingthe pivot of the foot ball during foot roll as (X, Y, Z)
        :type foot_ball_guide_pos: tuple
        :param kneeLock_guide_pos: kneeLock guide position as (X, Y, Z)
        :type kneeLock_guide_pos: tuple
        :param settings_guide_pos: settings guide position as (X, Y, Z)
        :type settings_guide_pos: tuple
        :param upper_guide_rot: Y-Rotation 180 to flip knee/knee (X, Y, Z)
        :type upper_guide_rot: tuple
        :param fk_color: FK controller color, settings controller color as RGB 0-1 [0, 0, 0]
        :type fk_color: list
        :param ik_color: IK controller, kneeLock controller as RGB 0-1 [0, 0, 0]
        :type ik_color: list
        
        """

        self.name = f"{limb_type}_{limb_side}"
        self.limb_type = limb_type
        self.limb_side = limb_side
        self.upper_guide_rot = upper_guide_rot
        self.bind_jnts = bind_jnts
        
        self.groups = create_groups(rig_module_name=self.name)
        
        upper_guide = create_guide(name=f"{self.name}_upper_guide", position=upper_guide_pos, color=guide_color)
        upper_guide.rotate.set(self.upper_guide_rot)
        lower_guide = create_guide(name=f"{self.name}_lower_guide", position=lower_guide_pos, color=guide_color)
        ankle_guide = create_guide(name=f"{self.name}_ankle_guide", position=ankle_guide_pos, color=guide_color)
        foot_guide = create_guide(name=f"{self.name}_foot_guide", position=foot_guide_pos, color=guide_color)
        foot_left_bank_guide = create_guide(name=f"{self.name}_foot_left_bank_guide", position=foot_left_bank_guide_pos, color=guide_color)
        foot_right_bank_guide = create_guide(name=f"{self.name}_foot_right_bank_guide", position=foot_right_bank_guide_pos, color=guide_color)
        foot_heel_guide = create_guide(name=f"{self.name}_foot_heel_guide", position=foot_heel_guide_pos, color=guide_color)
        foot_ball_guide = create_guide(name=f"{self.name}_foot_ball_guide", position=foot_ball_guide_pos, color=guide_color)
        foot_end_guide = create_guide(name=f"{self.name}_foot_end_guide", position=foot_end_guide_pos, color=guide_color)

        for guide in [foot_heel_guide, ankle_guide, foot_left_bank_guide, foot_right_bank_guide, foot_ball_guide, foot_end_guide]:
            pm.connectAttr(foot_guide.worldMatrix[0], guide.offsetParentMatrix)

        self.kneeLock_guide = create_guide(name=f"{self.name}_kneeLock_guide", position=kneeLock_guide_pos, color=guide_color)

        settings_guide = create_guide(name=f"{self.name}_settings_guide", position=settings_guide_pos, color=guide_color)

        lower_guide.translateZ.set(lock=True)
        lower_guide.node.setLimit("translateMinY", 0)

        self.main_input = transform(name=f"{self.name}_{main_module}_input")
        self.mainGuide_input = transform(name=f"{self.name}_{main_module}Guide_input")
        self.parent_module_input = transform(name=f"{self.name}_{parent_module}_input")
        self.parent_moduleGuide_input = transform(name=f"{self.name}_{parent_module}Guide_input")

        self.input_list = [parent_module, main_module, "worldSpace"]

        self.settings_ctrl = control.create(ctrl_type="gear", degree=3, name=f"{self.name}_settings_ctrl", normal=(0, 0, 1), color=fk_color)
        self.settings_ctrl.node.addAttr(attr="custom", niceName="CUSTOM ATTR", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="useIK", niceName= "use IK", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="upperLengthScaler", niceName="Upper Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="lowerLengthScaler", niceName="Lower Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="kneeIkBlendpos", niceName="knee IK Blendpos", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="enableIkStretch", niceName="Enable IK Stretch", attributeType="float", defaultValue=1, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{parent_module}:{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="ribbon", niceName="RIBBON", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="show_ribbon_ctrl", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="ribbonRoundness", niceName="Ribbon Roundness", attributeType="float", minValue=0.01, maxValue=5, defaultValue=1, keyable=True)
        self.settings_ctrl.node.addAttr(attr="kneeTangent", niceName="knee Tangent", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="soft_IK", niceName="SOFT IK", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="softIkStart", niceName="Soft IK Start", attributeType="float", defaultValue=0.8, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="enableSoftIk", niceName="Enable Soft IK", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="softIkCurve", niceName="Soft IK Curve", attributeType="enum", enumName="custom_curve:smoothstep_curve:cubic_curve", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="visibility_grps", niceName="VISIBILITY", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)

        for attr in ["custom", "ribbon", "soft_IK", "visibility_grps"]:
            pm.setAttr(f"{self.settings_ctrl.node}.{attr}", lock=True)
        
        setup_visibility_controls(settings_ctrl=self.settings_ctrl, groups=self.groups)

        self.parent_module_input_noMainXformM = multMatrix(name=f"{self.name}_{parent_module}_input_noMainXformM")
        pm.connectAttr(self.parent_module_input.offsetParentMatrix, self.parent_module_input_noMainXformM.matrixIn[0])
        pm.connectAttr(self.main_input.worldInverseMatrix[0], self.parent_module_input_noMainXformM.matrixIn[1])

        self.parent_module_input_noScaleM = pickMatrix(name=f"{self.name}_{parent_module}_input_noScaleM")
        pm.connectAttr(self.parent_module_input_noMainXformM.matrixSum, self.parent_module_input_noScaleM.inputMatrix)
        self.parent_module_input_noScaleM.useScale.set(0)
        self.parent_module_input_noScaleM.useShear.set(0)

        self.parent_module_input_WM = multMatrix(name=f"{self.name}_{parent_module}_input_WM")
        pm.connectAttr(self.parent_module_input_noScaleM.outputMatrix, self.parent_module_input_WM.matrixIn[0])
        pm.connectAttr(self.main_input.offsetParentMatrix, self.parent_module_input_WM.matrixIn[1])
        
        settings_POM = create_pom(module_name=self.name, name="settings_POM", source_matrix = settings_guide.worldMatrix[0], parentGuide_input = self.parent_moduleGuide_input.worldInverseMatrix[0])

        settings_WM = multMatrix(name=f"{self.name}_settings_WM")
        pm.connectAttr(settings_POM.matrixSum, settings_WM.matrixIn[0])
        pm.connectAttr(self.parent_module_input_WM.matrixSum, settings_WM.matrixIn[1])

        pm.connectAttr(settings_WM.matrixSum, self.settings_ctrl.offsetParentMatrix)

        self.orientPlane_guide = aimMatrix(name=f"{self.name}_orientPlane_guide")
        pm.connectAttr(upper_guide.worldMatrix[0], self.orientPlane_guide.inputMatrix)
        pm.connectAttr(ankle_guide.worldMatrix[0], self.orientPlane_guide.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0],self.orientPlane_guide.secondaryTargetMatrix)
        self.orientPlane_guide.secondaryMode.set(2)
        self.orientPlane_guide.secondaryTargetVector.set(0, 0, -1)

        lower_ctrl_guide_WM = blendMatrix(name=f"{self.name}_lower_ctrl_guide_WM")
        pm.connectAttr(self.orientPlane_guide.outputMatrix, lower_ctrl_guide_WM.inputMatrix)
        pm.connectAttr(ankle_guide.worldMatrix[0], lower_ctrl_guide_WM.target[0].targetMatrix)
        lower_ctrl_guide_WM.target[0].useMatrix.set(True)
        lower_ctrl_guide_WM.target[0].weight.set(0.5)
        for attr in ["rotateWeight", "rotateWeight", "shearWeight"]:
            pm.setAttr(f"{lower_ctrl_guide_WM.target[0]}.{attr}", 0)
        
        pm.connectAttr(lower_ctrl_guide_WM.outputMatrix, lower_guide.offsetParentMatrix)

        #===============================================================================================================================================
        #===============================================================================================================================================

        self.float_value_0 = floatConstant(name=f"{self.name}_float_value_0")
        self.float_value_0.inFloat.set(0)

        self.float_value_1 = floatConstant(name=f"{self.name}_float_value_1")
        self.float_value_1.inFloat.set(1)

        self.float_value_2 = floatConstant(name=f"{self.name}_float_value_2")
        self.float_value_2.inFloat.set(2)

        self.float_value_minus2 = floatConstant(name=f"{self.name}_float_value_minus2")
        self.float_value_minus2.inFloat.set(-2)

        self.float_value_4 = floatConstant(name=f"{self.name}_float_value_4")
        self.float_value_4.inFloat.set(4)

        upper_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_upper_FK_ctrl", ctrl_size=2, normal=(1,0,0), color=fk_color)
        lower_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_lower_FK_ctrl", ctrl_size=2, normal=(1,0,0), color=fk_color)
        ankle_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_ankle_FK_ctrl", ctrl_size=2, normal=(1,0,0), color=fk_color)
        foot_ball_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_ankle_FK_ctrl", ctrl_size=2, normal=(1,0,0), color=fk_color)

        foot_IK_ctrl = control.create(ctrl_type="box", degree=1, name="foot_IK_ctrl", size=[2, 2, 2], color=ik_color)
        foot_IK_ctrl.node.addAttr(attr="roll", attributeType="float", defaultValue=0, hidden=False, keyable=True)
        foot_IK_ctrl.node.addAttr(attr="bank", attributeType="float", defaultValue=0, hidden=False, keyable=True)

        knee_IK_ctrl = control.create(ctrl_type="pyramid", degree=1, name=f"{self.name}_knee_IK_ctrl", size=[0.5, 6, 0.5], color=ik_color)
        lock_ctrl_attrs(knee_IK_ctrl, ["translateX", "translateY", "translateZ", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"])

        self.kneeLock_IK_ctrl = control.create(ctrl_type="box", degree=1, name="kneeLock_IK_ctrl", size=[1, 1, 1], color=ik_color)
        lock_ctrl_attrs(self.kneeLock_IK_ctrl, attrs_to_lock=["rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"])

        self.kneeLock_IK_ctrl.node.addAttr(attr="Lock", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.kneeLock_IK_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)

        self.kneeLock_list = [main_module, "worldSpace"]

        upper_initial_length = distanceBetween(name=f"{self.name}_upper_initial_length")
        pm.connectAttr(upper_guide.worldMatrix[0], upper_initial_length.inMatrix1)
        pm.connectAttr(lower_guide.worldMatrix[0], upper_initial_length.inMatrix2)

        lower_initial_Length = distanceBetween(name=f"{self.name}_lower_initial_Length")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_initial_Length.inMatrix1)
        pm.connectAttr(ankle_guide.worldMatrix[0], lower_initial_Length.inMatrix2)

        upper_length_manualScale = multiply(name=f"{self.name}_upper_length_manualScale")
        pm.connectAttr(upper_initial_length.distance, upper_length_manualScale.input_[0])
        pm.connectAttr(self.settings_ctrl.node.upperLengthScaler, upper_length_manualScale.input_[1])

        lower_length_manualScale = multiply(name=f"{self.name}_lower_length_manualScale")
        pm.connectAttr(lower_initial_Length.distance, lower_length_manualScale.input_[0])
        pm.connectAttr(self.settings_ctrl.node.lowerLengthScaler, lower_length_manualScale.input_[1])

        initial_length = sum_(name=f"{self.name}_initial_length")
        pm.connectAttr(upper_length_manualScale.output, initial_length.input_[0])
        pm.connectAttr(lower_length_manualScale.output, initial_length.input_[1])


        self.upper_FK_guide_outWM = aimMatrix(name=f"{self.name}_upper_FK_guide_outWM")
        pm.connectAttr(upper_guide.worldMatrix[0], self.upper_FK_guide_outWM.inputMatrix)
        pm.connectAttr(lower_guide.worldMatrix[0], self.upper_FK_guide_outWM.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0], self.upper_FK_guide_outWM.secondaryTargetMatrix)
        self.upper_FK_guide_outWM.secondaryMode.set(2)
        self.upper_FK_guide_outWM.secondaryTargetVector.set(0, 0, -1)


        upper_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_upper_FK_guide_outWIM")
        pm.connectAttr(self.upper_FK_guide_outWM.outputMatrix, upper_FK_guide_outWIM.inputMatrix)

        upper_base_POM = create_pom(
            module_name=self.name, name="upper_base_POM", source_matrix = self.upper_FK_guide_outWM.outputMatrix, parentGuide_input = self.parent_moduleGuide_input.worldInverseMatrix[0])

        upper_baseWM = multMatrix(name=f"{self.name}_upper_baseWM")
        pm.connectAttr(upper_base_POM.matrixSum, upper_baseWM.matrixIn[0])
        pm.connectAttr(self.parent_module_input_WM.matrixSum, upper_baseWM.matrixIn[1])

        upper_baseWM_noMainXformM = multMatrix(name=f"{self.name}_upper_baseWM_noMainXformM")
        pm.connectAttr(upper_baseWM.matrixSum, upper_baseWM_noMainXformM.matrixIn[0])
        pm.connectAttr(self.main_input.worldInverseMatrix[0], upper_baseWM_noMainXformM.matrixIn[1])

        upper_baseWM_noScaleM = pickMatrix(name=f"{self.name}_upper_baseWM_noScaleM")
        pm.connectAttr(upper_baseWM_noMainXformM.matrixSum, upper_baseWM_noScaleM.inputMatrix)
        upper_baseWM_noScaleM.useScale.set(0)
        upper_baseWM_noScaleM.useShear.set(0)

        upper_WM_test = multMatrix(name=f"{self.name}_upper_WM_test")
        pm.connectAttr(upper_baseWM_noScaleM.outputMatrix, upper_WM_test.matrixIn[0])
        pm.connectAttr(self.main_input.offsetParentMatrix, upper_WM_test.matrixIn[1])

        upper_FK_ctrl_mainSpacePOM = create_pom(
            module_name=self.name, name="upper_FK_ctrl_mainSpacePOM", source_matrix = self.upper_FK_guide_outWM.outputMatrix, parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])

        foot_IK_ctrl_mainSpaceEnable = equal(name=f"{self.name}_foot_IK_ctrl_{main_module}SpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, foot_IK_ctrl_mainSpaceEnable.input1)
        foot_IK_ctrl_mainSpaceEnable.input2.set(1)

        foot_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_foot_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, foot_IK_ctrl_worldSpaceEnable.input1)
        foot_IK_ctrl_worldSpaceEnable.input2.set(2)

        self.upper_FK_ctrl_rotWM = parentMatrix(name=f"{self.name}_upper_FK_ctrl_rotWM")
        pm.connectAttr(upper_WM_test.matrixSum, self.upper_FK_ctrl_rotWM.inputMatrix)
        pm.connectAttr(foot_IK_ctrl_mainSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.upper_FK_ctrl_rotWM.target[0].targetMatrix)
        pm.connectAttr(upper_FK_ctrl_mainSpacePOM.matrixSum, self.upper_FK_ctrl_rotWM.target[0].offsetMatrix)
        pm.connectAttr(foot_IK_ctrl_worldSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[1].enableTarget)
        pm.connectAttr(self.upper_FK_guide_outWM.outputMatrix, self.upper_FK_ctrl_rotWM.target[1].offsetMatrix)

        upper_FK_ctrl_WM = blendMatrix(name=f"{self.name}_upper_FK_ctrl_WM")
        pm.connectAttr(self.upper_FK_ctrl_rotWM.outputMatrix, upper_FK_ctrl_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, upper_FK_ctrl_WM.target[0].targetMatrix)

        #Connecting to upper FK Controller
        pm.connectAttr(upper_FK_ctrl_WM.outputMatrix, upper_FK_ctrl.offsetParentMatrix)


        lower_FK_guide_outWM = aimMatrix(name=f"{self.name}_lower_FK_guide_outWM")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_FK_guide_outWM.inputMatrix)
        pm.connectAttr(ankle_guide.worldMatrix[0], lower_FK_guide_outWM.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0], lower_FK_guide_outWM.secondaryTargetMatrix)
        lower_FK_guide_outWM.secondaryMode.set(2)
        lower_FK_guide_outWM.secondaryTargetVector.set(0, 0, -1)

        lower_FK_ctrl_POM = create_pom(module_name=self.name, name="lower_FK_ctrl_POM", source_matrix = lower_FK_guide_outWM.outputMatrix, parentGuide_input = upper_FK_guide_outWIM.outputMatrix)

        lower_axes = extract_matrix_axes(module_name=self.name, name="lower_FK_ctrl_POM", input=lower_FK_ctrl_POM.matrixSum)

        lower_FK_ctrl_POM_manualScale = create_fourByFourMatrix(
            module_name=self.name,
            name="lower_FK_ctrl_POM_manualScale",
            inputs=[
                [lower_axes["X"].outputX, lower_axes["X"].outputY, lower_axes["X"].outputZ, lower_axes["X"].outputW],
                [lower_axes["Y"].outputX, lower_axes["Y"].outputY, lower_axes["Y"].outputZ, lower_axes["Y"].outputW],
                [lower_axes["Z"].outputX, lower_axes["Z"].outputY, lower_axes["Z"].outputZ, lower_axes["Z"].outputW],
                [upper_length_manualScale.output]
            ]
        )

        lower_FK_ctrl_WM = multMatrix(name=f"{self.name}_lower_FK_ctrl_WM")
        pm.connectAttr(lower_FK_ctrl_POM_manualScale.output, lower_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(upper_FK_ctrl.worldMatrix[0], lower_FK_ctrl_WM.matrixIn[1])

        #connection to FK Controller
        pm.connectAttr(lower_FK_ctrl_WM.matrixSum, lower_FK_ctrl.offsetParentMatrix)

        """self.ankle_FK_guide_outWM = blendMatrix(name=f"{self.name}_ankle_FK_guide_outWM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, self.ankle_FK_guide_outWM.inputMatrix)
        pm.connectAttr(ankle_guide.worldMatrix[0], self.ankle_FK_guide_outWM.target[0].targetMatrix)
        self.ankle_FK_guide_outWM.target[0].weight.set(1)
        self.ankle_FK_guide_outWM.target[0].translateWeight.set(1)
        for attr in ["scaleWeight", "rotateWeight", "shearWeight"]:
            pm.setAttr(f"{self.ankle_FK_guide_outWM.target[0]}.{attr}", 0)"""
        
        self.ankle_FK_guide_outWM = aimMatrix(name=f"{self.name}_ankle_FK_guide_outWM")
        pm.connectAttr(ankle_guide.worldMatrix[0], self.ankle_FK_guide_outWM.inputMatrix)
        pm.connectAttr(foot_guide.worldMatrix[0], self.ankle_FK_guide_outWM.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0], self.ankle_FK_guide_outWM.secondaryTargetMatrix)
        self.ankle_FK_guide_outWM.secondaryMode.set(2)
        self.ankle_FK_guide_outWM.secondaryTargetVector.set(0, 0, -1)

        self.foot_guide_outWM = blendMatrix(name=f"{self.name}_foot_guide_outWM")
        pm.connectAttr(self.ankle_FK_guide_outWM.outputMatrix, self.foot_guide_outWM.inputMatrix)
        pm.connectAttr(foot_guide.worldMatrix[0], self.foot_guide_outWM.target[0].targetMatrix)
        self.foot_guide_outWM.target[0].weight.set(1)
        self.foot_guide_outWM.target[0].translateWeight.set(1)
        for attr in ["scaleWeight", "shearWeight"]:
            pm.setAttr(f"{self.foot_guide_outWM.target[0]}.{attr}", 0)

        lower_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_lower_guide_outWIM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, lower_FK_guide_outWIM.inputMatrix)

        ankle_FK_ctrl_POM = create_pom(module_name=self.name, name="ankle_FK_ctrl_POM", source_matrix = self.ankle_FK_guide_outWM.outputMatrix, parentGuide_input = lower_FK_guide_outWIM.outputMatrix)

        ankle_axes = extract_matrix_axes(module_name=self.name, name="ankle_FK_ctrl_POM", input=ankle_FK_ctrl_POM.matrixSum)

        ankle_FK_ctrl_POM_manualScale = create_fourByFourMatrix(
            module_name=self.name,
            name="ankle_FK_ctrl_POM_manualScale",
            inputs=[
                [ankle_axes["X"].outputX, ankle_axes["X"].outputY, ankle_axes["X"].outputZ, ankle_axes["X"].outputW],
                [ankle_axes["Y"].outputX, ankle_axes["Y"].outputY, ankle_axes["Y"].outputZ, ankle_axes["Y"].outputW],
                [ankle_axes["Z"].outputX, ankle_axes["Z"].outputY, ankle_axes["Z"].outputZ, ankle_axes["Z"].outputW],
                [lower_length_manualScale.output]
            ]
        )

        ankle_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_ankle_FK_guide_outWIM")
        pm.connectAttr(self.ankle_FK_guide_outWM.outputMatrix, ankle_FK_guide_outWIM.inputMatrix)

        ankle_FK_ctrl_WM = multMatrix(name=f"{self.name}_ankle_FK_ctrl_WM")
        pm.connectAttr(ankle_FK_ctrl_POM_manualScale.output, ankle_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl.worldMatrix[0], ankle_FK_ctrl_WM.matrixIn[1])

        #Connection to ankle FK controller
        pm.connectAttr(ankle_FK_ctrl_WM.matrixSum, ankle_FK_ctrl.offsetParentMatrix)


        foot_ball_guide_outWM = aimMatrix(name=f"{self.name}_foot_ball_guide_outWM")
        pm.connectAttr(foot_ball_guide.worldMatrix[0], foot_ball_guide_outWM.inputMatrix)
        pm.connectAttr(foot_end_guide.worldMatrix[0], foot_ball_guide_outWM.primaryTargetMatrix)

        foot_ball_guide_outWIM = inverseMatrix(name=f"{self.name}_foot_ball_guide_outWIM")
        pm.connectAttr(foot_ball_guide_outWM.outputMatrix, foot_ball_guide_outWIM.inputMatrix)

        foot_ball_FK_ctrl_POM = multMatrix(name=f"{self.name}_foot_ball_FK_ctrl_POM")
        pm.connectAttr(foot_ball_guide_outWM.outputMatrix, foot_ball_FK_ctrl_POM.matrixIn[0])
        pm.connectAttr(ankle_FK_guide_outWIM.outputMatrix, foot_ball_FK_ctrl_POM.matrixIn[1])

        foot_ball_FK_ctrl_WM = multMatrix(name=f"{self.name}_foot_ball_FK_ctrl_WM")
        pm.connectAttr(foot_ball_FK_ctrl_POM.matrixSum, foot_ball_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(ankle_FK_ctrl.worldMatrix[0], foot_ball_FK_ctrl_WM.matrixIn[1])

        pm.connectAttr(foot_ball_FK_ctrl_WM.matrixSum, foot_ball_FK_ctrl.offsetParentMatrix)

        foot_end_outWM = blendMatrix(name=f"{self.name}_foot_end_outWM")
        pm.connectAttr(foot_ball_guide_outWM.outputMatrix, foot_end_outWM.inputMatrix)
        pm.connectAttr(foot_end_guide.worldMatrix[0], foot_end_outWM.target[0].targetMatrix)
        for attr in ["scaleWeight", "rotateWeight", "shearWeight"]:
            pm.setAttr(f"{foot_end_outWM.target[0]}.{attr}", 0)

        foot_end_FK_POM = multMatrix(name=f"{self.name}_foot_end_FK_POM")
        pm.connectAttr(foot_end_outWM.outputMatrix, foot_end_FK_POM.matrixIn[0])
        pm.connectAttr(foot_ball_guide_outWIM.outputMatrix, foot_end_FK_POM.matrixIn[1])

        foot_end_FK_WM = multMatrix(name=f"{self.name}_foot_end_FK_WM")
        pm.connectAttr(foot_end_FK_POM.matrixSum, foot_end_FK_WM.matrixIn[0])
        pm.connectAttr(foot_ball_FK_ctrl.worldMatrix[0], foot_end_FK_WM.matrixIn[1])

        #===============================================================================================================================================
        #===============================================================================================================================================

        #IK foot, reverse-foot, and ankle

        foot_IK_ctrl_POM = create_pom(module_name=self.name, name="foot_IK_ctrl_POM", source_matrix = foot_guide.worldMatrix[0], parentGuide_input = self.parent_moduleGuide_input.worldInverseMatrix[0])

        foot_IK_ctrl_parent_moduleSpaceWM =  multMatrix(name=f"{self.name}_foot_IK_ctrl_{parent_module}SpaceWM")
        pm.connectAttr(foot_IK_ctrl_POM.matrixSum, foot_IK_ctrl_parent_moduleSpaceWM.matrixIn[0])
        pm.connectAttr(self.parent_module_input_WM.matrixSum, foot_IK_ctrl_parent_moduleSpaceWM.matrixIn[1])

        foot_IK_ctrl_mainSpacePOM = create_pom(module_name=self.name, name="foot_IK_ctrl_mainSpacePOM", source_matrix = self.foot_guide_outWM.outputMatrix, parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])
        
        self.foot_IK_ctrl_WM = parentMatrix(f"{self.name}_foot_IK_ctrl_WM")
        pm.connectAttr(foot_IK_ctrl_parent_moduleSpaceWM.matrixSum, self.foot_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(foot_IK_ctrl_mainSpaceEnable.output, self.foot_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.foot_IK_ctrl_WM.target[0].targetMatrix)
        pm.connectAttr(foot_IK_ctrl_mainSpacePOM.matrixSum, self.foot_IK_ctrl_WM.target[0].offsetMatrix)
        pm.connectAttr(foot_IK_ctrl_worldSpaceEnable.output, self.foot_IK_ctrl_WM.target[1].enableTarget)
        pm.connectAttr(self.foot_guide_outWM.outputMatrix, self.foot_IK_ctrl_WM.target[1].offsetMatrix)

        pm.connectAttr(self.foot_IK_ctrl_WM.outputMatrix, foot_IK_ctrl.offsetParentMatrix)

        foot_left_bank_offset = transform(name=f"{self.name}_foot_left_bank_offset")
        foot_right_bank_offset = transform(name=f"{self.name}_foot_right_bank_offset")
        foot_heel_offset = transform(name=f"{self.name}_foot_heel_offset")
        foot_end_offset = transform(name=f"{self.name}_foot_end_offset")
        foot_ball_offset = transform(name=f"{self.name}_foot_ball_offset")

        reverse_foot_hierarchies = {
            "left_bank_hierarchy":{
                "name": "foot_left_bank",
                "guide": foot_left_bank_guide.worldMatrix[0],
                "parent": foot_IK_ctrl.worldMatrix[0],
                "parentGuide": foot_guide.worldInverseMatrix[0]
            },
            "right_bank": {
                "name": "foot_right_bank",
                "guide": foot_right_bank_guide.worldMatrix[0],
                "parent": foot_left_bank_offset.worldMatrix[0],
                "parentGuide": foot_left_bank_guide.worldInverseMatrix[0]
            },
            "heel_hierarchy": {
                "name": "foot_heel",
                "guide": foot_heel_guide.worldMatrix[0],
                "parent": foot_right_bank_offset.worldMatrix[0],
                "parentGuide": foot_right_bank_guide.worldInverseMatrix[0]
            },
            "end_hierarchy": {
                "name": "foot_end",
                "guide": foot_end_guide.worldMatrix[0],
                "parent": foot_heel_offset.worldMatrix[0],
                "parentGuide": foot_heel_guide.worldInverseMatrix[0]
            },
            "ball_hierarchy": {
                "name": "foot_ball",
                "guide": foot_ball_guide.worldMatrix[0],
                "parent": foot_end_offset.worldMatrix[0],
                "parentGuide": foot_end_guide.worldInverseMatrix[0]
            }
        }
        
        foot_hierarchies = {}

        for key, item in reverse_foot_hierarchies.items():
            local_hierarchy = hierarchy_prep(module_name=self.name, name=item["name"], guide=item["guide"], parent=item["parent"], parentGuide=item["parentGuide"])
            pm.connectAttr(f"{local_hierarchy['wm'].node}.matrixSum", f"{self.name}_{item['name']}_offset.offsetParentMatrix")

            foot_hierarchies[item["name"]] = local_hierarchy

        ankle_IK_POM = create_pom(module_name=self.name, name="ankle_IK", source_matrix = self.ankle_FK_guide_outWM.outputMatrix, parentGuide_input = foot_ball_guide.worldInverseMatrix[0])

        ankle_IK_baseWM = multMatrix(name=f"{self.name}_ankle_IK_WM")
        pm.connectAttr(ankle_IK_POM.matrixSum, ankle_IK_baseWM.matrixIn[0])
        pm.connectAttr(foot_ball_offset.worldMatrix[0], ankle_IK_baseWM.matrixIn[1])

        ankle_IK_offset = transform(name=f"{self.name}_ankle_IK_offset")

        pm.connectAttr(ankle_IK_baseWM.matrixSum, ankle_IK_offset.offsetParentMatrix)

        foot_roll_reverse_pma = plusMinusAverage(name=f"{self.name}_foot_roll_reverse_pma")
        foot_roll_reverse_pma.operation.set(2)
        foot_roll_reverse_pma.input1D[0].set(25)
        pm.connectAttr(foot_IK_ctrl.node.roll, foot_roll_reverse_pma.input1D[1])

        foot_roll_subtract_pma = plusMinusAverage(name=f"{self.name}_foot_roll_subtract_pma")
        foot_roll_subtract_pma.operation.set(1)
        foot_roll_subtract_pma.input1D[0].set(25)
        pm.connectAttr(foot_roll_reverse_pma.output1D, foot_roll_subtract_pma.input1D[1])

        foot_roll_tip_multidiv = multiplyDivide(name=f"{self.name}_foot_left_roll_tip_multidiv")
        foot_roll_tip_multidiv.input2X.set(-1)
        pm.connectAttr(foot_roll_reverse_pma.output1D, foot_roll_tip_multidiv.input1X)

        foot_heel_condition = condition(name=f"{self.name}_foot_heel_condition")
        foot_heel_condition.operation.set(4)
        foot_heel_condition.colorIfFalseR.set(0)
        pm.connectAttr(foot_IK_ctrl.node.roll, foot_heel_condition.firstTerm)
        pm.connectAttr(foot_IK_ctrl.node.roll, foot_heel_condition.colorIfTrueR)

        foot_roll_condition = condition(name=f"{self.name}_foot_roll_condition")
        foot_roll_condition.operation.set(2)
        pm.connectAttr(foot_IK_ctrl.node.roll, foot_roll_condition.firstTerm)
        foot_roll_condition.secondTerm.set(25)
        pm.connectAttr(foot_IK_ctrl.node.roll, foot_roll_condition.colorIfFalseR)
        foot_roll_condition.colorIfFalseG.set(0)
        pm.connectAttr(foot_roll_subtract_pma.output1D, foot_roll_condition.colorIfTrueR)
        pm.connectAttr(foot_roll_tip_multidiv.outputX, foot_roll_condition.colorIfTrueG)

        foot_roll_clamp_condition = condition(name=f"{self.name}_foot_roll_clamp_condition")
        foot_roll_clamp_condition.operation.set(4)
        pm.connectAttr(foot_roll_condition.outColorR, foot_roll_clamp_condition.firstTerm)
        pm.connectAttr(foot_roll_condition.outColorR, foot_roll_clamp_condition.colorIfFalseR)

        pm.connectAttr(foot_heel_condition.outColorR, foot_heel_offset.rotateX)
        pm.connectAttr(foot_roll_clamp_condition.outColorR, foot_ball_offset.rotateX)
        pm.connectAttr(foot_roll_condition.outColorG, foot_end_offset.rotateX)

        bank_left_condition = condition(name=f"{self.name}_bank_left_condition")
        bank_left_condition.operation.set(4)
        bank_left_condition.colorIfFalseR.set(0)
        pm.connectAttr(foot_IK_ctrl.node.bank, bank_left_condition.firstTerm)
        pm.connectAttr(foot_IK_ctrl.node.bank, bank_left_condition.colorIfTrueR)

        bank_right_condition = condition(name=f"{self.name}_bank_right_condition")
        bank_right_condition.operation.set(2),
        bank_right_condition.colorIfFalseR.set(0)
        pm.connectAttr(foot_IK_ctrl.node.bank, bank_right_condition.firstTerm)
        pm.connectAttr(foot_IK_ctrl.node.bank, bank_right_condition.colorIfTrueR)

        pm.connectAttr(bank_left_condition.outColorR, foot_left_bank_offset.rotateZ)
        pm.connectAttr(bank_right_condition.outColorR, foot_right_bank_offset.rotateZ)

        #IK knee

        knee_IK_guide_POM = create_pom(module_name=self.name, name="knee_IK_guide_POM", source_matrix = self.orientPlane_guide.outputMatrix, parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])

        knee_IK_clavicleSpaceWM = multMatrix(name=f"{self.name}_IK_clavicleSpaceWM")
        pm.connectAttr(knee_IK_guide_POM.matrixSum, knee_IK_clavicleSpaceWM.matrixIn[0])
        pm.connectAttr(self.main_input.worldMatrix[0], knee_IK_clavicleSpaceWM.matrixIn[1])

        knee_IK_mainSpacePOM = create_pom(module_name=self.name, name="knee_IK_mainSpacePOM", source_matrix=self.orientPlane_guide.outputMatrix, parentGuide_input=self.mainGuide_input.worldInverseMatrix[0])

        self.knee_IK_baseWM = parentMatrix(name=f"{self.name}_knee_IK_baseWM")
        pm.connectAttr(knee_IK_clavicleSpaceWM.matrixSum, self.knee_IK_baseWM.inputMatrix)
        pm.connectAttr(foot_IK_ctrl_mainSpaceEnable.output, self.knee_IK_baseWM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.knee_IK_baseWM.target[0].targetMatrix)
        pm.connectAttr(knee_IK_mainSpacePOM.matrixSum, self.knee_IK_baseWM.target[0].offsetMatrix)
        pm.connectAttr(foot_IK_ctrl_mainSpaceEnable.output, self.knee_IK_baseWM.target[1].enableTarget)
        pm.connectAttr(self.orientPlane_guide.outputMatrix, self.knee_IK_baseWM.target[1].offsetMatrix)

        knee_IK_pos_WM = blendMatrix(name=f"{self.name}_knee_IK_pos_WM")
        pm.connectAttr(self.knee_IK_baseWM.outputMatrix, knee_IK_pos_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, knee_IK_pos_WM.target[0].targetMatrix)
        pm.connectAttr(ankle_IK_offset.worldMatrix[0], knee_IK_pos_WM.target[1].targetMatrix)
        pm.connectAttr(self.settings_ctrl.node.kneeIkBlendpos, knee_IK_pos_WM.target[1].weight)
        knee_IK_pos_WM.target[1].scaleWeight.set(0)
        knee_IK_pos_WM.target[1].rotateWeight.set(0)
        
        knee_IK_rot_WM = aimMatrix(name=f"{self.name}_knee_IK_rot_WM")
        pm.connectAttr(knee_IK_pos_WM.outputMatrix, knee_IK_rot_WM.inputMatrix)
        pm.connectAttr(ankle_IK_offset.worldMatrix[0], knee_IK_rot_WM.primaryTargetMatrix)

        pm.connectAttr(knee_IK_rot_WM.outputMatrix, knee_IK_ctrl.offsetParentMatrix)


        #IK knee Lock

        kneeLock_IK_ctrl_mainSpacePOM = create_pom(module_name=self.name, name="kneeLock_IK_ctrl_mainSpacePOM", source_matrix = self.kneeLock_guide.worldMatrix[0], parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])

        kneeLock_IK_ctrl_mainSpaceWM = multMatrix(name=f"{self.name}_kneeLock_IK_ctrl_{main_module}SpaceWM")
        pm.connectAttr(kneeLock_IK_ctrl_mainSpacePOM.matrixSum, kneeLock_IK_ctrl_mainSpaceWM.matrixIn[0])
        pm.connectAttr(self.main_input.worldMatrix[0], kneeLock_IK_ctrl_mainSpaceWM.matrixIn[1])

        kneeLock_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_kneeLock_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(self.kneeLock_IK_ctrl.node.space, kneeLock_IK_ctrl_worldSpaceEnable.input1)
        kneeLock_IK_ctrl_worldSpaceEnable.input2.set(1)

        self.kneeLock_IK_ctrl_WM = parentMatrix(name=f"{self.name}_kneeLock_IK_ctrl_WM")
        pm.connectAttr(kneeLock_IK_ctrl_mainSpaceWM.matrixSum, self.kneeLock_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(kneeLock_IK_ctrl_worldSpaceEnable.output, self.kneeLock_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(self.kneeLock_guide.worldMatrix[0], self.kneeLock_IK_ctrl_WM.target[0].offsetMatrix)

        pm.connectAttr(self.kneeLock_IK_ctrl_WM.outputMatrix, self.kneeLock_IK_ctrl.offsetParentMatrix)


        #IK Prep

        upper_baseWM_noMainScale = remove_main_scale(module_name=self.name, name="upper_baseWM_noMainScale", world_matrix=upper_baseWM.matrixSum, main_input=self.main_input.worldInverseMatrix[0])

        ankle_IK_ctrl_noMainScale = remove_main_scale(module_name=self.name, name="ankle_IK_ctrl_noMainScale", world_matrix=ankle_IK_offset.worldMatrix[0], main_input=self.main_input.worldInverseMatrix[0])

        current_length = distanceBetween(name=f"{self.name}_current_length")
        pm.connectAttr(upper_baseWM_noMainScale.matrixSum, current_length.inMatrix1)
        pm.connectAttr(ankle_IK_ctrl_noMainScale.matrixSum, current_length.inMatrix2)

        length_ratio = divide(name=f"{self.name}_length_ratio")
        pm.connectAttr(current_length.distance, length_ratio.input1)
        pm.connectAttr(initial_length.output, length_ratio.input2)

        scaler = max_(name=f"{self.name}_scaler")
        pm.connectAttr(length_ratio.output, scaler.input_[0])
        pm.connectAttr(self.float_value_1.outFloat, scaler.input_[1])
        #scaler.input_[1].set(1)

        enable_ikStretch = remapValue(name=f"{self.name}_enable_ikStretch")
        pm.connectAttr(self.settings_ctrl.node.enableIkStretch, enable_ikStretch.inputValue)
        pm.connectAttr(scaler.output, enable_ikStretch.outputMax)
        enable_ikStretch.outputMin.set(1)

        upper_length = multiply(name=f"{self.name}_upper_length")
        pm.connectAttr(enable_ikStretch.outValue, upper_length.input_[0])
        pm.connectAttr(upper_length_manualScale.output, upper_length.input_[1])

        lower_length = multiply(name=f"{self.name}_lower_length")
        pm.connectAttr(enable_ikStretch.outValue, lower_length.input_[0])
        pm.connectAttr(lower_length_manualScale.output, lower_length.input_[1])

        length = sum_(name=f"{self.name}_length")
        pm.connectAttr(upper_length.output, length.input_[0])
        pm.connectAttr(lower_length.output, length.input_[1])

        clampedLength = min_(name=f"{self.name}_clampedLength")
        pm.connectAttr(length.output, clampedLength.input_[0])
        pm.connectAttr(current_length.distance, clampedLength.input_[1])

        clampedLength_squared = multiply(name=f"{self.name}_clampedLength_squared")
        pm.connectAttr(clampedLength.output, clampedLength_squared.input_[0])
        pm.connectAttr(clampedLength.output, clampedLength_squared.input_[1])


        #SOFT IK -> Maybe separate in to more functions 

        soft_IK_solver = create_ik_solver_setup(
            module_name=self.name,
            float_value_2=self.float_value_2,
            name = "softIK", 
            upper_length = upper_length.output, 
            lower_length = lower_length.output, 
            total_length = clampedLength.output, 
            total_length_squared = clampedLength_squared.output
            )
        
        upper_softIK_cosValue = soft_IK_solver["upper_cosValue"]
        upper_softIK_cosValueSquared = soft_IK_solver["upper_cosValueSquared"]

        upper_softIK_cosValueRemapped = remapValue(name=f"{self.name}_upper_softIK_cosValueRemapped")
        pm.connectAttr(self.settings_ctrl.node.softIkStart, upper_softIK_cosValueRemapped.inputMin)
        pm.connectAttr(upper_softIK_cosValue.output, upper_softIK_cosValueRemapped.inputValue)

        upper_softIK_cubicBlendValue = multiply(name=f"{self.name}_upper_softIK_cubicBlendValue")
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[0])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[1])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[2])

        ease_in_out_mult = multiply(name=f"{self.name}_ease_in_out_mult")
        pm.connectAttr(self.float_value_minus2.outFloat, ease_in_out_mult.input_[0])
        #ease_in_out_mult.input_[0].set(-2)
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_mult.input_[1])

        ease_in_out_sum = sum_(name=f"{self.name}_ease_in_out_sum")
        pm.connectAttr(ease_in_out_mult.output, ease_in_out_sum.input_[0])
        pm.connectAttr(self.float_value_2.outFloat, ease_in_out_sum.input_[1])
        #ease_in_out_sum.input_[1].set(2)

        ease_in_out_power = power(name=f"{self.name}_ease_in_out_power")
        pm.connectAttr(ease_in_out_sum.output, ease_in_out_power.input_)
        ease_in_out_power.exponent.set(3)

        ease_in_out_divide = divide(name=f"{self.name}_ease_in_out_divide")
        pm.connectAttr(ease_in_out_power.output, ease_in_out_divide.input1)
        ease_in_out_divide.input2.set(2)

        ease_in_out_subtract = subtract(name=f"{self.name}_ease_in_out_subtract")
        ease_in_out_subtract.input1.set(1)
        pm.connectAttr(ease_in_out_divide.output, ease_in_out_subtract.input2)

        ease_in_out_mult2 = multiply(name=f"{self.name}_ease_in_out_mult2")
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_mult2.input_[0])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_mult2.input_[1])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_mult2.input_[2])
        pm.connectAttr(self.float_value_4.outFloat, ease_in_out_mult2.input_[3])
        #ease_in_out_mult2.input_[3].set(4)

        upper_softIK_heightSquared = subtract(name=f"{self.name}_upper_softIK_heightSquared")
        upper_softIK_heightSquared.input1.set(1)
        pm.connectAttr(upper_softIK_cosValueSquared.output, upper_softIK_heightSquared.input2)

        upper_softIK_smoothStepBlendValue = smoothStep(name=f"{self.name}_upper_softIK_smoothStepBlendValue")
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_smoothStepBlendValue.input_)
        upper_softIK_smoothStepBlendValue.rightEdge.set(1)

        ease_in_out_condition = condition(name=f"{self.name}_ease_in_out_condition")
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_condition.firstTerm)
        ease_in_out_condition.secondTerm.set(0.5)
        ease_in_out_condition.operation.set(4)
        pm.connectAttr(ease_in_out_subtract.output, ease_in_out_condition.colorIfFalseR) #might need change
        pm.connectAttr(ease_in_out_mult2.output, ease_in_out_condition.colorIfTrueR) #might need change

        upper_softIK_linearTargetHeight = subtract(name=f"{self.name}_upper_softIK_linearTargetHeight")
        upper_softIK_linearTargetHeight.input1.set(1)
        pm.connectAttr(upper_softIK_cosValue.output, upper_softIK_linearTargetHeight.input2)

        upper_softIK_heighthSqaredClamped = max_(name=f"{self.name}_upper_softIK_heighthSqaredClamped")
        pm.connectAttr(self.float_value_0.outFloat, upper_softIK_heighthSqaredClamped.input_[0])
        #upper_softIK_heighthSqaredClamped.input_[0].set(0)
        pm.connectAttr(upper_softIK_heightSquared.output, upper_softIK_heighthSqaredClamped.input_[1])

        softIK_blendcurve_selector = choice(name=f"{self.name}_softIK_blendcurve_selector")
        pm.connectAttr(self.settings_ctrl.node.softIkCurve, softIK_blendcurve_selector.selector)
        pm.connectAttr(ease_in_out_condition.outColorR, softIK_blendcurve_selector.input_[0])
        pm.connectAttr(upper_softIK_smoothStepBlendValue.output, softIK_blendcurve_selector.input_[1])
        pm.connectAttr(upper_softIK_cubicBlendValue.output, softIK_blendcurve_selector.input_[2])

        upper_softIK_quadraticTargetHeight = multiply(name=f"{self.name}_upper_softIK_quadraticTargetHeight")
        pm.connectAttr(upper_softIK_linearTargetHeight.output, upper_softIK_quadraticTargetHeight.input_[0])
        pm.connectAttr(upper_softIK_linearTargetHeight.output, upper_softIK_quadraticTargetHeight.input_[1])

        upper_softIK_height = power(name=f"{self.name}_upper_softIK_height")
        pm.connectAttr(upper_softIK_heighthSqaredClamped.output, upper_softIK_height.input_)
        upper_softIK_height.exponent.set(0.5)

        segment_lengthRatio = divide(name=f"{self.name}_segment_lengthRatio")
        pm.connectAttr(upper_length.output, segment_lengthRatio.input1)
        pm.connectAttr(lower_length.output, segment_lengthRatio.input2)
        

        upper_softIK_blendedHeight = blendTwoAttr(name=f"{self.name}_upper_softIK_blendedHeight")
        pm.connectAttr(softIK_blendcurve_selector.output, upper_softIK_blendedHeight.attributesBlender)
        pm.connectAttr(upper_softIK_height.output, upper_softIK_blendedHeight.input_[0])
        pm.connectAttr(upper_softIK_quadraticTargetHeight.output, upper_softIK_blendedHeight.input_[1])

        lower_softIK_height = multiply(name=f"{self.name}_lower_softIK_height")
        pm.connectAttr(upper_softIK_height.output, lower_softIK_height.input_[0])
        pm.connectAttr(segment_lengthRatio.output, lower_softIK_height.input_[1])

        upper_softIK_blendedHeightSquared = multiply(name=f"{self.name}_upper_softIK_blendedHeightSquared")
        pm.connectAttr(upper_softIK_blendedHeight.output, upper_softIK_blendedHeightSquared.input_[0])
        pm.connectAttr(upper_softIK_blendedHeight.output, upper_softIK_blendedHeightSquared.input_[1])

        lower_softIK_heightSquared = multiply(name=f"{self.name}_lower_softIK_heightSquared")
        pm.connectAttr(lower_softIK_height.output, lower_softIK_heightSquared.input_[0])
        pm.connectAttr(lower_softIK_height.output, lower_softIK_heightSquared.input_[1])

        lower_softIK_blendedHeight = multiply(name=f"{self.name}_lower_softIK_blendedHeight")
        pm.connectAttr(upper_softIK_blendedHeight.output, lower_softIK_blendedHeight.input_[0])
        pm.connectAttr(segment_lengthRatio.output, lower_softIK_blendedHeight.input_[1])

        upper_softIK_scalerSquared = sum_(name=f"{self.name}_upper_softIK_scalerSquared")
        pm.connectAttr(upper_softIK_blendedHeightSquared.output, upper_softIK_scalerSquared.input_[0])
        pm.connectAttr(upper_softIK_cosValueSquared.output, upper_softIK_scalerSquared.input_[1])

        lower_softIK_cosValueSquared = subtract(name=f"{self.name}_lower_softIK_cosValueSquared")
        lower_softIK_cosValueSquared.input1.set(1)
        pm.connectAttr(lower_softIK_heightSquared.output, lower_softIK_cosValueSquared.input2)

        lower_softIK_blendedHeightSquared = multiply(name=f"{self.name}_lower_softIK_blendedHeightSquared")
        pm.connectAttr(lower_softIK_blendedHeight.output, lower_softIK_blendedHeightSquared.input_[0])
        pm.connectAttr(lower_softIK_blendedHeight.output, lower_softIK_blendedHeightSquared.input_[1])

        upper_softIK_scaler = power(name=f"{self.name}_upper_softIK_scaler")
        pm.connectAttr(upper_softIK_scalerSquared.output, upper_softIK_scaler.input_)
        upper_softIK_scaler.exponent.set(0.5)

        lower_softIK_scalerSquared = sum_(name=f"{self.name}_lower_softIK_scalerSquared")
        pm.connectAttr(lower_softIK_cosValueSquared.output, lower_softIK_scalerSquared.input_[0])
        pm.connectAttr(lower_softIK_blendedHeightSquared.output, lower_softIK_scalerSquared.input_[1])

        disable_soft_ik = not_(name=f"{self.name}_disable_soft_ik")
        pm.connectAttr(self.settings_ctrl.node.enableSoftIk, disable_soft_ik.input_)

        lower_softIK_scaler = power(name=f"{self.name}_lower_softIK_scaler")
        pm.connectAttr(lower_softIK_scalerSquared.output, lower_softIK_scaler.input_)
        lower_softIK_scaler.exponent.set(0.5)


        #knee Lock part

        upper_softIK_scaler_enable = max_(name=f"{self.name}_upper_softIK_scaler_enable")
        pm.connectAttr(disable_soft_ik.output, upper_softIK_scaler_enable.input_[0])
        pm.connectAttr(upper_softIK_scaler.output, upper_softIK_scaler_enable.input_[1])

        kneeLock_IK_ctrl_noMainScale = remove_main_scale(module_name=self.name, name="kneeLock_IK_ctrl_noMainScale", world_matrix=self.kneeLock_IK_ctrl.worldMatrix[0], main_input=self.main_input.worldInverseMatrix[0])

        lower_softIK_scaler_enable = max_(name=f"{self.name}_lower_softIK_scaler_enable")
        pm.connectAttr(disable_soft_ik.output, lower_softIK_scaler_enable.input_[0])
        pm.connectAttr(lower_softIK_scaler.output, lower_softIK_scaler_enable.input_[1])

        kneeLock_IK_upperLength = distanceBetween(name=f"{self.name}_kneeLock_IK_upperLength")
        pm.connectAttr(upper_baseWM_noMainScale.matrixSum, kneeLock_IK_upperLength.inMatrix1)
        pm.connectAttr(kneeLock_IK_ctrl_noMainScale.matrixSum, kneeLock_IK_upperLength.inMatrix2)

        kneeLock_IK_lowerLength = distanceBetween(name=f"{self.name}_kneeLock_IK_lowerLength")
        pm.connectAttr(kneeLock_IK_ctrl_noMainScale.matrixSum, kneeLock_IK_lowerLength.inMatrix1)
        pm.connectAttr(ankle_IK_ctrl_noMainScale.matrixSum, kneeLock_IK_lowerLength.inMatrix2)


        #IK Solver

        upper_lengthScaled = multiply(name=f"{self.name}_upper_lengthScaled")
        pm.connectAttr(upper_length.output, upper_lengthScaled.input_[0])
        pm.connectAttr(upper_softIK_scaler_enable.output, upper_lengthScaled.input_[1])

        lower_lengthScaled = multiply(name=f"{self.name}_lower_lengthScaled")
        pm.connectAttr(lower_length.output, lower_lengthScaled.input_[0])
        pm.connectAttr(lower_softIK_scaler_enable.output, lower_lengthScaled.input_[1])

        upper_kneeLock_lengthSwitch = blendTwoAttr(name=f"{self.name}_upper_kneeLock_lengthSwitch")
        pm.connectAttr(self.kneeLock_IK_ctrl.node.Lock, upper_kneeLock_lengthSwitch.attributesBlender)
        pm.connectAttr(upper_lengthScaled.output, upper_kneeLock_lengthSwitch.input_[0])
        pm.connectAttr(kneeLock_IK_upperLength.distance, upper_kneeLock_lengthSwitch.input_[1])

        lower_kneeLock_lengthSwitch = blendTwoAttr(name=f"{self.name}_lower_kneeLock_lengthSwitch")
        pm.connectAttr(self.kneeLock_IK_ctrl.node.Lock, lower_kneeLock_lengthSwitch.attributesBlender)
        pm.connectAttr(lower_lengthScaled.output, lower_kneeLock_lengthSwitch.input_[0])
        pm.connectAttr(kneeLock_IK_lowerLength.distance, lower_kneeLock_lengthSwitch.input_[1])

        ik_solver = create_ik_solver_setup(
            module_name=self.name,
            float_value_2=self.float_value_2,
            name="IK",
            upper_length = upper_kneeLock_lengthSwitch.output,
            lower_length = lower_kneeLock_lengthSwitch.output,
            total_length = clampedLength.output,
            total_length_squared = clampedLength_squared.output
            )

        upper_IK_cosValue = ik_solver["upper_cosValue"]
        lower_IK_cosValue = ik_solver["lower_cosValue"]
        lower_IK_cosValueSquared = ik_solver["lower_cosValueSquared"]

        upper_IK_acos = acos(name=f"{self.name}_upper_IK_acos")
        pm.connectAttr(upper_IK_cosValue.output, upper_IK_acos.input_)

        upper_IK_sin = sin(name=f"{self.name}_upper_IK_sin")
        pm.connectAttr(upper_IK_acos.output, upper_IK_sin.input_)

        lower_IK_sinSquared = subtract(name=f"{self.name}_lower_IK_sinSquared")
        lower_IK_sinSquared.input1.set(1)
        pm.connectAttr(lower_IK_cosValueSquared.output, lower_IK_sinSquared.input2)

        kneeLock_IK_ctrl_WPos = translationFromMatrix(name=f"{self.name}_kneeLock_IK_ctrl_WPos")
        pm.connectAttr(self.kneeLock_IK_ctrl.worldMatrix[0], kneeLock_IK_ctrl_WPos.input_)

        upper_baseWPos = translationFromMatrix(name=f"{self.name}_upper_baseWPos")
        pm.connectAttr(upper_WM_test.matrixSum, upper_baseWPos.input_)

        kneeLock_IK_poleVector = plusMinusAverage(name=f"{self.name}_kneeLock_IK_poleVector")
        kneeLock_IK_poleVector.operation.set(2)
        pm.connectAttr(kneeLock_IK_ctrl_WPos.output, kneeLock_IK_poleVector.input3D[0])
        pm.connectAttr(upper_baseWPos.output, kneeLock_IK_poleVector.input3D[1])

        knee_IK_poleVector = multiplyVectorByMatrix(name=f"{self.name}_knee_IK_poleVector")
        knee_IK_poleVector.input_.set(0, 1, 0)
        pm.connectAttr(knee_IK_ctrl.worldMatrix[0], knee_IK_poleVector.matrix)

        upper_IK_sin_negated = negate(name=f"{self.name}_upper_IK_sin_negated")
        pm.connectAttr(upper_IK_sin.output, upper_IK_sin_negated.input_)

        lower_IK_sinSquaredClamped = max_(name=f"{self.name}_lower_IK_sinSquaredClamped")
        pm.connectAttr(self.float_value_0.outFloat, lower_IK_sinSquaredClamped.input_[0])
        #lower_IK_sinSquaredClamped.input_[0].set(0)
        pm.connectAttr(lower_IK_sinSquared.output, lower_IK_sinSquaredClamped.input_[1])

        knee_IK_poleVectorSwitch = blendColors(name=f"{self.name}_knee_IK_poleVectorSwitch")
        pm.connectAttr(self.kneeLock_IK_ctrl.node.Lock, knee_IK_poleVectorSwitch.blender)
        
        pm.connectAttr(kneeLock_IK_poleVector.output3D, knee_IK_poleVectorSwitch.color1)
        pm.connectAttr(knee_IK_poleVector.output, knee_IK_poleVectorSwitch.color2)

        lower_IK_sin = power(name=f"{self.name}_lower_IK_sin")
        pm.connectAttr(lower_IK_sinSquaredClamped.output, lower_IK_sin.input_)
        lower_IK_sin.exponent.set(0.5)

        IK_baseWM = aimMatrix(name=f"{self.name}_IK_baseWM")
        pm.connectAttr(upper_WM_test.matrixSum, IK_baseWM.inputMatrix)
        pm.connectAttr(ankle_IK_offset.worldMatrix[0], IK_baseWM.primaryTargetMatrix)
        IK_baseWM.secondaryMode.set(2)
        pm.connectAttr(knee_IK_poleVectorSwitch.output, IK_baseWM.secondaryTargetVector)

        upper_IK_localRotMatrix = create_fourByFourMatrix(
            module_name=self.name,
            name="upper_IK_localRotMatrix",
            inputs=[
                [upper_IK_cosValue.output, upper_IK_sin.output],
                [upper_IK_sin_negated.output, upper_IK_cosValue.output]
            ]
        )

        lower_IK_sin_negated = negate(name=f"{self.name}_negate2")
        pm.connectAttr(lower_IK_sin.output, lower_IK_sin_negated.input_)

        lower_IK_cosValue_negated = negate(name=f"{self.name}_negate3")
        pm.connectAttr(lower_IK_cosValue.output, lower_IK_cosValue_negated.input_)

        upper_IK_WM = multMatrix(name=f"{self.name}_upper_IK_WM")
        pm.connectAttr(upper_IK_localRotMatrix.output, upper_IK_WM.matrixIn[0])
        pm.connectAttr(IK_baseWM.outputMatrix, upper_IK_WM.matrixIn[1])

        lower_IK_localRotMatrix = create_fourByFourMatrix(
            module_name=self.name,
            name="lower_IK_localRotMatrix",
            inputs=[
                [lower_IK_cosValue_negated.output, lower_IK_sin_negated.output],
                [lower_IK_sin.output, lower_IK_cosValue_negated.output],
                [0, 0, 1, 0],
                [upper_kneeLock_lengthSwitch.output]
            ]
        )

        lower_IK_WM = multMatrix(name=f"{self.name}_lower_IK_WM")
        pm.connectAttr(lower_IK_localRotMatrix.output, lower_IK_WM.matrixIn[0])
        pm.connectAttr(upper_IK_WM.matrixSum, lower_IK_WM.matrixIn[1])

        lower_IK_WIM = inverseMatrix(name=f"{self.name}_lower_IK_WIM")
        pm.connectAttr(lower_IK_WM.matrixSum, lower_IK_WIM.inputMatrix)

        ankle_IK_baseLocalMatrix = multMatrix(name=f"{self.name}_ankle_IK_baseLocalMatrix")
        pm.connectAttr(ankle_IK_offset.worldMatrix[0], ankle_IK_baseLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_IK_WIM.outputMatrix, ankle_IK_baseLocalMatrix.matrixIn[1])

        ankle_IK_axes = extract_matrix_axes(module_name=self.name, name="ankle_IK_baseLocalMatrix", input=ankle_IK_baseLocalMatrix.matrixSum)

        ankle_IK_localMatrix = create_fourByFourMatrix(
            module_name=self.name,
            name="ankle_IK_localMatrix",
            inputs=[
                [ankle_IK_axes["X"].outputX, ankle_IK_axes["X"].outputY, ankle_IK_axes["X"].outputZ, ankle_IK_axes["X"].outputW],
                [ankle_IK_axes["Y"].outputX, ankle_IK_axes["Y"].outputY, ankle_IK_axes["Y"].outputZ, ankle_IK_axes["Y"].outputW],
                [ankle_IK_axes["Z"].outputX, ankle_IK_axes["Z"].outputY, ankle_IK_axes["Z"].outputZ, ankle_IK_axes["Z"].outputW],
                [lower_kneeLock_lengthSwitch.output]
            ]
        )

        #IK/FK Switch
        
        lower_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_lower_FK_ctrl_outLocalMatrix")
        pm.connectAttr(lower_FK_ctrl.matrix, lower_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl_POM_manualScale.output, lower_FK_ctrl_outLocalMatrix.matrixIn[1])

        ankle_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_ankle_FK_ctrl_outLocalMatrix")
        pm.connectAttr(ankle_FK_ctrl.matrix, ankle_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(ankle_FK_ctrl_POM_manualScale.output, ankle_FK_ctrl_outLocalMatrix.matrixIn[1])

        blends = {
            "upper": create_ik_fk_blend(
                self.name,
                "upper_WM", 
                upper_FK_ctrl.worldMatrix[0], 
                upper_IK_WM.matrixSum, 
                self.settings_ctrl.node.useIK
            ),
            "lower_local": create_ik_fk_blend(
                self.name,
                "lower_localMatrix", 
                lower_FK_ctrl_outLocalMatrix.matrixSum, 
                lower_IK_localRotMatrix.output, 
                self.settings_ctrl.node.useIK
            ),
            "ankle_local": create_ik_fk_blend(
                self.name,
                "ankle_localMatrix", 
                ankle_FK_ctrl_outLocalMatrix.matrixSum, 
                ankle_IK_localMatrix.output, 
                self.settings_ctrl.node.useIK
            ),
            "foot_ball": create_ik_fk_blend(
                self.name,
                "foot_ball_localMatrix", 
                foot_ball_FK_ctrl.worldMatrix[0], 
                foot_ball_offset.worldMatrix[0], 
                self.settings_ctrl.node.useIK
            ),
            "foot_end": create_ik_fk_blend(
                self.name,
                "foot_end_localMatrix", 
                foot_end_FK_WM.matrixSum, 
                foot_end_offset.worldMatrix[0], 
                self.settings_ctrl.node.useIK
            )
        }

        upper_WM = blends["upper"]
        lower_localMatrix = blends["lower_local"]
        ankle_localMatrix = blends["ankle_local"]
        foot_ball_localMatrix = blends["foot_ball"]
        foot_end_localMatrix = blends["foot_end"]

        lower_WM = multMatrix(name=f"{self.name}_lower_WM")
        pm.connectAttr(lower_localMatrix.outputMatrix, lower_WM.matrixIn[0])
        pm.connectAttr(upper_WM.outputMatrix, lower_WM.matrixIn[1])

        ankle_WM = multMatrix(name=f"{self.name}_ankle_WM")
        pm.connectAttr(ankle_localMatrix.outputMatrix, ankle_WM.matrixIn[0])
        pm.connectAttr(lower_WM.matrixSum, ankle_WM.matrixIn[1])

        #Joints
        upper_jnt = joint(name=f"{self.name}_upper_jnt")
        pm.connectAttr(upper_WM.outputMatrix, upper_jnt.offsetParentMatrix)
        
        lower_jnt = joint(f"{self.name}_lower_jnt")
        pm.connectAttr(lower_WM.matrixSum, lower_jnt.offsetParentMatrix)

        ankle_jnt = joint(f"{self.name}_ankle_jnt")
        pm.connectAttr(ankle_WM.matrixSum, ankle_jnt.offsetParentMatrix)

        foot_ball_jnt = joint(name=f"{self.name}_foot_ball_jnt")
        pm.connectAttr(foot_ball_localMatrix.outputMatrix, foot_ball_jnt.offsetParentMatrix)

        foot_end_jnt = joint(name=f"{self.name}_foot_end_jnt")
        pm.connectAttr(foot_end_localMatrix.outputMatrix, foot_end_jnt.offsetParentMatrix)


        #Ribbon
        lower_tangent = blendMatrix(name=f"{self.name}_lower_tangent")
        pm.connectAttr(upper_WM.outputMatrix, lower_tangent.inputMatrix)
        pm.connectAttr(lower_WM.matrixSum, lower_tangent.target[0].targetMatrix)
        pm.connectAttr(self.settings_ctrl.node.kneeTangent, lower_tangent.target[0].rotateWeight)

        roundness_negate = negate(name=f"{self.name}_roundness_negate")
        pm.connectAttr(self.settings_ctrl.node.ribbonRoundness, roundness_negate.input_)

        lower_ribbon_pin_transform_grp = transform(name=f"{self.name}_lower_ribbon_pin_transform_grp")
        lower_ribbon_pin_start_transform_grp = transform(name=f"{self.name}_lower_ribbon_pin_start_transform_grp")
        lower_ribbon_pin_end_transform_grp = transform(name=f"{self.name}_lower_ribbon_pin_end_transform_grp")

        lower_ribbon_ctrl = control.create(ctrl_type="square", name=f"{self.name}_lower_ribbon_ctrl", normal=(1, 0, 0), color=ik_color)
        lower_start_ribbon_ctrl = control.create(ctrl_type="square", name=f"{self.name}_lower_start_ribbon_ctrl", normal=(1, 0, 0), color=ik_color)
        lower_end_ribbon_ctrl = control.create(ctrl_type="square", name=f"{self.name}_lower_end_ribbon_ctrl", normal=(1, 0, 0), color=ik_color)

        upper_midpoint = blendMatrix(name=f"{self.name}_upper_midpoint")
        pm.connectAttr(upper_WM.outputMatrix, upper_midpoint.inputMatrix)
        pm.connectAttr(lower_start_ribbon_ctrl.worldMatrix[0], upper_midpoint.target[0].targetMatrix)
        upper_midpoint.target[0].weight.set(0.5)

        upper_midpoint_aim = aimMatrix(name=f"{self.name}_upper_midpoint_aim")
        pm.connectAttr(upper_midpoint.outputMatrix, upper_midpoint_aim.inputMatrix)
        pm.connectAttr(lower_start_ribbon_ctrl.worldMatrix[0], upper_midpoint_aim.primaryTargetMatrix)
        
        lower_midpoint = blendMatrix(name=f"{self.name}_lower_midpoint")
        pm.connectAttr(lower_end_ribbon_ctrl.worldMatrix[0], lower_midpoint.inputMatrix)
        pm.connectAttr(ankle_WM.matrixSum, lower_midpoint.target[0].targetMatrix)
        lower_midpoint.target[0].weight.set(0.5)

        lower_midpoint_aim = aimMatrix(name=f"{self.name}_lower_midpoint_aim")
        pm.connectAttr(lower_midpoint.outputMatrix, lower_midpoint_aim.inputMatrix)
        pm.connectAttr(ankle_WM.matrixSum, lower_midpoint_aim.primaryTargetMatrix)
        pm.connectAttr(lower_end_ribbon_ctrl.worldMatrix[0], lower_midpoint_aim.secondaryTargetMatrix)

        upper_midpoint_ctrl = control.create(ctrl_type="square", name=f"{self.name}_upper_midpoint_ctrl", normal=(1, 0, 0), color=ik_color)
        lower_midpoint_ctrl = control.create(ctrl_type="square", name=f"{self.name}_lower_midpoint_ctrl", normal=(1, 0, 0), color=ik_color)
        pm.connectAttr(upper_midpoint_aim.outputMatrix, upper_midpoint_ctrl.offsetParentMatrix)
        pm.connectAttr(lower_midpoint_aim.outputMatrix, lower_midpoint_ctrl.offsetParentMatrix)

        curve_dict = setup_ribbon_system(
            module_name = self.name,
            groups = self.groups,
            upper_WM = upper_WM.outputMatrix,
            upper_midpoint_ctrl = upper_midpoint_ctrl.worldMatrix[0],
            lower_start_ribbon_ctrl = lower_start_ribbon_ctrl.worldMatrix[0],
            lower_ribbon_ctrl = lower_ribbon_ctrl.worldMatrix[0],
            lower_end_ribbon_ctrl = lower_end_ribbon_ctrl.worldMatrix[0],
            lower_midpoint_ctrl = lower_midpoint_ctrl.worldMatrix[0],
            ankle_WM = ankle_WM.matrixSum
        )

        pm.connectAttr(lower_tangent.outputMatrix, lower_ribbon_pin_transform_grp.offsetParentMatrix)
        pm.connectAttr(lower_ribbon_pin_transform_grp.worldMatrix[0], lower_ribbon_ctrl.offsetParentMatrix)

        pm.connectAttr(lower_ribbon_ctrl.worldMatrix[0], lower_ribbon_pin_start_transform_grp.offsetParentMatrix)
        pm.connectAttr(roundness_negate.output, lower_ribbon_pin_start_transform_grp.translateX)
        pm.connectAttr(lower_ribbon_pin_start_transform_grp.worldMatrix[0], lower_start_ribbon_ctrl.offsetParentMatrix)

        pm.connectAttr(lower_ribbon_ctrl.worldMatrix[0], lower_ribbon_pin_end_transform_grp.offsetParentMatrix)
        pm.connectAttr(roundness_negate.input_, lower_ribbon_pin_end_transform_grp.translateX) #============================== Input plugged through for autocompletion
        pm.connectAttr(lower_ribbon_pin_end_transform_grp.worldMatrix[0], lower_end_ribbon_ctrl.offsetParentMatrix)

        upper_bezier_curve = curve_dict["top_curve"]
        middle_bezier_curve = curve_dict["middle_curve"]
        down_bezier_curve = curve_dict["down_curve"]

        upper_bezier_curveShape = upper_bezier_curve.node.getShape()
        middle_bezier_curveShape = middle_bezier_curve.node.getShape()
        down_bezier_curveShape = down_bezier_curve.node.getShape()

        ribbon_loft = loft(name=f"{self.name}_ribbon_loft")
        pm.connectAttr(upper_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[0])
        pm.connectAttr(middle_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[1])
        pm.connectAttr(down_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[2])
        ribbon_loft.uniform.set(1)
        ribbon_loft.autoReverse.set(1)
        ribbon_loft.degree.set(3)
        ribbon_loft.sectionSpans.set(1)
        ribbon_loft.reverseSurfaceNormals.set(True)

        old_ribbon = pm.nurbsPlane(name=f"{self.name}_old_ribbon")[0]
        old_ribbonShape = old_ribbon.getShape()
        old_ribbon.overrideEnabled.set(1)
        old_ribbon.overrideDisplayType.set(1)

        pm.connectAttr(ribbon_loft.outputSurface, old_ribbon.create, force=True)
    
        for ribbon_control in [lower_start_ribbon_ctrl, lower_ribbon_ctrl, lower_end_ribbon_ctrl, upper_midpoint_ctrl, lower_midpoint_ctrl]:
            pm.parent(ribbon_control.node, self.groups["controls"].node)
            pm.connectAttr(self.settings_ctrl.node.show_ribbon_ctrl, ribbon_control.visibility)

        for grp in [lower_ribbon_pin_transform_grp, lower_ribbon_pin_end_transform_grp, lower_ribbon_pin_start_transform_grp]:
            pm.parent(grp.node, self.groups["rigNodes"].node)
        
        for crv in [upper_bezier_curve, middle_bezier_curve, down_bezier_curve]:
            pm.parent(crv.node, self.groups["rigNodes"].node)
            crv.visibility.set(0)

        pm.parent(old_ribbon, self.groups["rigNodes"].node)

        ribbon, ribbon_shape = rebuild_nurbsPlane(
            module_name=self.name,
            input_plane=old_ribbonShape, 
            spans_U=60, 
            spans_V=4, 
            degree_U=1, 
            degree_V=3)

        ribbon_pins, ribbon_joints = add_pin_joints(module_name=self.name, name="ribbon", ribbon=ribbon, number_of_pins=self.bind_jnts, scale_parent=self.main_input.worldMatrix[0])

        ribbon_pin_grp = transform(name=f"{self.name}_ribbon_pin_grp")
        ribbon_joints_grp = transform(name=f"{self.name}_ribbon_joints_grp")

        for pin, jnt in zip(ribbon_pins, ribbon_joints):
            pm.parent(pin, ribbon_pin_grp.node)
            pm.parent(jnt.node, ribbon_joints_grp.node)

        #visibility IK/FK ctrl
        IK_ctrl = [foot_IK_ctrl, knee_IK_ctrl, self.kneeLock_IK_ctrl]
        FK_ctrl = [upper_FK_ctrl, lower_FK_ctrl, ankle_FK_ctrl, foot_ball_FK_ctrl]

        for ctrl in IK_ctrl:
            pm.connectAttr(self.settings_ctrl.node.useIK, ctrl.visibility)

        reverse_ctrl_vis = subtract(name=f"{self.name}_reverse_ctrl_vis")
        reverse_ctrl_vis.input1.set(1)
        pm.connectAttr(self.settings_ctrl.node.useIK, reverse_ctrl_vis.input2)

        for ctrl in FK_ctrl:
            pm.connectAttr(reverse_ctrl_vis.output, ctrl.visibility)



        #helper prep

        lower_IK_WPos = translationFromMatrix(name=f"{self.name}_lower_IK_WPos")
        pm.connectAttr(lower_IK_WM.matrixSum, lower_IK_WPos.input_)

        upper_WPos = translationFromMatrix(name=f"{self.name}_upper_WPos")
        pm.connectAttr(upper_WM.outputMatrix, upper_WPos.input_)

        lower_WPos = translationFromMatrix(name=f"{self.name}_lower_WPos")
        pm.connectAttr(lower_WM.matrixSum, lower_WPos.input_)

        ankle_WPos = translationFromMatrix(name=f"{self.name}_ankle_WPos")
        pm.connectAttr(ankle_WM.matrixSum, ankle_WPos.input_)

        foot_ball_WPos = translationFromMatrix(name=f"{self.name}_foot_ball_WPos")
        pm.connectAttr(foot_ball_localMatrix.outputMatrix, foot_ball_WPos.input_)

        foot_end_WPos = translationFromMatrixDL(name=f"{self.name}_foot_end_WPos")
        pm.connectAttr(foot_end_localMatrix.outputMatrix, foot_end_WPos.input_)

        #helpers without autocompletion it sucks I know
        kneeLock_IK_helper = control.create_connection_curve(name=f"{self.name}_kneeLock_IK_helper", color=ik_color)
        kneeLock_IK_helperShape = kneeLock_IK_helper.node.getShape()
        pm.connectAttr(kneeLock_IK_ctrl_WPos.output, kneeLock_IK_helperShape.controlPoints[0])
        pm.connectAttr(lower_IK_WPos.output, kneeLock_IK_helperShape.controlPoints[1])

        upper_proxy_helper = control.create_connection_curve(name=f"{self.name}_upper_proxy_helper", color=limb_connection_color)
        upper_proxy_helperShape = upper_proxy_helper.node.getShape()
        upper_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(upper_WPos.output, upper_proxy_helperShape.controlPoints[0])
        pm.connectAttr(lower_WPos.output, upper_proxy_helperShape.controlPoints[1])

        lower_proxy_helper = control.create_connection_curve(name=f"{self.name}_lower_proxy_helper", color=limb_connection_color)
        lower_proxy_helperShape = lower_proxy_helper.node.getShape()
        lower_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(lower_WPos.output, lower_proxy_helperShape.controlPoints[0])
        pm.connectAttr(ankle_WPos.output, lower_proxy_helperShape.controlPoints[1])

        foot_ball_proxy_helper = control.create_connection_curve(name=f"{self.name}_foot_ball_proxy_helper", color=limb_connection_color)
        foot_ball_proxy_helperShape = foot_ball_proxy_helper.node.getShape()
        foot_ball_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(ankle_WPos.output, foot_ball_proxy_helperShape.controlPoints[0])
        pm.connectAttr(foot_ball_WPos.output, foot_ball_proxy_helperShape.controlPoints[1])

        foot_end_proxy_helper = control.create_connection_curve(name=f"{self.name}_foot_end_proxy_helper", color=limb_connection_color)
        foot_end_proxy_helperShape = foot_end_proxy_helper.node.getShape()
        foot_end_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(foot_ball_WPos.output, foot_end_proxy_helperShape.controlPoints[0])
        pm.connectAttr(foot_end_WPos.output, foot_end_proxy_helperShape.controlPoints[1])

        #outputs (could be removed later)
        self.ankle_output = transform(name=f"{self.name}_ankle_output")
        pm.connectAttr(ankle_WM.matrixSum, self.ankle_output.offsetParentMatrix)

        self.ankleGuide_output = transform(name=f"{self.name}_ankleGuide_output")
        pm.connectAttr(ankle_guide.worldMatrix[0], self.ankleGuide_output.offsetParentMatrix)

        #Organizing outliner
        outliner_data = {
            "inputs": [self.main_input, self.mainGuide_input, self.parent_module_input, self.parent_moduleGuide_input],
            "guides": [upper_guide, lower_guide, ankle_guide, settings_guide, self.kneeLock_guide, foot_guide, foot_heel_guide, foot_end_guide, foot_ball_guide, foot_left_bank_guide, foot_right_bank_guide],
            "controls": [upper_FK_ctrl, lower_FK_ctrl, ankle_FK_ctrl, foot_IK_ctrl, knee_IK_ctrl, self.settings_ctrl, self.kneeLock_IK_ctrl, foot_ball_FK_ctrl],
            "helpers": [kneeLock_IK_helper, upper_proxy_helper, lower_proxy_helper, foot_ball_proxy_helper, foot_end_proxy_helper],
            "joints": [upper_jnt, lower_jnt, ankle_jnt, foot_ball_jnt, foot_end_jnt, ribbon_joints_grp],
            "rigNodes": [foot_left_bank_offset, foot_right_bank_offset, foot_heel_offset, foot_end_offset, foot_ball_offset, ankle_IK_offset, ribbon_pin_grp, ribbon],
            "outputs": [self.ankle_output, self.ankleGuide_output]
        }

        for group_name, nodes in outliner_data.items():
            for node in nodes:
                try:
                    pm.parent(node.node, self.groups[group_name].node)
                except:
                    pm.parent(node, self.groups[group_name].node)

    def addParent(self, parent_name="parent"):
        """Adds a new parent internally by creating attributes, connections and inputs.
        Manual input connection is requiered."""
        parent_name = str(parent_name)  # Sicherheit
    
        parent_input = transform(name=f"{self.name}_{parent_name}_input")
        parentGuide_input = transform(name=f"{self.name}_{parent_name}Guide_input")

        pm.parent(parent_input.node, self.groups["inputs"].node)
        pm.parent(parentGuide_input.node, self.groups["inputs"].node)

        self.input_list.append(parent_name)
        self.kneeLock_list.append(parent_name)

        target_index = len(self.input_list) - 1

        kneeTarget_index = len(self.kneeLock_list) - 1

        enumNameStr = ":".join(self.input_list)
        self.settings_ctrl.node.deleteAttr("space")
        self.settings_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=enumNameStr, defaultValue=0, hidden=False, keyable=True)

        knee_enumNameStr = ":".join(self.kneeLock_list)
        self.kneeLock_IK_ctrl.node.deleteAttr("space")
        self.kneeLock_IK_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=knee_enumNameStr, defaultValue=0, hidden=False, keyable=True)

        upper_FK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="upper_FK_ctrl_parentSpacePOM", source_matrix = self.upper_FK_guide_outWM.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        ankle_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="ankle_IK_ctrl_parentSpacePOM", source_matrix = self.ankle_FK_guide_outWM.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        knee_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="knee_IK_ctrl_parentSpacePOM", source_matrix = self.orientPlane_guide.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0]
        )

        ankle_IK_ctrl_parentSpaceEnable = equal(name=f"{self.name}_ankle_IK_ctrl_{parent_name}SpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, ankle_IK_ctrl_parentSpaceEnable.input1)
        ankle_IK_ctrl_parentSpaceEnable.input2.set(target_index)

        #upper fk ctrl space switch
        pm.connectAttr(ankle_IK_ctrl_parentSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.upper_FK_ctrl_rotWM.target[target_index].targetMatrix)
        pm.connectAttr(upper_FK_ctrl_parentSpacePOM.matrixSum, self.upper_FK_ctrl_rotWM.target[target_index].offsetMatrix)

        #ankle ik ctrl space switch
        pm.connectAttr(ankle_IK_ctrl_parentSpaceEnable.output, self.ankle_IK_ctrl_WM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.ankle_IK_ctrl_WM.target[target_index].targetMatrix)
        pm.connectAttr(ankle_IK_ctrl_parentSpacePOM.matrixSum, self.ankle_IK_ctrl_WM.target[target_index].offsetMatrix)

        #knee ik ctrl space switch
        pm.connectAttr(ankle_IK_ctrl_parentSpaceEnable.output, self.knee_IK_baseWM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.knee_IK_baseWM.target[target_index].targetMatrix)
        pm.connectAttr(knee_IK_ctrl_parentSpacePOM.matrixSum, self.knee_IK_baseWM.target[target_index].offsetMatrix)

        kneeLock_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="kneeLock_IK_ctrl_parentSpacePOM", source_matrix = self.kneeLock_guide.worldMatrix[0], parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        kneeLock_IK_ctrl_parentSpaceEnable = equal(name=f"{self.name}_kneeLock_IK_ctrl_{parent_name}Enable")
        pm.connectAttr(self.kneeLock_IK_ctrl.node.space, kneeLock_IK_ctrl_parentSpaceEnable.input1)
        kneeLock_IK_ctrl_parentSpaceEnable.input2.set(kneeTarget_index)

        #kneeLock space switch
        pm.connectAttr(kneeLock_IK_ctrl_parentSpaceEnable.output, self.kneeLock_IK_ctrl_WM.target[kneeTarget_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.kneeLock_IK_ctrl_WM.target[kneeTarget_index].targetMatrix)
        pm.connectAttr(kneeLock_IK_ctrl_parentSpacePOM.matrixSum, self.kneeLock_IK_ctrl_WM.target[kneeTarget_index].offsetMatrix)

    @property
    def rig_module(self):
        return self.groups
    
    @property
    def module_name(self):
        return str(self.groups)

    @property
    def out_parent_input(self):
        return self.parent_module_input

    @property
    def out_parentGuide_input(self):
        return self.parent_moduleGuide_input

    @property
    def out_main_input(self):
        return self.main_input
    
    @property
    def out_mainGuide_input(self):
        return self.mainGuide_input
    
    @property
    def out_ankle_output(self):
        return self.ankle_output

    @property
    def out_ankleGuide_output(self):
        return self.ankleGuide_output