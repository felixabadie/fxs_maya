import json
import pymel.core as pm
from prox_node_setup.generated_nodes import *

def colorize(transform:pm.nodetypes.Transform, color=[1, 0, 0]):
    
    """
    Takes a pymel Transform and colors Maya-viewport-wireframes with 'color'.
    Parameter color can be of type list [r, g, b] or int (maya-color-index)
    Works on PolyMeshes, NURBS-Curves, Cameras.
    """

    if isinstance(transform, list):
        print("COLOUR LETS GOOOOOOOO!")
        transform = transform[0]

    is_rgb = isinstance(color, (tuple, list))
    color_attribute = "overrideColorRGB" if is_rgb else "overrideColor"
    for shape in transform.getShapes():
        shape.setAttr("overrideEnabled", 1)
        shape.setAttr("overrideRGBColors", is_rgb)
        shape.setAttr(color_attribute, color)

def create_groups(rig_module_name:str = "test"):
    
    """
    This function creates groups in rig module based on
    Jean Paul Tossings video tutorials
    """

    groups = {}
    mod = transform(name=f"{rig_module_name}_mod")

    sub_names = [
        "SETUP", "inputs", "guides", "controls", 
        "rigNodes", "joints", "geo", "helpers", "outputs"
    ]

    for name in sub_names:
        parent = mod.node if name in ["SETUP", "inputs", "guides", "controls", "rigNodes", "joints", "geo", "helpers", "outputs"] else groups["inputs"].node
        groups[name] = transform(name=f"{rig_module_name}_{name}", parent=parent)

    for name, grp in groups.items():

        if name in ["guides", "controls", "rigNodes", "joints", "geo", "helpers"]:
            attrs = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]
        
        else:
            attrs = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ", "visibility"]

        for attr in attrs:
            pm.setAttr(f"{grp.node}.{attr}", lock=True)
            pm.setAttr(f"{grp.node}.{attr}", keyable=False)
            pm.setAttr(f"{grp.node}.{attr}", channelBox=False)
     
    return groups

def create_groups_(rig_module_name:str):
    
    """
    This function creates groups in rig module based on
    Jean Paul Tossings video tutorials
    """

    groups = {}
    mod = pm.group(empty=True, name=f"{rig_module_name}_mod")

    sub_names = [
        "SETUP", "inputs", "parent_intput", "parentGuide_input", "guides", 
        "controls", "rigNodes", "joints", "geo", "helpers", "outputs"
    ]

    for name in sub_names:
        parent = mod if name in ["SETUP", "inputs", "guides", "controls", "rigNodes", "joints", "geo", "helpers", "outputs"] else groups["inputs"]

        groups[name] = pm.group(empty=True, name=f"{rig_module_name}_{name}", parent=parent)
        
    for grp in groups.values():
        for attr in ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ", "visibility"]:
            
            pm.setAttr(f"{grp}.{attr}", lock=True)
            pm.setAttr(f"{grp}.{attr}", keyable=False)
            pm.setAttr(f"{grp}.{attr}", channelBox=False)
              
    return groups


def create_guide(name:str, position:tuple=(0, 0, 0), color:list=[0, 0, 0]):
    
    """
    This function creates a spaceLocator as a guide at a desired location
    and with a desired color.
    """
    guide = transform(name=name)
    guide_shape = locator(name=f"{name}Shape", parent=guide.node)
    guide.translate.set(position)

    #guide = pm.spaceLocator(name=name)
    #guide.setTranslation(position, space="world")

    colorize(guide.node, color)

    return guide


def blend_target(targetMatrix, useMatrix=True, weight=1.0, scaleWeight=1.0, translateWeight=1.0, rotateWeight=1.0, shearWeight=1.0):
    target = {"targetMatrix": targetMatrix, "useMatrix": useMatrix, "weight": weight, "scaleWeight": scaleWeight, "translateWeight": translateWeight, "rotateWeight": rotateWeight, "shearWeight": shearWeight}
    return target


def parent_target(targetMatrix, offsetMatrix, enableWeight=True, weight=1.0):
    target = {"targetMatrix": targetMatrix, "offsetMatrix": offsetMatrix, "enableWeight": enableWeight, "weight": weight}
    return target


def remapValue_color(color_Position=0.0, color_Color=(0.0, 0.0, 0.0), color_Interp=0):
    color = {"color_Position": color_Position, "color_Color": color_Color, "color_Interp": color_Interp}
    return color
    

def remapValue_value(value_Position=0.0, value_FloatValue=0.0, value_Interp=0):
    value = {"value_Position": value_Position, "value_FloatValue": value_FloatValue ,"value_Interp": value_Interp}
    return value


def set_or_connect(value, node_attr, value_type=None):

    """
    This function decides if an input is to be set or connected
    basesd on the properties of the input (Might need a rework)
    """

    if isinstance(value, pm.Attribute):
        pm.connectAttr(value, node_attr, force=True)
        return

    if value is None:
        return
    
    if value_type is None:
        if isinstance(value, (list, tuple)):
            if len(value) == 3:
                value_type = "double3"
            elif len(value) == 4:
                value_type = "double4"
        elif isinstance(value, pm.datatypes.Matrix):
            value_type = "matrix"

    if value_type:
        node_attr.set(value, type=value_type)
    else:
        node_attr.set(value)


