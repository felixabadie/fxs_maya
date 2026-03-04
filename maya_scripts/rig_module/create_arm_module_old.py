from maya import cmds

guide_color = (1, 1, 1)
right_fk_color = (1, 0, 0)
right_ik_color = (0, 0.85, 0.83)
left_fk_color = (0, 0, 1)
left_ik_color = (1, 0.6, 0)

def colorize(name, color=(0, 0, 0)):
    """
    Activates Drawing overrides to change color, color space in RGB from 0 to 1
    """

    rgb = ("R", "G", "B")


    cmds.setAttr(f"{name[0]}.overrideEnabled", 1)
    cmds.setAttr(f"{name[0]}.overrideRGBColors", 1)

    for channel, color in zip(rgb, color):

        cmds.setAttr(f"{name[0]}.overrideColor%s" %channel, color)


def create_groups(rig_module_name):
    """Creates empty rig module based on Jean Paul Tossings structure"""
    

    all_groups = []
    
    mod_grp = cmds.group(empty=True, name=f"{rig_module_name}_mod")
    all_groups.append(mod_grp)
    setup_grp = cmds.group(empty=True, name=f"{rig_module_name}_SETUP", parent=mod_grp)
    all_groups.append(setup_grp)
    inputs_grp = cmds.group(empty=True, name=f"{rig_module_name}_inputs", parent=mod_grp)
    all_groups.append(inputs_grp)
    parent_input_grp = cmds.group(empty=True, name=f"{rig_module_name}_parent_input", parent=inputs_grp)
    all_groups.append(parent_input_grp)
    parentGuide_input_grp = cmds.group(empty=True, name=f"{rig_module_name}_parentGuide_input", parent=inputs_grp)
    all_groups.append(parentGuide_input_grp)
    guides_grp = cmds.group(empty=True, name=f"{rig_module_name}_guides", parent=mod_grp)
    all_groups.append(guides_grp)
    controls_grp = cmds.group(empty=True, name=f"{rig_module_name}_controls", parent=mod_grp)
    all_groups.append(controls_grp)
    rigNodes_grp = cmds.group(empty=True, name=f"{rig_module_name}_rigNodes", parent=mod_grp)
    all_groups.append(rigNodes_grp)
    joints_grp = cmds.group(empty=True, name=f"{rig_module_name}_joints", parent=mod_grp)
    all_groups.append(joints_grp)
    geo_grp = cmds.group(empty=True, name=f"{rig_module_name}_geo", parent=mod_grp)
    all_groups.append(geo_grp)
    helpers = cmds.group(empty=True, name=f"{rig_module_name}_helpers", parent=mod_grp)
    all_groups.append(helpers)
    outputs = cmds.group(empty=True, name=f"{rig_module_name}_outputs", parent=mod_grp)
    all_groups.append(outputs)

    for current_group in all_groups:
        cmds.setAttr(f"{current_group}.tx", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.ty", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.tz", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.rx", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.ry", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.rz", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.sx", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.sy", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.sz", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{current_group}.v", lock=True, keyable=False, channelBox=False)

    return setup_grp, inputs_grp, guides_grp, controls_grp, joints_grp, rigNodes_grp, joints_grp, geo_grp, helpers, outputs

"""def list_all_children(parent):
    all_children = []
    children = cmds.listRelatices(parent, children=True, fullPath=True) or []
    for child in children:
        all_children.extend(list_all_children(child))
    return all_children"""

def create_left_control_module(name, base_parent):

    upper_guide = cmds.spaceLocator(name=f"{name}_upper_guide")
    cmds.xform(upper_guide[0], translation=(2, 4, 0), worldSpace=True)
    lower_guide = cmds.spaceLocator(name=f"{name}_lower_guide")
    cmds.xform(lower_guide[0], translation=(0, 0, 0), worldSpace=True)
    hand_guide = cmds.spaceLocator(name=f"{name}_hand_guide")
    cmds.xform(hand_guide[0], translation=(8, 4, 0), worldSpace=True)

    colorize(upper_guide, guide_color)
    colorize(lower_guide, guide_color)
    colorize(hand_guide, guide_color)

    upper_fk_ctrl = cmds.circle(name=f"{name}_upper_fk_ctrl", radius=2, normal=(1, 0, 0))
    lower_fk_ctrl = cmds.circle(name=f"{name}_lower_fk_ctrl", radius=2, normal=(1, 0, 0))
    hand_fk_ctrl = cmds.circle(name=f"{name}_hand_fk_ctrl", radius=2, normal=(1, 0, 0))

    colorize(upper_fk_ctrl, left_fk_color)
    colorize(lower_fk_ctrl, left_fk_color)
    colorize(hand_fk_ctrl, left_fk_color)

    arm_L_orientPlane_guide = cmds.createNode("aimMatrix", name=f"{name}_orientPlane_guide")

    cmds.connectAttr(f"{upper_guide[0]}.worldMatrix[0]", f"{arm_L_orientPlane_guide}.inputMatrix")
    cmds.connectAttr(f"{hand_guide[0]}.worldMatrix[0]", f"{arm_L_orientPlane_guide}.primary.primaryTargetMatrix")
    cmds.connectAttr(f"{upper_guide[0]}.worldMatrix[0]", f"{arm_L_orientPlane_guide}.secondary.secondaryTargetMatrix")

    arm_L_lower_ctrl_guide_WM = cmds.createNode("blendMatrix", name=f"{name}_lower_ctrl_guide_WM")
    
    cmds.connectAttr(f"{arm_L_orientPlane_guide}.outputMatrix", f"{arm_L_lower_ctrl_guide_WM}.inputMatrix")
    cmds.connectAttr(f"{hand_guide[0]}.worldMatrix[0]", f"{arm_L_lower_ctrl_guide_WM}.target[0].targetMatrix")
    cmds.setAttr(f"{arm_L_lower_ctrl_guide_WM}.target[0].weight", 0.5)
    cmds.setAttr(f"{arm_L_lower_ctrl_guide_WM}.target[0].scaleWeight", 0)
    cmds.setAttr(f"{arm_L_lower_ctrl_guide_WM}.target[0].translateWeight", 1)
    cmds.setAttr(f"{arm_L_lower_ctrl_guide_WM}.target[0].rotateWeight", 0)
    cmds.setAttr(f"{arm_L_lower_ctrl_guide_WM}.target[0].shearWeight", 0)
    cmds.connectAttr(f"{arm_L_lower_ctrl_guide_WM}.outputMatrix", f"{lower_guide[0]}.offsetParentMatrix")

    arm_main_input = cmds.group(empty=True, name=f"{name}_main_input")
    arm_mainGuide_input = cmds.group(empty=True, name=f"{name}_mainGuide_input")

    arm_upper_guide_outWM = cmds.createNode("aimMatrix", name=f"{name}_upper_guide_outWM")
    arm_upper_base_POM = cmds.createNode("multMatrix", name=f"{name}_upper_base_POM")
    arm_upper_baseWM = cmds.createNode("multMatrix", name=f"{name}_upper_baseWM")
    arm_upper_guide_outWIM = cmds.createNode("inverseMatrix", name=f"{name}_upper_guide_outWIM")

    arm_lower_guide_outWM = cmds.createNode("aimMatrix", name=f"{name}_lower_guide_outWM")
    arm_lower_basePOM = cmds.createNode("multMatrix", name=f"{name}_lower_base_POM")
    arm_lower_baseWM =  cmds.createNode("multMatrix", name=f"{name}_lower_baseWM")
    arm_lower_guide_outWIM = cmds.createNode("inverseMatrix", name=f"{name}_lower_guide_outWIM")

    arm_hand_guide_outWM = cmds.createNode("blendMatrix", name=f"{name}_hand_guide_outWM")
    arm_hand_base_POM = cmds.createNode("multMatrix", name=f"{name}_hand_base_POM")
    arm_hand_baseWM =  cmds.createNode("multMatrix", name=f"{name}_hand_baseWM")

    cmds.connectAttr(f"{upper_guide[0]}.worldMatrix[0]", f"{arm_upper_guide_outWM}.inputMatrix")
    cmds.connectAttr(f"{lower_guide[0]}.worldMatrix[0]", f"{arm_upper_guide_outWM}.primary.primaryTargetMatrix")
    cmds.connectAttr(f"{upper_guide[0]}.worldMatrix[0]", f"{arm_upper_guide_outWM}.secondary.secondaryTargetMatrix")
    cmds.setAttr(f"{arm_upper_guide_outWM}.primary.primaryInputAxisX", 1)
    cmds.setAttr(f"{arm_upper_guide_outWM}.primary.primaryInputAxisY", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.primary.primaryInputAxisZ", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.primary.primaryMode", 1)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryInputAxisX", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryInputAxisY", 1)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryInputAxisZ", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryMode", 2)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryTargetVectorX", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryTargetVectorY", 0)
    cmds.setAttr(f"{arm_upper_guide_outWM}.secondary.secondaryTargetVectorZ", -1)

    cmds.connectAttr(f"{arm_upper_guide_outWM}.outputMatrix", f"{arm_upper_base_POM}.matrixIn[0]")
    cmds.connectAttr(f"{arm_mainGuide_input}.worldInverseMatrix[0]", f"{arm_upper_base_POM}.matrixIn[1]")

    cmds.connectAttr(f"{arm_upper_base_POM}.matrixSum", f"{arm_upper_baseWM}.matrixIn[0]")
    cmds.connectAttr(f"{arm_main_input}.worldMatrix[0]", f"{arm_upper_baseWM}.matrixIn[1]")
    cmds.connectAttr(f"{arm_upper_baseWM}.matrixSum", f"{upper_fk_ctrl[0]}.offsetParentMatrix")

    cmds.connectAttr(f"{arm_upper_guide_outWM}.outputMatrix", f"{arm_upper_guide_outWIM}.inputMatrix")

    cmds.connectAttr(f"{lower_guide[0]}.worldMatrix[0]", f"{arm_lower_guide_outWM}.inputMatrix")
    cmds.connectAttr(f"{hand_guide[0]}.worldMatrix[0]", f"{arm_lower_guide_outWM}.primary.primaryTargetMatrix")
    cmds.connectAttr(f"{upper_guide[0]}.worldMatrix[0]", f"{arm_lower_guide_outWM}.secondary.secondaryTargetMatrix")
    cmds.setAttr(f"{arm_lower_guide_outWM}.primary.primaryInputAxisX", 1)
    cmds.setAttr(f"{arm_lower_guide_outWM}.primary.primaryInputAxisY", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.primary.primaryInputAxisZ", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.primary.primaryMode", 1)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryInputAxisX", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryInputAxisY", 1)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryInputAxisZ", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryMode", 2)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryTargetVectorX", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryTargetVectorY", 0)
    cmds.setAttr(f"{arm_lower_guide_outWM}.secondary.secondaryTargetVectorZ", -1)

    cmds.connectAttr(f"{arm_lower_guide_outWM}.outputMatrix", f"{arm_lower_basePOM}.matrixIn[0]")
    cmds.connectAttr(f"{arm_upper_guide_outWIM}.outputMatrix", f"{arm_lower_basePOM}.matrixIn[1]")

    cmds.connectAttr(f"{arm_lower_basePOM}.matrixSum", f"{arm_lower_baseWM}.matrixIn[0]")
    cmds.connectAttr(f"{upper_fk_ctrl[0]}.worldMatrix[0]", f"{arm_lower_baseWM}.matrixIn[1]")
    cmds.connectAttr(f"{arm_lower_baseWM}.matrixSum", f"{lower_fk_ctrl[0]}.offsetParentMatrix")

    cmds.connectAttr(f"{arm_lower_guide_outWM}.outputMatrix", f"{arm_hand_guide_outWM}.inputMatrix")
    cmds.connectAttr(f"{hand_guide[0]}.worldMatrix[0]", f"{arm_hand_guide_outWM}.target[0].targetMatrix")
    cmds.setAttr(f"{arm_hand_guide_outWM}.target[0].weight", 1)
    cmds.setAttr(f"{arm_hand_guide_outWM}.target[0].scaleWeight", 0)
    cmds.setAttr(f"{arm_hand_guide_outWM}.target[0].translateWeight", 1)
    cmds.setAttr(f"{arm_hand_guide_outWM}.target[0].rotateWeight", 0)
    cmds.setAttr(f"{arm_hand_guide_outWM}.target[0].shearWeight", 0)

    cmds.connectAttr(f"{arm_lower_guide_outWM}.outputMatrix", f"{arm_lower_guide_outWIM}.inputMatrix")

    cmds.connectAttr(f"{arm_hand_guide_outWM}.outputMatrix", f"{arm_hand_base_POM}.matrixIn[0]")
    cmds.connectAttr(f"{arm_lower_guide_outWIM}.outputMatrix", f"{arm_hand_base_POM}.matrixIn[1]")

    cmds.connectAttr(f"{arm_hand_base_POM}.matrixSum", f"{arm_hand_baseWM}.matrixIn[0]")
    cmds.connectAttr(f"{lower_fk_ctrl[0]}.worldMatrix[0]", f"{arm_hand_baseWM}.matrixIn[1]")
    cmds.connectAttr(f"{arm_hand_baseWM}.matrixSum", f"{hand_fk_ctrl[0]}.offsetParentMatrix")


