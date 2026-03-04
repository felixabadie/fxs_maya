from maya import cmds as cmds

guide_color = (1, 1, 1)
god_color = (1, 0, 1)
demigod_color = (0.7, 0, 0.7)
main_color = (0.4, 0, 0.4)


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

    return guides_grp, controls_grp, outputs
    


def create_root_guide(name, groups):

    """ Creates a Locator as a guide for the root module """

    loc_name = f"{name}_guide"
    root_guide = cmds.spaceLocator(name=loc_name)
    colorize(root_guide, guide_color)
    print("Created Locator")
    
    root_god_ctrl_name = f"{name}_god_ctrl"
    root_demigod_ctrl_name = f"{name}_demigod_ctrl"
    root_main_ctrl_name = f"{name}_main_ctrl"
    print("Created Controls")

    root_god_ctrl = cmds.circle(name=root_god_ctrl_name, radius=8, normal=(0, 1, 0))
    root_demigod_ctrl = cmds.circle(name=root_demigod_ctrl_name, radius=7, normal=(0, 1, 0))
    root_main_ctrl = cmds.circle(name=root_main_ctrl_name, radius=6, normal=(0, 1, 0))

    colorize(root_god_ctrl, god_color)
    colorize(root_demigod_ctrl, demigod_color)
    colorize(root_main_ctrl, main_color)

    root_main_output = cmds.group(empty=True, name=f"{name}_main_output", parent=f"{name}_outputs")
    root_mainGuide_output = cmds.group(empty=True, name=f"{name}_mainGuide_output", parent=f"{name}_outputs")

    cmds.connectAttr(f"{root_guide[0]}.worldMatrix[0]", f"{root_god_ctrl[0]}.offsetParentMatrix")
    cmds.connectAttr(f"{root_god_ctrl[0]}.worldMatrix[0]", f"{root_demigod_ctrl[0]}.offsetParentMatrix")
    cmds.connectAttr(f"{root_demigod_ctrl[0]}.worldMatrix[0]", f"{root_main_ctrl[0]}.offsetParentMatrix")
    cmds.connectAttr(f"{root_main_ctrl[0]}.worldMatrix[0]", f"{root_main_output}.offsetParentMatrix")
    cmds.connectAttr(f"{root_guide[0]}.worldMatrix[0]", f"{root_mainGuide_output}.offsetParentMatrix")

    cmds.parent(root_guide, groups[0])
    cmds.parent(root_god_ctrl, groups[1])
    cmds.parent(root_demigod_ctrl, groups[1])
    cmds.parent(root_main_ctrl, groups[1])
    cmds.parent(root_main_output, groups[2])
    cmds.parent(root_mainGuide_output, groups[2])


class CreateRootModule:
    def __init__(self):
        self.win_id = "root_module_creator_win"

        if cmds.window(self.win_id, query=True, exists=True):
            cmds.deleteUI(self.win_id)

        cmds.window(self.win_id, title="Root Module Creator", widthHeight=(400, 150), backgroundColor=(0, 0.153, 0.212))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
        cmds.text(
            label=(
                "This Tool will create a Root Rig module with a guide and 3 Controllers \n based on Jean Paul Tossings Rig-Structure"
            ),
            align="left"
        )

        cmds.text(label = ("Module Name: "), align="left")
        self.name = cmds.textField(text="Enter Name", editable=True)

        cmds.rowLayout(numberOfColumns=2)
        cmds.button(label="Start", c=self.execute)
        cmds.button(label="Cancel", c=self.cancel)
        cmds.setParent('..')

        cmds.showWindow(self.win_id)

    def execute (self, *args):

        rig_module_name = cmds.textField(self.name, query=True, text=True)

        returngroups =  create_groups(rig_module_name)
        create_root_guide(rig_module_name, returngroups)




    def cancel (self, *args):
        pass

if __name__ == "__main__":
    CreateRootModule()