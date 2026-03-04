import os
import json
import requests
from string import Template
from bs4 import BeautifulSoup

dict_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts\prox_node_setup"

maya_nodes = ["aimMatrix", "blendMatrix", "multMatrix", "inverseMatrix", "rowFromMatrix", "fourByFourMatrix", "pickMatrix", "equal", "distanceBetween",
              "sum", "subtract", "multiply", "divide", "max", "power", "negate", "condition", "choice", "blendTwoAttr", "blendColors", "remapValue", "smoothStep", "not"]


full_dict = {}


def export_json_data(name, data, directory):

    """
    Exports Data as JSON to directory
    """

    filename = f"{name}.json"
    full_path = os.path.join(directory, filename)

    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)


for node_name in maya_nodes:

    attribute_dict = {}

    docs_page = f"https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/Nodes/{node_name}.html"
    page_to_scrape = requests.get(docs_page)
    soup = BeautifulSoup(page_to_scrape.text, "html.parser")
    


    #docstring

    node_docstring = soup.find("mayadoc-description")

    if node_docstring is not None:
        text = node_docstring.get_text("\n", strip=True)
    else:
        text = f"{node_name}: No description available"


    #Attributes

    node_attributes = soup.find_all("td",  attrs={"class":"attrName"})
    node_attribute_type = soup.find_all("td", attrs={"class":"attrType", "width":"10%"})
    node_attribute_default = soup.find_all("td", attrs={"class":"attrType", "width":"20%"})

    attributes = []

    for td in node_attributes:
        codes = td.find_all("code")
        if len(codes) >= 2:
            long_name = codes[0].get_text(strip=True)
            short_name = codes[1].get_text(strip=True)
            attributes.append((long_name, short_name))

    attribute_dict = {}

    for (long_name, short_name), node_type, node_default in zip(attributes, node_attribute_type, node_attribute_default):

        attribute_dict[long_name] = {
            "short": short_name,
            "type": node_type.get_text(strip=True),
            "default": node_default.get_text(strip=True)
        }



    attribute_dict[long_name]

    full_dict[node_name] = {
        "docstring" : text,
        "attributes" : attribute_dict
    }

    export_json_data("test_dict", full_dict, dict_dir)

    print(full_dict)