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

class LimbManager:
    def __init__(self):
        self.win_id = "fxs_limb_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Limb Rigging Manager") as win:
            with pm.columnLayout(adj=True):
                self.name = TextFieldHelper("Limb name: ")
                self.limb_side = TextFieldHelper("Limb side ('L' or 'R'): ")
                self.bind_jnts = pm.intFieldGrp(label="Amount bind joints: ", numberOfFields=1)
                self.parent = TextFieldHelper("Parent Group: ")
                self.main = TextFieldHelper("Root Group")
                self.parent_output = TextFieldHelper("Parent Output Group: ")
                self.parent_outputGuide = TextFieldHelper("Parent Output Guide: ")
                self.main_output = TextFieldHelper("Root Controller output group: ")
                self.mainGuide_output = TextFieldHelper("Root Controller output guide: ")
                self.upper_guide_pos = CompoundFieldSlot("Initial position of the upper guide: ")
                self.lower_guide_pos = CompoundFieldSlot("Initial position of the lower guide: ")
                self.hand_guide_pos = CompoundFieldSlot("Initial position of the hand/feet guide: ")
                self.elbowLock_guide_pos = CompoundFieldSlot("Initial position of the elbow/kneeLock guide: ")
                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)
    
    def execute(self, *args):
        
        try:
            name = self.name.control.getText()
            limb_side = self.limb_side.control.getText()
            parent = self.parent.control.getText()
            main = self.main.control.getText()

        except AttributeError:
            pm.error("Naming Error")

        if pm.intFieldGrp(self.bind_jnts, query=True, value1=True) > 0:
            bind_jnts = pm.intFieldGrp(self.bind_jnts, query=True, value1=True)
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
            "hand_guide_pos": self.hand_guide_pos,
            "elbowLock_guide_pos": self.elbowLock_guide_pos
        }

        resolved_positions = {}

        for attr_name, slot in guide_positions.items():
            values = slot.get_values()
            if all(v is not None and v != 0.0 for v in values):
                resolved_positions[attr_name] = values
            else:
                pm.warning(f"{attr_name} contains nonvalid values")
                resolved_positions[attr_name] = None

        kwargs = {"parent_module": parent, "main_module":main, "limb_type": name, "limb_side": limb_side, "fk_color": fk_ctrl_color, "ik_color": ik_ctrl_color, "bind_jnts": bind_jnts}
        for attr_name, value in resolved_positions.items():
            if value is not None:
                kwargs[attr_name] = value
        
        self.module = LimbModule(**kwargs)

        try:
            pm.connectAttr(self.parent_output.obj.offsetParentMatrix, self.module.out_parent_input.offsetParentMatrix)
            pm.connectAttr(self.parent_outputGuide.obj.offsetParentMatrix, self.module.out_parentGuide_input.offsetParentMatrix)
            
            pm.connectAttr(self.main_output.obj.offsetParentMatrix, self.module.out_main_input.offsetParentMatrix)
            pm.connectAttr(self.mainGuide_output.obj.offsetParentMatrix, self.module.out_mainGuide_input.offsetParentMatrix)
        except:
            print("Parent Module connection not possible, manual connection requiered")


