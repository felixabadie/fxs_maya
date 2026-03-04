import os
import re
import json
import keyword
import builtins
from string import Template
from collections import OrderedDict

#Data extracted from Maya and its documentation
full_maya_data_export_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\full_maya_data_export.json"
all_maya_nodes_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\all_nodes.json"
output_file = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\generated_nodes.py"
output_pyi_file = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\generated_nodes.pyi"
temp_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup"


"""full_maya_data_export_dir = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\full_maya_data_export.json"
output_file = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\generated_nodes.py"
output_pyi_file = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\generated_nodes.pyi"
"""

"""
Nodes that are sadly not available:

(transform: not in json file)
ambientLight: not in json file
angleDimension: not in json file
arcLengthDimension: not in json file
areaLight: not in json file
baseLattice: not in json file
bezierCurve: not in json file
buttonManip: not in json file
camera: not in json file
clusterHandle: not in json file
collisionModel: not in json file
container: not in json file
curveVarGroup: not in json file
dagContainer: not in json file
deformBend: not in json file
deformFlare: not in json file
deformSine: not in json file
deformSquash: not in json file
deformTwist: not in json file
deformWave: not in json file
directedDisc: not in json file
directionalLight: not in json file
distanceDimShape: not in json file
dropoffLocator: not in json file
dynHolder: not in json file
dynamicConstraint: not in json file
environmentFog: not in json file
fluidTexture2D: not in json file
fluidTexture3D: not in json file
follicle: not in json file
geometryConstraint: not in json file
geometryVarGroup: not in json file
greasePlane: not in json file
greasePlaneRenderShape: not in json file
hairConstraint: not in json file
hairSystem: not in json file
ikEffector: not in json file
imagePlane: not in json file
implicitBox: not in json file
implicitCone: not in json file
implicitSphere: not in json file
lattice: not in json file
lineModifier: not in json file
locator: not in json file
lodGroup: not in json file
mesh: not in json file
meshVarGroup: not in json file
nCloth: not in json file
nParticle: not in json file
nRigid: not in json file
nurbsCurve: not in json file
nurbsSurface: not in json file
objectFilter: not in json file
objectScriptFilter: not in json file
objectSet: not in json file
objectTypeFilter: not in json file
oldNormalConstraint: not in json file
oldTangentConstraint: not in json file
orientationMarker: not in json file
paramDimension: not in json file
particle: not in json file
pfxHair: not in json file
pfxToon: not in json file
pointEmitter: not in json file
pointLight: not in json file
polyBevel2: not in json file
polyBevel3: not in json file
positionMarker: not in json file
renderBox: not in json file
renderCone: not in json file
renderRect: not in json file
renderSphere: not in json file
resultCurveTimeToAngular: not in json file
resultCurveTimeToLinear: not in json file
resultCurveTimeToTime: not in json file
resultCurveTimeToUnitless: not in json file
selectionListOperator: not in json file
shadingEngine: not in json file
sketchPlane: not in json file
softModHandle: not in json file
spotLight: not in json file
spring: not in json file
stereoRigCamera: not in json file
subdiv: not in json file
subdivSurfaceVarGroup: not in json file
surfaceVarGroup: not in json file
textureBakeSet: not in json file
transform: not in json file
unknownTransform: not in json file
vertexBakeSet: not in json file
volumeLight: not in json file
"""

node_class_template = Template("""class $CLASS_NAME(object):
    '''$DOCSTRING'''
    
    def __init__(
        self,
        name: str = "$DEFAULTNAME",
        n: str = "",
        parent=None,
        p=None,
        shared: bool = False,
        s: bool = False,
        skipSelect: bool = False,
        ss: bool = False,
        **kwargs
    ):
                               
        node_name = n if n else name
        node_parent = p if p else parent

        create_kwargs = {
            'name': node_name,
            'shared': shared or s,
            'skipSelect': skipSelect or ss
        }
                               
        if node_parent is not None:
            create_kwargs['parent'] = node_parent
        
        # add additional kwargs
        create_kwargs.update(kwargs)
        
        self._node: $NODETYPE = pm.createNode("$NODE", **create_kwargs)
$ATTRIBUTE_ASSIGNMENTS
    
    @property
    def node(self):
        return self._node
""")


