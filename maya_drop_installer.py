import os
from pathlib import Path
import sys
import importlib
from site import addsitedir
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
MAIN_PATH = Path(__file__).parent
CAPITO_PATH = f"{MAIN_PATH}/capito"
CAPITO_SETTINGS_DIR = "capito_settings"
SETUP_KEY = "CG_SCRIPTS_PATH"

BACHELOR_TOOL_DIR = f"{MAIN_PATH}/pose_estimation/sourcecode"
SCRIPTS_DIR = f"{MAIN_PATH}/maya_scripts"

site_packages_dir="C:\\Users\\Felix\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages"

addsitedir(site_packages_dir)
sys.path.append(str(CAPITO_PATH))

import pymel.core as pm
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
        f"sys.path.append(r'{str(MAIN_PATH)}')",
        f"sys.path.append(r'{str(BACHELOR_TOOL_DIR)}')",
        f"sys.path.append(r'{str(SCRIPTS_DIR)}')",
        f"sys.path.append(r'{str(CAPITO_PATH)}')",
        "import pymel.core as pm",
        'importlib.import_module("capito.maya.setup")',
        "import pose_prediction.sourcecode.setup.add_shelves()"
    ]

    user_setup = USER_SCRIPT_DIR / "userSetup.py"

    action = "Created"

    if user_setup.exists():
        result = pm.confirmDialog(
            title='Warning', message='userSetup.py already exists.\nReplace?',
            button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No'
        )
        if result == "No":
            msg_q.append(("error.png", "Copying of userSetup.py aborted by user"))
            msg_q.append(("info.png", "  -> Recommendation: Rename current userSetup.py, install again, compare and merge files."))
            return
        action = "Replaced"
    with open(user_setup, "w+") as cf:
        cf.write("\n".join(file_content))
    msg_q.append(("confirm.png", f"{action} userSetup.py in user script dir."))

def import_setup():
    importlib.import_module("capito.maya.setup")

def install_shelf():
    import pose_estimation.sourcecode.setup.add_shelves

def show_results():
    ratios = (30, 200)
    padding = 3

    with pm.window(title="fxs_maya Installation Summary") as win:
        with pm.formLayout(numberOfDivisions=100) as fl:
            with pm.columnLayout(adj=True, bgc=[0, 0, 0]) as log_area:
                for msg in msg_q:
                    with pm.rowLayout(nc=2, cw=ratios):
                        pm.image(i=msg[0])
                        pm.text(label=msg[1])
            with pm.columnLayout(adj=True) as text_area:
                pm.text(
                    wordWrap=True, align="left",
                    label="""If there are no red messages you can try to run cg3 without restart.
To see if installation really worked properly a Maya restart is recommended.
If there are red messages follow the recommendations or contact admin."""
                )
            with pm.horizontalLayout() as button_area:
                pm.button(label="Exit Maya",
                          c=pm.Callback(pm.mel.eval, "quit"))
                close_button = pm.button(label="Try without Restart", c=import_setup)

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

    close_button.setCommand(pm.Callback(win.delete))
    
    win.show()
    win.setWidthHeight((600,200))
    maya_gui.center_window(win)


def onMayaDroppedPythonFile(*args, **kwargs):
    global msg_q
    msg_q = []
    if sanity_checks():
        create_settings_dir()
        create_userSetup()
        install_shelf()
        show_results()
    else:
        pm.confirmDialog(
            title='Installation Aborted', button=['OK'],
            message=f'Users "maya/scripts" directory doesn\'t exist.\nExpected at "{USER_SCRIPT_DIR}"'
        )