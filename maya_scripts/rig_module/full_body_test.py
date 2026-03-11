import json
import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from utilities import TextFieldHelper, CompoundFieldSlot

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

#create_root_module()

class BipedManager:
    def __init__(self):
        self.win_id = "fxs_biped_rigging_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Biped Rigging Manager") as win:
            with pm.columnLayout(adj=True):
                self.root_name = TextFieldHelper()
                self.spine_name = TextFieldHelper()
                self.clavicle_name = TextFieldHelper()
                self.leg_start_name = TextFieldHelper()
                self.arm_name = TextFieldHelper()
                self.leg_name = TextFieldHelper()
                self.spine_bind_jnts = pm.intFieldGrp(label="Amount spine bind joints: ", numberOfFields=1)
                self.arm_bind_jnts = pm.intFieldGrp(label="Amount arm bind joints: ", numberOfFields=1)
                self.leg_bind_jnts = pm.intFieldGrp(label="Amount leg bind joints: ", numberOfFields=1)

                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self):
        root_name = str(self.root_name)
        spine_name = str(self.spine_name)
        clavicle_base_name = str(self.clavicle_name)
        leg_start_base_name = str(self.leg_start_name)
        arm_base_name = str(self.arm_name)
        leg_base_name = str(self.leg_name)

        bind_jnts_dict = {}
        bind_jnts_keys = ["spine_bind_jnts", "arm_bind_jnts", "leg_bind_jnts"]

        for jnts, i in enumerate(self.spine_bind_jnts, self.arm_bind_jnts, self.leg_bind_jnts):
            if pm.intFieldGrp(jnts, query=True, value=True) > 0:
                bind_jnts_dict[bind_jnts_keys[i]] = pm.intFieldGrp(jnts, query=True, value=True)
            else:
                print("Not enough bind joints (using 5 instead)")
                bind_jnts_dict[bind_jnts_keys[i]] = 5

        try:
            spine_bind_jnts = int(self.spine_bind_jnts)
            arm_bind_jnts   = int(self.arm_bind_jnts)
            leg_bind_jnts   = int(self.leg_bind_jnts)
        except ValueError:
            pm.warning("Bind joints must be a number")
            return





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