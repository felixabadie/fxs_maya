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





# Example: Embedding classes in a dictionary and executing them later

class Greeter:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        pass

    def greet(self):
        return f"Hello, {self.name}!"

class Adder:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def compute(self):
        return self.a + self.b

# Create instances of the classes
greeter_instance = Greeter("Alice")
adder_instance = Adder(5, 7)

# Store them in a dictionary
actions = {
    "say_hello": greeter_instance,
    "add_numbers": adder_instance
}

# Later: Access and execute the correct method
try:
    # Example 1: Call greet() from Greeter
    result1 = actions["say_hello"].greet()
    print(result1)  # Output: Hello, Alice!

    # Example 2: Call compute() from Adder
    result2 = actions["add_numbers"].compute()
    print(result2)  # Output: 12

except KeyError as e:
    print(f"Error: No such action '{e.args[0]}' in dictionary.")
except AttributeError as e:
    print(f"Error: Method not found - {e}")
