import os
import json
import utils
import logging
from enum import Enum
import pymel.core as pm
from utilities import colorize
from prox_node_setup.generated_nodes import *
#from maya import OpenMaya as om


LOGGER = logging.getLogger("Rig Control")

def create(ctrl_type, degree = 1, name="ctl", size=[1, 1, 1], normal=(0, 1, 0), color=[1, 1, 1]):

    """
    Docstring for create
    
    :param ctl_type: Name of Controller in JSON file
    :param degree: Cubic = 0, Linear = 1
    :param name: Name of controller
    :param size: Size of controller
    """

    root_path = utils.get_project_root()
    json_dir = os.path.join(root_path, "controls")
    json_path = os.path.join(json_dir, f"{ctrl_type}.json")
    if json_path:
        LOGGER.info(f"Creating {ctrl_type} control from json")
        return create_ctrl_from_json(json_path, degree, name, ctrl_size=size, ctrl_normal=normal, color=color)
    


def create_ctrl_from_json(file_path, degree, name, ctrl_size=[1, 1, 1], ctrl_normal=(0, 1, 0), color = [1, 1, 1]):
    with open(file_path, "r") as f:
        shape_data = json.load(f)

    shape_list = []
    ctrl = transform(name=name)

    for shape in shape_data:
        #new_curve = curve
        new_curve = pm.curve(degree=degree, point=shape["points"])
        pm.closeCurve(new_curve, ch=False, ps=False, rpo=True)
        shape_list.append(pm.rename(new_curve, shape["name"]))

    #ctrl = shape_list.pop(0)

    for shape in shape_list:
        shapes = pm.listRelatives(shape, shapes=True, fullPath=True)
        pm.parent(shapes, ctrl.node, add=True, shape=True)
        pm.delete(shape)

    pm.scale(ctrl.node, ctrl_size)


    #orienting contr
    if ctrl_normal != (0, 1, 0):
        temp_loc = pm.spaceLocator()
        pm.move(temp_loc, ctrl_normal[0], ctrl_normal[1], ctrl_normal[2])
        aim_const = pm.aimConstraint(temp_loc, ctrl.node, 
                                    aimVector=(0, 1, 0), 
                                    upVector=(0, 0, 1))
        pm.delete(aim_const, temp_loc)

    pm.makeIdentity(ctrl.node, apply=True, t=1, r=1, s=1, n=0)
    pm.xform(ctrl.node, zeroTransformPivots=True)

    #pm.rename(ctrl, name, ignoreShape=True),,

    colorize(ctrl.node, color=color)
    return ctrl


def create_connection_curve(name, degree=1, points=[(0, 0, 0), (1, 0, 0)], color = [1, 1, 1]):
    
    temp_curve = pm.curve(degree=degree, point=points)
    ctrl = transform(name=name)
    shapes = pm.listRelatives(temp_curve, shapes=True, fullPath=True)
    pm.parent(shapes, ctrl.node, add=True, shape=True)
    pm.delete(temp_curve)

    colorize(ctrl.node, color=color)

    return ctrl


def get_bezier_points(joints):
    point_list = []

    for joint in joints:
        point_list.append(
            tuple(joint.node.getTranslation(space="world"))
        )
    
    point_list.insert(0, point_list[0])
    point_list.insert(3, point_list[3])
    point_list.insert(2, utils.get_center([point_list[0], point_list[2]]))
    point_list.insert(4, utils.get_center([point_list[3], point_list[4]]))

    return point_list

