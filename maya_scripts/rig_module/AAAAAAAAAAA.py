import json
import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from manual_node_classes import create_guide, colorize, create_groups, create_groups_

guide_color = [1, 1, 1]
limb_connection_color = [0, 0, 0]


class Limb():

    def __init__(self, main_module:str, connection_module:str , limb_type:str, limb_side:str, upper_guide_pos:tuple = (2, 0, 0), lower_guide_pos:tuple = (0, 0, 0), 
                 hand_guide_pos:tuple = (12, 0, 0), elbowLock_guide_pos:tuple = (7, 0, -4), settings_guide_pos:tuple = (4, 4, -4), 
                 upper_guide_rot:tuple = (0, 0, 0), fk_color:list = [0, 0, 1], ik_color:list = [0, 0.85, 0.83]):
        """
        Docstring for __init__
        
        :param self: Description
        :param main_module: name of main controller for naming the inputs
        :type main_module: str
        :param connection_module: name of the connecting module (clavicle or leg)
        :type connection_module: str
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
        
        groups = create_groups(rig_module_name=self.name)
        
        self.groups = groups

        upper_guide = create_guide(name=f"{self.name}_upper_guide", position=upper_guide_pos, color=guide_color)
        lower_guide = create_guide(name=f"{self.name}_lower_guide", position=lower_guide_pos, color=guide_color)
        hand_guide = create_guide(name=f"{self.name}_hand_guide", position=hand_guide_pos, color=guide_color)

        elbowLock_guide = create_guide(name=f"{self.name}_elbowLock_guide", position=elbowLock_guide_pos, color=guide_color)

        upper_guide.rotate.set(self.upper_guide_rot)

        #========================================= necessary ================================================
        self.elbowLock_guide = elbowLock_guide
        #====================================================================================================


        settings_guide = create_guide(name=f"{self.name}_settings_guide", position=settings_guide_pos, color=guide_color)

        lower_guide.translateZ.set(lock=True)
        lower_guide.node.setLimit("translateMinY", 0)

        main_input = transform(name=f"{self.name}_{main_module}_input")
        mainGuide_input = transform(name=f"{self.name}_{main_module}Guide_input")
        connection_module_input = transform(name=f"{self.name}_{connection_module}_input")
        connection_moduleGuide_input = transform(name=f"{self.name}_{connection_module}Guide_input")
        
        pm.parent(main_input.node, self.groups["inputs"].node)
        pm.parent(mainGuide_input.node, self.groups["inputs"].node)
        pm.parent(connection_module_input.node, self.groups["inputs"].node)
        pm.parent(connection_moduleGuide_input.node, self.groups["inputs"].node)

        input_list = [connection_module, main_module, "worldSpace"]
        self.input_list = input_list

        settings_ctrl = control.create(ctrl_type="gear", degree=3, name=f"{self.name}_settings_ctrl", normal=(0, 0, 1))
        settings_ctrl.node.addAttr(attr="useIK", niceName= "use IK", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="upperLengthScaler", niceName="Upper Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="lowerLengthScaler", niceName="Lower Length Scaler", attributeType="float", defaultValue=1, minValue=0, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="elbowIkBlendpos", niceName="Elbow IK Blendpos", attributeType="float", defaultValue=0.5, minValue=0, maxValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="enableIkStretch", niceName="Enable IK Stretch", attributeType="float", defaultValue=1, minValue=0, maxValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="softIkStart", niceName="Soft IK Start", attributeType="float", defaultValue=0.8, minValue=0, maxValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="enableSoftIk", niceName="Enable Soft IK", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="softIkCurve", niceName="Soft IK Curve", attributeType="enum", enumName="custom_curve:smoothstep_curve:cubic_curve", defaultValue=0, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showGuides", niceName="Show Guides", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showCtrl", niceName="Show Controller", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showRigNodes", niceName="Show Rig Nodes", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showJoints", niceName="Show Joints", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showProxyGeo", niceName="Show proxy geo", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
        settings_ctrl.node.addAttr(attr="showHelpers", niceName="Show Helpers", attributeType="bool", defaultValue=1, hidden=False, keyable=True)

        settings_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{connection_module}:{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)
        
        colorize(settings_ctrl.node, fk_color)
        
        self.settings_ctrl = settings_ctrl

        connection_module_input_noMainXformM = multMatrix(name=f"{self.name}_{connection_module}_input_noMainXformM")
        pm.connectAttr(connection_module_input.offsetParentMatrix, connection_module_input_noMainXformM.matrixIn[0])
        pm.connectAttr(main_input.worldInverseMatrix[0], connection_module_input_noMainXformM.matrixIn[1])

        connection_module_input_noScaleM = pickMatrix(name=f"{self.name}_{connection_module}_input_noScaleM")
        pm.connectAttr(connection_module_input_noMainXformM.matrixSum, connection_module_input_noScaleM.inputMatrix)
        connection_module_input_noScaleM.useScale.set(0)
        connection_module_input_noScaleM.useShear.set(0)

        connection_module_input_WM = multMatrix(name=f"{self.name}_{connection_module}_input_WM")
        pm.connectAttr(connection_module_input_noScaleM.outputMatrix, connection_module_input_WM.matrixIn[0])
        pm.connectAttr(main_input.offsetParentMatrix, connection_module_input_WM.matrixIn[1])

        settings_POM = multMatrix(name=f"{self.name}_settings_POM")
        pm.connectAttr(settings_guide.worldMatrix[0], settings_POM.matrixIn[0])
        pm.connectAttr(connection_moduleGuide_input.worldInverseMatrix[0], settings_POM.matrixIn[1])
        
        settings_WM = multMatrix(name=f"{self.name}_settings_WM")
        pm.connectAttr(settings_POM.matrixSum, settings_WM.matrixIn[0])
        pm.connectAttr(connection_module_input_WM.matrixSum, settings_WM.matrixIn[1])

        pm.connectAttr(settings_WM.matrixSum, settings_ctrl.offsetParentMatrix)

        upper_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_upper_FK_ctrl", ctrl_size=2, normal=(1,0,0))
        lower_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_lower_FK_ctrl", ctrl_size=2, normal=(1,0,0))
        hand_FK_ctrl = control.create_circle_ctrl(name=f"{self.name}_hand_FK_ctrl", ctrl_size=2, normal=(1,0,0))

        hand_IK_ctrl = control.create(ctrl_type="box", degree=1, name="hand_IK_ctrl", size=[2, 2, 2])
        colorize(hand_IK_ctrl.node, color=ik_color)

        for ctrl in (upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl):
            colorize(ctrl.node, color=fk_color)

        elbow_IK_ctrl = control.create(ctrl_type="pyramid", degree=1, name="elbow_IK_ctrl", size=[0.5, 6, 0.5])

        colorize(elbow_IK_ctrl.node, color=ik_color)

        elbowLock_IK_ctrl = control.create(ctrl_type="box", degree=1, name="elbowLock_IK_ctrl", size=[1, 1, 1])

        for attr in ["rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]:
            pm.setAttr(f"{elbowLock_IK_ctrl.node}.{attr}", lock=True)
            pm.setAttr(f"{elbowLock_IK_ctrl.node}.{attr}", keyable=False)
            pm.setAttr(f"{elbowLock_IK_ctrl.node}.{attr}", channelBox=False)

        colorize(elbowLock_IK_ctrl.node, color=ik_color)

        elbowLock_IK_ctrl.node.addAttr(attr="Lock", attributeType="float", defaultValue=0, minValue=0, maxValue=1, hidden=False, keyable=True)
        elbowLock_IK_ctrl.node.addAttr(attr="space", niceName="Space", attributeType="enum", enumName=f"{main_module}:worldSpace", defaultValue=0, hidden=False, keyable=True)

        elbowLock_list = [main_module, "worldSpace"]

        #========================================= necessary ================================================
        self.elbowLock_IK_ctrl = elbowLock_IK_ctrl
        self.elbowLock_list = elbowLock_list
        #====================================================================================================




        orientPlane_guide = aimMatrix(name=f"{self.name}_orientPlane_guide")
        pm.connectAttr(upper_guide.worldMatrix[0], orientPlane_guide.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], orientPlane_guide.primaryTargetMatrix)
        pm.connectAttr(upper_guide.worldMatrix[0],orientPlane_guide.secondaryTargetMatrix)
        orientPlane_guide.secondaryMode.set(2)
        orientPlane_guide.secondaryTargetVector.set(0, 0, -1)


        #========================================= necessary ================================================
        self.orientPlane_guide = orientPlane_guide
        #====================================================================================================


        lower_ctrl_guide_WM = blendMatrix(name=f"{self.name}_lower_ctrl_guide_WM")
        pm.connectAttr(orientPlane_guide.outputMatrix, lower_ctrl_guide_WM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_ctrl_guide_WM.target[0].targetMatrix)
        lower_ctrl_guide_WM.target[0].useMatrix.set(True)
        lower_ctrl_guide_WM.target[0].weight.set(0.5)
        lower_ctrl_guide_WM.target[0].rotateWeight.set(0)
        lower_ctrl_guide_WM.target[0].scaleWeight.set(0)
        lower_ctrl_guide_WM.target[0].shearWeight.set(0)

        pm.connectAttr(lower_ctrl_guide_WM.outputMatrix, lower_guide.offsetParentMatrix)

        upper_initial_length = distanceBetween(name=f"{self.name}_upper_initial_length")
        pm.connectAttr(upper_guide.worldMatrix[0], upper_initial_length.inMatrix1)
        pm.connectAttr(lower_guide.worldMatrix[0], upper_initial_length.inMatrix2)

        lower_initial_Length = distanceBetween(name=f"{self.name}_lower_initial_Length")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_initial_Length.inMatrix1)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_initial_Length.inMatrix2)

        upper_length_manualScale = multiply(name=f"{self.name}_upper_length_manualScale")
        pm.connectAttr(upper_initial_length.distance, upper_length_manualScale.input_[0])
        pm.connectAttr(settings_ctrl.node.upperLengthScaler, upper_length_manualScale.input_[1])

        lower_length_manualScale = multiply(name=f"{self.name}_lower_length_manualScale")
        pm.connectAttr(lower_initial_Length.distance, lower_length_manualScale.input_[0])
        pm.connectAttr(settings_ctrl.node.lowerLengthScaler, lower_length_manualScale.input_[1])

        initial_length = sum_(name=f"{self.name}_initial_length")
        pm.connectAttr(upper_length_manualScale.output, initial_length.input_[0])
        pm.connectAttr(lower_length_manualScale.output, initial_length.input_[1])

    


        upper_FK_guide_outWM = aimMatrix(name=f"{self.name}_upper_FK_guide_outWM")
        pm.connectAttr(upper_guide.worldMatrix[0], upper_FK_guide_outWM.inputMatrix)
        pm.connectAttr(lower_guide.worldMatrix[0], upper_FK_guide_outWM.primaryTargetMatrix)
        upper_FK_guide_outWM.primaryInputAxis.set(1, 0, 0)
        upper_FK_guide_outWM.primaryMode.set(1)
        pm.connectAttr(upper_guide.worldMatrix[0], upper_FK_guide_outWM.secondaryTargetMatrix)
        upper_FK_guide_outWM.secondaryMode.set(2)
        upper_FK_guide_outWM.secondaryTargetVector.set(0, 0, -1)


        # ==================================== necessary ===============================
        self.upper_FK_guide_outWM = upper_FK_guide_outWM
        # ==============================================================================


        upper_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_upper_FK_guide_outWIM")
        pm.connectAttr(upper_FK_guide_outWM.outputMatrix, upper_FK_guide_outWIM.inputMatrix)

        upper_base_POM = multMatrix(name=f"{self.name}_upper_base_POM")
        pm.connectAttr(upper_FK_guide_outWM.outputMatrix, upper_base_POM.matrixIn[0])
        pm.connectAttr(connection_moduleGuide_input.worldInverseMatrix[0], upper_base_POM.matrixIn[1])

        upper_baseWM = multMatrix(name=f"{self.name}_upper_baseWM")
        pm.connectAttr(upper_base_POM.matrixSum, upper_baseWM.matrixIn[0])
        pm.connectAttr(connection_module_input_WM.matrixSum, upper_baseWM.matrixIn[1])

        upper_baseWM_noMainXformM = multMatrix(name=f"{self.name}_upper_baseWM_noMainXformM")
        pm.connectAttr(upper_baseWM.matrixSum, upper_baseWM_noMainXformM.matrixIn[0])
        pm.connectAttr(main_input.worldInverseMatrix[0], upper_baseWM_noMainXformM.matrixIn[1])

        upper_baseWM_noScaleM = pickMatrix(name=f"{self.name}_upper_baseWM_noScaleM")
        pm.connectAttr(upper_baseWM_noMainXformM.matrixSum, upper_baseWM_noScaleM.inputMatrix)
        upper_baseWM_noScaleM.useScale.set(0)
        upper_baseWM_noScaleM.useShear.set(0)

        upper_WM_test = multMatrix(name=f"{self.name}_upper_WM_test")
        pm.connectAttr(upper_baseWM_noScaleM.outputMatrix, upper_WM_test.matrixIn[0])
        pm.connectAttr(main_input.offsetParentMatrix, upper_WM_test.matrixIn[1])

        upper_FK_ctrl_mainSpacePOM = multMatrix(name=f"{self.name}_upper_FK_ctrl_{main_module}SpacePOM")
        pm.connectAttr(upper_FK_guide_outWM.outputMatrix, upper_FK_ctrl_mainSpacePOM.matrixIn[0])
        pm.connectAttr(mainGuide_input.worldInverseMatrix[0], upper_FK_ctrl_mainSpacePOM.matrixIn[1])

        hand_IK_ctrl_mainSpaceEnable = equal(name=f"{self.name}_hand_IK_ctrl_{main_module}SpaceEnable")
        pm.connectAttr(settings_ctrl.node.space, hand_IK_ctrl_mainSpaceEnable.input1)
        hand_IK_ctrl_mainSpaceEnable.input2.set(1)

        hand_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_hand_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(settings_ctrl.node.space, hand_IK_ctrl_worldSpaceEnable.input1)
        hand_IK_ctrl_worldSpaceEnable.input2.set(2)

        upper_FK_ctrl_rotWM = parentMatrix(name=f"{self.name}_upper_FK_ctrl_rotWM")
        pm.connectAttr(upper_WM_test.matrixSum, upper_FK_ctrl_rotWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, upper_FK_ctrl_rotWM.target[0].enableTarget)
        pm.connectAttr(main_input.offsetParentMatrix, upper_FK_ctrl_rotWM.target[0].targetMatrix)
        pm.connectAttr(upper_FK_ctrl_mainSpacePOM.matrixSum, upper_FK_ctrl_rotWM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, upper_FK_ctrl_rotWM.target[1].enableTarget)
        pm.connectAttr(upper_FK_guide_outWM.outputMatrix, upper_FK_ctrl_rotWM.target[1].offsetMatrix)


        #============================= necessary ============================
        self.upper_FK_ctrl_rotWM = upper_FK_ctrl_rotWM
        #====================================================================


        upper_FK_ctrl_WM = blendMatrix(name=f"{self.name}_upper_FK_ctrl_WM")
        pm.connectAttr(upper_FK_ctrl_rotWM.outputMatrix, upper_FK_ctrl_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, upper_FK_ctrl_WM.target[0].targetMatrix)

        #Connecting to upper FK Controller
        pm.connectAttr(upper_FK_ctrl_WM.outputMatrix, upper_FK_ctrl.offsetParentMatrix)



        lower_FK_guide_outWM = aimMatrix(name=f"{self.name}_lower_FK_guide_outWM")
        pm.connectAttr(lower_guide.worldMatrix[0], lower_FK_guide_outWM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], lower_FK_guide_outWM.primaryTargetMatrix)
        lower_FK_guide_outWM.primaryInputAxis.set(1, 0, 0)
        lower_FK_guide_outWM.primaryMode.set(1)
        lower_FK_guide_outWM.primaryTargetVector.set(0, 0, 0)
        pm.connectAttr(upper_guide.worldMatrix[0], lower_FK_guide_outWM.secondaryTargetMatrix)
        lower_FK_guide_outWM.secondaryInputAxis.set(0, 1, 0)
        lower_FK_guide_outWM.secondaryMode.set(2)
        lower_FK_guide_outWM.secondaryTargetVector.set(0, 0, -1)

        lower_FK_ctrl_POM = multMatrix(name=f"{self.name}_lower_FK_ctrl_POM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, lower_FK_ctrl_POM.matrixIn[0])
        pm.connectAttr(upper_FK_guide_outWIM.outputMatrix, lower_FK_ctrl_POM.matrixIn[1])

        lower_FK_ctrl_POM_axisX = rowFromMatrix(name=f"{self.name}_lower_FK_ctrl_POM_axisX")
        pm.connectAttr(lower_FK_ctrl_POM.matrixSum, lower_FK_ctrl_POM_axisX.matrix)
        lower_FK_ctrl_POM_axisX.input_.set(0)

        lower_FK_ctrl_POM_axisY = rowFromMatrix(name=f"{self.name}_lower_FK_ctrl_POM_axisY")
        pm.connectAttr(lower_FK_ctrl_POM.matrixSum, lower_FK_ctrl_POM_axisY.matrix)
        lower_FK_ctrl_POM_axisY.input_.set(1)

        lower_FK_ctrl_POM_axisZ = rowFromMatrix(name=f"{self.name}_lower_FK_ctrl_POM_axisZ")
        pm.connectAttr(lower_FK_ctrl_POM.matrixSum, lower_FK_ctrl_POM_axisZ.matrix)
        lower_FK_ctrl_POM_axisZ.input_.set(2)
        
        lower_FK_ctrl_POM_manualScale = fourByFourMatrix(name=f"{self.name}_lower_FK_ctrl_POM_manualScale")
        pm.connectAttr(lower_FK_ctrl_POM_axisX.outputX, lower_FK_ctrl_POM_manualScale.in00)
        pm.connectAttr(lower_FK_ctrl_POM_axisX.outputY, lower_FK_ctrl_POM_manualScale.in01)
        pm.connectAttr(lower_FK_ctrl_POM_axisX.outputZ, lower_FK_ctrl_POM_manualScale.in02)
        pm.connectAttr(lower_FK_ctrl_POM_axisX.outputW, lower_FK_ctrl_POM_manualScale.in03)
        pm.connectAttr(lower_FK_ctrl_POM_axisY.outputX, lower_FK_ctrl_POM_manualScale.in10)
        pm.connectAttr(lower_FK_ctrl_POM_axisY.outputY, lower_FK_ctrl_POM_manualScale.in11)
        pm.connectAttr(lower_FK_ctrl_POM_axisY.outputZ, lower_FK_ctrl_POM_manualScale.in12)
        pm.connectAttr(lower_FK_ctrl_POM_axisY.outputW, lower_FK_ctrl_POM_manualScale.in13)
        pm.connectAttr(lower_FK_ctrl_POM_axisZ.outputX, lower_FK_ctrl_POM_manualScale.in20)
        pm.connectAttr(lower_FK_ctrl_POM_axisZ.outputY, lower_FK_ctrl_POM_manualScale.in21)
        pm.connectAttr(lower_FK_ctrl_POM_axisZ.outputZ, lower_FK_ctrl_POM_manualScale.in22)
        pm.connectAttr(lower_FK_ctrl_POM_axisZ.outputW, lower_FK_ctrl_POM_manualScale.in23)
        pm.connectAttr(upper_length_manualScale.output, lower_FK_ctrl_POM_manualScale.in30)

        lower_FK_ctrl_WM = multMatrix(name=f"{self.name}_lower_FK_ctrl_WM")
        pm.connectAttr(lower_FK_ctrl_POM_manualScale.output, lower_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(upper_FK_ctrl.worldMatrix[0], lower_FK_ctrl_WM.matrixIn[1])

        #connection to FK Controller
        pm.connectAttr(lower_FK_ctrl_WM.matrixSum, lower_FK_ctrl.offsetParentMatrix)



        hand_FK_guide_outWM = blendMatrix(name=f"{self.name}_hand_FK_guide_outWM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, hand_FK_guide_outWM.inputMatrix)
        pm.connectAttr(hand_guide.worldMatrix[0], hand_FK_guide_outWM.target[0].targetMatrix)
        hand_FK_guide_outWM.target[0].weight.set(1)
        hand_FK_guide_outWM.target[0].scaleWeight.set(0)
        hand_FK_guide_outWM.target[0].translateWeight.set(1)
        hand_FK_guide_outWM.target[0].rotateWeight.set(0)
        hand_FK_guide_outWM.target[0].shearWeight.set(0)


        #=================================== necessary ================================================
        self.hand_FK_guide_outWM = hand_FK_guide_outWM
        #==============================================================================================


        lower_FK_guide_outWIM = inverseMatrix(name=f"{self.name}_lower_guide_outWIM")
        pm.connectAttr(lower_FK_guide_outWM.outputMatrix, lower_FK_guide_outWIM.inputMatrix)

        hand_FK_ctrl_POM = multMatrix(name=f"{self.name}_hand_FK_ctrl_POM")
        pm.connectAttr(hand_FK_guide_outWM.outputMatrix, hand_FK_ctrl_POM.matrixIn[0])
        pm.connectAttr(lower_FK_guide_outWIM.outputMatrix, hand_FK_ctrl_POM.matrixIn[1])

        hand_FK_ctrl_POM_axisX = rowFromMatrix(name=f"{self.name}_hand_FK_ctrl_POM_axisX")
        pm.connectAttr(hand_FK_ctrl_POM.matrixSum, hand_FK_ctrl_POM_axisX.matrix)
        hand_FK_ctrl_POM_axisX.input_.set(0)

        hand_FK_ctrl_POM_axisY = rowFromMatrix(name=f"{self.name}_hand_FK_ctrl_POM_axisY")
        pm.connectAttr(hand_FK_ctrl_POM.matrixSum, hand_FK_ctrl_POM_axisY.matrix)
        hand_FK_ctrl_POM_axisY.input_.set(1)

        hand_FK_ctrl_POM_axisZ = rowFromMatrix(name=f"{self.name}_hand_FK_ctrl_POM_axisZ")
        pm.connectAttr(hand_FK_ctrl_POM.matrixSum, hand_FK_ctrl_POM_axisZ.matrix)
        hand_FK_ctrl_POM_axisZ.input_.set(2)

        hand_FK_ctrl_POM_manualScale = fourByFourMatrix(name=f"{self.name}_hand_FK_ctrl_POM_manualScale")
        pm.connectAttr(hand_FK_ctrl_POM_axisX.outputX, hand_FK_ctrl_POM_manualScale.in00)
        pm.connectAttr(hand_FK_ctrl_POM_axisX.outputY, hand_FK_ctrl_POM_manualScale.in01)
        pm.connectAttr(hand_FK_ctrl_POM_axisX.outputZ, hand_FK_ctrl_POM_manualScale.in02)
        pm.connectAttr(hand_FK_ctrl_POM_axisX.outputW, hand_FK_ctrl_POM_manualScale.in03)
        pm.connectAttr(hand_FK_ctrl_POM_axisY.outputX, hand_FK_ctrl_POM_manualScale.in10)
        pm.connectAttr(hand_FK_ctrl_POM_axisY.outputY, hand_FK_ctrl_POM_manualScale.in11)
        pm.connectAttr(hand_FK_ctrl_POM_axisY.outputZ, hand_FK_ctrl_POM_manualScale.in12)
        pm.connectAttr(hand_FK_ctrl_POM_axisY.outputW, hand_FK_ctrl_POM_manualScale.in13)
        pm.connectAttr(hand_FK_ctrl_POM_axisZ.outputX, hand_FK_ctrl_POM_manualScale.in20)
        pm.connectAttr(hand_FK_ctrl_POM_axisZ.outputY, hand_FK_ctrl_POM_manualScale.in21)
        pm.connectAttr(hand_FK_ctrl_POM_axisZ.outputZ, hand_FK_ctrl_POM_manualScale.in22)
        pm.connectAttr(hand_FK_ctrl_POM_axisZ.outputW, hand_FK_ctrl_POM_manualScale.in23)
        pm.connectAttr(lower_length_manualScale.output, hand_FK_ctrl_POM_manualScale.in30)

        hand_FK_ctrl_WM = multMatrix(name=f"{self.name}_hand_FK_ctrl_WM")
        pm.connectAttr(hand_FK_ctrl_POM_manualScale.output, hand_FK_ctrl_WM.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl.worldMatrix[0], hand_FK_ctrl_WM.matrixIn[1])

        #Connection to Hand FK controller
        pm.connectAttr(hand_FK_ctrl_WM.matrixSum, hand_FK_ctrl.offsetParentMatrix)



        #IK hand

        hand_IK_ctrl_POM = multMatrix(name=f"{self.name}_hand_IK_ctrl_POM")
        pm.connectAttr(hand_FK_guide_outWM.outputMatrix, hand_IK_ctrl_POM.matrixIn[0])
        pm.connectAttr(connection_moduleGuide_input.worldInverseMatrix[0], hand_IK_ctrl_POM.matrixIn[1])

        hand_IK_ctrl_connection_moduleSpaceWM =  multMatrix(name=f"{self.name}_hand_IK_ctrl_{connection_module}SpaceWM")
        pm.connectAttr(hand_IK_ctrl_POM.matrixSum, hand_IK_ctrl_connection_moduleSpaceWM.matrixIn[0])
        pm.connectAttr(connection_module_input_WM.matrixSum, hand_IK_ctrl_connection_moduleSpaceWM.matrixIn[1])

        hand_IK_ctrl_mainSpacePOM = multMatrix(f"{self.name}_hand_IK_ctrl_{main_module}SpacePOM")
        pm.connectAttr(hand_FK_guide_outWM.outputMatrix, hand_IK_ctrl_mainSpacePOM.matrixIn[0])
        pm.connectAttr(mainGuide_input.worldInverseMatrix[0], hand_IK_ctrl_mainSpacePOM.matrixIn[1])
        
        hand_IK_ctrl_WM = parentMatrix(f"{self.name}_hand_IK_ctrl_WM")
        pm.connectAttr(hand_IK_ctrl_connection_moduleSpaceWM.matrixSum, hand_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, hand_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(main_input.offsetParentMatrix, hand_IK_ctrl_WM.target[0].targetMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpacePOM.matrixSum, hand_IK_ctrl_WM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, hand_IK_ctrl_WM.target[1].enableTarget)
        pm.connectAttr(hand_FK_guide_outWM.outputMatrix, hand_IK_ctrl_WM.target[1].offsetMatrix)


        #=========================================================================
        self.hand_IK_ctrl_WM = hand_IK_ctrl_WM
        #=========================================================================


        pm.connectAttr(hand_IK_ctrl_WM.outputMatrix, hand_IK_ctrl.offsetParentMatrix)


        #IK elbow

        elbow_IK_guide_POM = multMatrix(name=f"{self.name}_elbow_IK_guide_POM")
        pm.connectAttr(orientPlane_guide.outputMatrix, elbow_IK_guide_POM.matrixIn[0])
        pm.connectAttr(mainGuide_input.worldInverseMatrix[0], elbow_IK_guide_POM.matrixIn[1])

        elbow_IK_clavicleSpaceWM = multMatrix(name=f"{self.name}_IK_clavicleSpaceWM")
        pm.connectAttr(elbow_IK_guide_POM.matrixSum, elbow_IK_clavicleSpaceWM.matrixIn[0])
        pm.connectAttr(main_input.worldMatrix[0], elbow_IK_clavicleSpaceWM.matrixIn[1])

        elbow_IK_mainSpacePOM = multMatrix(name=f"{self.name}_elbow_IK_{main_module}SpacePOM")
        pm.connectAttr(orientPlane_guide.outputMatrix, elbow_IK_mainSpacePOM.matrixIn[0])
        pm.connectAttr(mainGuide_input.worldInverseMatrix[0], elbow_IK_mainSpacePOM.matrixIn[1])

        elbow_IK_baseWM = parentMatrix(name=f"{self.name}_elbow_IK_baseWM")
        pm.connectAttr(elbow_IK_clavicleSpaceWM.matrixSum, elbow_IK_baseWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl_mainSpaceEnable.output, elbow_IK_baseWM.target[0].enableTarget)
        pm.connectAttr(main_input.offsetParentMatrix, elbow_IK_baseWM.target[0].targetMatrix)
        pm.connectAttr(elbow_IK_mainSpacePOM.matrixSum, elbow_IK_baseWM.target[0].offsetMatrix)
        pm.connectAttr(hand_IK_ctrl_worldSpaceEnable.output, elbow_IK_baseWM.target[1].enableTarget)
        pm.connectAttr(orientPlane_guide.outputMatrix, elbow_IK_baseWM.target[1].offsetMatrix)


        #=========================================================================
        self.elbow_IK_baseWM = elbow_IK_baseWM
        #=========================================================================


        elbow_IK_pos_WM = blendMatrix(name=f"{self.name}elbow_IK_pos_WM")
        pm.connectAttr(elbow_IK_baseWM.outputMatrix, elbow_IK_pos_WM.inputMatrix)
        pm.connectAttr(upper_WM_test.matrixSum, elbow_IK_pos_WM.target[0].targetMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], elbow_IK_pos_WM.target[1].targetMatrix)
        pm.connectAttr(settings_ctrl.node.elbowIkBlendpos, elbow_IK_pos_WM.target[1].weight)
        
        elbow_IK_rot_WM = aimMatrix(name=f"{self.name}_elbow_IK_rot_WM")
        pm.connectAttr(elbow_IK_pos_WM.outputMatrix, elbow_IK_rot_WM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], elbow_IK_rot_WM.primaryTargetMatrix)

        pm.connectAttr(elbow_IK_rot_WM.outputMatrix, elbow_IK_ctrl.offsetParentMatrix)


        #IK Elbow Lock

        elbowLock_IK_ctrl_mainSpacePOM = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_{main_module}SpacePOM")
        pm.connectAttr(elbowLock_guide.worldMatrix[0], elbowLock_IK_ctrl_mainSpacePOM.matrixIn[0])
        pm.connectAttr(mainGuide_input.worldInverseMatrix[0], elbowLock_IK_ctrl_mainSpacePOM.matrixIn[1])

        elbowLock_IK_ctrl_mainSpaceWM = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_{main_module}SpaceWM")
        pm.connectAttr(elbowLock_IK_ctrl_mainSpacePOM.matrixSum, elbowLock_IK_ctrl_mainSpaceWM.matrixIn[0])
        pm.connectAttr(main_input.worldMatrix[0], elbowLock_IK_ctrl_mainSpaceWM.matrixIn[1])

        elbowLock_IK_ctrl_worldSpaceEnable = equal(name=f"{self.name}_elbowLock_IK_ctrl_worldSpaceEnable")
        pm.connectAttr(elbowLock_IK_ctrl.node.space, elbowLock_IK_ctrl_worldSpaceEnable.input1)
        elbowLock_IK_ctrl_worldSpaceEnable.input2.set(1)

        elbowLock_IK_ctrl_WM = parentMatrix(name=f"{self.name}_elbowLock_IK_ctrl_WM")
        pm.connectAttr(elbowLock_IK_ctrl_mainSpaceWM.matrixSum, elbowLock_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(elbowLock_IK_ctrl_worldSpaceEnable.output, elbowLock_IK_ctrl_WM.target[0].enableTarget)
        pm.connectAttr(elbowLock_guide.worldMatrix[0], elbowLock_IK_ctrl_WM.target[0].offsetMatrix)

        #=========================================================================
        self.elbowLock_IK_ctrl_WM = elbowLock_IK_ctrl_WM
        #=========================================================================

        """elbowLock_IK_ctrl_WM = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_WM")
        pm.connectAttr(elbowLock_IK_ctrl_mainSpacePOM.matrixSum, elbowLock_IK_ctrl_WM.matrixIn[0])
        pm.connectAttr(main_input.worldMatrix[0], elbowLock_IK_ctrl_WM.matrixIn[1])"""

        pm.connectAttr(elbowLock_IK_ctrl_WM.outputMatrix, elbowLock_IK_ctrl.offsetParentMatrix)


        #IK Prep

        upper_baseWM_noMainScale = multMatrix(name=f"{self.name}_upper_baseWM_noMainScale")
        pm.connectAttr(upper_baseWM.matrixSum, upper_baseWM_noMainScale.matrixIn[0])
        pm.connectAttr(main_input.worldInverseMatrix[0], upper_baseWM_noMainScale.matrixIn[1])

        hand_IK_ctrl_noMainScale = multMatrix(name=f"{self.name}_hand_IK_ctrl_noMainScale")
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], hand_IK_ctrl_noMainScale.matrixIn[0])
        pm.connectAttr(main_input.worldInverseMatrix[0], hand_IK_ctrl_noMainScale.matrixIn[1])

        current_length = distanceBetween(name=f"{self.name}_current_length")
        pm.connectAttr(upper_baseWM_noMainScale.matrixSum, current_length.inMatrix1)
        pm.connectAttr(hand_IK_ctrl_noMainScale.matrixSum, current_length.inMatrix2)

        length_ratio = divide(name=f"{self.name}_length_ratio")
        pm.connectAttr(current_length.distance, length_ratio.input1)
        pm.connectAttr(initial_length.output, length_ratio.input2)

        scaler = max_(name=f"{self.name}_scaler")
        pm.connectAttr(length_ratio.output, scaler.input_[0])
        scaler.input_[1].set(1)

        enable_ikStretch = remapValue(name=f"{self.name}_enable_ikStretch")
        pm.connectAttr(settings_ctrl.node.enableIkStretch, enable_ikStretch.inputValue)
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


        #SOFT IK

        softIK_upper_length_squared = multiply(name=f"{self.name}_softIK_upper_length_squared")
        pm.connectAttr(upper_length.output, softIK_upper_length_squared.input_[0])
        pm.connectAttr(upper_length.output, softIK_upper_length_squared.input_[1])

        softIK_lower_length_squared = multiply(name=f"{self.name}_softIK_lower_length_squared")
        pm.connectAttr(lower_length.output, softIK_lower_length_squared.input_[0])
        pm.connectAttr(lower_length.output, softIK_lower_length_squared.input_[1])

        upper_softIK_numplus = sum_(name=f"{self.name}_upper_softIK_numplus")
        pm.connectAttr(softIK_upper_length_squared.output, upper_softIK_numplus.input_[0])
        pm.connectAttr(clampedLength_squared.output, upper_softIK_numplus.input_[1])

        upper_softIK_denominator = multiply(name=f"{self.name}_upper_softIK_denominator")
        upper_softIK_denominator.input_[0].set(2)
        pm.connectAttr(upper_length.output, upper_softIK_denominator.input_[1])
        pm.connectAttr(clampedLength.output, upper_softIK_denominator.input_[2])

        upper_softIK_numenator = subtract(name=f"{self.name}_upper_softIK_numenator")
        pm.connectAttr(upper_softIK_numplus.output, upper_softIK_numenator.input1)
        pm.connectAttr(softIK_lower_length_squared.output, upper_softIK_numenator.input2)

        upper_softIK_cosValue = divide(name=f"{self.name}_upper_softIK_cosValue")
        pm.connectAttr(upper_softIK_numenator.output, upper_softIK_cosValue.input1)
        pm.connectAttr(upper_softIK_denominator.output, upper_softIK_cosValue.input2)

        upper_softIK_cosValueSquared = multiply(name=f"{self.name}_upper_softIK_cosValueSquared")
        pm.connectAttr(upper_softIK_cosValue.output, upper_softIK_cosValueSquared.input_[0])
        pm.connectAttr(upper_softIK_cosValue.output, upper_softIK_cosValueSquared.input_[1])

        upper_softIK_cosValueRemapped = remapValue(name=f"{self.name}_upper_softIK_cosValueRemapped")
        pm.connectAttr(settings_ctrl.node.softIkStart, upper_softIK_cosValueRemapped.inputMin)
        pm.connectAttr(upper_softIK_cosValue.output, upper_softIK_cosValueRemapped.inputValue)

        upper_softIK_cubicBlendValue = multiply(name=f"{self.name}_upper_softIK_cubicBlendValue")
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[0])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[1])
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, upper_softIK_cubicBlendValue.input_[2])

        ease_in_out_mult = multiply(name=f"{self.name}_ease_in_out_mult")
        ease_in_out_mult.input_[0].set(-2)
        pm.connectAttr(upper_softIK_cosValueRemapped.outValue, ease_in_out_mult.input_[1])

        ease_in_out_sum = sum_(name=f"{self.name}_ease_in_out_sum")
        pm.connectAttr(ease_in_out_mult.output, ease_in_out_sum.input_[0])
        ease_in_out_sum.input_[1].set(2)

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
        ease_in_out_mult2.input_[3].set(4)

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
        pm.connectAttr(upper_softIK_heightSquared.output, upper_softIK_heighthSqaredClamped.input_[0])
        upper_softIK_heighthSqaredClamped.input_[1].set(0)

        softIK_blendcurve_selector = choice(name=f"{self.name}_softIK_blendcurve_selector")
        pm.connectAttr(settings_ctrl.node.softIkCurve, softIK_blendcurve_selector.selector)
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
        pm.connectAttr(settings_ctrl.node.enableSoftIk, disable_soft_ik.input_)

        lower_softIK_scaler = power(name=f"{self.name}_lower_softIK_scaler")
        pm.connectAttr(lower_softIK_scalerSquared.output, lower_softIK_scaler.input_)
        lower_softIK_scaler.exponent.set(0.5)


        #Elbow Lock part

        upper_softIK_scaler_enable = max_(name=f"{self.name}_upper_softIK_scaler_enable")
        pm.connectAttr(disable_soft_ik.output, upper_softIK_scaler_enable.input_[0])
        pm.connectAttr(upper_softIK_scaler.output, upper_softIK_scaler_enable.input_[1])

        elbowLock_IK_ctrl_noMainScale = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_noMainScale")
        pm.connectAttr(elbowLock_IK_ctrl.worldMatrix[0], elbowLock_IK_ctrl_noMainScale.matrixIn[0])
        pm.connectAttr(main_input.worldInverseMatrix[0], elbowLock_IK_ctrl_noMainScale.matrixIn[1])

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
        pm.connectAttr(elbowLock_IK_ctrl.node.Lock, upper_elbowLock_lengthSwitch.attributesBlender)
        pm.connectAttr(upper_lengthScaled.output, upper_elbowLock_lengthSwitch.input_[0])
        pm.connectAttr(elbowLock_IK_upperLength.distance, upper_elbowLock_lengthSwitch.input_[1])

        lower_elbowLock_lengthSwitch = blendTwoAttr(name=f"{self.name}_lower_elbowLock_lengthSwitch")
        pm.connectAttr(elbowLock_IK_ctrl.node.Lock, lower_elbowLock_lengthSwitch.attributesBlender)
        pm.connectAttr(lower_lengthScaled.output, lower_elbowLock_lengthSwitch.input_[0])
        pm.connectAttr(elbowLock_IK_lowerLength.distance, lower_elbowLock_lengthSwitch.input_[1])

        IK_upper_length_squared = multiply(name=f"{self.name}_IK_upper_length_squared")
        pm.connectAttr(upper_elbowLock_lengthSwitch.output, IK_upper_length_squared.input_[0])
        pm.connectAttr(upper_elbowLock_lengthSwitch.output, IK_upper_length_squared.input_[1])

        IK_lower_length_squared = multiply(name=f"{self.name}_IK_lower_length_squared")
        pm.connectAttr(lower_elbowLock_lengthSwitch.output, IK_lower_length_squared.input_[0])
        pm.connectAttr(lower_elbowLock_lengthSwitch.output, IK_lower_length_squared.input_[1])

        sum_a2_c2 = sum_(name=f"{self.name}_sum_a2_c2")
        pm.connectAttr(IK_upper_length_squared.output, sum_a2_c2.input_[0])
        pm.connectAttr(clampedLength_squared.output, sum_a2_c2.input_[1])

        sum_a2_b2 = sum_(name=f"{self.name}_sum_a2_b2")
        pm.connectAttr(IK_upper_length_squared.output, sum_a2_b2.input_[0])
        pm.connectAttr(IK_lower_length_squared.output, sum_a2_b2.input_[1])

        upper_IK_denominator = multiply(name=f"{self.name}_upper_IK_denominator")
        upper_IK_denominator.input_[0].set(2)
        pm.connectAttr(upper_elbowLock_lengthSwitch.output, upper_IK_denominator.input_[1])
        pm.connectAttr(clampedLength.output, upper_IK_denominator.input_[2])

        sum_a2_b2_minus_c2 = subtract(name=f"{self.name}_sum_a2_b2_minus_c2")
        pm.connectAttr(sum_a2_b2.output, sum_a2_b2_minus_c2.input1)
        pm.connectAttr(clampedLength_squared.output, sum_a2_b2_minus_c2.input2)

        lower_IK_denominator = multiply(name=f"{self.name}_lower_IK_denominator")
        lower_IK_denominator.input_[0].set(2)
        pm.connectAttr(upper_elbowLock_lengthSwitch.output, lower_IK_denominator.input_[1])
        pm.connectAttr(lower_elbowLock_lengthSwitch.output, lower_IK_denominator.input_[2])

        sum_a2_c2__minus_b2 = subtract(name=f"{self.name}_sum_a2_c2__minus_b2")
        pm.connectAttr(sum_a2_c2.output, sum_a2_c2__minus_b2.input1)
        pm.connectAttr(IK_lower_length_squared.output, sum_a2_c2__minus_b2.input2)

        upper_IK_cosValue = divide(name=f"{self.name}_upper_IK_cosValue")
        pm.connectAttr(sum_a2_c2__minus_b2.output, upper_IK_cosValue.input1)
        pm.connectAttr(upper_IK_denominator.output, upper_IK_cosValue.input2)

        lower_IK_cosValue = divide(name=f"{self.name}_lower_IK_cosValue")
        pm.connectAttr(sum_a2_b2_minus_c2.output, lower_IK_cosValue.input1)
        pm.connectAttr(lower_IK_denominator.output, lower_IK_cosValue.input2)

        upper_IK_acos = acos(name=f"{self.name}_upper_IK_acos")
        pm.connectAttr(upper_IK_cosValue.output, upper_IK_acos.input_)

        lower_IK_cosValueSquared = multiply(name=f"{self.name}_lower_IK_cosValueSquared")
        pm.connectAttr(lower_IK_cosValue.output, lower_IK_cosValueSquared.input_[0])
        pm.connectAttr(lower_IK_cosValue.output, lower_IK_cosValueSquared.input_[1])

        upper_IK_sin = sin(name=f"{self.name}_upper_IK_sin")
        pm.connectAttr(upper_IK_acos.output, upper_IK_sin.input_)

        lower_IK_sinSquared = subtract(name=f"{self.name}_lower_IK_sinSquared")
        lower_IK_sinSquared.input1.set(1)
        pm.connectAttr(lower_IK_cosValueSquared.output, lower_IK_sinSquared.input2)

        elbowLock_IK_ctrl_WPos = translationFromMatrix(name=f"{self.name}_elbowLock_IK_ctrl_WPos")
        pm.connectAttr(elbowLock_IK_ctrl.worldMatrix[0], elbowLock_IK_ctrl_WPos.input_)

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
        lower_IK_sinSquaredClamped.input_[0].set(0)
        pm.connectAttr(lower_IK_sinSquared.output, lower_IK_sinSquaredClamped.input_[1])

        elbow_IK_poleVectorSwitch = blendColors(name=f"{self.name}_elbow_IK_poleVectorSwitch")
        pm.connectAttr(elbowLock_IK_ctrl.node.Lock, elbow_IK_poleVectorSwitch.blender)
        
        pm.connectAttr(elbowLock_IK_poleVector.output3D, elbow_IK_poleVectorSwitch.color1)
        pm.connectAttr(elbow_IK_poleVector.output, elbow_IK_poleVectorSwitch.color2)

        lower_IK_sin = power(name=f"{self.name}_lower_IK_sin")
        pm.connectAttr(lower_IK_sinSquaredClamped.output, lower_IK_sin.input_)
        lower_IK_sin.exponent.set(0.5)

        IK_baseWM = aimMatrix(name=f"{self.name}_IK_baseWM")
        pm.connectAttr(upper_WM_test.matrixSum, IK_baseWM.inputMatrix)
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], IK_baseWM.primaryTargetMatrix)
        IK_baseWM.primaryInputAxis.set(1, 0, 0)
        IK_baseWM.primaryMode.set(1)
        IK_baseWM.primaryTargetVector.set(0, 0, 0)
        IK_baseWM.secondaryInputAxis.set(0, 1, 0)
        IK_baseWM.secondaryMode.set(2)
        pm.connectAttr(elbow_IK_poleVectorSwitch.output, IK_baseWM.secondaryTargetVector)

        upper_IK_localRotMatrix = fourByFourMatrix(name=f"{self.name}_upper_IK_localRotMatrix")
        pm.connectAttr(upper_IK_cosValue.output, upper_IK_localRotMatrix.in00)
        pm.connectAttr(upper_IK_sin.output, upper_IK_localRotMatrix.in01)
        pm.connectAttr(upper_IK_sin_negated.output, upper_IK_localRotMatrix.in10)
        pm.connectAttr(upper_IK_cosValue.output, upper_IK_localRotMatrix.in11)

        lower_IK_sin_negated = negate(name=f"{self.name}_negate2")
        pm.connectAttr(lower_IK_sin.output, lower_IK_sin_negated.input_)

        lower_IK_cosValue_negated = negate(name=f"{self.name}_negate3")
        pm.connectAttr(lower_IK_cosValue.output, lower_IK_cosValue_negated.input_)

        upper_IK_WM = multMatrix(name=f"{self.name}_upper_IK_WM")
        pm.connectAttr(upper_IK_localRotMatrix.output, upper_IK_WM.matrixIn[0])
        pm.connectAttr(IK_baseWM.outputMatrix, upper_IK_WM.matrixIn[1])

        lower_IK_localRotMatrix = fourByFourMatrix(name=f"{self.name}_lower_IK_localRotMatrix")
        pm.connectAttr(lower_IK_cosValue_negated.output, lower_IK_localRotMatrix.in00)
        pm.connectAttr(lower_IK_sin_negated.output, lower_IK_localRotMatrix.in01)
        pm.connectAttr(lower_IK_sin.output, lower_IK_localRotMatrix.in10)
        pm.connectAttr(lower_IK_cosValue_negated.output, lower_IK_localRotMatrix.in11)
        pm.connectAttr(upper_elbowLock_lengthSwitch.output, lower_IK_localRotMatrix.in30)

        lower_IK_WM = multMatrix(name=f"{self.name}_lower_IK_WM")
        pm.connectAttr(lower_IK_localRotMatrix.output, lower_IK_WM.matrixIn[0])
        pm.connectAttr(upper_IK_WM.matrixSum, lower_IK_WM.matrixIn[1])

        lower_IK_WIM = inverseMatrix(name=f"{self.name}_lower_IK_WIM")
        pm.connectAttr(lower_IK_WM.matrixSum, lower_IK_WIM.inputMatrix)

        hand_IK_baseLocalMatrix = multMatrix(name=f"{self.name}_hand_IK_baseLocalMatrix")
        pm.connectAttr(hand_IK_ctrl.worldMatrix[0], hand_IK_baseLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_IK_WIM.outputMatrix, hand_IK_baseLocalMatrix.matrixIn[1])

        hand_IK_localMatrix_axisX = rowFromMatrix(name=f"{self.name}_hand_IK_localMatrix_axisX")
        pm.connectAttr(hand_IK_baseLocalMatrix.matrixSum, hand_IK_localMatrix_axisX.matrix)
        hand_IK_localMatrix_axisX.input_.set(0)

        hand_IK_localMatrix_axisY = rowFromMatrix(name=f"{self.name}_hand_IK_localMatrix_axisY")
        pm.connectAttr(hand_IK_baseLocalMatrix.matrixSum, hand_IK_localMatrix_axisY.matrix)
        hand_IK_localMatrix_axisY.input_.set(1)

        hand_IK_localMatrix_axisZ = rowFromMatrix(name=f"{self.name}_hand_IK_localMatrix_axisZ")
        pm.connectAttr(hand_IK_baseLocalMatrix.matrixSum, hand_IK_localMatrix_axisZ.matrix)
        hand_IK_localMatrix_axisZ.input_.set(2)

        hand_IK_localMatrix = fourByFourMatrix(name=f"{self.name}_hand_IK_localMatrix")
        pm.connectAttr(hand_IK_localMatrix_axisX.outputX, hand_IK_localMatrix.in00)
        pm.connectAttr(hand_IK_localMatrix_axisX.outputY, hand_IK_localMatrix.in01)
        pm.connectAttr(hand_IK_localMatrix_axisX.outputZ, hand_IK_localMatrix.in02)
        pm.connectAttr(hand_IK_localMatrix_axisX.outputW, hand_IK_localMatrix.in03)
        pm.connectAttr(hand_IK_localMatrix_axisY.outputX, hand_IK_localMatrix.in10)
        pm.connectAttr(hand_IK_localMatrix_axisY.outputY, hand_IK_localMatrix.in11)
        pm.connectAttr(hand_IK_localMatrix_axisY.outputZ, hand_IK_localMatrix.in12)
        pm.connectAttr(hand_IK_localMatrix_axisY.outputW, hand_IK_localMatrix.in13)
        pm.connectAttr(hand_IK_localMatrix_axisZ.outputX, hand_IK_localMatrix.in20)
        pm.connectAttr(hand_IK_localMatrix_axisZ.outputY, hand_IK_localMatrix.in21)
        pm.connectAttr(hand_IK_localMatrix_axisZ.outputZ, hand_IK_localMatrix.in22)
        pm.connectAttr(hand_IK_localMatrix_axisZ.outputW, hand_IK_localMatrix.in23)
        pm.connectAttr(lower_elbowLock_lengthSwitch.output, hand_IK_localMatrix.in30)


        #upper IK/FK Switch

        upper_WM = blendMatrix(name=f"{self.name}_upper_WM")
        pm.connectAttr(upper_FK_ctrl.worldMatrix[0], upper_WM.inputMatrix)
        pm.connectAttr(upper_IK_WM.matrixSum, upper_WM.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.useIK, upper_WM.target[0].weight)


        #lower IK/FK Switch

        lower_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_lower_FK_ctrl_outLocalMatrix")
        pm.connectAttr(lower_FK_ctrl.matrix, lower_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(lower_FK_ctrl_POM_manualScale.output, lower_FK_ctrl_outLocalMatrix.matrixIn[1])

        lower_localMatrix = blendMatrix(name=f"{self.name}_lower_localMatrix")
        pm.connectAttr(lower_FK_ctrl_outLocalMatrix.matrixSum, lower_localMatrix.inputMatrix)
        pm.connectAttr(lower_IK_localRotMatrix.output, lower_localMatrix.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.useIK, lower_localMatrix.target[0].weight)

        lower_WM = multMatrix(name=f"{self.name}_lower_WM")
        pm.connectAttr(lower_localMatrix.outputMatrix, lower_WM.matrixIn[0])
        pm.connectAttr(upper_WM.outputMatrix, lower_WM.matrixIn[1])        


        #hand IK/FK Switch

        hand_FK_ctrl_outLocalMatrix = multMatrix(name=f"{self.name}_hand_FK_ctrl_outLocalMatrix")
        pm.connectAttr(hand_FK_ctrl.matrix, hand_FK_ctrl_outLocalMatrix.matrixIn[0])
        pm.connectAttr(hand_FK_ctrl_POM_manualScale.output, hand_FK_ctrl_outLocalMatrix.matrixIn[1])

        hand_localMatrix = blendMatrix(name=f"{self.name}_hand_localMatrix")
        pm.connectAttr(hand_FK_ctrl_outLocalMatrix.matrixSum, hand_localMatrix.inputMatrix)
        pm.connectAttr(hand_IK_localMatrix.output, hand_localMatrix.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.useIK, hand_localMatrix.target[0].weight)

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


        #visibility IK/FK ctrl
        IK_ctrl = [hand_IK_ctrl, elbow_IK_ctrl, elbowLock_IK_ctrl]
        FK_ctrl = [upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl]

        for ctrl in IK_ctrl:
            pm.connectAttr(settings_ctrl.node.useIK, ctrl.visibility)

        reverse_ctrl_vis = subtract(name=f"{self.name}_reverse_ctrl_vis")
        reverse_ctrl_vis.input1.set(1)
        pm.connectAttr(settings_ctrl.node.useIK, reverse_ctrl_vis.input2)

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

        elbowLock_IK_helper = control.create_connection_curve(name=f"{self.name}_elbowLock_IK_helper")
        elbowLock_IK_helperShape = elbowLock_IK_helper.node.getShape()
        pm.connectAttr(elbowLock_IK_ctrl_WPos.output, elbowLock_IK_helperShape.controlPoints[0])
        pm.connectAttr(lower_IK_WPos.output, elbowLock_IK_helperShape.controlPoints[1])
        colorize(elbowLock_IK_helper.node, ik_color)

        upper_proxy_helper = control.create_connection_curve(name=f"{self.name}_upper_proxy_helper")
        upper_proxy_helperShape = upper_proxy_helper.node.getShape()
        upper_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(upper_WPos.output, upper_proxy_helperShape.controlPoints[0])
        pm.connectAttr(lower_WPos.output, upper_proxy_helperShape.controlPoints[1])
        colorize(upper_proxy_helper.node, limb_connection_color)

        lower_proxy_helper = control.create_connection_curve(name=f"{self.name}_lower_proxy_helper")
        lower_proxy_helperShape = lower_proxy_helper.node.getShape()
        lower_proxy_helperShape.lineWidth.set(2)
        pm.connectAttr(lower_WPos.output, lower_proxy_helperShape.controlPoints[0])
        pm.connectAttr(hand_WPos.output, lower_proxy_helperShape.controlPoints[1])
        colorize(lower_proxy_helper.node, limb_connection_color)

        #outputs (could be removed later)
        hand_output = transform(name=f"{self.name}_hand_output")
        pm.connectAttr(hand_WM.matrixSum, hand_output.offsetParentMatrix)

        handGuide_output = transform(name=f"{self.name}_handGuide_output")
        pm.connectAttr(hand_guide.worldMatrix[0], handGuide_output.offsetParentMatrix)


        #Organizing outliner
        guide_list = [upper_guide, lower_guide, hand_guide, settings_guide, elbowLock_guide]
        control_list = [upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl, hand_IK_ctrl, elbow_IK_ctrl, settings_ctrl, elbowLock_IK_ctrl]
        helper_list = [elbowLock_IK_helper, upper_proxy_helper, lower_proxy_helper]
        joint_list = [upper_jnt, lower_jnt, hand_jnt]


        #groups = create_groups(rig_module_name=self.name)
        for guide in guide_list:
            pm.parent(guide.node, self.groups["guides"].node)

        for ctrl in control_list:
            pm.parent(ctrl.node, self.groups["controls"].node)

        for hlpr in helper_list:
            pm.parent(hlpr.node, self.groups["helpers"].node)

        for jnt in joint_list:
            pm.parent(jnt.node, self.groups["joints"].node)

        pm.parent(hand_output.node, self.groups["outputs"].node)
        pm.parent(handGuide_output.node, self.groups["outputs"].node)


        #visibility guides, ctrl, rigNodes (none yet), joints, proxy geo (none yet) and helpers
        vis_attrs = ["showGuides", "showCtrl", "showRigNodes", "showJoints", "showProxyGeo", "showHelpers"]
        vis_groups = ["guides", "controls", "rigNodes", "joints", "geo", "helpers"]

        for vis_attr, vis_group in zip(vis_attrs, vis_groups):
            pm.connectAttr(f"{settings_ctrl.node}.{vis_attr}", self.groups[vis_group].node.visibility)
            settings_ctrl.node.setAttr(vis_attr, keyable=False, channelBox=True)

    
    def addParent(self, parent_name="parent"):

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


        upper_FK_ctrl_parentSpacePOM = multMatrix(name=f"{self.name}_upper_FK_ctrl_{parent_name}SpacePOM")
        pm.connectAttr(self.upper_FK_guide_outWM.outputMatrix, upper_FK_ctrl_parentSpacePOM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], upper_FK_ctrl_parentSpacePOM.matrixIn[1])

        hand_IK_ctrl_parentSpacePOM = multMatrix(name=f"{self.name}_hand_IK_ctrl_{parent_name}SpacePOM")
        pm.connectAttr(self.hand_FK_guide_outWM.outputMatrix, hand_IK_ctrl_parentSpacePOM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], hand_IK_ctrl_parentSpacePOM.matrixIn[1])

        elbow_IK_ctrl_parentSpacePOM = multMatrix(name=f"{self.name}_elbow_IK_ctrl_{parent_name}SpacePOM")
        pm.connectAttr(self.orientPlane_guide.outputMatrix, elbow_IK_ctrl_parentSpacePOM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], elbow_IK_ctrl_parentSpacePOM.matrixIn[1])

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


        elbowLock_IK_ctrl_parentSpacePOM = multMatrix(name=f"{self.name}_elbowLock_IK_ctrl_{parent_name}SpacePOM")
        pm.connectAttr(self.elbowLock_guide.worldMatrix[0], elbowLock_IK_ctrl_parentSpacePOM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], elbowLock_IK_ctrl_parentSpacePOM.matrixIn[1])

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
        

a = Limb(main_module="root", connection_module="clavicle", limb_type="arm", limb_side="l", upper_guide_pos=(2, 10, 0), lower_guide_pos=(0, 1, 0), hand_guide_pos=(2, 0, 0), upper_guide_rot=(0, 180, 0))

#a.addParent(parent_name="hip")



class Clavicle:
    def __init__(self, main_module:str, connection_module:str , limb_type:str, limb_side:str, start_guide_pos:tuple = (0, 0, 0), end_guide_pos:tuple = (0, 0, 0), clavicle_ctrl_color:list = [0, 0, 0]):

        self.name = f"{limb_type}_{limb_side}"
        self.limb_type = limb_type
        self.limb_side = limb_side

        groups = create_groups(rig_module_name=self.name)
        self.groups = groups

        start_guide = create_guide(name=f"{self.name}_start_guide", position=start_guide_pos, color=guide_color)
        end_guide = create_guide(name=f"{self.name}_end_guide", position=end_guide_pos, color=guide_color)

        #main_input = transform(name=f"{self.name}_{main_module}_input")
        #mainGuide_input = transform(name=f"{self.name}_{main_module}Guide_input")

        parent_input = transform(name=f"{self.name}_{connection_module}_input")
        parentGuide_input = transform(name=f"{self.name}_{connection_module}Guide_input")

        end_output = transform(name=f"{self.name}_end_output")
        endGuide_output = transform(name=f"{self.name}_endGuide_output")

        pm.parent([parent_input.node, parentGuide_input.node], groups["inputs"].node)

        start_guide_orientedM = aimMatrix(name=f"{self.name}_start_guide_orientedM")
        pm.connectAttr(start_guide.worldMatrix[0], start_guide_orientedM.inputMatrix)
        pm.connectAttr(end_guide.worldMatrix[0], start_guide_orientedM.primaryTargetMatrix)
        start_guide_orientedM.secondaryMode.set(2)
        start_guide_orientedM.secondaryTargetVector.set(0, 0, -1)

        module_POM = multMatrix(name=f"{self.name}_POM")
        pm.connectAttr(end_guide.worldMatrix[0], module_POM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], module_POM.matrixIn[1])

        start_POM = multMatrix(name=f"{self.name}_start_POM")
        pm.connectAttr(start_guide_orientedM.outputMatrix, start_POM.matrixIn[0])
        pm.connectAttr(parentGuide_input.worldInverseMatrix[0], start_POM.matrixIn[1])

        ctrl_WM = multMatrix(name=f"{self.name}_ctrl_WM")
        pm.connectAttr(module_POM.matrixSum, ctrl_WM.matrixIn[0])
        pm.connectAttr(parent_input.worldMatrix[0], ctrl_WM.matrixIn[1])

        start_baseWM = multMatrix(name=f"{self.name}_start_baseWM")
        pm.connectAttr(start_POM.matrixSum, start_baseWM.matrixIn[0])
        pm.connectAttr(parent_input.worldMatrix[0], start_baseWM.matrixIn[1])

        ctrl = control.create(ctrl_type="fourArrows", name=f"{self.name}_ctrl", normal=(1, 0, 0))
        pm.connectAttr(ctrl_WM.matrixSum, ctrl.offsetParentMatrix)
        ctrl.node.addAttr(attr="lockLength", niceName="Lock Length", attributeType="float", minValue=0, maxValue=1, defaultValue=0, hidden=False, keyable=True)

        colorize(ctrl.node, clavicle_ctrl_color)

        start_WM = aimMatrix(name=f"{self.name}_startWM")
        pm.connectAttr(start_baseWM.matrixSum, start_WM.inputMatrix)
        pm.connectAttr(ctrl.worldMatrix[0], start_WM.primaryTargetMatrix)

        start_WM_noMainScale = multMatrix(name=f"{self.name}_start_WM_noMainScale")
        pm.connectAttr(start_WM.outputMatrix, start_WM_noMainScale.matrixIn[0])
        pm.connectAttr(parent_input.worldInverseMatrix[0], start_WM_noMainScale.matrixIn[1])

        ctrl_noMainScale = multMatrix(name=f"{self.name}_ctrl_noMainScale")
        pm.connectAttr(ctrl.worldMatrix[0], ctrl_noMainScale.matrixIn[0])
        pm.connectAttr(parent_input.worldInverseMatrix[0], ctrl_noMainScale.matrixIn[1])

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

        end_localM = fourByFourMatrix(name=f"{self.name}_end_localM")
        pm.connectAttr(end_localTx.output, end_localM.in30)

        end_WM = multMatrix(name=f"{self.name}_end_WM")
        pm.connectAttr(end_localM.output, end_WM.matrixIn[0])
        pm.connectAttr(start_WM.outputMatrix, end_WM.matrixIn[1])

        start_guide_orientedRotationM = pickMatrix(name=f"{self.name}_start_guide_orientedRotationM")
        pm.connectAttr(start_guide_orientedM.outputMatrix, start_guide_orientedRotationM.inputMatrix)
        start_guide_orientedRotationM.useTranslate.set(0)

        start_guide_posWM = fourByFourMatrix(name=f"{self.name}_start_guide_posWM")
        pm.connectAttr(end_guide.translateX, start_guide_posWM.in30)
        pm.connectAttr(end_guide.translateY, start_guide_posWM.in31)
        pm.connectAttr(end_guide.translateZ, start_guide_posWM.in32)

        endGuide_output_WM = addMatrix(name=f"{self.name}_endGuide_output_WM")
        pm.connectAttr(start_guide_orientedRotationM.outputMatrix, endGuide_output_WM.matrixIn[0])
        pm.connectAttr(start_guide_posWM.output, endGuide_output_WM.matrixIn[1])

        start_jnt = joint(name=f"{self.name}_start_jnt")
        pm.connectAttr(start_WM.outputMatrix, start_jnt.offsetParentMatrix)

        end_jnt = joint(name=f"{self.name}_end_jnt")
        pm.connectAttr(end_WM.matrixSum, end_jnt.offsetParentMatrix)

        pm.connectAttr(end_WM.matrixSum, end_output.offsetParentMatrix)
        pm.connectAttr(endGuide_output_WM.matrixSum, endGuide_output.offsetParentMatrix)

        guide_list = [start_guide, end_guide]
        joint_list = [start_jnt, end_jnt]
        output_list = [end_output, endGuide_output]

        for guide in guide_list:
            pm.parent(guide.node, self.groups["guides"].node)
        
        for jnt in joint_list:
            pm.parent(jnt.node, self.groups["joints"].node)

        for out in output_list:
            pm.parent(out.node, self.groups["outputs"].node)
        
        pm.parent(ctrl.node, self.groups["controls"].node)


b = Clavicle(main_module="root", connection_module="chest", limb_type="clavicle", limb_side="L", start_guide_pos=(1, 8, 0), end_guide_pos=(2, 9, 0), clavicle_ctrl_color=[1, 0, 0])