class CreateArmModule:
    def __init__(self):
        self.win_id = "arm_module_creator_win"

        if cmds.window(self.win_id, query=True, exists=True):
            cmds.deleteUI(self.win_id)

        cmds.window(self.win_id, title="Arm Module Creator", widthHeight=(400, 150), backgroundColor=(0, 0.153, 0.212))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
        cmds.text(
            label=(
                "This Tool will either create a left or right arm Rig module with guides and fk/ik Controllers \n based on Jean Paul Tossings Matrix Rigging"
            ),
            align="left"
        )

        cmds.text(label = ("Module Name: "), align="left")
        self.name = cmds.textField(text="Enter Name", editable=True)

        cmds.separator(h=10)

        cmds.rowLayout(numberOfColumns=2)
        self.left_checkbox = cmds.checkBox(label="left", value=False)
        self.right_checkbox = cmds.checkBox(label="right", value=False)
        cmds.setParent('..')

        cmds.separator(h=5)

        cmds.text(label = "Select the root module in the ouliner before starting the program")

        self.root_module = cmds.ls(selection=True)

        cmds.rowLayout(numberOfColumns=2)
        cmds.button(label="Start", c=self.execute) #logic needs to be changed
        cmds.button(label="Cancel", c=self.cancel)
        cmds.setParent('..')

        cmds.showWindow(self.win_id)

    def execute(self, *args):
        print("arm_module")

        rig_module_name = cmds.textField(self.name, query=True, text=True)

        left = cmds.checkBox(self.left_checkbox, query=True, value=True)
        right = cmds.checkBox(self.right_checkbox, query=True, value=True)

        base_root = self.root_module
        print(f"root name: {base_root}")

        if left == True:

            left_rig_module_name = rig_module_name + "_L"
            create_left_control_module(left_rig_module_name, base_root)

        if right == True:

            right_rig_module_name = rig_module_name + "_R"


    def cancel (self, *args):
        print("cancel_tool")


if __name__ == "__main__":
    CreateArmModule()