def create_bezier_ribbon(name:str, annchor_joints:list, offset_up=(0, 0, 1), offset_low=(0, 0, 1)):

    bezier_points = get_bezier_points(annchor_joints)

    pins = {
        "start_pin": {"parent": annchor_joints[0], "curve_points": [0 , 1]},
        "end_pin": {"parent": annchor_joints[-1], "curve_points": [5, 6]},
        "mid_pin": {"match transforms": annchor_joints[1], "curve_points": [3]},
        "start_mid": {"match transforms": annchor_joints[1], "pos": 2, "curve_points": [2]},
        "end_mid": {"match transforms": annchor_joints[1], "pos": 4, "curve_points": [4]}
    }

    
    temp_bezier_curve = pm.curve(point=bezier_points, bezier=True, name=f"{name}_temp_bezier")
    temp_up_curve = pm.curve(point=bezier_points, bezier=True, name=f"{name}_temp_up_bezier")
    temp_low_curve = pm.curve(point=bezier_points, bezier=True, name=f"{name}_temp_low_bezier")

    for pin, pin_data in pins.items():
        pin_node = locator(name=f"{name}_{pin}")

        
def create_bezier_curve(name:str, input_points:list, degree=3) -> transform:

    temp_bezier_curve = pm.curve(point=input_points, name=f"{name}_temp_curve")
    transform_grp = transform(name=f"{name}")
    pymel_shapes = pm.listRelatives(temp_bezier_curve, shapes=True, fullPath=True)
    pm.parent(pymel_shapes, transform_grp.node, add=True, shape=True)
    pm.delete(temp_bezier_curve)

    return transform_grp





def create_circle_ctrl(name, ctrl_size, normal=(1, 0, 0), color = [1, 1, 1]):
    ctrl_node, make_node = pm.circle(name=name, normal=normal)
    ctrl = transform(name=name)
    
    shapes = pm.listRelatives(ctrl_node, shapes=True, fullPath=True)
    pm.parent(shapes, ctrl.node, add=True, shape=True)
    pm.delete(ctrl_node)
    
    pm.scale(ctrl.node, ctrl_size, ctrl_size, ctrl_size)
    pm.makeIdentity(ctrl.node, apply=True, t=1, r=1, s=1, n=0)
    pm.xform(ctrl.node, zeroTransformPivots=True)
    pm.rename(ctrl.node, name, ignoreShape=True)
    
    colorize(ctrl.node, color=color)

    return ctrl



def create_square(name, dimension=(1, 1), center=(0, 0, 0), normal=(0, 1, 0), color = [1, 1, 1]):
    
    t = transform(name=name)
    
    ctrl = makeNurbsSquare(name=f"{name}_makeNurbsSquare")
    ctrl.sideLength1.set(dimension[0])
    ctrl.sideLength2.set(dimension[1])

    ctrl.center.set(center)
    ctrl.normal.set(normal)

    curve1 = nurbsCurve(name=f"{name}_nurbsCurve1", parent=t.node)
    curve2 = nurbsCurve(name=f"{name}_nurbsCurve2", parent=t.node)
    curve3 = nurbsCurve(name=f"{name}_nurbsCurve3", parent=t.node)
    curve4 = nurbsCurve(name=f"{name}_nurbsCurve4", parent=t.node)

    pm.connectAttr(ctrl.outputCurve1, curve1.create)
    pm.connectAttr(ctrl.outputCurve2, curve2.create)
    pm.connectAttr(ctrl.outputCurve3, curve3.create)
    pm.connectAttr(ctrl.outputCurve4, curve4.create)

    colorize(t.node, color=color)

    return t



"""def write_json_from_dag(out_path):
    dag_iter = om.MItDag(om.MItDag.kDepthFirst, om.MFn.kCurve)
    output = []

    while not dag_iter.isDone():
        curve_iter = om.MItCurveCV(dag_iter.currentItem())
        curve = om.MFnDagNode(dag_iter.currentItem())
        dag_iter.next()
        node = {"name": curve.name(), "points": []}

        while not curve_iter.isDone():
            pos = curve_iter.position()
            curve_iter.next()
            node["points"].append([pos.x, pos.y, pos.z])

        output.append(node)

    with open(out_path, mode="w") as output_file:
        json.dump(output, output_file)"""