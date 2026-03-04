import os
import re
import json
import keyword
from string import Template
from collections import OrderedDict

#Data extracted from Maya and its documentation
full_maya_data_export_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\full_maya_data_export.json"
output_file = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\generated_nodes.py"
output_pyi_file = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup\generated_nodes.pyi"
temp_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup"


"""full_maya_data_export_dir = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\full_maya_data_export.json"
output_file = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\generated_nodes.py"
output_pyi_file = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup\generated_nodes.pyi"
"""


"""
Namen von array bzw bei tieferen hierarchien überprüfen -> sind aktuell seltsam
außerdem noch überlegen ob node vom Type pymel.nodetypes.Node callable sein soll
evtl -> __call__() anschauen
"""

#selection of nodes to be considered
maya_nodes = [
    "transform", "aimMatrix", "blendMatrix", "multMatrix", "inverseMatrix", "rowFromMatrix",
    "fourByFourMatrix", "pickMatrix", "equal", "distanceBetween", "sum",
    "subtract", "multiply", "divide", "max", "min", "power", "negate",
    "condition", "choice", "blendTwoAttr", "blendColors", "remapValue",
    "smoothStep", "not"
]


node_class_template = Template("""class $CLASS_NAME(object):
    '''$DOCSTRING'''
    
    def __init__(self, name='$DEFAULTNAME'):
        self.name = name
        self._node: $NODETYPE = pm.createNode("$NODE", name=name)
$ATTRIBUTE_ASSIGNMENTS
    
    @property
    def node(self):
        return self._node
""")