def export_json_data(name, data, directory):
    """export data as json file"""
    path = os.path.join(directory, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def get_docstring(node_name, full_data):
    """get docstring from json file"""
    if node_name in full_data and "docstring" in full_data[node_name]:
        return full_data[node_name]["docstring"]
    else:
        return f"{node_name} node"
    
#check if name available (fix but ugly)
def keywordcheck(input):
        if keyword.iskeyword(input):
            input += "_"
            return input
        elif input in dir(builtins):
            input += "_"
            return input
        else:
            return input


SEGMENT_RE = re.compile(r"""
    (?P<name>[a-zA-Z]\w*)           #attribute name
    (?:\[(?P<index>-?\d+)\])?       #optional index
""", re.VERBOSE)


full_hierarchy = {}


def extract_data_from_attr_path(node_name, path, full_data) -> list:
    """
    Check a Maya attribute like a.b[3].c and it in a structured List.
    [{'name': 'a', 'index': None}, {'name': 'b', 'index': 3}, {'name': 'c', 'index': None}]
    Raises ValueError for invalid segments.

    Parameters:
        path (str): full attribute path

    Returns:
        parts: structured List
    """

    parts = []

    is_array = full_data[node_name]["attributes"][path]["isArray"]

    for segment in path.split("."):
        m = SEGMENT_RE.fullmatch(segment)
        if not m:
            raise ValueError(f"Invalid segment: {segment}")
        
        name = m.group("name")
        index = m.group("index")
        parts.append({
            "name": name,
            "is_array": is_array,
            "index": int(index) if index is not None else None
            
        })
    return parts


def generate_attr_hierarchical_structure(attr_list: list, node_name: str, full_data) -> dict:
    """
    Generates nestled dictionaries to represent
    atribute hierarchy

    Parameters:
        attr_list: list[str] of all attributes

    Returns:
        hierarchy: dict hierarchy
    """
    hierarchy = {}

    for attr in attr_list:

        parts = extract_data_from_attr_path(node_name, attr, full_data)
        current = hierarchy

        for p in parts:
            name = p["name"]
            is_array_flag = p["is_array"]
            if name not in current:
                current[name] = {
                    "children": {},
                    "is_array": is_array_flag          #is true if [i] in attribute path (example)
                }

            else:
                #if attribute exists already, is_array gets updated.
                if is_array_flag:
                    current[name]["is_array"] = True
        
            current = current[name]["children"]

    return hierarchy


def create_pyi_files(node_name, hierarchy, full_data):
    """
    Traverses hierarchy and creates .pyi-code
    
    :param node_name: name of the current node
    :param hierarchy: hierarchical structure of the node attributes
    """

    
    #helper functios
    def make_class_base(prefix: str, attr_name: str):
        if prefix:
            return f"{prefix}{attr_name.capitalize()}"
        return f"{node_name.capitalize()}{attr_name.capitalize()}"
    
    def slot_class_name(class_base: str):
        return f"{class_base}Slot"
    
    def array_class_name(class_base: str):
        return f"{class_base}Array"
    
    def compound_class_name(class_base: str):
        return f"{class_base}Compound"
    

    #Ordered dict because of insert order
    classes_to_create = OrderedDict()

    def collect_classes(attr_name, attr_node, prefix=""):
        """
        Recursive: collects all necessary classes

        :param attr_name: current attr name
        :param attr_node: Description
        :param predix: Description
        """

        class_base = make_class_base(prefix, attr_name)
        is_array = attr_node["is_array"]
        children = attr_node["children"]
        has_children = len(children) > 0

        #Case 1: array of compounds
        if is_array and has_children:
            slot = slot_class_name(class_base)
            array = array_class_name(class_base)

            #if slot not defined: define by creating entry in classes_to_create
            if slot not in classes_to_create:
                fields = []
                for child_name, child_node in children.items():
                    if child_node["children"]:
                        #child classes named recursively -> child_base dependant on slot

                        child_class_base = f"{slot}_{child_name.capitalize()}"
                        if child_node.get("is_array", False):
                            #generates child slot/array via recursive collect
                            collect_classes(child_name, child_node, prefix=f"{slot}_")
                            child_type = array_class_name(child_class_base) if child_node.get("is_array", False) else compound_class_name(child_class_base)
                        
                        else:
                            collect_classes(child_name, child_node, prefix=f"{slot}_")
                            child_type = compound_class_name(child_class_base)

                    else:
                        child_type = "pm.Attribute"
                    fields.append((child_name, child_type))
                classes_to_create[slot] = {
                    "class_type": "slot",
                    "fields": fields,
                    "doc": f"One element of {node_name}.{attr_name}[i]"
                }

            #Array class (methods only)
            if array not in classes_to_create:
                classes_to_create[array] = {
                    "class_type": "array",
                    "slot": slot,
                    "doc": f"Provides autocompletion for array of {slot}"
                }

            for child_name, child_node in children.items():
                if child_node.get("children"):
                    collect_classes(child_name, child_node, prefix=f"{slot}_")
            
            return array
        

        #Case 2: compound without array
        elif has_children and not is_array:
            compound = compound_class_name(class_base)
            if compound not in classes_to_create:
                fields = []
                for child_name, child_node in children.items():
                    if child_node["children"]:
                        child_class_base = f"{compound}_{child_name.capitalize()}"
                        
                        #collect child definition recursively
                        collect_classes(child_name, child_node, prefix=f"{compound}_")
                        
                        #child type depends on whether child is array or compound
                        if child_node.get("is_array", False):
                            child_type = array_class_name(child_class_base)
                        else:
                            child_type = compound_class_name(child_class_base)
                    else:
                        child_type = "pm.Attribute"
                    fields.append((child_name, child_type))
                classes_to_create[compound] = {
                    "class_type": "compound",
                    "fields": fields,
                    "doc": f"Compound attribute {attr_name}"
                }

            #traverse children
            for child_name, child_node in children.items():
                if child_node.get("children"):
                    collect_classes(child_name, child_node, prefix=f"{compound}_")

            return compound
        

        #Case 3: array without compound
        elif is_array and not has_children:
            array = array_class_name(class_base)
            if array not in classes_to_create:
                classes_to_create[array] = {
                    "class_type": "array_simple",
                    "slot": None,
                    "doc": f"Provides autocompletion for array of simple attributes: {attr_name}"
                }
            return array
        
        #Case 4: simpe attribute
        return "pm.Attribute"
    

    #Collect type for all top level attributes
    top_level_types = OrderedDict()
    for attr_name, attr_node in hierarchy.items():
        attr_type = collect_classes(attr_name, attr_node, prefix="")
        top_level_types[attr_name] = attr_type

    
    lines = []
    for class_name, description in classes_to_create.items():
        class_type = description["class_type"]
        if class_type == "slot":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{description['doc']}'''")
            for field_name, field_type in description["fields"]:
                #field_name = keywordcheck(field_name)
                lines.append(f"    {keywordcheck(field_name)}: {field_type}")
            lines.append("")
        
        elif class_type == "compound":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{description['doc']}'''")
            for field_name, field_type in description["fields"]:
                #field_name = keywordcheck(field_name)
                lines.append(f"    {field_name(field_name)}: {field_type}")
            lines.append("")

        elif class_type == "array":
            slot = description["slot"]
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{description['doc']}'''")
            lines.append(f"    def __getitem__(self, idx: int) -> {slot}: ...")
            lines.append(f"    def __iter__(self): ...")
            lines.append(f"    def __len__(self) -> int: ...")
            lines.append("")

        elif class_type == "array_simple":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{description['doc']}'''")
            lines.append(f"    def __getitem__(self, idx: int) -> pm.Attribute: ...")
            lines.append(f"    def __iter__(self): ...")
            lines.append(f"    def __len__(self) -> int: ...")
            lines.append("")

    #Create Main class
    docstring = get_docstring(node_name, full_data)
    adapted_node_name = keywordcheck(node_name)
    nodetype = f"pm.nodetypes.{node_name[0].upper() + node_name[1:]}"
    #nodetype = f"pm.nodetypes.DependNode"

    lines.append(f"class {adapted_node_name}(object):")
    lines.append(f"    '''{docstring}'''")
    lines.append(f"    _node: {nodetype}")
    lines.append("")

    init_signature = (
        f"    def __init__(self, "
        f"name: str = '{node_name}', "
        f"n: str = '', "
        f"parent: str | pm.PyNode | None = None, "
        f"p: str | pm.PyNode | None = None, "
        f"shared: bool = False, "
        f"s: bool = False, "
        f"skipSelect: bool = False, "
        f"ss: bool = False, "
        f"**kwargs"  # for aditional parameters
        f") -> None: ..."
    )

    lines.append(init_signature)

    for attr_name, attr_type in top_level_types.items():
        attr_name = keywordcheck(attr_name)
        lines.append(f"    {attr_name}: {attr_type}")
    lines.append("")
    lines.append(f"    @property")
    lines.append(f"    def node(self) -> {nodetype}: ...")

    return "\n".join(lines)


def generate_class_code(node_name, maya_attrs, full_data):
    """
    generate code for python
    
    :param node_name: name of the current node
    :param maya_attrs: list of all node attributes
    :param full_data: full data including docstrings and more
    """

    docstring = get_docstring(node_name, full_data)

    main_params_list = []

    node_hierarchy = generate_attr_hierarchical_structure(maya_attrs, node_name, full_data)
    

    full_hierarchy[node_name] = node_hierarchy

    for attr in node_hierarchy:
        main_params_list.append(attr)
    

    nodetype = f"pm.nodetypes.{node_name[0].upper() + node_name[1:]}"


    #Attribute assignments
    assignments = [
        f"        self.{keywordcheck(attr)} = self._node.attr('{attr}')"
        for attr in main_params_list
    ]

    attribute_assignments_str = "\n".join(assignments)

    adapted_node_name = keywordcheck(node_name)

    #apply template
    class_code = node_class_template.substitute(
        CLASS_NAME=adapted_node_name,
        DEFAULTNAME=node_name,
        NODETYPE=nodetype,
        NODE=node_name,
        DOCSTRING=docstring,
        ATTRIBUTE_ASSIGNMENTS=attribute_assignments_str
    )

    class_pyi_code = create_pyi_files(node_name, node_hierarchy, full_data)

    return class_code, class_pyi_code


def main():
    #Load JSON file
    with open(full_maya_data_export_dir, 'r') as f:
        full_data = json.load(f)

    with open(all_maya_nodes_dir, 'r') as f:
        all_nodes = json.load(f)

    n_list = all_nodes["maya_nodes"]

    generated_node_code = "import pymel.core as pm\n\n"
    generated_pyi_code = "import pymel.core as pm\n\n"

    for node_name in n_list:
        if node_name not in full_data:
            print(f"{node_name}: not in json file")
            continue
    
        maya_attrs = full_data[node_name]["attributes"]

        class_code, class_pyi_code = generate_class_code(node_name, maya_attrs, full_data)
        generated_node_code += class_code + "\n\n"
        generated_pyi_code += class_pyi_code + "\n\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generated_node_code)

    with open(output_pyi_file, 'w', encoding='utf-8') as f:
        f.write(generated_pyi_code)

    export_json_data("temp2", full_hierarchy, directory=temp_dir)

if __name__ == "__main__":
    main()