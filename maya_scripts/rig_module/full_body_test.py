import json
import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from utilities import create_guide, colorize, create_groups, add_pins_to_ribbon, add_pins_to_ribbon_uv, create_groups_

from rig_module.base_limb import Limb, Clavicle
from rig_module.spine import Spine
from rig_module.leg import Leg
from rig_module import create_root_module

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
right_fk_color = [1, 0, 0]
left_ik_color = [0, 0.85, 0.83]
left_fk_color = [0, 0, 1]
right_ik_color = [1, 0.6, 0]

#create_root_module()

spine = Spine(
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
)