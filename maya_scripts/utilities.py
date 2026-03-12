import json
import logging
import pymel.core as pm
from pathlib import Path
from maya_scripts.prox_node_setup.generated_nodes import *

LOGGER = logging.getLogger("Rigging Utils")

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]

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


def create_ik_fk_blend(module_name, blend_name, fk_source, ik_source, blend_attr):
        blend = blendMatrix(name=f"{module_name}_{blend_name}")
        pm.connectAttr(fk_source, blend.inputMatrix)
        pm.connectAttr(ik_source, blend.target[0].targetMatrix)
        pm.connectAttr(blend_attr, blend.target[0].weight)
        return blend


def setup_visibility_controls(settings_ctrl, groups):
        vis_mapping = {
            "showGuides": "guides",
            "showCtrl": "controls",
            "showRigNodes": "rigNodes",
            "showJoints": "joints",
            "showProxyGeo": "geo",
            "showHelpers": "helpers"
        }
        for attr_name, group_name in vis_mapping.items():
            settings_ctrl.node.addAttr(attr=f"{attr_name}", attributeType="bool", defaultValue=1, hidden=False, keyable=True)
            pm.connectAttr(f"{settings_ctrl.node}.{attr_name}", groups[group_name].node.visibility)
            settings_ctrl.node.setAttr(attr_name, keyable=False, channelBox=True)


def get_local_ribbon_pin_position(pos_name):
        positions = {"top": (0, 0, 0.5), "middle": (0, 0, 0), "down": (0, 0, -0.5)}
        return positions.get(pos_name, (0, 0, 0))


def setup_ribbon_system(module_name, groups, upper_WM, upper_midpoint_ctrl, lower_start_ribbon_ctrl, lower_ribbon_ctrl, lower_end_ribbon_ctrl, lower_midpoint_ctrl, end_WM):
        pin_grp = transform(name=f"{module_name}_nurbsPin_grp")
        sections = {
            "upper": {"parent_matrix": upper_WM},
            "upper_midpoint": {"parent_matrix": upper_midpoint_ctrl},
            "lower_start": {"parent_matrix": lower_start_ribbon_ctrl},
            "lower": {"parent_matrix": lower_ribbon_ctrl},
            "lower_end": {"parent_matrix": lower_end_ribbon_ctrl},
            "lower_midpoint": {"parent_matrix": lower_midpoint_ctrl},
            "hand": {"parent_matrix": end_WM}
        }
        curve_points = {'top': [], 'middle': [], 'down': []}

        for section_name, config in sections.items():
            for height in ["top", "middle", "down"]:
                pin = create_guide(name=f"{module_name}_{section_name}_{height}_ribbon_pin", color=pin_color, position=get_local_ribbon_pin_position(height))

                tfm = translationFromMatrix(name=f"{module_name}_{section_name}_{height}_ribbon_pin_tFM")
                pm.connectAttr(pin.worldMatrix[0], tfm.input_)
                pm.connectAttr(config["parent_matrix"], pin.offsetParentMatrix)
                pm.parent(pin.node, pin_grp.node)
                pm.parent(pin_grp.node, groups["rigNodes"].node)
                pin_grp.visibility.set(0)
                curve_points[height].append(tfm)

        return create_bezier_curves(curve_points)


def create_bezier_curves(module_name, curve_points:dict):

    ribbon_curves = {}

    for crv, points in curve_points.items():
        input_nodes = []
        positions = []
        for index, p in enumerate(points):
            if index == 0 or index == len(points) - 1:
                input_nodes.append(p)
                input_nodes.append(p)
                positions.append(pm.getAttr(p.node.output))
                positions.append(pm.getAttr(p.node.output))
            else:
                input_nodes.append(p)
                positions.append(pm.getAttr(p.node.output))
        
        temp_bezier_curve = pm.curve(point=positions, bezier=True, name=f"temp_{crv}_curve")
        ribbon_curves[f"{crv}_curve"] = transform(name=f"{module_name}_{crv}_bezier_curve")
        shapes = pm.listRelatives(temp_bezier_curve, shapes=True, fullPath=True)
        pm.parent(shapes, ribbon_curves[f"{crv}_curve"].node, add=True, shape=True)
        pm.delete(temp_bezier_curve)

        for index, node in enumerate(input_nodes):
            pm.connectAttr(node.output, ribbon_curves[f"{crv}_curve"].node.controlPoints[index])          

    return ribbon_curves


