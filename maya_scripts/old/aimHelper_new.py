from typing import Tuple
import pymel.core as pc
from pymel.core.nodetypes import Mesh, Transform


def create_cpom(plane_shape: Mesh, name: str) -> Tuple[Transform, Transform]:
    # create nodes
    closest_point_node = pc.createNode("closestPointOnMesh", name=f"{name}_cpom")
    in_loc = pc.spaceLocator()
    in_loc.rename(f"{name}_in_loc")
    pos_loc = pc.spaceLocator()
    pos_loc.rename(f"{name}_pos_loc")
    # connect nodes
    in_loc.translate >> closest_point_node.inPosition
    plane_shape.attr("worldMatrix[0]") >> closest_point_node.inputMatrix
    plane_shape.attr("worldMesh[0]") >> closest_point_node.inMesh
    closest_point_node.position >> pos_loc.translate

    return in_loc, pos_loc


def constraint_setup(jointgroup, ik_handle, parent_ctrl, chain_ctrl, in_loc, pos_loc):
    const = pc.pointConstraint(jointgroup, in_loc, maintainOffset=False)
    pc.delete(const)
    pc.parentConstraint(parent_ctrl, in_loc, maintainOffset=True)
    pc.pointConstraint(pos_loc, jointgroup, maintainOffset=False)
    pc.pointConstraint(pos_loc, ik_handle, maintainOffset=False)
    pc.orientConstraint(chain_ctrl, jointgroup)
    pc.orientConstraint(chain_ctrl, ik_handle)


class TextFieldHelper:
    def __init__(self, label, buttonLabel="Set", text="Not set"):
        self.control = pc.textFieldButtonGrp(
            label=label, buttonLabel=buttonLabel, text=text,
            bc=self.set_text
        ) # PEP8
                
    def set_text(self):
        sel = pc.selected()
        if not sel:
            pc.warning("Warning")
            return
        self.control.setText(sel[0].name())
        self.obj = sel[0]


class RestrictedAimHelper:
    def __init__(self):
        self.win_id = "fa_aim_helper_win"
        
        if pc.window(self.win_id, query=True, exists=True):
            pc.deleteUI(self.win_id)
        
        with pc.window(self.win_id, title="Chain Connection Rigger") as win:
            with pc.columnLayout(adj=True):
                self.body_ctrl_tfh = TextFieldHelper("Body Controller: ")
                self.dnt_tfh = TextFieldHelper("DNT Grp: ")
                self.plane_tfh = TextFieldHelper("Plane: ")
                self.chain_ctrl_tfh = TextFieldHelper("Chain Controller: ")
                self.wheel_ctrl_tfh = TextFieldHelper("Wheel Controller: ")
                self.upper_joint_tfh = TextFieldHelper("Upper Joint: ")
                self.lower_joint_tfh = TextFieldHelper("Lower Joint: ")
                pc.text(label="Please select the corresponding components and press OK")
                with pc.horizontalLayout():
                    pc.button(label="Cancel")
                    pc.button(label="OK", c=self.execute)
    
    def execute(self, *args):
        lower_ik = self.upper_joint_tfh.obj.message.listConnections(type="ikHandle")[0]
        upper_in_loc, upper_pos_loc = create_cpom(self.plane_tfh.obj.getShape(), self.upper_joint_tfh.obj.name())
        upper_joint_grp = self.upper_joint_tfh.obj.getParent()
        
        upper_ik = self.lower_joint_tfh.obj.message.listConnections(type="ikHandle")[0]
        lower_in_loc, lower_pos_loc = create_cpom(self.plane_tfh.obj.getShape(), self.lower_joint_tfh.obj.name())
        lower_joint_grp = self.lower_joint_tfh.obj.getParent()
         
        constraint_setup(upper_joint_grp, upper_ik, self.body_ctrl_tfh.obj, self.chain_ctrl_tfh.obj, upper_in_loc, upper_pos_loc)
        constraint_setup(lower_joint_grp, lower_ik, self.wheel_ctrl_tfh.obj, self.chain_ctrl_tfh.obj, lower_in_loc, lower_pos_loc)

        loc_grp = [upper_in_loc, upper_pos_loc, lower_in_loc, lower_pos_loc]
        grp_node = pc.group(loc_grp)
        grp_node.rename(f"{self.upper_joint_tfh.obj.name()}_grp")
        pc.parent(*loc_grp, grp_node)
        pc.parent(grp_node, self.dnt_tfh.obj)


RestrictedAimHelper()