import pymel.core as pc
from typing import Tuple
from pymel.core.nodetypes import Mesh, Transform

class TextFieldHelper:
    def __init__(self, label, buttonLabel="Set", text="Not set"):
        self.control = pc.textFieldButtonGrp(
            label=label, buttonLabel=buttonLabel, text=text,
            bc=self.set_text
        )
                
    def set_text(self):
        sel = pc.selected()
        if not sel:
            pc.warning("Warning")
            return
        self.control.setText(sel[0].name())
        self.obj = sel[0]

    def create_mouth_curve(edge):
        pass

    def create_locators_on_curve(mout_loop, high_res_curve):
        pass

    def create_control_curve(high_res_curve):
        pass 

    def create_curve_ctrl(low_res_curve):
        pass

class MouthRigger():
    def __init__(self):
        self.win_id = "MouthRigger"
        
        if pc.window(self.win_id, query=True, exists=True):
            pc.deleteUI(self.win_id)
        
        with pc.window(self.win_id, title="Mouth Rigger") as win:
            with pc.columnLayout(adj=True):
                self.mouth_loop_tfh = TextFieldHelper("Mouth Loop: ")
                self.base_jnt_tfh = TextFieldHelper("Base Joint: ")
                pc.text(label="Please select the corresponding components and press OK")
                with pc.horizontalLayout():
                    pc.button(label="Cancel")
                    pc.button(label="OK", c=self.execute)
    
    def execute(self, *args):
        mouth_loop = self.mouth_loop_tfh
        high_res_curve = self.create_mouth_curve(mouth_loop)
        low_res_curve = self.create_control_curve(high_res_curve)

    
    pass

MouthRigger()