def rebuild_nurbsPlane(module_name, groups, input_plane, spans_U:int, spans_V:int, degree_U, degree_V):
        rebSurface = rebuildSurface(name=f"{module_name}_{input_plane.getName()}_rebuildSurface")
        pm.connectAttr(input_plane.worldSpace[0], rebSurface.inputSurface)
        rebSurface.spansU.set(spans_U)
        rebSurface.spansV.set(spans_V)
        rebSurface.degreeU.set(degree_U)
        rebSurface.degreeV.set(degree_V)

        pm.rename(input_plane, newname=f"{module_name}_oldRibbon")
        pm.parent(input_plane, groups["rigNodes"].node)

        input_plane.visibility.set(0)
        newPlane = pm.nurbsPlane(name=f"{module_name}_newRibbon")[0]
        newPlaneShape = newPlane.getShape()
        pm.connectAttr(rebSurface.outputSurface, newPlaneShape.create, force=True)

        newPlane.overrideEnabled.set(1)
        newPlane.overrideDisplayType.set(1)

        return newPlane, newPlaneShape


def add_pin_joints(module_name, name, ribbon, number_of_pins, scale_parent):
            jnt_list = []

            pin_list = add_pins_to_ribbon_uv(f"{module_name}", ribbon, number_of_pins)
            scaleFM = scaleFromMatrix(name=f"{module_name}_scaleFM")
            pm.connectAttr(scale_parent, scaleFM.input_)
            for index, pin in enumerate(pin_list):
                jnt = joint(name=f"{name}_{index}_bnd_jnt")
                pm.connectAttr(scaleFM.output, jnt.scale)
                pm.makeIdentity(jnt.node, apply=True, t=0, r=1, s=0, n=0, pn=True)
                pm.xform(jnt.node, translation=(0, 0, 0))
                pm.connectAttr(pin.worldMatrix[0], jnt.offsetParentMatrix)
                jnt_list.append(jnt)

            return pin_list, jnt_list


def extract_matrix_axes(module_name, name, input):
        """Creates 3 rowFromMatrix nodes with the corresponding rows"""
        axes = {}

        for i, axis_name in enumerate(["X", "Y", "Z"]):
            axis = rowFromMatrix(name=f"{module_name}_{name}_axis{axis_name}")
            pm.connectAttr(input, axis.matrix)
            axis.input_.set(i)
            axes[axis_name] = axis
    
        return axes


def create_fourByFourMatrix(module_name, name, inputs = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]):
        """Creates fourByFourMatrix node and connects the inputs
        
        in00, in01, in02, in03 \n
        in10, in11, in12, in13 \n
        in20, in21, in22, in23 \n
        in30, in31, in32, in33
        """
        fbfM = fourByFourMatrix(name=f"{module_name}_{name}")
        for i, input in enumerate(inputs):
            if input is not None:
                for j, plug in enumerate(input):
                    if plug is not None:
                        if isinstance(plug, float | int):
                            pm.setAttr(f"{fbfM.node}.in{i}{j}", plug)
                        else:
                            pm.connectAttr(plug, f"{fbfM.node}.in{i}{j}")
        return fbfM


def remove_main_scale(module_name, name, world_matrix, main_input):
        """Creates am multMatrix node and multiplies its first input 
        with the worldInverseMatrix of the mainInput to remove its scale"""
        no_main_scale = multMatrix(name=f"{module_name}_{name}")
        pm.connectAttr(world_matrix, no_main_scale.matrixIn[0])
        pm.connectAttr(main_input, no_main_scale.matrixIn[1])
        return no_main_scale
        

