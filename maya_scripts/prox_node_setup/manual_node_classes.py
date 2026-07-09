import pymel.core as pm
import json

from prox_node_setup.generated_nodes import *



identityMatrix = pm.datatypes.Matrix()

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


class maya_nodes:


    def aimMatrix(name, inputMatrix, primary_targetMatrix, secondary_targetMatrix, postSpaceMatrix=None, preSpaceMatrix=None, primary_aim_mode = 1,  secondary_aim_mode = 0, 
                        primary_inputAxis=(1, 0, 0), primary_targetVector=(0, 0, 0), secondary_inputAxis=(0, 1, 0), secondary_targetVector=(0, 0, 0), 
                        enable=True, envelope=1):
        
        """
        This function either takes a name for an aimMatrix node and creates the node or an already existing aimMatrix node 
        and connects the input and target matrices. All other inputs are seperated into node attributes as incoming 
        connections and values that are directly set. The function returns a pymel node.

        secondary aimMode: 0 = None; 1 = Aim, 2 = Align

        Transform an Input matrix so that the specified Primary Axis point to the specified primaryTarget. 
        The secondary Target will be use optionaly to aim the secondary Axis in that general direction (up vector). 
        """

        from pymel.core.nodetypes import AimMatrix

        if pm.objExists(name):
            aimMatrix_node = pm.PyNode(name)
            if pm.nodeType(aimMatrix_node) != "aimMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a aimMatrix node")
            
        else:
            aimMatrix_node:AimMatrix = pm.createNode("aimMatrix", name=name)
        
        if postSpaceMatrix is None:
            postSpaceMatrix = pm.datatypes.Matrix()
        if preSpaceMatrix is None:
            preSpaceMatrix = pm.datatypes.Matrix()

        set_or_connect(inputMatrix, aimMatrix_node.inputMatrix)
        set_or_connect(postSpaceMatrix, aimMatrix_node.postSpaceMatrix)
        set_or_connect(preSpaceMatrix, aimMatrix_node.preSpaceMatrix)
        set_or_connect(primary_targetMatrix, aimMatrix_node.primaryTargetMatrix)
        set_or_connect(primary_inputAxis, aimMatrix_node.primaryInputAxis)
        set_or_connect(primary_aim_mode, aimMatrix_node.primaryMode)
        set_or_connect(primary_targetVector, aimMatrix_node.primary_targetVector)
        set_or_connect(secondary_targetMatrix, aimMatrix_node.secondary_targetMatrix)
        set_or_connect(secondary_inputAxis, aimMatrix_node.secondary_inputAxis)
        set_or_connect(secondary_aim_mode, aimMatrix_node.secondaryMode)
        set_or_connect(secondary_targetVector, aimMatrix_node.secondaryTargetVector)
        set_or_connect(enable, aimMatrix_node.enable)
        set_or_connect(envelope, aimMatrix_node.envelope)
        return aimMatrix_node


    def blendMatrix(name, inputMatrix, postSpaceMatrix=None, preSpaceMatrix=None, targets=None, enable=True, envelope=1):
        """
        targetMatrix, useMatrix:bool=True, weight:float=1, scaleWeight:float=1, translateWeight:float=1, rotateWeight:float=1, shearWeight:float=1

        This function either takes a name for a blendMatrix node and creates it or an already existing blendMatrix node and connects the 
        input and targetMatrix. All other attributes are weights that determine how the result is blended 
        (weight, scaleWeight, translateWeight, rotateWeight and shearWeight). The function returns a pymel node.

        targets is a list of dictionaries, that gets initiated using the blend_target()-function. This ensures autocompletion and supports any length of input
        with default values

        Example for targets:
        targets = [
            blend_target(targetMatrix=hand_guide.worldMatrix[0], useMatrix=True, weight=0.5, rotateWeight=0, translateWeight=1, scaleWeight=0, shearWeight=0)
            blend_target(blend_target(targetMatrix=arm_L_upper_WM_test.matrixSum))
        ]
        BlendNode take a base matrix (InpuMatrix) and blend it successively with each target. Blend is happening in a stack manner. 
        The results of the previous blend get blended with next target and so on.
        """

        from pymel.core.nodetypes import BlendMatrix

        if pm.objExists(name):
            blendMatrix_node = pm.PyNode(name)
            if pm.nodeType(blendMatrix_node) != "blendMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a blendMatrix node")
            
        else:
            blendMatrix_node:BlendMatrix = pm.createNode("blendMatrix", name=name)
        
        if targets is None:
            targets = []

        targets = [t if t is not None else {} for t in targets]

        set_or_connect(inputMatrix, blendMatrix_node.inputMatrix)
        set_or_connect(enable, blendMatrix_node.enable)
        set_or_connect(envelope, blendMatrix_node.envelope)
        set_or_connect(postSpaceMatrix, blendMatrix_node.postSpaceMatrix)
        set_or_connect(preSpaceMatrix, blendMatrix_node.preSpaceMatrix)

        for i, target in enumerate(targets):
            if not isinstance(target, dict):
                pm.warning(f"Target {i} is not a dictionary.")
                continue
            
            set_or_connect(target.get["targetMatrix"], blendMatrix_node.target[i].targetMatrix)
            set_or_connect(target.get("useMatrix", True), blendMatrix_node.target[i].useMatrix)
            set_or_connect(target.get("weight", 1.0), blendMatrix_node.target[i].weight)
            set_or_connect(target.get("scaleWeight", 1.0), blendMatrix_node.target[i].scaleWeight)
            set_or_connect(target.get("translateWeight", 1.0), blendMatrix_node.target[i].translateWeight)
            set_or_connect(target.get("rotateWeight", 1.0), blendMatrix_node.target[i].rotateWeight)
            set_or_connect(target.get("shearWeight", 1.0), blendMatrix_node.target[i].shearWeight)
    
        return blendMatrix_node


    def multMatrix(name, inputs:list=None):
        
        """
        This function either takes a name for a multMatrix node and creates it or an already existing multMatrix node 
        and connects all Inputs (List of inputs). The function returns a pymel node.

        Multiply a list of matrices together. 
        """

        from pymel.core.nodetypes import MultMatrix

        if pm.objExists(name):
            multMatrix_node = pm.PyNode(name)
            if pm.nodeType(multMatrix_node) != "multMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a multMatrix node")
            
        else:
            multMatrix_node:MultMatrix = pm.createNode("multMatrix", name=name)

        if inputs is None:
            inputs=[]

        for i, input_attr in enumerate(inputs):
            if input_attr is None:
                continue

            pm.connectAttr(input_attr, f"{multMatrix_node}.matrixIn[{i}]", force=True)

        return multMatrix_node


    def inverseMatrix(name, matrix):
        
        """
        This function creates an inverseMatrix Node and connects
        matrix to the nodes inputMatrix plug. The function outputs a
        pymel node.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            inverseMatrix_node = pm.PyNode(name)
            if pm.nodeType(inverseMatrix_node) != "inverseMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a inverseMatrix node")
            
        else:
            inverseMatrix_node = pm.createNode("inverseMatrix", name=name)

        pm.connectAttr(matrix, inverseMatrix_node.inputMatrix)
        return inverseMatrix_node


    def rowFromMatrix(name, matrix, row):
        
        """
        This function either takes a name for a rowFromMatrix node and creates it or 
        an already existing rowFromMatrix node and sets its inputs.
        The function outputs a pymel node.

        Extract the row at the input index from of the given matrix
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            rowFromMatrix_node = pm.PyNode(name)
            if pm.nodeType(rowFromMatrix_node) != "rowFromMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a rowFromMatrix node")
            
        else:
            rowFromMatrix_node = pm.createNode("rowFromMatrix", name=name)
        
        pm.connectAttr(matrix, rowFromMatrix_node.matrix)
        set_or_connect(row, rowFromMatrix_node.input)
        return rowFromMatrix_node


    def parentMatrix(name, inputMatrix, enable=True, envelope=1.0, postSpaceMatrix=None, preSpaceMatrix=None, targets=None):
        """
        targetMatrix, offsetMatrix, enableWeight=True, weight=1.0

        This function either takes a name for a parentMatrix node and creates it or 
        an already existing parentMatrix node. The target compartment needs to be
        structured the following way:

        targets = [
            parent_target(targetMatrix=PLACEHOLDER, offsetmatrix=PLACEHOLDER...)
            parent_target(...)
        ]

        targets is a list of dictionaries, that gets initiated using the parent_target()-function. 
        This ensures autocompletion and supports any length of input with default values.
        This function returns a pymel node

        Parent Matrix takes an input matrix and blends in the effect other parent targets. 
        It normalizes the effect of all the targets.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            parentMatrix_node = pm.PyNode(name)
            if pm.nodeType(parentMatrix_node) != "parentMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a parentMatrix node")
            
        else:
            parentMatrix_node = pm.createNode("parentMatrix", name=name)
        
        if targets is None:
            targets = []

        targets = [t if t is not None else {} for t in targets]

        set_or_connect(inputMatrix, parentMatrix_node.inputMatrix)
        set_or_connect(enable, parentMatrix_node.enable)
        set_or_connect(envelope, parentMatrix_node.envelope)
        set_or_connect(postSpaceMatrix, parentMatrix_node.postSpaceMatrix)
        set_or_connect(preSpaceMatrix, parentMatrix_node.preSpaceMatrix)

        for i, target in enumerate(targets):
            if not isinstance(target, dict):
                pm.warning(f"Target {i} is not a dictionary.")
                continue

            set_or_connect(target.get("enableTarget"), parentMatrix_node.target[i].enableTarget)
            set_or_connect(target.get("weight"), parentMatrix_node.target[i].weight)
            set_or_connect(target.get("targetMatrix"), parentMatrix_node.target[i].targetMatrix)
            set_or_connect(target.get("offsetMatrix"), parentMatrix_node.target[i].offsetMatrix)
        return parentMatrix_node


    def fourByFourMatrix(name, inputs = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]):

        """
        This function either takes a name for a fourByFourMatrix node and creates it or an 
        already existing fourByFourMatry node and connects all inputs.
        Due to the fixed amount of input plugs the inputs need to be fully defined as a matrix row. 
        In its default configuration the fourByFourMatrix is the identity Matrix as shown in the inputs.
        This function returns a pymel node

        This node outputs a 4x4 matrix based on 16 input values. 
        This output matrix attribute can be connected to any attribute that is type "matrix".

        The first row of the matrix is defined by in00, in01, in02, in03.
        The 2nd row of the matrix is defined by in10, in11, in12, in13.
        The 3rd row of the matrix is defined by in20, in21, in22, in23.
        The 4th row of the matrix is defined by in30, in31, in32, in33.
        """

        from pymel.core.nodetypes import FourByFourMatrix

        if pm.objExists(name):
            fourByFourMatrix_node = pm.PyNode(name)
            if pm.nodeType(fourByFourMatrix_node) != "fourByFourMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a fourByFourMatrix node")
            
        else:
            fourByFourMatrix_node:FourByFourMatrix = pm.createNode("fourByFourMatrix", name=name)
        
        for i, input in enumerate(inputs):
            if input is not None:
                for j, plug in enumerate(input):
                    if plug is not None:
                        pm.connectAttr(plug, f"{fourByFourMatrix_node}.in{i}{j}")
        return fourByFourMatrix_node


    def pickMatrix(name, matrix, use_translate=1, use_rotate=1, use_scale=1, use_shear=1):
        
        """
        This function either takes a name for a pickMatrix node and creates it or 
        an already existing pickMatrix node and can be used to connect a matrix and extract
        translation, rotation, scale or shear values from a matrix.
        This function returns a pymel node

        Pick element of a matrix (scale, translate, rotate and shear) and build a matrix only with the selected one. 
        """

        from pymel.core.nodetypes import PickMatrix

        if pm.objExists(name):
            pickMatrix_node = pm.PyNode(name)
            if pm.nodeType(pickMatrix_node) != "pickMatrix":
                raise TypeError(f"Node '{name}' exists but but is not a pickMatrix node")
            
        else:
            pickMatrix_node:PickMatrix = pm.createNode("pickMatrix", name=name)

        pm.connectAttr(matrix, pickMatrix_node.inputMatrix)
        set_or_connect(use_translate, pickMatrix_node.useTranslate)
        set_or_connect(use_rotate, pickMatrix_node.useRotate)
        set_or_connect(use_scale, pickMatrix_node.useScale)
        set_or_connect(use_shear, pickMatrix_node.useShear)
        return pickMatrix_node


    def equal(name, in_01=0.0, in_02=0.0, epsilon=0.0):
        """
        This function either takes a name for an eqaul node and creates it or 
        an already existing equal node and connects/sets all inputs.
        This function outputs a pymel node
        
        This node outputs the result of the comparison (==), logical operation. 
        It outputs true if the inputs are equal more or less the give epsilon.
        """

        #no PyMEL nodeTyoe

        if pm.objExists(name):
            equal_node = pm.PyNode(name)
            if pm.nodeType(equal_node) != "equal":
                raise TypeError(f"Node '{name}' exists but but is not a equal node")
            
        else:
            equal_node = pm.createNode("equal", name=name)
        
        set_or_connect(in_01, equal_node.input1)
        set_or_connect(in_02, equal_node.input2)
        set_or_connect(epsilon, equal_node.epsilon)
        return equal_node


    def distanceBetween(name, inMatrix_1, inMatrix_2, point_01 = (0, 0, 0), point_02 = (0, 0, 0)):

        """
        This fuction either takes a name for a distanceBetween node and creates it or
        an already existing distanceBetween node and connects/sets all inputs.
        This function outputs a pymel node.
        
        This node computes the distance between two points: point1 and point2. 
        If inMatrix1 and inMatrix2 are provided, they are used to multiply the points before the computation.
        The distance result returned is unitless.
        """

        from pymel.core.nodetypes import DistanceBetween

        if pm.objExists(name):
            distanceBetween_node = pm.PyNode(name)
            if pm.nodeType(distanceBetween_node) != "distanceBetween":
                raise TypeError(f"Node '{name}' exists but but is not a distanceBetween node")
            
        else:
            distanceBetween_node:DistanceBetween = pm.createNode("distanceBetween", name=name)

        set_or_connect(inMatrix_1, distanceBetween_node.inMatrix1)
        set_or_connect(inMatrix_2, distanceBetween_node.inMatrix2)
        set_or_connect(point_01, distanceBetween_node.point1)
        set_or_connect(point_02, distanceBetween_node.point2)
        return distanceBetween_node


    def sum(name, inputs:list=None):

        """
        This function either takes a name for a sum node and creates it 
        or an already existing sum node and connects/sets all inputs.
        This function outputs a pymel node.

        This node outputs the sum of the list of inputs.
        """

        #no PyMEL nodeType
        
        if pm.objExists(name):
            sum_node = pm.PyNode(name)
            if pm.nodeType(sum_node) != "sum":
                raise TypeError(f"Node '{name}' exists but but is not a sum node")
            
        else:
            sum_node = pm.createNode("sum", name=name)

        if not inputs:
            inputs=[]

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{sum_node}.input[{i}]", type="float")
                pm.connectAttr(input, f"{sum_node}.input[{i}]", force=True)
        return sum_node
        

    def subtract(name, in_01, in_02):

        """
        This function either takes a name for a subtract node and creates it 
        or an already existing subtract node and connects/sets all inputs.
        THis function outputs a pymel node.
        
        This node outputs the difference between input1 and input2.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            subtract_node = pm.PyNode(name)
            if pm.nodeType(subtract_node) != "subtract":
                raise TypeError(f"Node '{name}' exists but but is not a subtract node")
            
        else:
            subtract_node = pm.createNode("subtract", name=name)

        set_or_connect(in_01, subtract_node.input1)
        set_or_connect(in_02, subtract_node.input2)
        return subtract_node


    def multiply(name, inputs:list=None):

        """
        This function either takes a name for a multiply node and creates it 
        or an already existing multiply node and connects/sets all inputs. 
        Inputs are in a list. This function outputs a pymel node.

        This node outputs the product of its inputs.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            multiply_node = pm.PyNode(name)
            if pm.nodeType(multiply_node) != "multiply":
                raise TypeError(f"Node '{name}' exists but but is not a multiply node")
            
        else:
            multiply_node = pm.createNode("multiply", name=name)
        
        if not inputs:
            inputs = []

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{multiply_node}.input[{i}]", type="float")
                pm.connectAttr(input, f"{multiply_node}.input[{i}]", force=True)
        return multiply_node


    def divide(name, in_01, in_02):

        """
        This function either takes a name for a divide node and creates it or 
        an already existing divide node and connects/sets all inputs.
        This function outputs a pymel node.
        
        This node outputs the quotient of its inputs. Produce an error if the divisor is 0.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            divide_node = pm.PyNode(name)
            if pm.nodeType(divide_node) != "divide":
                raise TypeError(f"Node '{name}' exists but but is not a divide node")
            
        else:
            divide_node = pm.createNode("divide", name=name)
        
        set_or_connect(in_01, divide_node.input1)
        set_or_connect(in_02, divide_node.input2)
        return divide_node
    

    def max(name, inputs:list=None):

        """
        This function either takes a name for a max node and creates it 
        or an already existing max node and connects/sets all inputs.
        This functon outputs a pymel node.

        This node outputs the maximum value from the list of inputs.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            max_node = pm.PyNode(name)
            if pm.nodeType(max_node) != "max":
                raise TypeError(f"Node '{name}' exists but but is not a max node")
            
        else:
            max_node = pm.createNode("max", name=name)

        if not inputs:
            inputs = []

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{max_node}.input[{i}]", type="float")
                set_or_connect(input, max_node.input[i])
                #pm.connectAttr(input, f"{max_node}.input[{i}]", force=True)
        return max_node


    def min(name, inputs:list=None):

        """
        This function either takes a name for a min node and creates it 
        or an already existing min node and connects/sets all inputs.
        This functon outputs a pymel node.

        This node outputs the minimum value from the list of inputs.
        """

        if pm.objExists(name):
            min_node = pm.PyNode(name)
            if pm.nodeType(min_node) != "min":
                raise TypeError(f"Node '{name}' exists but but is not a min node")
            
        else:
            min_node = pm.createNode("min", name=name)
        
        if not inputs:
            inputs = []

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{min_node}.input[{i}]", type="float")
                set_or_connect(input, min_node.input[i])
        return min_node


    def power(name, input, exponent):

        """
        This function either takes a name for a power node and creates it 
        or an already existing power node and connects/sets all inputs.
        This function outputs a pymel node.

        This node outputs the input raised to the power of the exponent.
        """

        #no PyMEL nodeType

        if pm.objExists(name):
            power_node = pm.PyNode(name)
            if pm.nodeType(power_node) != "power":
                raise TypeError(f"Node '{name}' exists but but is not a power node")
            
        else:
            power_node = pm.createNode("power", name=name)

        set_or_connect(input, power_node.input)
        set_or_connect(exponent, power_node.exponent)
        return power_node


    def negate(name, input):

        """
        This function creates a negate node.

        This node outputs the negated value to its input. For example, 
        if the input is 5, the output will be -5
        """

        if pm.objExists(name):
            negate_node = pm.PyNode(name)
            if pm.nodeType(negate_node) != "negate":
                raise TypeError(f"Node '{name}' exists but but is not a negate node")
            
        else:
            negate_node = pm.createNode("negate", name=name)

        pm.connectAttr(input, negate_node.input)
        return negate_node


    def condition(name, first_term=0.0, second_term=0.0, operation=0, color_if_false=(1, 1, 1), color_if_true=(0, 0, 0)):

        """
        This function either takes a name for a condition node and creates it 
        or an already existing condition node and connects/sets all inputs.
        This node outputs a pymel node.

        Condition is a utility node that allows you to switch between two colors or textures, 
        depending on a simple mathematical relationship between two input values. 
        If the relationship Is Not Equal To, etc) is true, then the first color or texture is output. 
        If the relationship is false, then the second color or texture is output.
        """

        from pymel.core.nodetypes import Condition

        if pm.objExists(name):
            condition_node = pm.PyNode(name)
            if pm.nodeType(condition_node) != "condition":
                raise TypeError(f"Node '{name}' exists but but is not a condition node")
            
        else:
            condition_node:Condition = pm.createNode("condition", name=name)
        
        set_or_connect(color_if_false, condition_node.colorIfFalse)
        set_or_connect(color_if_true, condition_node.colorIfTrue)
        set_or_connect(first_term, condition_node.firstTerm)
        set_or_connect(second_term, condition_node.secondTerm)
        set_or_connect(operation, condition_node.operation)
        return condition_node


    def choice(name, selector=0, inputs:list=None):

        """
        This function either takes a name for a choice node and creates it 
        or an already existing choice node an connects/sets all inputs.
        This function outputs a pymel node.

        This node is used to choose between one of many inputs. 
        The selector attribute's value is an integer that specifies the index 
        of which of the input multi-attributes should be passed on to the output.
        """

        from pymel.core.nodetypes import Choice

        if pm.objExists(name):
            choice_node = pm.PyNode(name)
            if pm.nodeType(choice_node) != "choice":
                raise TypeError(f"Node '{name}' exists but but is not a choice node")
            
        else:
            choice_node:Choice = pm.createNode("choice", name=name)
        
        if not inputs:
            inputs = []

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{choice_node}.input[{i}]", type="double")
                set_or_connect(input, choice_node.input[i])
                #pm.connectAttr(input, f"{choice_node}.input[{i}]", force=True)
        set_or_connect(selector, choice_node.selector)
        #pm.connectAttr(selector, choice_node.selector)
        return choice_node


    def blendTwoAttr(name, attr_blender=0.0, inputs:list=None):

        """
        This function either takes a name for a blendTwoAttr node and creates it 
        or an already existing blendTwoAttr node and connects/sets all inputs.
        This function outputs a pymel node.
        
        The blendTwoAttr node blends the values of the input(0) and input(1) 
        attributes of the node using a blending function specified by the attributesBlender attribute. 
        The value of the output attribute of this blend node is computed by:
         
        output = (1 - attributesBlender) * input(0) + attributesBlender * input(1)
        """

        from pymel.core.nodetypes import BlendTwoAttr

        if pm.objExists(name):
            blendTwoAttr_node = pm.PyNode(name)
            if pm.nodeType(blendTwoAttr_node) != "blendTwoAttr":
                raise TypeError(f"Node '{name}' exists but but is not a blendTwoAttr node")
            
        else:
            blendTwoAttr_node:BlendTwoAttr = pm.createNode("blendTwoAttr", name=name)
        
        set_or_connect(attr_blender, blendTwoAttr_node.attributesBlender)

        for i, input in enumerate(inputs):
            if input is not None:
                pm.setAttr(f"{blendTwoAttr_node}.input[{i}]", type="double")
                set_or_connect(input, blendTwoAttr_node.input[i])
                #pm.connectAttr(input, f"{blendTwoAttr_node}.input[{i}]")
        return blendTwoAttr_node


    def blendColors(name, blender=0.5, color_01=(0.0, 0.0, 0.0), color_02=(0.0, 0.0, 0.0)):

        """
        This function either takes a name for a blendColors node and creates it 
        or an already existing blendColors node and connects/sets all inputs.
        This function outputs a pymel node.
        
        Blend Colors is a utility node that allows you to blend together two 
        input colors or textures, using a third value to control the blend. 
        The color of the output is determined by the Blender attribute, 
        which can range from 0 to 1. When Blender is 1, the Output is set to Color 1. 
        When Blender is 0, Output is set to Color 2. When Blender is 0.5, 
        Output is an equal mix of the two colors. By applying a texture map to Blender 
        (say, an image of white text on a black background) you can create a shader 
        that uses Color 1 for the text, and Color 2 for the background.
        
        Here is the formula used for color blending:

        Output[i] = Color1[i] * Blender[i] + Color2[i] * (1.0 - Blender[i]) 
        """
        
        from pymel.core.nodetypes import BlendColors

        if pm.objExists(name):
            blendColors_node = pm.PyNode(name)
            if pm.nodeType(blendColors_node) != "blendColors":
                raise TypeError(f"Node '{name}' exists but but is not a blendColors node")
            
        else:
            blendColors_node:BlendColors = pm.createNode("blendColors", name=name)
        
        set_or_connect(blender, blendColors_node.blender)
        set_or_connect(color_01, blendColors_node.color1)
        set_or_connect(color_02, blendColors_node.color2)
        return blendColors_node


    def remapValue(name, input_max=1, input_min=0, input_value=0, output_max=1, output_min=0, colors:list=None, values:list=None):

        """
        This function either takes a name for a remapValue node and creates it 
        or an already existing remapValue node and connects/sets all inputs.
        This function outputs a pymel node.

        color: {"color_Position": 0.0, "color_Color": (0, 0, 0), "color_Interp": 0}

        value: {"value_Position": 0.0, "value_FloatValue": 0.0, "value_Interp": 0}

        Remap Value is a utility node that allows you to take an input scalar value 
        and remap its value using a gradient. One can remap this to a new output scalar value and/or color.
        The input value is used to select a point along the gradient to use for the output value. 
        The value specified by the Min attribute determines the input value that indexes the far left 
        of the ramp while the Max attribute determines the value at far right.
        The outColor is determined by the color gradient and the outValue by the value gradient. 
        If one only uses the outValue, for example, then the color gradient is ignored.
        """

        from pymel.core.nodetypes import RemapValue

        if pm.objExists(name):
            remapValue_node = pm.PyNode(name)
            if pm.nodeType(remapValue_node) != "remapValue":
                raise TypeError(f"Node '{name}' exists but but is not a remapValue node")
            
        else:
            remapValue_node:RemapValue = pm.createNode("remapValue", name=name)

        set_or_connect(input_max, remapValue_node.inputMax)
        set_or_connect(input_min, remapValue_node.inputMin)
        set_or_connect(input_value, remapValue_node.inputValue)
        set_or_connect(output_max, remapValue_node.outputMax)
        set_or_connect(output_min, remapValue_node.outputMin)

        if colors is None:
            colors = []

        colors = [c if c is not None else {} for c in colors]

        for i, color in enumerate(colors):
            if not isinstance(color, dict):
                pm.warning(f"color{i} is not a dictionary.")
                continue
            
            set_or_connect(color.get["color_Position"], remapValue_node.color[i].color_Position)
            set_or_connect(color.get["color_Color"], remapValue_node.color[i].color_Color)
            set_or_connect(color.get["color_Interp"], remapValue_node.color[i].color_Interp)
        
        if values is None:
            values = []

        values = [v if v is not None else {} for v in values]

        for i, value in enumerate(values):
            if not isinstance(value, dict):
                pm.warning(f"value{i} is not a dictionary")
                continue

            set_or_connect(value.get("value_Position"), remapValue_color.value[i].value_Position)
            set_or_connect(value.get("value_FloatValue"), remapValue_color.value[i].value_FloatValue)
            set_or_connect(value.get("value_Interp"), remapValue_color.value[i].value_Interp)

        return remapValue_node
    

    def smoothStep(name, input=0.0, leftEdge=0.0, rightEdge=0.0):

        """
        This function either takes a name for a smoothStep node and creates it 
        or an already existing smoothStep node and connects/sets all inputs.
        This function outputs a pymel node.

        Compute the smooth step function. The function returns 0 if the input is less than or equal to the left edge, 
        1 if the input is greater than or equal to the right edge, and interpolates using a Hermite polynomial, 
        between 0 and 1 otherwise. The gradient of the smoothstep function is zero at both edges. 
        The right edge value will be clamped to the left edge if it is lower than the left edge.
        """

        if pm.objExists(name):
            smoothStep_node = pm.PyNode(name)
            if pm.nodeType(smoothStep_node) != "smoothStep":
                raise TypeError(f"Node '{name}' exists but but is not a smoothStep node")
            
        else:
            smoothStep_node = pm.createNode("smoothStep", name=name)

        set_or_connect(input, smoothStep_node.input)
        set_or_connect(leftEdge, smoothStep_node.leftEdge)
        set_or_connect(rightEdge, smoothStep_node.rightEdge)

        return smoothStep_node
    

    def not_node(name, input):

        """
        Docstring for not_node
        
        :param name: Description
        :param input: Description
        """

        if pm.objExists(name):
            not_maya_node = pm.PyNode(name)
            if pm.nodeType(not_maya_node) != "not":
                raise TypeError(f"Node '{name}' exists but but is not a not node")
            
        else:
            not_maya_node = pm.createNode("not", name=name)

        set_or_connect(input)
        return not_maya_node
    
    
    def test():
        print("function loaded correctly...........")