"""def add_pins_to_ribbon(name:str, ribbon, number_of_pins):
    param_length_u = ribbon.getShape().minMaxRangeU.get()

    pin_list = []

    for i in range(number_of_pins):
        u_pos = (i/float(number_of_pins-1)) * param_length_u[1]
        pin_list.append(pin_on_nurbs_surface(name, ribbon, u_pos=u_pos, name_suf=str(i)))

    return pin_list"""

def add_pins_to_ribbon(name:str, ribbon, number_of_pins):
    param_length_u = ribbon.getShape().minMaxRangeU.get()
    param_length_v = ribbon.getShape().minMaxRangeV.get()

    pin_list = []

    for i in range(number_of_pins):
        u_pos = (i/float(number_of_pins-1)) * param_length_u[1]
        v_pos = (i/float(number_of_pins-1)) * param_length_v[1]
        pin_list.append(pin_on_nurbs_surface(name, ribbon, u_pos=u_pos, v_pos=1, name_suf=str(i))) 

    return pin_list


def pin_on_nurbs_surface(name, nurbs_surface, u_pos=0.5, v_pos=0.5, name_suf="#"):
    # Adjusted from Chris Lesage (https://gist.github.com/chris-lesage/0dd01f1af56c00668f867393bb68c4d7)
    # And then taken from Julian Schmoll (https://github.com/julianschmoll/maya_rigging_tools/blob/main/maya_frog_rigging_tools/skin/uv_pins.py#L47)

    point_on_surface = pointOnSurfaceInfo(name=f"{name}_pin_{name_suf}_pos")
    pm.connectAttr(nurbs_surface.getShape().worldSpace[0], point_on_surface.inputSurface)

    param_length_u = nurbs_surface.getShape().minMaxRangeU.get()
    param_length_v = nurbs_surface.getShape().minMaxRangeV.get()

    pin_name = f"{name}_pin_{name_suf}"
    pin_locator = pm.spaceLocator(name=pin_name).getShape()
    pin_locator.addAttr('parameterU', at='double', keyable=True, dv=u_pos)
    pin_locator.addAttr('parameterV', at='double', keyable=True, dv=v_pos)

    pin_locator.parameterU.setMin(param_length_u[0])
    pin_locator.parameterV.setMin(param_length_v[0])
    pin_locator.parameterU.setMax(param_length_u[1])
    pin_locator.parameterV.setMax(param_length_v[1])
    pin_locator.parameterU.connect(point_on_surface.parameterU)
    pin_locator.parameterV.connect(point_on_surface.parameterV)

    mtx = fourByFourMatrix(name=f"{pin_name}_mtx")
    out_matrix = decomposeMatrix(name=f"{pin_name}_dcmp")
    pm.connectAttr(mtx.output, out_matrix.inputMatrix)
    pm.connectAttr(out_matrix.outputTranslate, pin_locator.getTransform().translate)
    pm.connectAttr(out_matrix.outputRotate, pin_locator.getTransform().rotate)

    point_on_surface.normalizedTangentUX.connect(mtx.in00)
    point_on_surface.normalizedTangentUY.connect(mtx.in01)
    point_on_surface.normalizedTangentUZ.connect(mtx.in02)
    mtx.in03.set(0)

    point_on_surface.normalizedNormalX.connect(mtx.in10)
    point_on_surface.normalizedNormalY.connect(mtx.in11)
    point_on_surface.normalizedNormalZ.connect(mtx.in12)
    mtx.in13.set(0)

    point_on_surface.normalizedTangentVX.connect(mtx.in20)
    point_on_surface.normalizedTangentVY.connect(mtx.in21)
    point_on_surface.normalizedTangentVZ.connect(mtx.in22)
    mtx.in23.set(0)

    point_on_surface.positionX.connect(mtx.in30)
    point_on_surface.positionY.connect(mtx.in31)
    point_on_surface.positionZ.connect(mtx.in32)
    mtx.in33.set(1)

    return pm.PyNode(pin_name)



def add_pins_to_ribbon_uv(name:str, ribbon, number_of_pins):

    pin_list = []

    uv_pin = uvPin(name=f"{name}_uvPin")
    pm.connectAttr(ribbon.getShape().worldSpace[0], uv_pin.originalGeometry)
    pm.connectAttr(ribbon.getShape().worldSpace[0], uv_pin.deformedGeometry)


    for i in range(number_of_pins):

        u_pos = (i/float(number_of_pins-1))
        v_pos = 0.5
        name_suf=str(i)
        pin_name = f"{name}_pin_{name_suf}"
        pin_locator = pm.spaceLocator(name=pin_name)
        pin_locatorShape = pin_locator.getShape()
        pin_locatorShape.addAttr('parameterU', at='double', keyable=True, dv=u_pos)
        pin_locatorShape.addAttr('parameterV', at='double', keyable=True, dv=v_pos)

        pin_locatorShape.parameterU.set(u_pos)
        pin_locatorShape.parameterV.set(v_pos)
        
        pm.connectAttr(pin_locatorShape.parameterU, uv_pin.coordinate[i].coordinateU)
        pm.connectAttr(pin_locatorShape.parameterV, uv_pin.coordinate[i].coordinateV)

        pm.connectAttr(uv_pin.outputMatrix[i], pin_locator.offsetParentMatrix)
    
        pin_list.append(pm.PyNode(pin_name))

    return pin_list