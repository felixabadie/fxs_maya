"""Creates empty rig module based on Jean Paul Tossings structure"""

from maya import cmds as cmds

def create_groups(rig_module_name):
    
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

class EmptyRigModuleCreator:
    def __init__(self):
        self.win_id = "empty_rig_module_creator_win"

        if cmds.window(self.win_id, query=True, exists=True):
            cmds.deleteUI(self.win_id)

        cmds.window(self.win_id, title="Empty Rig Module Creator", widthHeight=(400, 150), backgroundColor=(0, 0.153, 0.212))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
        cmds.text(
            label=(
                "This Tool will create an empty rig module group as used by Jean Paul Tossings"
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

    def execute(self, *args):
        rig_module_name = cmds.textField(self.name, query=True, text=True)

        create_groups(rig_module_name)

    def cancel(self, *args):
        cmds.deleteUI(self.win_id)

if __name__ == "__main__":
    EmptyRigModuleCreator()