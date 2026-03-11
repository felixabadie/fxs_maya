import maya.utils
import traceback
import importlib
import maya.cmds as cmds
import maya.mel as mel
from pathlib import Path

MAYA_SCRIPTS_PATH = Path(__file__).parent.parent
MODULES_PATH = MAYA_SCRIPTS_PATH / "rig_module"

ICONS_PATH = MAYA_SCRIPTS_PATH / "setup/images"

def create_shelf():
    try:
        topShelf = mel.eval('$tmp = $gShelfTopLevel')

        shelf_name = "rigging_modules"

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
                    if label in ["RootModule", "LimbModule", "LegModule", "SpineModule", "Biped"]:
                        cmds.deleteUI(ch)
                except Exception:
                    pass

        py_root_module_cmd = "from maya_scripts.rig_module import root; root.RootManager()"
        py_limb_module_cmd = "from maya_scripts.rig_module import base_limb; base_limb.LimbManager()"
        py_leg_module_cmd = "from maya_scripts.rig_module import leg; leg.LegManager()"
        py_spine_module_cmd = "from maya_scripts.rig_module import spine; spine.SpineManager()"
        py_biped_module_cmd = "from maya_scripts.rig_module import full_body_test; full_body_test.BipedManager()"
        py_clavicle_module_cmd = "from maya_scripts.rig_module import clavicle; clavicle.ClavicleManager()"

        root_icon = ICONS_PATH / "root.png"
        limb_icon = ICONS_PATH / "limb.png"
        leg_icon = ICONS_PATH / "leg.png"
        spine_icon = ICONS_PATH / "spine.png"
        biped_icon = ICONS_PATH / "full_body.png"
        clavicle_icon = ICONS_PATH / "shoulder.png"

        cmds.shelfButton(
            parent=shelf_name,
            command=py_biped_module_cmd,
            sourceType="python",
            image=biped_icon,
            label="BipedModule",
            annotation="Create Biped Rig out of Rigging Modules"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_root_module_cmd,
            sourceType="python",
            image=root_icon,
            label="root_module",
            annotation="Create Root Module"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_spine_module_cmd,
            sourceType="python",
            image=spine_icon,
            label="SpineModule",
            annotation="Create Spine Module"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_clavicle_module_cmd,
            sourceType="python",
            image=clavicle_icon,
            label="ClavicleModule",
            annotation="Create Clavicle Module"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_limb_module_cmd,
            sourceType="python",
            image=limb_icon,
            label="limb_module",
            annotation="Create Limb Module"
        )

        cmds.shelfButton(
            parent=shelf_name,
            command=py_leg_module_cmd,
            sourceType="python",
            image=leg_icon,
            label="LimbModule",
            annotation="Create Leg Module"
        )




    except Exception:
        print("usersetup: Fehler beim Anlegen der Shelf buttons:")
        traceback.print_exc()

maya.utils.executeDeferred(create_shelf)