def export_json_data(name, data, directory):
    path = os.path.join(directory, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def get_docstring(node_name, full_data):
    """get docstring from json file"""
    if node_name in full_data and "docstring" in full_data[node_name]:
        return full_data[node_name]["docstring"]
    else:
        return f"{node_name} node"
    

def keywordcheck(input):
        if keyword.iskeyword(input):
            adapted_input = input[0] + input
            return adapted_input
        else:
            return input


SEGMENT_RE = re.compile(r"""
    (?P<name>[a-zA-Z]\w*)           #attribute name
    (?:\[(?P<index>-?\d+)\])?       #optional index
""", re.VERBOSE)


full_hierarchy = {}


def extract_data_from_attr_path(path: str):
    """
    Check a Maya attribute like a.b[3].c and it in a structured List.
    [{'name': 'a', 'index': None}, {'name': 'b', 'index': 3}, {'name': 'c', 'index': None}]
    Raises ValueError for invalid segments.
    """

    parts = []

    for segment in path.split("."):
        m = SEGMENT_RE.fullmatch(segment)
        if not m:
            raise ValueError(f"Invalid segment: {segment}")
        
        name = m.group("name")
        index = m.group("index")
        parts.append({
            "name": name,
            "index": int(index) if index is not None else None
            
        })

    return parts


def generate_attr_hierarchical_structure(attr_list):
    """
    list = list[str] all attributes.
    returns dict hierarchy


    """
    hierarchy = {}

    for attr in attr_list:

        parts = extract_data_from_attr_path(attr)
        current = hierarchy

        for p in parts:
            name = p["name"]
            is_array_flag = (p["index"] is not None)

            #Ensure entry exists
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
    Neue, robustere create_pyi_files-Implementierung (Ansatz A).
    - Build-Phase: sammelt alle benötigten Hilfsklassen (Slot/Array/Compound).
    - Emit-Phase: schreibt die Klassen (Kinder zuerst, Eltern danach).
    - Minimale Abweichung zu deiner bisherigen API / Namensgebung.
    """

    # Hilfsfunktionen
    def make_class_base(prefix, attr_name):
        if prefix:
            return f"{prefix}{attr_name.capitalize()}"
        return f"{node_name.capitalize()}{attr_name.capitalize()}"

    def slot_class_name(class_base):
        return f"{class_base}Slot"

    def array_class_name(class_base):
        return f"{class_base}Array"

    def compound_class_name(class_base):
        return f"_{class_base}"

    # OrderedDict hält Einfügereihenfolge -> Kinder werden zuerst eingefügt (durch rekursives Traversal)
    classes_to_emit = OrderedDict()

    def collect(attr_name, attr_node, prefix=""):
        """
        Rekursiv: sammelt in classes_to_emit die benötigten Klassen.
        Der Rückgabewert ist der *Typname* (string) der für dieses Attribut in der Parent-Klasse benutzt werden soll.
        """
        class_base = make_class_base(prefix, attr_name)
        is_array = bool(attr_node.get("is_array", False))
        children = attr_node.get("children", {}) or {}
        has_children = len(children) > 0

        # Fall 1: array of compound (z.B. value[i] mit Unterfeldern)
        if is_array and has_children:
            slot = slot_class_name(class_base)
            arr = array_class_name(class_base)

            # Wenn Slot noch nicht definiert: definieren (eintrag in classes_to_emit)
            if slot not in classes_to_emit:
                # Felder: für jedes child bestimmen wir den Typ (pm.Attribute oder weiter referenzierte Klasse)
                fields = []
                for child_name, child_node in children.items():
                    # Wenn child selbst Compound/Array -> referenziere spätere Klasse
                    if child_node.get("children"):
                        # Kind-Klassen benennen wir rekursiv: child_base hängt vom slot ab
                        # Wir erzeugen den Name, der später beim Emit aufgelöst ist
                        child_class_base = f"{slot}_{child_name.capitalize()}"
                        if child_node.get("is_array", False):
                            # this will generate child slot/array via recursive collect
                            collect(child_name, child_node, prefix=f"{slot}_")
                            child_type = array_class_name(child_class_base) if child_node.get("is_array", False) else compound_class_name(child_class_base)
                        else:
                            collect(child_name, child_node, prefix=f"{slot}_")
                            child_type = compound_class_name(child_class_base)
                    else:
                        child_type = "pm.Attribute"
                    fields.append((child_name, child_type))
                classes_to_emit[slot] = {
                    "kind": "slot",
                    "fields": fields,
                    "doc": f"One element of {node_name}.{attr_name}[i]"
                }

            # Array class (methods only)
            if arr not in classes_to_emit:
                classes_to_emit[arr] = {
                    "kind": "array",
                    "slot": slot,
                    "doc": f"Provides autocomplete for array of {slot}"
                }

            # Rekursionsschritt für children (sichert, dass tieferliegende Klassen gesammelt werden)
            for child_name, child_node in children.items():
                if child_node.get("children"):
                    collect(child_name, child_node, prefix=f"{slot}_")

            return arr

        # Fall 2: compound (nicht array)
        elif has_children and not is_array:
            comp = compound_class_name(class_base)

            if comp not in classes_to_emit:
                fields = []
                for child_name, child_node in children.items():
                    if child_node.get("children"):
                        child_class_base = f"{comp}_{child_name.capitalize()}"
                        # collect child definition recursively
                        collect(child_name, child_node, prefix=f"{comp}_")
                        # child type depends on whether child is array or compound
                        if child_node.get("is_array", False):
                            child_type = array_class_name(child_class_base)
                        else:
                            child_type = compound_class_name(child_class_base)
                    else:
                        child_type = "pm.Attribute"
                    fields.append((child_name, child_type))
                classes_to_emit[comp] = {
                    "kind": "compound",
                    "fields": fields,
                    "doc": f"Compound attribute {attr_name}"
                }

            # traverse children (so deep children are collected)
            for child_name, child_node in children.items():
                if child_node.get("children"):
                    collect(child_name, child_node, prefix=f"{comp}_")

            return comp

        # Fall 3: array ohne compound -> einfache Array-Klasse
        elif is_array and not has_children:
            arr = array_class_name(class_base)
            if arr not in classes_to_emit:
                classes_to_emit[arr] = {
                    "kind": "array_simple",
                    "slot": None,
                    "doc": f"Provides autocomplete for array of simple attributes {attr_name}"
                }
            return arr

        # Fall 4: einfache leaf-attribute
        return "pm.Attribute"


    # --- Sammelphase: für alle top-level attributes den Typ ermitteln (collect)
    top_level_types = OrderedDict()
    for attr_name, attr_node in hierarchy.items():
        attr_type = collect(attr_name, attr_node, prefix="")
        top_level_types[attr_name] = attr_type

    # --- Emit-Phase: wir geben zuerst alle gesammelten Hilfsklassen aus (in Einfügereihenfolge)
    lines = []
    for class_name, meta in classes_to_emit.items():
        kind = meta["kind"]
        if kind == "slot":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{meta['doc']}'''")
            for field_name, field_type in meta["fields"]:
                lines.append(f"    {field_name}: {field_type}")
            lines.append("")
        elif kind == "compound":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{meta['doc']}'''")
            for field_name, field_type in meta["fields"]:
                lines.append(f"    {field_name}: {field_type}")
            lines.append("")
        elif kind == "array":
            # array that references a slot class
            slot = meta["slot"]
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{meta['doc']}'''")
            lines.append(f"    def __getitem__(self, idx: int) -> {slot}: ...")
            lines.append(f"    def __iter__(self): ...")
            lines.append(f"    def __len__(self) -> int: ...")
            lines.append("")
        elif kind == "array_simple":
            lines.append(f"class {class_name}(object):")
            lines.append(f"    '''{meta['doc']}'''")
            lines.append(f"    def __getitem__(self, idx: int) -> pm.Attribute: ...")
            lines.append(f"    def __iter__(self): ...")
            lines.append(f"    def __len__(self) -> int: ...")
            lines.append("")

    # --- Hauptklasse erzeugen (Node-Klasse)
    docstring = get_docstring(node_name, full_data)
    adapted_node_name = keywordcheck(node_name)
    nodetype = f"pm.nodetypes.{node_name[0].upper() + node_name[1:]}"

    lines.append(f"class {adapted_node_name}(object):")
    lines.append(f"    '''{docstring}'''")
    lines.append(f"    _node: {nodetype}")
    lines.append("")

    # Top-level attributes mit Typen (aus top_level_types)
    for attr_name, attr_type in top_level_types.items():
        lines.append(f"    {attr_name}: {attr_type}")
    lines.append("")
    lines.append(f"    def node(self) -> {nodetype}: ...")
    lines.append("")

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

    attr_list = []
    for attr in maya_attrs:
        attr_list.append(attr)

    #node_hierarchy = generate_attr_hierarchical_structure(attr_list)
    node_hierarchy = generate_attr_hierarchical_structure(attr_list)
    

    full_hierarchy[node_name] = node_hierarchy

    for attr in node_hierarchy:
        main_params_list.append(attr)
    

    nodetype = f"pm.nodetypes.{node_name[0].upper() + node_name[1:]}"


    #Attribute assignments
    assignments = [
        f"        self.{attr} = self._node.attr('{attr}')"
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

    generated_node_code = "import pymel.core as pm\n\n"
    generated_pyi_code = "import pymel.core as pm\n\n"

    for node_name in maya_nodes:
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