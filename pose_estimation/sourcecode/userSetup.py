"""File to autoload python files on maya launch"""
import sys
import os
import traceback
import importlib
from site import addsitedir

import maya.utils
import maya.cmds as cmds
import maya.mel as mel

tool_dir = r"D:\fa026_Bachelor\repository\pose_estimation\sourcecode"
site_packages_dir = r"D:\fa026_Bachelor\venv\Lib\site-packages"
pymel_dir = r"K:\pipeline\pymel\pymel"
scripts_dir = r"D:\fa026_Bachelor\maya_scripts\maya_scripts"

addsitedir(site_packages_dir)
#addsitedir(scripts_dir)


sys.path.append(tool_dir)
sys.path.append(site_packages_dir)
sys.path.append(r'K:\pipeline\capito')
sys.path.append(pymel_dir)
sys.path.append(scripts_dir)


import pymel.core as pc
importlib.import_module("capito.maya.setup")


def _create_shelf_button():
    try:
        import maya_deployment
    except Exception:
        print("usersetup: cannot import maya_deployment")
        traceback.print_exc()
        return

    try:
        topShelf = mel.eval('$tmp = $gShelfTopLevel')

        shelf_name = "pose_prediction"

        if not cmds.shelfLayout(shelf_name, exists=True):
            cmds.shelfLayout(shelf_name, parent=topShelf)
            print(f"usersetup: Shelf '{shelf_name}' created.")
        else:
            print(f"usersetup: Shelf '{shelf_name}' exists.")

        all_shelves = cmds.tabLayout(topShelf, q=True, childArray=True) or []
        for shelf in all_shelves:
            children = cmds.shelfLayout(shelf, q=True, childArray=True) or []
            for ch in children:
                try:
                    label = cmds.shelfButton(ch, q=True, label=True)
                    if label in ["DataGeneration", "DataPrep", "DrawingGUI", "PoseServer"]:
                        cmds.deleteUI(ch)
                except Exception:
                    pass

        py_data_generation_cmd = "import data_generation; data_generation.DataGeneration()"
        py_data_prep_cmd = "import data_prep; data_prep.main()"
        py_drawingboard_cmd = "import maya_deployment; maya_deployment.show_paint_tool()"
        py_pose_server_cmd = "import pose_server_launcher; pose_server_launcher.show_server_tool()"

        data_generation_icon = os.path.join(tool_dir, "maya_icons", "start.png")
        data_prep_icon = os.path.join(tool_dir, "maya_icons", "split_data.png")
        deploy_icon_path = os.path.join(tool_dir, "maya_icons", "Deploy.png")
        server_icon_path = os.path.join(tool_dir, "maya_icons", "server.png")

        cmds.shelfButton(
            parent=shelf_name,
            command=py_data_generation_cmd,
            sourceType="python",
            image=data_generation_icon,
            label="DataGeneration",
            annotation="Start Data Generation"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_data_prep_cmd,
            sourceType="python",
            image=data_prep_icon,
            label="DataPrep",
            annotation="Splits Data For CNN-Training"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_pose_server_cmd,
            sourceType="python",
            image=server_icon_path,
            label="PoseServer",
            annotation="Start Pose Server"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_drawingboard_cmd,
            sourceType="python",
            image=deploy_icon_path,
            label="DrawingGUI",
            annotation="Drawing Interface for pose prediction"
        )


    except Exception:
        print("usersetup: Fehler beim Anlegen der Shelf buttons:")
        traceback.print_exc()

maya.utils.executeDeferred(_create_shelf_button)