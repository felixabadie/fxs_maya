import os
from pathlib import Path
import sys
import importlib
import site
from maya.OpenMaya import MGlobal as _MGlobal


def get_maya_user_folder():
    contents = [
        d for d in Path(os.environ["MAYA_APP_DIR"]).iterdir()
        if d.is_dir() and d.name in _MGlobal.mayaVersion()
    ]
    
    if not contents:
        return None
    return contents[0]


MAYA_APP_DIR = os.environ["MAYA_APP_DIR"]
USER_SCRIPT_DIR = get_maya_user_folder() / "scripts"
CAPITO_PATH = Path(__file__).parent
CAPITO_SETTINGS_DIR = "capito_settings"
SETUP_KEY = "CG_SCRIPTS_PATH"

ROOT_PATH = Path(__file__).parent.parent.parent

tool_dir = str(ROOT_PATH) + r"\hdm\Bachelor\pose_estimation\sourcecode"
site_packages_dir = str(ROOT_PATH) + r"\WORK\venv\Lib\site-packages"
scripts_dir = str(ROOT_PATH) + r"\WORK\maya_scripts"

'''tool_dir = r"E:\hdm\Bachelor\pose_estimation\sourcecode"
site_packages_dir = r"E:\WORK\venv\Lib\site-packages"
scripts_dir = r"E:\WORK\maya_scripts"'''

shelf_name = "pose_prediction"

stop = False
# try:
#     import pymel.core as pc
# except ImportError:
#     from subprocess import check_call
#     mayapy = Path(sys.executable).parent / "mayapy"
#     target = USER_SCRIPT_DIR / "site-packages"
#     print(f"Trying to install pymel. This may take a few seconds.")
#     print(f"Using mayapy location:")
#     print(mayapy)
#     print("Installing to site-package location:")
#     print(target)
#     result = check_call([
#         str(mayapy), "-m", "pip", "install", "--target", str(target), "pymel"],
#         shell=True
#     ) # '"pymel==1.4"'])
#     print(result)    
sys.path.append(str(CAPITO_PATH))

import pymel.core as pc
maya_gui = importlib.import_module("capito.maya.ui.maya_gui")

msg_q = []


def sanity_checks():
    if not USER_SCRIPT_DIR.exists():
        return False
    msg_q.append(("info.png", f"User script dir: {USER_SCRIPT_DIR}"))
    return True

def create_settings_dir():
    if (USER_SCRIPT_DIR / CAPITO_SETTINGS_DIR).exists():
        msg_q.append(("info.png", f"Directory '{CAPITO_SETTINGS_DIR}' already exists in {USER_SCRIPT_DIR}."))
        return
    (USER_SCRIPT_DIR / CAPITO_SETTINGS_DIR).mkdir()
    msg_q.append(("confirm.png", f"Directory '{CAPITO_SETTINGS_DIR}' created in {USER_SCRIPT_DIR}"))

def create_userSetup():
    file_content = [
        "import sys",
        "import importlib",
        "import os",
        "import traceback",
        "import maya.utils",
        "import maya.cmds as cmds",
        "import maya.mel as mel",
        "",
        "tool_dir = r'E:\hdm\Bachelor\pose_estimation\sourcecode'",
        "site_packages_dir = r'E:\WORK\venv\Lib\site-packages'",
        "scripts_dir = r'E:\WORK\maya_scripts'",
        "",
        f"sys.path.append(r'{str(CAPITO_PATH)}')",
        f"sys.path.append(r'{tool_dir}')",
        f"sys.path.append(r'{site_packages_dir}')",
        f"sys.path.append(r'{scripts_dir}')",
        "import pymel.core as pc",
        'importlib.import_module("capito.maya.setup")',
        """
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
        """


        


    ]
    user_setup = USER_SCRIPT_DIR / "userSetup.py"

    action = "Created"
    if user_setup.exists():
        result = pc.confirmDialog(
            title='Warning', message='userSetup.py already exists.\nReplace?',
            button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No'
        )
        if result == "No":
            msg_q.append(("error.png", "Copying of userSetup.py aborted by user."))
            msg_q.append(("info.png", "  -> Recommendation: Rename current userSetup.py, install again, compare and merge files."))
            return
        action = "Replaced"
    with open(user_setup, "w+") as cf:
        cf.write("\n".join(file_content))
    msg_q.append(("confirm.png", f"{action} userSetup.py in user script dir."))


def import_setup():
    importlib.import_module("capito.maya.setup")


def show_results():
    ratios = (30, 200)
    padding = 3
    with pc.window(title="Capito Installation Summary") as win:
        with pc.formLayout(numberOfDivisions=100) as fl:
            with pc.columnLayout(adj=True, bgc=[0, 0, 0]) as log_area:
                for msg in msg_q:
                    with pc.rowLayout(nc=2, cw=ratios):
                        pc.image(i=msg[0])
                        pc.text(label=msg[1])
            with pc.columnLayout(adj=True) as text_area:
                pc.text(
                    wordWrap=True, align="left",
                    label="""If there are no red messages you can try to run cg3 without restart.
To see if installation really worked properly a Maya restart is recommended.
If there are red messages follow the recommendations or contact admin."""
                )
            with pc.horizontalLayout() as button_area:
                pc.button(label="Exit Maya",
                            c=pc.Callback(pc.mel.eval, "quit"))
                close_button = pc.button(label="Try without Restart", c=import_setup)

    fl.attachForm(log_area, "top", padding)
    fl.attachForm(log_area, "left", padding)
    fl.attachForm(log_area, "right", padding)

    fl.attachForm(text_area, "left", 2 * padding)
    fl.attachForm(text_area, "right", 2 * padding)

    fl.attachForm(button_area, "bottom", padding)
    fl.attachForm(button_area, "left", padding)
    fl.attachForm(button_area, "right", padding)

    fl.attachControl(text_area, "bottom", padding, button_area)
    fl.attachControl(log_area, "bottom", padding, text_area)

    close_button.setCommand(pc.Callback(win.delete))
    
    win.show()
    win.setWidthHeight((600,200))
    maya_gui.center_window(win)


def onMayaDroppedPythonFile(*args, **kwargs):
    global msg_q
    msg_q = []
    if sanity_checks():
        create_settings_dir()
        create_userSetup()
        show_results()
    else:
        pc.confirmDialog(
            title='Installation Aborted', button=['OK'],
            message=f'Users "maya/scripts" directory doesn\'t exist.\nExpected at "{USER_SCRIPT_DIR}"'
        )