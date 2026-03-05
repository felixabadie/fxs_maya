import maya.utils
import traceback
import importlib
import maya.cmds as cmds
import maya.mel as mel
from pathlib import Path

SOURCECODE_PATH = Path(__file__).parent.parent
ICONS_PATH = SOURCECODE_PATH / "maya_icons"

def create_shelf():
    try:
        import pose_estimation.sourcecode
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

        py_data_generation_cmd = "from pose_estimation.sourcecode import data_generation; data_generation.DataGeneration()"
        py_data_prep_cmd = "from pose_estimation.sourcecode import data_prep; data_prep.main()"
        py_drawingboard_cmd = "from pose_estimation.sourcecode import maya_deployment; maya_deployment.show_paint_tool()"
        py_pose_server_cmd = "from pose_estimation.sourcecode import pose_server_launcher; pose_server_launcher.show_server_tool()"

        #py_data_generation_cmd = f"from {str(SOURCECODE_PATH)} import data_generation; data_generation.DataGeneration()"
        #py_data_prep_cmd = f"from {str(SOURCECODE_PATH)} import data_prep; data_prep.main()"
        #py_drawingboard_cmd = f"from {str(SOURCECODE_PATH)} import maya_deployment; maya_deployment.show_paint_tool()"
        #py_pose_server_cmd = f"from {str(SOURCECODE_PATH)} import pose_server_launcher; pose_server_launcher.show_server_tool()"

        data_generation_icon = ICONS_PATH / "start.png"
        data_prep_icon = ICONS_PATH / "split_data.png"
        deploy_icon_path = ICONS_PATH / "Deploy.png"
        server_icon_path = ICONS_PATH / "server.png"

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

maya.utils.executeDeferred(create_shelf)