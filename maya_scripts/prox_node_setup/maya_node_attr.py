import os
import json
import requests
import pymel.core as pm
from string import Template
from bs4 import BeautifulSoup
import maya.api.OpenMaya as om
from urllib.parse import urljoin

export_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup"
export_dir_v2 = r"D:\fa026_Bachelor\maya_scripts\prox_node_setup"

"""
Special nodes: blendMatrix (target -> array of compounds), 

multMatrix (matrix In -> array), 
sum (input -> array), multiply (input -> array), max (input -> array), min (input -> array), 
choice (input -> array), blendTwoAttr (input -> array, 

remapValue (Color -> array of compounds, Value -> array of compounds), 
"""

# output dict that contains information on every single, node and its attributes
full_dict = {}

# output dict representing all supported nodes
all_nodes = {}

def export_json_data(name, data, directory):
    path = os.path.join(directory, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

nodes_index_dir = r"https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/Nodes/"

class Get_Attr_From_Maya:
    def __init__(self):
        node_list_updated = []
        node_list = pm.allNodeTypes(includeAbstract=False)
        
        # Check to see what nodes can be created in maya
        for node_name in node_list:

            try:
                node = pm.createNode(node_name)
                node_list_updated.append(node_name)
                pm.delete(all=True)
            except:
                print(f"{node_name} cannot be created")

        node_list_updated.append("transform") 

        all_nodes["maya_nodes"] = node_list_updated


        for node_name in node_list_updated:

            try:

                docs_page = f"https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/Nodes/{node_name}.html"
                page_to_scrape = requests.get(docs_page)
                soup = BeautifulSoup(page_to_scrape.text, "html.parser")


                #docstring
                node_docstring = soup.find("mayadoc-description")

                if node_docstring is not None:
                    text = node_docstring.get_text("\n", strip=True)
                else:
                    text = f"{node_name}: No description available"



                #scraped attributes

                scraped_attrs = {}

                node_attr_names = soup.find_all("td",  attrs={"class":"attrName"})
                node_attr_types = soup.find_all("td", attrs={"class":"attrType", "width":"10%"})
                node_attr_default = soup.find_all("td", attrs={"class":"attrType", "width":"20%"})

                for (name_td, type_td, def_td) in zip(node_attr_names, node_attr_types, node_attr_default):

                    codes = name_td.find_all("code")
                    if len(codes) >= 2:
                        long_name = codes[0].get_text(strip=True)
                        short_name = codes[1].get_text(strip=True)

                        scraped_attrs[long_name] = {
                            "shortName": short_name,
                            "scrapedType": type_td.get_text(strip=True),
                            "scrapedDefault": def_td.get_text(strip=True)
                        }

                #create node
                node = pm.createNode(node_name)
                node_instance_name = node.name()

                #get API-object
                sel = om.MSelectionList()
                sel.add(node_instance_name)
                mobj = sel.getDependNode(0)

                fn = om.MFnDependencyNode(mobj)

                node_dict = {
                    "docstring": text,
                    "attributes": {}
                }

                # Alle Attribute sicher per API
                for i in range(fn.attributeCount()):
                    attr_obj = fn.attribute(i)
                    plug = om.MPlug(mobj, attr_obj)

                    attr_name = plug.partialName(useLongNames=True)

                    try:
                        default_value = node.getAttr(attr_name)
                        
                    except Exception as e:
                        default_value = None

                    api_type = attr_obj.apiTypeStr
                    is_array = plug.isArray
                    is_comp = plug.isCompound

                    scraped = scraped_attrs.get(attr_name, None)

                    node_dict["attributes"][attr_name] = {
                        "shortName": scraped["shortName"] if scraped else None,
                        "OpenMayaType": api_type,
                        "ScrapedType": scraped["scrapedType"] if scraped else None,
                        "OpenMayaDefault": str(default_value),
                        "ScrapedDefault": scraped["scrapedDefault"] if scraped else None,
                        "isArray": bool(is_array),
                        "isCompound": bool(is_comp)
                    }

                #node_name = node_name[:-1]
                full_dict[node_name] = node_dict

                pm.delete(node)

            except Exception as e:
                print(f"{node_name} - node failed: {e}")

        export_json_data("full_maya_data_export", full_dict, export_dir)
        export_json_data("all_nodes", all_nodes, export_dir)

Get_Attr_From_Maya()