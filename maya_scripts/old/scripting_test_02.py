from typing import Tuple
import pymel.core as pc
from pymel.core.nodetypes import DependNode

from pymel.core.nodetypes import Mesh, Transform

class TextFieldHelper:
    def __init__(self, label, buttonLabel="Set", text="Not set"):
        self.control = pc.textFieldButtonGrp(
            label=label, buttonLabel=buttonLabel, text=text,
            bc=self.set_text
        )
        self.obj = None  # Initialisieren, um Fehler zu vermeiden

    def set_text(self, *_):
        sel = pc.ls(sl=True, type=Transform)
        if not sel:
            pc.warning("Please select an object!")
            return
        
        self.obj = sel[0]  # Speichere das Objekt
        pc.textFieldButtonGrp(self.control, edit=True, text=self.obj.name())

def get_joint_chain(joint):
    child_joints = [joint]

    def traverse_hierarchy(joint):
        children = joint.getChildren(ad=True, type='joint')

        for child in children:
            if child.getParent() == joint:
                child_joints.append(child)
                traverse_hierarchy(child)

    traverse_hierarchy(joint)
    return(child_joints)

class createArm:
    def __init__(self) -> None:
        self.win_id = "create_arm_tool"

        if pc.window(self.win_id, query=True, exists=True):
            pc.deleteUI(self.win_id)

        with pc.window(self.win_id, title="create arm") as win:
            with pc.columnLayout(adj=True):
                self.shoulder_joint = TextFieldHelper("Select shoulder joint: ")
                pc.text(label="Please select and press OK")
                with pc.horizontalLayout():
                    pc.button(label="Cancel")
                    pc.button(label="OK", c=self.execute)

    def get_joint_chain():
        pass