class LimbModule:

    def __init__(self, parent_module:str, main_module:str, limb_type:str, limb_side:str, bind_jnts=10, upper_guide_pos:tuple = (4, 25, 0), lower_guide_pos:tuple = (0, 0, 0), 
                 hand_guide_pos:tuple = (14, 25, 0), elbowLock_guide_pos:tuple = (9, 25, -7), settings_guide_pos:tuple = (5, 25, -4), 
                 upper_guide_rot:tuple = (0, 0, 0), fk_color:list = [0, 0, 1], ik_color:list = [0, 0.85, 0.83]):
        
        self.win_id = "fxs_limb_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Arm or basic Limb Rigging Module"):
            with pm.columnLayout(adj=True):
                self.limb_type = TextFieldHelper("Module name: ")
                self.limb_side = TextFieldHelper("Limb side ('L' or 'R'): ")
                self.bind_jnts = TextFieldHelper("Amount bind joints: ")
                self.root_module = TextFieldHelper("Rig root module: ")
                self.parent_module = TextFieldHelper("parent module: ")

        

        
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
        :param hand_guide_pos: hand guide position as (X, Y, Z)
        :type hand_guide_pos: tuple
        :param elbowLock_guide_pos: elbowLock guide position as (X, Y, Z)
        :type elbowLock_guide_pos: tuple
        :param settings_guide_pos: settings guide position as (X, Y, Z)
        :type settings_guide_pos: tuple
        :param upper_guide_rot: Y-Rotation 180 to flip elbow/knee (X, Y, Z)
        :type upper_guide_rot: tuple
        :param fk_color: FK controller color, settings controller color as RGB 0-1 [0, 0, 0]
        :type fk_color: list
        :param ik_color: IK controller, elbowLock controller as RGB 0-1 [0, 0, 0]
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
        hand_guide = create_guide(name=f"{self.name}_hand_guide", position=hand_guide_pos, color=guide_color)

        self.elbowLock_guide = create_guide(name=f"{self.name}_elbowLock_guide", position=elbowLock_guide_pos, color=guide_color)

        settings_guide = create_guide(name=f"{self.name}_settings_guide", position=settings_guide_pos, color=guide_color)

        lower_guide.translateZ.set(lock=True)
        lower_guide.node.setLimit("translateMinY", 0)

        self.main_input = transform(name=f"{self.name}_{main_module}_input")
        self.mainGuide_input = transform(name=f"{self.name}_{main_module}Guide_input")
        self.parent_module_input = transform(name=f"{self.name}_{parent_module}_input")
        self.parent_moduleGuide_input = transform(name=f"{self.name}_{parent_module}Guide_input")

        self.input_list = [parent_module, main_module, "worldSpace"]

        a = aimMatrix()
        

        self.settings_ctrl = control.create(ctrl_type="gear", degree=3, name=f"{self.name}_settings_ctrl", normal=(0, 0, 1), color=fk_color)
        self.settings_ctrl.node.addAttr(attr="custom", niceName="CUSTOM ATTR", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="useIK", niceName= "use IK", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="upperLengthScaler", niceName="Upper Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="lowerLengthScaler", niceName="Lower Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="elbowIkBlendpos", niceName="Elbow IK Blendpos", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="enableIkStretch", niceName="Enable IK Stretch", attributeType="float", defaultValue=1, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{parent_module}:{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="ribbon", niceName="RIBBON", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="show_ribbon_ctrl", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="ribbonRoundness", niceName="Ribbon Roundness", attributeType="float", minValue=0.01, maxValue=5, defaultValue=1, keyable=True)
        self.settings_ctrl.node.addAttr(attr="elbowTangent", niceName="Elbow Tangent", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="soft_IK", niceName="SOFT IK", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=False)
        self.settings_ctrl.node.addAttr(attr="softIkStart", niceName="Soft IK Start", attributeType="float", defaultValue=0.8, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="enableSoftIk", niceName="Enable Soft IK", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="softIkCurve", niceName="Soft IK Curve", attributeType="enum", enumName="custom_curve:smoothstep_curve:cubic_curve", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="visibility_grps", niceName="VISIBILITY", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        setup_visibility_controls(settings_ctrl=self.settings_ctrl, groups=self.groups)

        for attr in ["custom", "ribbon", "soft_IK", "visibility_grps"]:
            pm.setAttr(f"{self.settings_ctrl.node}.{attr}", lock=True)

        parent_module_input_noMainXformM = multMatrix(name=f"{self.name}_{parent_module}_input_noMainXformM")
        pm.connectAttr(self.parent_module_input.offsetParentMatrix, parent_module_input_noMainXformM.matrixIn[0])
        pm.connectAttr(self.main_input.worldInverseMatrix[0], parent_module_input_noMainXformM.matrixIn[1])

        parent_module_input_noScaleM = pickMatrix(name=f"{self.name}_{parent_module}_input_noScaleM")
        pm.connectAttr(parent_module_input_noMainXformM.matrixSum, parent_module_input_noScaleM.inputMatrix)
        parent_module_input_noScaleM.useScale.set(0)
        parent_module_input_noScaleM.useShear.set(0)

        parent_module_input_WM = multMatrix(name=f"{self.name}_{parent_module}_input_WM")
        pm.connectAttr(parent_module_input_noScaleM.outputMatrix, parent_module_input_WM.matrixIn[0])
        pm.connectAttr(self.main_input.offsetParentMatrix, parent_module_input_WM.matrixIn[1])
        
        settings_POM = create_pom(module_name=self.name, name="settings_POM", source_matrix = settings_guide.worldMatrix[0], parentGuide_input = self.parent_moduleGuide_input.worldInverseMatrix[0])

        settings_WM = multMatrix(name=f"{self.name}_settings_WM")
        pm.connectAttr(settings_POM.matrixSum, settings_WM.matrixIn[0])
        pm.connectAttr(parent_module_input_WM.matrixSum, settings_WM.matrixIn[1])

        pm.connectAttr(settings_WM.matrixSum, self.settings_ctrl.offsetParentMatrix)

        self.orientPlane_guide = aimMatrix(name=f"{self.name}_orientPlane_guide")
        pm.connectAttr(upper_guide.worldMatrix[0], self.orientPlane_guide.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], self.orientPlane_guide.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0],self.orientPlane_guide.secondaryTargetMatrix)
        self.orientPlane_guide.secondaryMode.set(2)
        self.orientPlane_guide.secondaryTargetVector.set(0, 0, -1)

        lower_ctrl_guide_WM = blendMatrix(name=f"{self.name}_lower_ctrl_guide_WM")
        pm.connectAttr(self.orientPlane_guide.outputMatrix, lower_ctrl_guide_WM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_ctrl_guide_WM.target[0].targetMatrix)
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
        hand_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_hand_FK_ctrl", ctrl_size=2, normal=(1,0,0), color=fk_color)

        hand_IK_ctrl = control.create(ctrl_type="box", degree=1, name="hand_IK_ctrl", size=[2, 2, 2], color=ik_color)

        elbow_IK_ctrl = control.create(ctrl_type="pyramid", degree=1, name=f"{self.name}_elbow_IK_ctrl", size=[0.5, 6, 0.5], color=ik_color)
        lock_ctrl_attrs(elbow_IK_ctrl, ["translateX", "translateY", "translateZ", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"])

        self.elbowLock_IK_ctrl = control.create(ctrl_type="box", degree=1, name="elbowLock_IK_ctrl", size=[1, 1, 1], color=ik_color)
        lock_ctrl_attrs(self.elbowLock_IK_ctrl, attrs_to_lock=["rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"])

        self.elbowLock_IK_ctrl.node.addAttr(attr="Lock", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        self.elbowLock_IK_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)

        self.elbowLock_list = [main_module, "worldSpace"]

        upper_initial_length = distanceBetween(name=f"{self.name}_upper_initial_length")
        pm.connectAttr(upper_guide.worldMatrix[0], upper_initial_length.inMatrix1)
        pm.connectAttr(lower_guide.worldMatrix[0], upper_initial_length.inMatrix2)

        lower_initial_Length = distanceBetween(name=f"{self.name}_lower_initial_Length")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_initial_Length.inMatrix1)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_initial_Length.inMatrix2)

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
        pm.connectAttr(parent_module_input_WM.matrixSum, upper_baseWM.matrixIn[1])

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

        hand_IK_ctrl_mainSpaceEnable = equal(name=f"{self.name}_hand_IK_ctrl_{main_module}SpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, hand_IK_ctrl_mainSpaceEnable.input1)
        hand_IK_ctrl_mainSpaceEnable.input2.set(1)

        hand_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_hand_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, hand_IK_ctrl_worldSpaceEnable.input1)
        hand_IK_ctrl_worldSpaceEnable.input2.set(2)

        self.upper_FK_ctrl_rotWM = parentMatrix(name=f"{self.name}_upper_FK_ctrl_rotWM")
        pm.connectAttr(upper_WM_test.matrixSum, self.upper_FK_ctrl_rotWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.upper_FK_ctrl_rotWM.target[0].targetMatrix)
        pm.connectAttr(upper_FK_ctrl_mainSpacePOM.matrixSum, self.upper_FK_ctrl_rotWM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[1].enableTarget)
        pm.connectAttr(self.upper_FK_guide_outWM.outputMatrix, self.upper_FK_ctrl_rotWM.target[1].offsetMatrix)

        upper_FK_ctrl_WM = blendMatrix(name=f"{self.name}_upper_FK_ctrl_WM")
        pm.connectAttr(self.upper_FK_ctrl_rotWM.outputMatrix, upper_FK_ctrl_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, upper_FK_ctrl_WM.target[0].targetMatrix)

        #Connecting to upper FK Controller
        pm.connectAttr(upper_FK_ctrl_WM.outputMatrix, upper_FK_ctrl.offsetParentMatrix)


        lower_FK_guide_outWM = aimMatrix(name=f"{self.name}_lower_FK_guide_outWM")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_FK_guide_outWM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_FK_guide_outWM.primaryTargetMatrix)
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

        self.hand_FK_guide_outWM = blendMatrix(name=f"{self.name}_hand_FK_guide_outWM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, self.hand_FK_guide_outWM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], self.hand_FK_guide_outWM.target[0].targetMatrix)
        self.hand_FK_guide_outWM.target[0].weight.set(1)
        self.hand_FK_guide_outWM.target[0].translateWeight.set(1)
        for attr in ["scaleWeight", "rotateWeight", "shearWeight"]:
            pm.setAttr(f"{self.hand_FK_guide_outWM.target[0]}.{attr}", 0)

        lower_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_lower_guide_outWIM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, lower_FK_guide_outWIM.inputMatrix)

        hand_FK_ctrl_POM = create_pom(module_name=self.name, name="hand_FK_ctrl_POM", source_matrix = self.hand_FK_guide_outWM.outputMatrix, parentGuide_input = lower_FK_guide_outWIM.outputMatrix)

        hand_axes = extract_matrix_axes(module_name=self.name, name="hand_FK_ctrl_POM", input=hand_FK_ctrl_POM.matrixSum)

        hand_FK_ctrl_POM_manualScale = create_fourByFourMatrix(
            module_name=self.name,
            name="hand_FK_ctrl_POM_manualScale",
            inputs=[
                [hand_axes["X"].outputX, hand_axes["X"].outputY, hand_axes["X"].outputZ, hand_axes["X"].outputW],
                [hand_axes["Y"].outputX, hand_axes["Y"].outputY, hand_axes["Y"].outputZ, hand_axes["Y"].outputW],
                [hand_axes["Z"].outputX, hand_axes["Z"].outputY, hand_axes["Z"].outputZ, hand_axes["Z"].outputW],
                [lower_length_manualScale.output]
            ]
        )

        hand_FK_ctrl_WM = multMatrix(name=f"{self.name}_hand_FK_ctrl_WM")
        pm.connectAttr(hand_FK_ctrl_POM_manualScale.output, hand_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl.worldMatrix[0], hand_FK_ctrl_WM.matrixIn[1])

        #Connection to Hand FK controller
        pm.connectAttr(hand_FK_ctrl_WM.matrixSum, hand_FK_ctrl.offsetParentMatrix)

        #===============================================================================================================================================
        #===============================================================================================================================================

        #IK hand

        hand_IK_ctrl_POM = create_pom(module_name=self.name, name="hand_IK_ctrl_POM", source_matrix = self.hand_FK_guide_outWM.outputMatrix, parentGuide_input = self.parent_moduleGuide_input.worldInverseMatrix[0])

        hand_IK_ctrl_parent_moduleSpaceWM =  multMatrix(name=f"{self.name}_hand_IK_ctrl_{parent_module}SpaceWM")
        pm.connectAttr(hand_IK_ctrl_POM.matrixSum, hand_IK_ctrl_parent_moduleSpaceWM.matrixIn[0])
        pm.connectAttr(parent_module_input_WM.matrixSum, hand_IK_ctrl_parent_moduleSpaceWM.matrixIn[1])

        hand_IK_ctrl_mainSpacePOM = create_pom(module_name=self.name, name="hand_IK_ctrl_mainSpacePOM", source_matrix = self.hand_FK_guide_outWM.outputMatrix, parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])
        
        self.hand_IK_ctrl_WM = parentMatrix(f"{self.name}_hand_IK_ctrl_WM")
        pm.connectAttr(hand_IK_ctrl_parent_moduleSpaceWM.matrixSum, self.hand_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, self.hand_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.hand_IK_ctrl_WM.target[0].targetMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpacePOM.matrixSum, self.hand_IK_ctrl_WM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, self.hand_IK_ctrl_WM.target[1].enableTarget)
        pm.connectAttr(self.hand_FK_guide_outWM.outputMatrix, self.hand_IK_ctrl_WM.target[1].offsetMatrix)


        pm.connectAttr(self.hand_IK_ctrl_WM.outputMatrix, hand_IK_ctrl.offsetParentMatrix)


        #IK elbow

        elbow_IK_guide_POM = create_pom(module_name=self.name, name="elbow_IK_guide_POM", source_matrix = self.orientPlane_guide.outputMatrix, parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])

        elbow_IK_clavicleSpaceWM = multMatrix(name=f"{self.name}_IK_clavicleSpaceWM")
        pm.connectAttr(elbow_IK_guide_POM.matrixSum, elbow_IK_clavicleSpaceWM.matrixIn[0])
        pm.connectAttr(self.main_input.worldMatrix[0], elbow_IK_clavicleSpaceWM.matrixIn[1])

        elbow_IK_mainSpacePOM = create_pom(module_name=self.name, name="elbow_IK_mainSpacePOM", source_matrix=self.orientPlane_guide.outputMatrix, parentGuide_input=self.mainGuide_input.worldInverseMatrix[0])

        self.elbow_IK_baseWM = parentMatrix(name=f"{self.name}_elbow_IK_baseWM")
        pm.connectAttr(elbow_IK_clavicleSpaceWM.matrixSum, self.elbow_IK_baseWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, self.elbow_IK_baseWM.target[0].enableTarget)
        pm.connectAttr(self.main_input.offsetParentMatrix, self.elbow_IK_baseWM.target[0].targetMatrix)
        pm.connectAttr(elbow_IK_mainSpacePOM.matrixSum, self.elbow_IK_baseWM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, self.elbow_IK_baseWM.target[1].enableTarget)
        pm.connectAttr(self.orientPlane_guide.outputMatrix, self.elbow_IK_baseWM.target[1].offsetMatrix)

        elbow_IK_pos_WM = blendMatrix(name=f"{self.name}_elbow_IK_pos_WM")
        pm.connectAttr(self.elbow_IK_baseWM.outputMatrix, elbow_IK_pos_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, elbow_IK_pos_WM.target[0].targetMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], elbow_IK_pos_WM.target[1].targetMatrix)
        pm.connectAttr(self.settings_ctrl.node.elbowIkBlendpos, elbow_IK_pos_WM.target[1].weight)
        elbow_IK_pos_WM.target[1].scaleWeight.set(0)
        elbow_IK_pos_WM.target[1].rotateWeight.set(0)
        
        elbow_IK_rot_WM = aimMatrix(name=f"{self.name}_elbow_IK_rot_WM")
        pm.connectAttr(elbow_IK_pos_WM.outputMatrix, elbow_IK_rot_WM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], elbow_IK_rot_WM.primaryTargetMatrix)

        pm.connectAttr(elbow_IK_rot_WM.outputMatrix, elbow_IK_ctrl.offsetParentMatrix)


        #IK Elbow Lock

        elbowLock_IK_ctrl_mainSpacePOM = create_pom(module_name=self.name, name="elbowLock_IK_ctrl_mainSpacePOM", source_matrix = self.elbowLock_guide.worldMatrix[0], parentGuide_input = self.mainGuide_input.worldInverseMatrix[0])

        elbowLock_IK_ctrl_mainSpaceWM = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_{main_module}SpaceWM")
        pm.connectAttr(elbowLock_IK_ctrl_mainSpacePOM.matrixSum, elbowLock_IK_ctrl_mainSpaceWM.matrixIn[0])
        pm.connectAttr(self.main_input.worldMatrix[0], elbowLock_IK_ctrl_mainSpaceWM.matrixIn[1])

        elbowLock_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_elbowLock_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(self.elbowLock_IK_ctrl.node.space, elbowLock_IK_ctrl_worldSpaceEnable.input1)
        elbowLock_IK_ctrl_worldSpaceEnable.input2.set(1)

        self.elbowLock_IK_ctrl_WM = parentMatrix(name=f"{self.name}_elbowLock_IK_ctrl_WM")
        pm.connectAttr(elbowLock_IK_ctrl_mainSpaceWM.matrixSum, self.elbowLock_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(elbowLock_IK_ctrl_worldSpaceEnable.output, self.elbowLock_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(self.elbowLock_guide.worldMatrix[0], self.elbowLock_IK_ctrl_WM.target[0].offsetMatrix)

        pm.connectAttr(self.elbowLock_IK_ctrl_WM.outputMatrix, self.elbowLock_IK_ctrl.offsetParentMatrix)


        #IK Prep

        upper_baseWM_noMainScale = remove_main_scale(module_name=self.name, name="upper_baseWM_noMainScale", world_matrix=upper_baseWM.matrixSum, main_input=self.main_input.worldInverseMatrix[0])

        hand_IK_ctrl_noMainScale = remove_main_scale(module_name=self.name, name="hand_IK_ctrl_noMainScale", world_matrix=hand_IK_ctrl.worldMatrix[0], main_input=self.main_input.worldInverseMatrix[0])

        current_length = distanceBetween(name=f"{self.name}_current_length")
        pm.connectAttr(upper_baseWM_noMainScale.matrixSum, current_length.inMatrix1)
        pm.connectAttr(hand_IK_ctrl_noMainScale.matrixSum, current_length.inMatrix2)

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
            name = "softIK", 
            upper_length = upper_length.output, 
            lower_length = lower_length.output, 
            total_length = clampedLength.output, 
            total_length_squared = clampedLength_squared.output,
            float_value_2=self.float_value_2
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

        upper_softIK_heightSqaredClamped = max_(name=f"{self.name}_upper_softIK_heightSqaredClamped")
        pm.connectAttr(self.float_value_0.outFloat, upper_softIK_heightSqaredClamped.input_[0])
        #upper_softIK_heightSqaredClamped.input_[0].set(0)
        pm.connectAttr(upper_softIK_heightSquared.output, upper_softIK_heightSqaredClamped.input_[1])

        softIK_blendcurve_selector = choice(name=f"{self.name}_softIK_blendcurve_selector")
        pm.connectAttr(self.settings_ctrl.node.softIkCurve, softIK_blendcurve_selector.selector)
        pm.connectAttr(ease_in_out_condition.outColorR, softIK_blendcurve_selector.input_[0])
        pm.connectAttr(upper_softIK_smoothStepBlendValue.output, softIK_blendcurve_selector.input_[1])
        pm.connectAttr(upper_softIK_cubicBlendValue.output, softIK_blendcurve_selector.input_[2])

        upper_softIK_quadraticTargetHeight = multiply(name=f"{self.name}_upper_softIK_quadraticTargetHeight")
        pm.connectAttr(upper_softIK_linearTargetHeight.output, upper_softIK_quadraticTargetHeight.input_[0])
        pm.connectAttr(upper_softIK_linearTargetHeight.output, upper_softIK_quadraticTargetHeight.input_[1])

        upper_softIK_height = power(name=f"{self.name}_upper_softIK_height")
        pm.connectAttr(upper_softIK_heightSqaredClamped.output, upper_softIK_height.input_)
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


        #Elbow Lock part

        upper_softIK_scaler_enable = max_(name=f"{self.name}_upper_softIK_scaler_enable")
        pm.connectAttr(disable_soft_ik.output, upper_softIK_scaler_enable.input_[0])
        pm.connectAttr(upper_softIK_scaler.output, upper_softIK_scaler_enable.input_[1])

        elbowLock_IK_ctrl_noMainScale = remove_main_scale(module_name=self.name, name="elbowLock_IK_ctrl_noMainScale", world_matrix=self.elbowLock_IK_ctrl.worldMatrix[0], main_input=self.main_input.worldInverseMatrix[0])

        lower_softIK_scaler_enable = max_(name=f"{self.name}_lower_softIK_scaler_enable")
        pm.connectAttr(disable_soft_ik.output, lower_softIK_scaler_enable.input_[0])
        pm.connectAttr(lower_softIK_scaler.output, lower_softIK_scaler_enable.input_[1])

        elbowLock_IK_upperLength = distanceBetween(name=f"{self.name}_elbowLock_IK_upperLength")
        pm.connectAttr(upper_baseWM_noMainScale.matrixSum, elbowLock_IK_upperLength.inMatrix1)
        pm.connectAttr(elbowLock_IK_ctrl_noMainScale.matrixSum, elbowLock_IK_upperLength.inMatrix2)

        elbowLock_IK_lowerLength = distanceBetween(name=f"{self.name}_elbowLock_IK_lowerLength")
        pm.connectAttr(elbowLock_IK_ctrl_noMainScale.matrixSum, elbowLock_IK_lowerLength.inMatrix1)
        pm.connectAttr(hand_IK_ctrl_noMainScale.matrixSum, elbowLock_IK_lowerLength.inMatrix2)


        #IK Solver

        upper_lengthScaled = multiply(name=f"{self.name}_upper_lengthScaled")
        pm.connectAttr(upper_length.output, upper_lengthScaled.input_[0])
        pm.connectAttr(upper_softIK_scaler_enable.output, upper_lengthScaled.input_[1])

        lower_lengthScaled = multiply(name=f"{self.name}_lower_lengthScaled")
        pm.connectAttr(lower_length.output, lower_lengthScaled.input_[0])
        pm.connectAttr(lower_softIK_scaler_enable.output, lower_lengthScaled.input_[1])

        upper_elbowLock_lengthSwitch = blendTwoAttr(name=f"{self.name}_upper_elbowLock_lengthSwitch")
        pm.connectAttr(self.elbowLock_IK_ctrl.node.Lock, upper_elbowLock_lengthSwitch.attributesBlender)
        pm.connectAttr(upper_lengthScaled.output, upper_elbowLock_lengthSwitch.input_[0])
        pm.connectAttr(elbowLock_IK_upperLength.distance, upper_elbowLock_lengthSwitch.input_[1])

        lower_elbowLock_lengthSwitch = blendTwoAttr(name=f"{self.name}_lower_elbowLock_lengthSwitch")
        pm.connectAttr(self.elbowLock_IK_ctrl.node.Lock, lower_elbowLock_lengthSwitch.attributesBlender)
        pm.connectAttr(lower_lengthScaled.output, lower_elbowLock_lengthSwitch.input_[0])
        pm.connectAttr(elbowLock_IK_lowerLength.distance, lower_elbowLock_lengthSwitch.input_[1])

        ik_solver = create_ik_solver_setup(
            module_name=self.name,
            name="IK",
            upper_length = upper_elbowLock_lengthSwitch.output,
            lower_length = lower_elbowLock_lengthSwitch.output,
            total_length = clampedLength.output,
            total_length_squared = clampedLength_squared.output,
            float_value_2=self.float_value_2
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

        elbowLock_IK_ctrl_WPos = translationFromMatrix(name=f"{self.name}_elbowLock_IK_ctrl_WPos")
        pm.connectAttr(self.elbowLock_IK_ctrl.worldMatrix[0], elbowLock_IK_ctrl_WPos.input_)

        upper_baseWPos = translationFromMatrix(name=f"{self.name}_upper_baseWPos")
        pm.connectAttr(upper_WM_test.matrixSum, upper_baseWPos.input_)

        elbowLock_IK_poleVector = plusMinusAverage(name=f"{self.name}_elbowLock_IK_poleVector")
        elbowLock_IK_poleVector.operation.set(2)
        pm.connectAttr(elbowLock_IK_ctrl_WPos.output, elbowLock_IK_poleVector.input3D[0])
        pm.connectAttr(upper_baseWPos.output, elbowLock_IK_poleVector.input3D[1])

        elbow_IK_poleVector = multiplyVectorByMatrix(name=f"{self.name}_elbow_IK_poleVector")
        elbow_IK_poleVector.input_.set(0, 1, 0)
        pm.connectAttr(elbow_IK_ctrl.worldMatrix[0], elbow_IK_poleVector.matrix)

        upper_IK_sin_negated = negate(name=f"{self.name}_upper_IK_sin_negated")
        pm.connectAttr(upper_IK_sin.output, upper_IK_sin_negated.input_)

        lower_IK_sinSquaredClamped = max_(name=f"{self.name}_lower_IK_sinSquaredClamped")
        pm.connectAttr(self.float_value_0.outFloat, lower_IK_sinSquaredClamped.input_[0])
        #lower_IK_sinSquaredClamped.input_[0].set(0)
        pm.connectAttr(lower_IK_sinSquared.output, lower_IK_sinSquaredClamped.input_[1])

        elbow_IK_poleVectorSwitch = blendColors(name=f"{self.name}_elbow_IK_poleVectorSwitch")
        pm.connectAttr(self.elbowLock_IK_ctrl.node.Lock, elbow_IK_poleVectorSwitch.blender)
        
        pm.connectAttr(elbowLock_IK_poleVector.output3D, elbow_IK_poleVectorSwitch.color1)
        pm.connectAttr(elbow_IK_poleVector.output, elbow_IK_poleVectorSwitch.color2)

        lower_IK_sin = power(name=f"{self.name}_lower_IK_sin")
        pm.connectAttr(lower_IK_sinSquaredClamped.output, lower_IK_sin.input_)
        lower_IK_sin.exponent.set(0.5)

        IK_baseWM = aimMatrix(name=f"{self.name}_IK_baseWM")
        pm.connectAttr(upper_WM_test.matrixSum, IK_baseWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], IK_baseWM.primaryTargetMatrix)
        IK_baseWM.secondaryMode.set(2)
        pm.connectAttr(elbow_IK_poleVectorSwitch.output, IK_baseWM.secondaryTargetVector)

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
                [upper_elbowLock_lengthSwitch.output]
            ]
        )

        lower_IK_WM = multMatrix(name=f"{self.name}_lower_IK_WM")
        pm.connectAttr(lower_IK_localRotMatrix.output, lower_IK_WM.matrixIn[0])
        pm.connectAttr(upper_IK_WM.matrixSum, lower_IK_WM.matrixIn[1])

        lower_IK_WIM = inverseMatrix(name=f"{self.name}_lower_IK_WIM")
        pm.connectAttr(lower_IK_WM.matrixSum, lower_IK_WIM.inputMatrix)

        hand_IK_baseLocalMatrix = multMatrix(name=f"{self.name}_hand_IK_baseLocalMatrix")
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], hand_IK_baseLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_IK_WIM.outputMatrix, hand_IK_baseLocalMatrix.matrixIn[1])

        hand_IK_axes = extract_matrix_axes(module_name=self.name, name="hand_IK_baseLocalMatrix", input=hand_IK_baseLocalMatrix.matrixSum)

        hand_IK_localMatrix = create_fourByFourMatrix(
            module_name=self.name,
            name="hand_IK_localMatrix",
            inputs=[
                [hand_IK_axes["X"].outputX, hand_IK_axes["X"].outputY, hand_IK_axes["X"].outputZ, hand_IK_axes["X"].outputW],
                [hand_IK_axes["Y"].outputX, hand_IK_axes["Y"].outputY, hand_IK_axes["Y"].outputZ, hand_IK_axes["Y"].outputW],
                [hand_IK_axes["Z"].outputX, hand_IK_axes["Z"].outputY, hand_IK_axes["Z"].outputZ, hand_IK_axes["Z"].outputW],
                [lower_elbowLock_lengthSwitch.output]
            ]
        )

        #IK/FK Switch
        
        lower_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_lower_FK_ctrl_outLocalMatrix")
        pm.connectAttr(lower_FK_ctrl.matrix, lower_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl_POM_manualScale.output, lower_FK_ctrl_outLocalMatrix.matrixIn[1])

        hand_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_hand_FK_ctrl_outLocalMatrix")
        pm.connectAttr(hand_FK_ctrl.matrix, hand_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(hand_FK_ctrl_POM_manualScale.output, hand_FK_ctrl_outLocalMatrix.matrixIn[1])

        blends = {
            "upper": create_ik_fk_blend(
                module_name=self.name, 
                blend_name="upper_WM", 
                fk_source=upper_FK_ctrl.worldMatrix[0], 
                ik_source=upper_IK_WM.matrixSum, 
                blend_attr=self.settings_ctrl.node.useIK
                ),
            "lower_local": create_ik_fk_blend(
                module_name=self.name,
                blend_name="lower_localMatrix", 
                fk_source=lower_FK_ctrl_outLocalMatrix.matrixSum, 
                ik_source=lower_IK_localRotMatrix.output, 
                blend_attr=self.settings_ctrl.node.useIK
                ),
            "hand_local": create_ik_fk_blend(
                module_name=self.name,
                blend_name="hand_localMatrix", 
                fk_source=hand_FK_ctrl_outLocalMatrix.matrixSum, 
                ik_source=hand_IK_localMatrix.output, 
                blend_attr=self.settings_ctrl.node.useIK
                )
        }

        upper_WM = blends["upper"]
        lower_localMatrix = blends["lower_local"]
        hand_localMatrix = blends["hand_local"]

        lower_WM = multMatrix(name=f"{self.name}_lower_WM")
        pm.connectAttr(lower_localMatrix.outputMatrix, lower_WM.matrixIn[0])
        pm.connectAttr(upper_WM.outputMatrix, lower_WM.matrixIn[1])

        hand_WM = multMatrix(name=f"{self.name}_hand_WM")
        pm.connectAttr(hand_localMatrix.outputMatrix, hand_WM.matrixIn[0])
        pm.connectAttr(lower_WM.matrixSum, hand_WM.matrixIn[1])

        #Joints
        upper_jnt = joint(name=f"{self.name}_upper_jnt")
        pm.connectAttr(upper_WM.outputMatrix, upper_jnt.offsetParentMatrix)
        
        lower_jnt = joint(f"{self.name}_lower_jnt")
        pm.connectAttr(lower_WM.matrixSum, lower_jnt.offsetParentMatrix)

        hand_jnt = joint(f"{self.name}_hand_jnt")
        pm.connectAttr(hand_WM.matrixSum, hand_jnt.offsetParentMatrix)


        #Ribbon
        lower_tangent = blendMatrix(name=f"{self.name}_lower_tangent")
        pm.connectAttr(upper_WM.outputMatrix, lower_tangent.inputMatrix)
        pm.connectAttr(lower_WM.matrixSum, lower_tangent.target[0].targetMatrix)
        pm.connectAttr(self.settings_ctrl.node.elbowTangent, lower_tangent.target[0].rotateWeight)

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
        pm.connectAttr(hand_WM.matrixSum, lower_midpoint.target[0].targetMatrix)
        lower_midpoint.target[0].weight.set(0.5)

        lower_midpoint_aim = aimMatrix(name=f"{self.name}_lower_midpoint_aim")
        pm.connectAttr(lower_midpoint.outputMatrix, lower_midpoint_aim.inputMatrix)
        pm.connectAttr(hand_WM.matrixSum, lower_midpoint_aim.primaryTargetMatrix)
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
            hand_WM = hand_WM.matrixSum
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

        pm.connectAttr(ribbon_loft.outputSurface, old_ribbonShape.create, force=True)
    
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
            groups=self.groups,
            input_plane=old_ribbonShape, 
            spans_U=60, 
            spans_V=4, 
            degree_U=1, 
            degree_V=3)

        ribbon_pins, ribbon_joints = add_pin_joints(
            module_name=self.name,
            name="ribbon", 
            ribbon=ribbon, 
            number_of_pins=self.bind_jnts, 
            scale_parent=self.main_input.worldMatrix[0])

        ribbon_pin_grp = transform(name=f"{self.name}_ribbon_pin_grp")
        ribbon_joints_grp = transform(name=f"{self.name}_ribbon_joints_grp")

        for pin, jnt in zip(ribbon_pins, ribbon_joints):
            pm.parent(pin, ribbon_pin_grp.node)
            pm.parent(jnt.node, ribbon_joints_grp.node)
        

        #visibility IK/FK ctrl
        IK_ctrl = [hand_IK_ctrl, elbow_IK_ctrl, self.elbowLock_IK_ctrl]
        FK_ctrl = [upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl]

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

        hand_WPos = translationFromMatrix(name=f"{self.name}_hand_WPos")
        pm.connectAttr(hand_WM.matrixSum, hand_WPos.input_)

        
        #helpers without autocompletion it sucks I know
        elbowLock_IK_helper = control.create_connection_curve(name=f"{self.name}_elbowLock_IK_helper", color=ik_color)
        elbowLock_IK_helperShape = elbowLock_IK_helper.node.getShape()
        pm.connectAttr(elbowLock_IK_ctrl_WPos.output, elbowLock_IK_helperShape.controlPoints[0])
        pm.connectAttr(lower_IK_WPos.output, elbowLock_IK_helperShape.controlPoints[1])

        upper_proxy_helper = control.create_connection_curve(name=f"{self.name}_upper_proxy_helper", color=limb_connection_color)
        upper_proxy_helperShape = upper_proxy_helper.node.getShape()
        upper_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(upper_WPos.output, upper_proxy_helperShape.controlPoints[0])
        pm.connectAttr(lower_WPos.output, upper_proxy_helperShape.controlPoints[1])

        lower_proxy_helper = control.create_connection_curve(name=f"{self.name}_lower_proxy_helper", color=limb_connection_color)
        lower_proxy_helperShape = lower_proxy_helper.node.getShape()
        lower_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(lower_WPos.output, lower_proxy_helperShape.controlPoints[0])
        pm.connectAttr(hand_WPos.output, lower_proxy_helperShape.controlPoints[1])

        #outputs (could be removed later)
        self.hand_output = transform(name=f"{self.name}_self.hand_output")
        pm.connectAttr(hand_WM.matrixSum, self.hand_output.offsetParentMatrix)

        self.handGuide_output = transform(name=f"{self.name}_self.handGuide_output")
        pm.connectAttr(hand_guide.worldMatrix[0], self.handGuide_output.offsetParentMatrix)

        outliner_data = {
            "inputs": [self.main_input, self.mainGuide_input, self.parent_module_input, self.parent_moduleGuide_input],
            "guides": [upper_guide, lower_guide, hand_guide, settings_guide, self.elbowLock_guide],
            "controls": [upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl, hand_IK_ctrl, elbow_IK_ctrl, self.settings_ctrl, self.elbowLock_IK_ctrl],
            "helpers": [elbowLock_IK_helper, upper_proxy_helper, lower_proxy_helper],
            "joints": [upper_jnt, lower_jnt, hand_jnt, ribbon_joints_grp],
            "rigNodes": [ribbon_pin_grp, ribbon],
            "outputs": [self.hand_output, self.handGuide_output]
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
        self.elbowLock_list.append(parent_name)

        target_index = len(self.input_list) - 1

        elbowTarget_index = len(self.elbowLock_list) - 1

        enumNameStr = ":".join(self.input_list)
        self.settings_ctrl.node.deleteAttr("space")
        self.settings_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=enumNameStr, defaultValue=0, hidden=False, keyable=True)

        elbow_enumNameStr = ":".join(self.elbowLock_list)
        self.elbowLock_IK_ctrl.node.deleteAttr("space")
        self.elbowLock_IK_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=elbow_enumNameStr, defaultValue=0, hidden=False, keyable=True)

        upper_FK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="upper_FK_ctrl_parentSpacePOM", source_matrix = self.upper_FK_guide_outWM.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        hand_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="hand_IK_ctrl_parentSpacePOM", source_matrix = self.hand_FK_guide_outWM.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        elbow_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="elbow_IK_ctrl_parentSpacePOM", source_matrix = self.orientPlane_guide.outputMatrix, parentGuide_input = parentGuide_input.worldInverseMatrix[0]
        )

        hand_IK_ctrl_parentSpaceEnable = equal(name=f"{self.name}_hand_IK_ctrl_{parent_name}SpaceEnable")
        pm.connectAttr(self.settings_ctrl.node.space, hand_IK_ctrl_parentSpaceEnable.input1)
        hand_IK_ctrl_parentSpaceEnable.input2.set(target_index)

        #upper fk ctrl space switch
        pm.connectAttr(hand_IK_ctrl_parentSpaceEnable.output, self.upper_FK_ctrl_rotWM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.upper_FK_ctrl_rotWM.target[target_index].targetMatrix)
        pm.connectAttr(upper_FK_ctrl_parentSpacePOM.matrixSum, self.upper_FK_ctrl_rotWM.target[target_index].offsetMatrix)

        #hand ik ctrl space switch
        pm.connectAttr(hand_IK_ctrl_parentSpaceEnable.output, self.hand_IK_ctrl_WM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.hand_IK_ctrl_WM.target[target_index].targetMatrix)
        pm.connectAttr(hand_IK_ctrl_parentSpacePOM.matrixSum, self.hand_IK_ctrl_WM.target[target_index].offsetMatrix)

        #elbow ik ctrl space switch
        pm.connectAttr(hand_IK_ctrl_parentSpaceEnable.output, self.elbow_IK_baseWM.target[target_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.elbow_IK_baseWM.target[target_index].targetMatrix)
        pm.connectAttr(elbow_IK_ctrl_parentSpacePOM.matrixSum, self.elbow_IK_baseWM.target[target_index].offsetMatrix)

        elbowLock_IK_ctrl_parentSpacePOM = create_pom(
            module_name=self.name, name="elbowLock_IK_ctrl_parentSpacePOM", source_matrix = self.elbowLock_guide.worldMatrix[0], parentGuide_input = parentGuide_input.worldInverseMatrix[0])

        elbowLock_IK_ctrl_parentSpaceEnable = equal(name=f"{self.name}_elbowLock_IK_ctrl_{parent_name}Enable")
        pm.connectAttr(self.elbowLock_IK_ctrl.node.space, elbowLock_IK_ctrl_parentSpaceEnable.input1)
        elbowLock_IK_ctrl_parentSpaceEnable.input2.set(elbowTarget_index)

        #elbowLock space switch
        pm.connectAttr(elbowLock_IK_ctrl_parentSpaceEnable.output, self.elbowLock_IK_ctrl_WM.target[elbowTarget_index].enableTarget)
        pm.connectAttr(parent_input.offsetParentMatrix, self.elbowLock_IK_ctrl_WM.target[elbowTarget_index].targetMatrix)
        pm.connectAttr(elbowLock_IK_ctrl_parentSpacePOM.matrixSum, self.elbowLock_IK_ctrl_WM.target[elbowTarget_index].offsetMatrix)

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
    def out_hand_output(self):
        return self.hand_output

    @property
    def out_handGuide_output(self):
        return self.handGuide_output