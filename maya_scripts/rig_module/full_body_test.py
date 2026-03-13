import json
import pymel.core as pm
from maya_scripts.prox_node_setup.generated_nodes import *
from utilities import TextFieldHelper

from rig_module.root import RootModule
from rig_module.base_limb import LimbModule
from rig_module.spine import SpineModule
from rig_module.leg import LegModule
from rig_module.clavicle import ClavicleModule
from rig_module import create_root_module

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
right_fk_color = [1, 0, 0]
left_ik_color = [0, 0.85, 0.83]
left_fk_color = [0, 0, 1]
right_ik_color = [1, 0.6, 0]

"""
Todo:

When everything works build build_registry system. Claude code on discord -> Use preexisting templates
"""

class BipedManager:
    def __init__(self):
        self.win_id = "fxs_biped_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Biped Rigging Manager") as win:
            with pm.columnLayout(adj=True):
                self.root_name = TextFieldHelper("Root module name: ")
                self.spine_name = TextFieldHelper("Spine module name: ")
                self.clavicle_name = TextFieldHelper("Clavicle module name: ")
                self.leg_start_name = TextFieldHelper("Leg_start module name: ")
                self.arm_name = TextFieldHelper("Arm module name: ")
                self.leg_name = TextFieldHelper("Leg module name: ")
                self.spine_bind_jnts = pm.intFieldGrp(label="Amount spine bind joints: ", numberOfFields=1)
                self.arm_bind_jnts = pm.intFieldGrp(label="Amount arm bind joints: ", numberOfFields=1)
                self.leg_bind_jnts = pm.intFieldGrp(label="Amount leg bind joints: ", numberOfFields=1)

                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self, *args):
        root_name = self.root_name.control.getText()
        spine_name = self.spine_name.control.getText()
        clavicle_base_name = self.clavicle_name.control.getText()
        leg_start_base_name = self.leg_start_name.control.getText()
        arm_base_name = self.arm_name.control.getText()
        leg_base_name = self.leg_name.control.getText()

        left_prefix = "L"
        right_prefix = "R"

        bind_jnts_dict = {}
        bind_jnts_keys = ["spine_bind_jnts", "arm_bind_jnts", "leg_bind_jnts"]

        bind_jnts_list = [self.spine_bind_jnts, self.arm_bind_jnts, self.leg_bind_jnts]

        for i, jnts in enumerate(bind_jnts_list):
            if pm.intFieldGrp(jnts, query=True, value1=True) > 0:
                bind_jnts_dict[bind_jnts_keys[i]] = pm.intFieldGrp(jnts, query=True, value1=True)
            else:
                print("Not enough bind joints (using 5 instead)")
                bind_jnts_dict[bind_jnts_keys[i]] = 5

    
        root = RootModule(
            name=root_name,
            ctrl_size=10
        )

        spine = SpineModule(
            parent_module=root_name,
            name=spine_name,
            bind_jnts=bind_jnts_dict["spine_bind_jnts"],
            com_guide_pos=(0, 14, 0), 
            hip_guide_pos=(0, 12, 0), 
            mid_guide_pos=(0, 0, 0), 
            chest_guide_pos=(0, 24, 0),
            settings_guide_pos=(5, 16, 0)
        )

        l_arm_clavicle = ClavicleModule(
            parent_module=spine_name,
            limb_type=clavicle_base_name,
            limb_side=left_prefix,
            start_guide_pos=(2, 24, 1), 
            end_guide_pos=(3, 26, 0), 
            clavicle_ctrl_color=left_fk_color
        )

        l_arm = LimbModule(
            parent_module=clavicle_base_name,
            main_module=root_name,
            limb_type=arm_base_name,
            limb_side=left_prefix,
            upper_guide_pos=(4, 25, 0), 
            hand_guide_pos=(14, 25, 0),
            settings_guide_pos=(5, 25, -4),
            elbowLock_guide_pos=(9, 25, -7),
            fk_color=left_fk_color, 
            ik_color=left_ik_color
        )

        r_arm_clavicle = ClavicleModule(
            parent_module=spine_name,
            limb_type=clavicle_base_name,
            limb_side=right_prefix,
            start_guide_pos=(-2, 24, 1),
            end_guide_pos=(-3, 26, 0),
            clavicle_ctrl_color=right_fk_color
        )

        r_arm = LimbModule(
            parent_module=clavicle_base_name,
            main_module=root_name,
            limb_type=arm_base_name,
            limb_side=right_prefix,
            upper_guide_pos=(-4, 25, 0),
            hand_guide_pos=(-14, 25, 0),
            settings_guide_pos=(-5, 25, -4),
            elbowLock_guide_pos=(-9, 25, -7),
            fk_color=right_fk_color,
            ik_color=right_ik_color
        )

        l_leg_start = ClavicleModule(
            parent_module=spine_name,
            limb_type=leg_start_base_name,
            limb_side=left_prefix,
            start_guide_pos=(2, 12, 0),
            end_guide_pos=(3, 10, 0),
            clavicle_ctrl_color=left_fk_color
        )

        l_leg = LegModule(
            parent_module=leg_start_base_name,
            main_module=root_name,
            limb_type=leg_base_name,
            limb_side=left_prefix,
            upper_guide_pos=(4, 10, 0),
            upper_guide_rot=(180, 0, 0),
            lower_guide_pos=(0, 1, 0),
            ankle_guide_pos=(0, 1, 0),
            foot_guide_pos=(4, 0, 0),
            foot_left_bank_guide_pos=(1, 0, 0),
            foot_right_bank_guide_pos=(-1, 0, 0),
            foot_heel_guide_pos=(0, 0, -1),
            foot_end_guide_pos=(0, 0, 5),
            foot_ball_guide_pos=(0, 0, 3),
            settings_guide_pos=(5, 13, -2),
            kneeLock_guide_pos=(4, 5, 8),
            fk_color=left_fk_color,
            ik_color=left_ik_color
        )

        r_leg_start = ClavicleModule(
            parent_module=spine_name,
            limb_type=leg_start_base_name,
            limb_side=right_prefix,
            start_guide_pos=(-2, 12, 0),
            end_guide_pos=(-3, 10, 0),
            clavicle_ctrl_color=left_fk_color
        )

        r_leg = LegModule(
            parent_module=leg_start_base_name,
            main_module=root_name,
            limb_type=leg_base_name,
            limb_side=right_prefix,
            upper_guide_pos=(-4, 10, 0),
            upper_guide_rot=(180, 0, 0),
            lower_guide_pos=(0, 1, 0),
            ankle_guide_pos=(0, 1, 0),
            foot_guide_pos=(-4, 0, 0),
            foot_left_bank_guide_pos=(1, 0, 0),
            foot_right_bank_guide_pos=(-1, 0, 0),
            foot_heel_guide_pos=(0, 0, 1),
            foot_end_guide_pos=(0, 0, 5),
            foot_ball_guide_pos=(0, 0, 3),
            settings_guide_pos=(-5, 13, -2),
            kneeLock_guide_pos=(-4, 5, 8),
            fk_color=right_fk_color,
            ik_color=right_ik_color
        )

        for mod in [l_arm, r_arm, l_leg, r_leg]:
            pm.connectAttr(root.out_main_output.offsetParentMatrix, mod.out_main_input.offsetParentMatrix)
            pm.connectAttr(root.out_mainGuide_output.offsetParentMatrix, mod.out_mainGuide_input.offsetParentMatrix)

        pm.connectAttr(root.out_main_output.offsetParentMatrix, spine.out_parent_input.offsetParentMatrix)
        pm.connectAttr(root.out_mainGuide_output.offsetParentMatrix, spine.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(spine.out_chest_output.offsetParentMatrix, l_arm_clavicle.out_parent_input.offsetParentMatrix)
        pm.connectAttr(spine.out_chestGuide_output.offsetParentMatrix, l_arm_clavicle.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(l_arm_clavicle.out_end_output.offsetParentMatrix, l_arm.out_parent_input.offsetParentMatrix)
        pm.connectAttr(l_arm_clavicle.out_endGuide_output.offsetParentMatrix, l_arm.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(spine.out_chest_output.offsetParentMatrix, r_arm_clavicle.out_parent_input.offsetParentMatrix)
        pm.connectAttr(spine.out_chestGuide_output.offsetParentMatrix, r_arm_clavicle.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(r_arm_clavicle.out_end_output.offsetParentMatrix, r_arm.out_parent_input.offsetParentMatrix)
        pm.connectAttr(r_arm_clavicle.out_endGuide_output.offsetParentMatrix, r_arm.out_parentGuide_input.offsetParentMatrix)



        pm.connectAttr(spine.out_hip_output.offsetParentMatrix, l_leg_start.out_parent_input.offsetParentMatrix)
        pm.connectAttr(spine.out_hipGuide_output.offsetParentMatrix, l_leg_start.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(l_leg_start.out_end_output.offsetParentMatrix, l_leg.out_parent_input.offsetParentMatrix)
        pm.connectAttr(l_leg_start.out_endGuide_output.offsetParentMatrix, l_leg.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(spine.out_hip_output.offsetParentMatrix, r_leg_start.out_parent_input.offsetParentMatrix)
        pm.connectAttr(spine.out_hipGuide_output.offsetParentMatrix, r_leg_start.out_parentGuide_input.offsetParentMatrix)

        pm.connectAttr(r_leg_start.out_end_output.offsetParentMatrix, r_leg.out_parent_input.offsetParentMatrix)
        pm.connectAttr(r_leg_start.out_endGuide_output.offsetParentMatrix, r_leg.out_parentGuide_input.offsetParentMatrix)




"""spine = Spine(
    name="spine", 
    com_guide_pos=(0, 14, 0), 
    hip_guide_pos=(0, 12, 0), 
    mid_guide_pos=(0, 0, 0), 
    chest_guide_pos=(0, 24, 0),
    settings_guide_pos=(5, 16, 0)
)

l_arm_clavicle = Clavicle(
    parent_module="chest",
    limb_type="clavicle", 
    limb_side="L", 
    start_guide_pos=(2, 24, 1), 
    end_guide_pos=(3, 26, 0), 
    clavicle_ctrl_color=left_fk_color
)

l_arm = Limb(
    limb_type="arm", 
    limb_side="L",
    main_module="root",
    parent_module="clavicle",
    upper_guide_pos=(4, 25, 0), 
    hand_guide_pos=(14, 25, 0),
    settings_guide_pos=(5, 25, -4),
    elbowLock_guide_pos=(9, 25, -7),
    fk_color=left_fk_color, 
    ik_color=left_ik_color
)

r_arm_clavicle = Clavicle(
    parent_module="chest",
    limb_type="clavicle",
    limb_side="R",
    start_guide_pos=(-2, 24, 1),
    end_guide_pos=(-3, 26, 0),
    clavicle_ctrl_color=right_fk_color
)

r_arm = Limb(
    limb_type="arm",
    limb_side="R",
    main_module="root",
    parent_module="clavicle",
    upper_guide_pos=(-4, 25, 0),
    hand_guide_pos=(-14, 25, 0),
    settings_guide_pos=(-5, 25, -4),
    elbowLock_guide_pos=(-9, 25, -7),
    fk_color=right_fk_color,
    ik_color=right_ik_color
)

l_leg_clavicle = Clavicle(
    parent_module="hip",
    limb_type="leg_start",
    limb_side="L",
    start_guide_pos=(2, 12, 0),
    end_guide_pos=(3, 10, 0),
    clavicle_ctrl_color=left_fk_color
)

l_leg = Leg(
    limb_type="leg", 
    limb_side="L",
    main_module="root",
    parent_module="leg_start",
    upper_guide_pos=(4, 10, 0),
    upper_guide_rot=(180, 0, 0),
    lower_guide_pos=(0, 1, 0),
    ankle_guide_pos=(0, 1, 0),
    foot_guide_pos=(4, 0, 0),
    foot_left_bank_guide_pos=(1, 0, 0),
    foot_right_bank_guide_pos=(-1, 0, 0),
    foot_heel_guide_pos=(0, 0, -1),
    foot_end_guide_pos=(0, 0, 5),
    foot_ball_guide_pos=(0, 0, 3),
    settings_guide_pos=(5, 13, -2),
    kneeLock_guide_pos=(4, 5, 8),
    fk_color=left_fk_color,
    ik_color=left_ik_color
)

r_leg_clavicle = Clavicle(
    parent_module="hip",
    limb_type="leg_start",
    limb_side="R",
    start_guide_pos=(-2, 12, 0),
    end_guide_pos=(-3, 10, 0),
    clavicle_ctrl_color=right_fk_color
)

r_leg = Leg(
    limb_type="leg", 
    limb_side="R",
    main_module="root",
    parent_module="leg_start",
    upper_guide_pos=(-4, 10, 0),
    upper_guide_rot=(180, 0, 0),
    lower_guide_pos=(0, 1, 0),
    ankle_guide_pos=(0, 1, 0),
    foot_guide_pos=(-4, 0, 0),
    foot_left_bank_guide_pos=(1, 0, 0),
    foot_right_bank_guide_pos=(-1, 0, 0),
    foot_heel_guide_pos=(0, 0, 1),
    foot_end_guide_pos=(0, 0, 5),
    foot_ball_guide_pos=(0, 0, 3),
    settings_guide_pos=(-5, 13, -2),
    kneeLock_guide_pos=(-4, 5, 8),
    fk_color=right_fk_color,
    ik_color=right_ik_color
)"""