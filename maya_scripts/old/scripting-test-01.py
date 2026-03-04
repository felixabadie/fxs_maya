from typing import Tuple
import pymel.core as pc
from pymel.core.nodetypes import Mesh, Transform



def createBezierCurve(start_obj, mid_obj, end_obj):
    
    dimension = 3

    start_pos = pc.xform(start_obj, query=True, worldSpace=True, translation=True)
    mid_pos = pc.xform(mid_obj, query=True, worldSpace=True, translation=True)
    end_pos = pc.xform(end_obj, query=True, worldSpace=True, translation=True)

    start_ctrl = pc.spaceLocator()
    start_ctrl.translate.set(start_pos)
    mid_ctrl = pc.spaceLocator()
    mid_ctrl.translate.set(mid_pos)
    end_ctrl = pc.spaceLocator()
    end_ctrl.translate.set(end_pos)

 #   pc.parentConstraint(start_ctrl, start_obj, maintainOffset=False)
 #   pc.parentConstraint(mid_ctrl, mid_obj, maintainOffset=False)
 #   pc.parentConstraint(end_ctrl, end_obj, maintainOffset=False)


 #   mid_point = [(start_pos[i] + end_pos[i] / 2 for i in range(dimension))]
    cpt01 = [(start_pos[i] * 0.75 + end_pos[i] * 0.25) for i in range(dimension)]
    cpt02 = [(start_pos[i] * 0.25 + end_pos[i] * 0.75) for i in range(dimension)]

    curve = pc.curve(d=dimension, p=[start_pos, cpt01, mid_pos, cpt02, end_pos])

    pc.select(clear=True)
    pc.select(curve)

    connectJointToCurveControl(start_obj, start_pos)
    connectJointToCurveControl(mid_obj, mid_pos)
    connectJointToCurveControl(end_obj, end_pos)

def connectJointToCurveControl(joint, ctrl):
    
    decomp_node = pc.createNode("decomposeMatrix", name=joint.name() + "_decomp")
    pc.connectAttr(joint.worldMatrix[0], decomp_node.inputMatrix)
    pc.connectAttr(decomp_node.outputTranslate, ctrl.translate)


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


class PointConnect:
    def __init__(self) -> None:
        self.win_id = "connect_point_tool"

        if pc.window(self.win_id, query=True, exists=True):
            pc.deleteUI(self.win_id)

        with pc.window(self.win_id, title="Connect two points with curve") as win:
            with pc.columnLayout(adj=True):
                self.start_point = TextFieldHelper("Select Start Point: ")
                self.mid_point = TextFieldHelper("Select Mid Point: ")
                self.end_point =  TextFieldHelper("Select End Point: ")
                pc.text(label="Please selct and press OK")
                with pc.horizontalLayout():
                    pc.button(label="Cancel")
                    pc.button(label="OK", c=self.execute)


    def execute(self, *args):
        if not self.start_point.obj or not self.end_point.obj:
            pc.warning("Please select both a start and end point!")
            return

        createBezierCurve(self.start_point.obj, self.mid_point.obj, self.end_point.obj)


    def close_window(self, *_):
        if pc.window(self.win_id, exists=True):
            pc.deleteUI(self.win_id)



PointConnect()