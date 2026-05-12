import pymel.core as pm

"""
utility script to add end joints to fingers for better deformation. Can be added to mgear build scripts
"""

fingers_thumbs = [
    jnt for jnt in pm.ls(type="joint")
    if not jnt.getChildren()
    and ("finger" in jnt.name() or "thumb" in jnt.name())
]

pm.select(cl=True)

new_joints = []
for joint in fingers_thumbs:
    pm.select(joint)
    end_joint = pm.joint()
    end_joint.rename(f"{joint.name()[:-4]}_end_helper")
    end_joint.radius.set(joint.radius.get())
    end_joint.tx.set(joint.tx.get())
    new_joints.append(end_joint)

pm.select(new_joints)
pm.sets("rig_deformers_grp", add=True)