def create_pom(module_name, name:str, source_matrix, parentGuide_input):
    """Creates a multMatrix node as a Parent ofset matrix."""
    pom = multMatrix(name=f"{module_name}_{name}")
    pm.connectAttr(source_matrix, pom.matrixIn[0])
    pm.connectAttr(parentGuide_input, pom.matrixIn[1])
    return pom


def hierarchy_prep(module_name, name, guide, parent, parentGuide):
        outputs = {}
        outputs["pom"] = create_pom(module_name=module_name, name=name, source_matrix=guide, parentGuide_input=parentGuide)
        outputs["wm"] = multMatrix(name=f"{module_name}_{name}_WM")
        outputs["pom"].matrixSum >> outputs["wm"].matrixIn[0]
        pm.connectAttr(parent, outputs["wm"].matrixIn[1])
        return outputs


def lock_ctrl_attrs(ctrl, attrs_to_lock):
    for attr in attrs_to_lock:
        pm.setAttr(f"{ctrl.node}.{attr}", lock=True)
        pm.setAttr(f"{ctrl.node}.{attr}", keyable=False)
        pm.setAttr(f"{ctrl.node}.{attr}", channelBox=False)


def create_ik_solver_setup(module_name, name, upper_length, lower_length, total_length, total_length_squared, float_value_2):
        """Creates all necessary nodes for an IK-solver using the law of cosines"""
        nodes = {}
        
        nodes["upper_length_squared"] = multiply(name=f"{module_name}_{name}_upper_length_squared")
        pm.connectAttr(upper_length, nodes["upper_length_squared"].input_[0])
        pm.connectAttr(upper_length, nodes["upper_length_squared"].input_[1])

        nodes["lower_length_squared"] = multiply(name=f"{module_name}_{name}_lower_length_squared")
        pm.connectAttr(lower_length, nodes["lower_length_squared"].input_[0])
        pm.connectAttr(lower_length, nodes["lower_length_squared"].input_[1])

        nodes["upper_numplus"] = sum_(name=f"{module_name}_upper_{name}_numplus")
        pm.connectAttr(nodes["upper_length_squared"].output, nodes["upper_numplus"].input_[0])
        pm.connectAttr(total_length_squared, nodes["upper_numplus"].input_[1])

        nodes["upper_numenator"] = subtract(name=f"{module_name}_upper_{name}_numenator")
        pm.connectAttr(nodes["upper_numplus"].output, nodes["upper_numenator"].input1)
        pm.connectAttr(nodes["lower_length_squared"].output, nodes["upper_numenator"].input2)

        nodes["upper_denominator"] = multiply(name=f"{module_name}_upper_{name}_denominator")
        pm.connectAttr(float_value_2.outFloat, nodes["upper_denominator"].input_[0])
        #nodes["upper_denominator"].input_[0].set(2)
        pm.connectAttr(upper_length, nodes["upper_denominator"].input_[1])
        pm.connectAttr(total_length, nodes["upper_denominator"].input_[2])

        nodes["upper_cosValue"] = divide(name=f"{module_name}_upper_{name}_cosValue")
        pm.connectAttr(nodes["upper_numenator"].output, nodes["upper_cosValue"].input1)
        pm.connectAttr(nodes["upper_denominator"].output, nodes["upper_cosValue"].input2)

        nodes["upper_cosValueSquared"] = multiply(name=f"{module_name}_upper_{name}_cosValueSquared")
        pm.connectAttr(nodes["upper_cosValue"].output, nodes["upper_cosValueSquared"].input_[0])
        pm.connectAttr(nodes["upper_cosValue"].output, nodes["upper_cosValueSquared"].input_[1])

        nodes["lower_numplus"] = sum_(name=f"{module_name}_lower_{name}_numplus")
        pm.connectAttr(nodes["upper_length_squared"].output, nodes["lower_numplus"].input_[0])
        pm.connectAttr(nodes["lower_length_squared"].output, nodes["lower_numplus"].input_[1])

        nodes["lower_numenator"] = subtract(name=f"{module_name}_lower_{name}_numenator")
        pm.connectAttr(nodes["lower_numplus"].output, nodes["lower_numenator"].input1)
        pm.connectAttr(total_length_squared, nodes["lower_numenator"].input2)

        nodes["lower_denominator"] = multiply(name=f"{module_name}_lower_{name}_denominator")
        pm.connectAttr(float_value_2.outFloat, nodes["lower_denominator"].input_[0])
        #nodes["lower_denominator"].input_[0].set(2)
        pm.connectAttr(upper_length, nodes["lower_denominator"].input_[1])
        pm.connectAttr(lower_length, nodes["lower_denominator"].input_[2])

        nodes["lower_cosValue"] = divide(name=f"{module_name}_lower_{name}_cosValue")
        pm.connectAttr(nodes["lower_numenator"].output, nodes["lower_cosValue"].input1)
        pm.connectAttr(nodes["lower_denominator"].output, nodes["lower_cosValue"].input2)

        nodes["lower_cosValueSquared"] = multiply(name=f"{module_name}_lower_{name}_cosValueSquared")
        pm.connectAttr(nodes["lower_cosValue"].output, nodes["lower_cosValueSquared"].input_[0])
        pm.connectAttr(nodes["lower_cosValue"].output, nodes["lower_cosValueSquared"].input_[1])

        return nodes


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


