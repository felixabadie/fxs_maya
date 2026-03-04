import os
import sys
import json
import requests
import pymel.core as pm



tool_dir = r"D:\fa026_Bachelor\repository\pose_estimation\sourcecode"
site_packages_dir = r"D:\fa026_Bachelor\venv\Lib\site-packages"
scripts_dir = r"D:\fa026_Bachelor\maya_scripts"


sys.path.append(tool_dir)
sys.path.append(site_packages_dir)
sys.path.append(scripts_dir)

from prox_node_setup.generated_nodes import *
from pyi_test.nodeTest import __remapValue

"""loc = pm.spaceLocator(name="a")
loc1 = pm.spaceLocator(name="b")


blend = blendMatrix(name="blend")
remap = remapValue(name="remap")


pm.connectAttr(loc.worldMatrix[0], blend.target[3].targetMatrix)
pm.connectAttr(loc1.worldMatrix[0], blend.target[4].targetMatrix)

pm.connectAttr(loc.translateX, remap.value[0].value_Position)
pm.connectAttr(loc1.translateY, remap.value[6].value_FloatValue)

pm.connectAttr(loc1.scaleX, remap.color[0].color_Position)
pm.connectAttr(loc.rotate, remap.color[6].color_Color)

pm.connectAttr(remap.outColorB, loc1.scaleY)

multM = multMatrix(name="multM")

remap2 = remapValue(name="remap2")
__remap2 = __remapValue(name="__remap2")

tr = transform(name="tr")

tr.instObjGroups[0].objectGroups[0].objectGrpColor

for i in range(20):
    pm.connectAttr(loc1.translate, remap2.color[i].color_Color)
    pm.connectAttr(loc1.translate, __remap2.color[i].color_Color)
    
    pm.connectAttr(loc1.translateX, remap2.value[i].value_FloatValue)

    pm.connectAttr(loc1.worldMatrix[0], multM.matrixIn[i])
    pm.connectAttr(loc.translateX, tr.instObjGroups[i].objectGroups[i].objectGrpColor)"""

name = "finger"

metacarpal_IK_jnt = joint(name=f"{name}_metacarpal_IK_jnt")
prox_phalange_IK_jnt = joint(name=f"{name}_prox_phalange_IK_jnt")
middle_phalange_IK_jnt = joint(name=f"{name}_middle_phalange_IK_jnt")
distal_phalange_IK_jnt = joint(name=f"{name}_distal_phalange_IK_jnt")
finger_end_jnt = joint(name=f"{name}_finger_end_jnt")

joint_list = [finger_end_jnt, distal_phalange_IK_jnt, middle_phalange_IK_jnt, prox_phalange_IK_jnt, metacarpal_IK_jnt]

for i in range(len(joint_list)):
    try:
        pm.parent(joint_list[i].node, joint_list[i+1].node)
    except:
        pass

ik_solver, ik_effector = pm.ikHandle(
    startJoint=metacarpal_IK_jnt.node,
    endEffector=finger_end_jnt.node,
    solver="ikRPsolver",
    name="test_ik_solver"
)

