import pymel.core as pm
import maya.api.OpenMaya as om
import re

"""def remove_prefix(name, prefix):
    sub = re.sub(f"{prefix}", "", name)
    return sub"""

def process_plug(plug):
    
    results = []

    if plug.isArray:
        plug.evaluateNumElements()
        for i in range(plug.numElements()):
            element_plug = plug.elementByPhysicalIndex(i)
            results.extend(process_plug(element_plug))

    elif plug.isCompound:
        for j in range(plug.numChildren()):
            child_plug = plug.child(j)
            results.extend(process_plug(child_plug))

    else:
        results.append(plug)

    return results


daten = {}

selection = pm.selected()
node = pm.PyNode(selection[0])
full_node_name = node.name()

sel = om.MSelectionList()
sel.add(full_node_name)
mobj = sel.getDependNode(0)

fn = om.MFnDependencyNode(mobj)
connections_list = node.listConnections(connections=True, plugs=True)

connections = []
modified_attrs = []

for source, destination in connections_list:
    connection = [source.name(), destination.name()]
    connections.append(connection)

for i in range(fn.attributeCount()):
    attr_obj = fn.attribute(i)
    plug = om.MPlug(mobj, attr_obj)
        
    attr_name = plug.partialName(useLongNames=True, includeNodeName=False, useFullAttributePath=True)

    try:
        plug_or_subplugs = process_plug(plug)

        for p in plug_or_subplugs:
            current_plug_name = p.partialName(useLongNames=True, includeNodeName=False, useFullAttributePath=True)

            clean_attr_name = re.sub(r'\[\d+\]', '', current_plug_name) # reomve array index

            try:
                current_default_value = pm.attributeQuery(clean_attr_name, node=node, listDefault=True)

            except Exception as ef:
                print(f"Problems with getting default value for {current_plug_name}: {ef}")
                continue

            if not current_default_value:
                continue

            try:
                current_value = node.getAttr(current_plug_name)

            except Exception as eg:
                print(f"Problems with getting current value for {current_plug_name}: {eg}")
                continue

            if current_value != current_default_value[0]:
                modified_attrs.append([current_plug_name, current_value])

    except Exception as major_error:
        print(f"Yea man no idea here: {major_error}")
        continue
    
    
node_data = {}
node_data["node_name"] = full_node_name
node_data["node_type"] = fn.typeName
node_data["connections"] = connections
node_data["modified_attributes"] = modified_attrs

daten[full_node_name] = node_data
print(daten)

#print(pm.attributeQuery("weight", node=node, listDefault=True))
#print(node.getAttr("target[0].weight"))