def align_center(obj1, obj2, obj3):
    matrix_1 = pm.xform(obj1, query=True, worldSpace=True, matrix=True)
    matrix_2 = pm.xform(obj2, query=True, worldSpace=True, matrix=True)
    center_matrix = []

    for index, pnt1 in enumerate(matrix_1):
        pnt2 = matrix_2[index]
        diff = (abs(pnt1) + abs(pnt2)) / 2
        pnt3 = min(pnt1, pnt2) + diff
        center_matrix.append(pnt3)

    pm.xform(obj3, worldSpace=True, matrix=center_matrix)


def get_center(translations):
    x_sum, y_sum, z_sum = 0, 0, 0
    num_translations = len(translations)

    for x, y, z in translations:
        x_sum += x
        y_sum += y
        z_sum += z

    center_x = x_sum / num_translations
    center_y = y_sum / num_translations
    center_z = z_sum / num_translations

    return center_x, center_y, center_z


def match_transforms(source_obj, target_obj, **kwargs):
    LOGGER.info(f"Matching transforms of {source_obj} to {target_obj}")
    constraint = pm.parentConstraint(source_obj, target_obj, **kwargs)
    pm.delete(constraint)


class TextFieldHelper:
    def __init__(self, label, buttonLabel="Set", text="Not set"):
        self.control = pm.textFieldButtonGrp(
            label=label, buttonLabel=buttonLabel, text=text,
            bc=self.set_text
        ) # PEP8
                
    def set_text(self):
        sel = pm.selected()
        if not sel:
            pm.warning("Warning")
            return
        self.control.setText(sel[0].name())
        self.obj = sel[0]

class CompoundFieldSlot:
    def __init__(self, label):
        with pm.columnLayout(adj=True):
            self.field = pm.floatFieldGrp(
                label=label,
                extraLabel="X-Y-Z",
                numberOfFields=3,
            )

    def get_values(self):
        return (
            pm.floatFieldGrp(self.field, q=True, value1=True),
            pm.floatFieldGrp(self.field, q=True, value2=True),
            pm.floatFieldGrp(self.field, q=True, value3=True)
        )
    
    def __iter__(self):
        return iter(self.get_values())  # damit tuple(self.com_guide_pos) funktioniert


def getPosFromObj(obj_name):
    position = pm.xform(obj_name)
    return position


with pm.window(title="Test") as win:
    with pm.columnLayout(adj=True):
        pm.floatFieldGrp(
            numberOfFields=3,
            label="Position",
            extraLabel="X",   # nur EIN extraLabel möglich, leider
        )

win.show()