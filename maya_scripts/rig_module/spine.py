import json
from maya_scripts import control
import pymel.core as pm
from maya_scripts.prox_node_setup.generated_nodes import *
from maya_scripts.utilities import (
    create_guide, 
    create_groups,
    create_ik_fk_blend, 
    setup_visibility_controls, 
    setup_ribbon_system, 
    rebuild_nurbsPlane, 
    add_pin_joints, 
    hierarchy_prep,
    TextFieldHelper,
    CompoundFieldSlot
)

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
spine_IK_color = [1, 0.97, 0.66]
spine_FK_color = [0.19, 0.84, 0.62]
com_color = [0, 0.85, 0]

class SpineManager:
    def __init__(self):
        
        self.win_id = "fxs_spine_rigging_win"
        
        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Spine Rigging Module") as win:
            with pm.columnLayout(adj=True):
                self.name = TextFieldHelper("Spine name: ")
                self.bind_jnts = pm.intFieldGrp(label="Amount bind joints: ", numberOfFields=1)
                self.parent_output = TextFieldHelper("Parent Output Group: ")
                self.parent_outputGuide = TextFieldHelper("Parent Output Guide: ")
                self.com_guide_pos = CompoundFieldSlot("COM Position: ")
                self.hip_guide_pos = CompoundFieldSlot("Hip Position: ")
                self.chest_guide_pos = CompoundFieldSlot("Chest Position: ")
                pm.text(label="Please fill out the following fields or select the corresponding components and press: OK")
                
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)


    def execute(self, *args):
        
        name = str(self.name)
        parent_output = str(self.parent_output)
        parent_outputGuide = str(self.parent_outputGuide)

        if pm.intFieldGrp(self.bind_jnts, query=True, value=True) > 0:
            bind_jnts = pm.intFieldGrp(self.bind_jnts, query=True, value=True)
        else:
            print("Not enough bind joints (using 5 instead)")
            bind_jnts = 5

        guide_positions = {
            "com_guide_pos": self.com_guide_pos,
            "hip_guide_pos": self.hip_guide_pos,
            "chest_guide_pos": self.chest_guide_pos,
        }

        resolved_positions = {}

        for attr_name, slot in guide_positions.items():
            values = slot.get_values()
            if all(v is not None and v != 0.0 for v in values):
                resolved_positions[attr_name] = values
            else:
                pm.warning(f"{attr_name} contains nonvalid values")
                resolved_positions[attr_name] = None

        kwargs = {"name": name, "bind_jnts": bind_jnts}
        for attr_name, value in resolved_positions.items():
            if value is not None:
                kwargs[attr_name] = value

        self.module = SpineModule(**kwargs)
        
        try:
            pm.connectAttr(f"{parent_output}.offsetParentMatrix", f"{self.module.out_parent_input}.offsetParentMatrix")
            pm.connectAttr(f"{parent_outputGuide}.offsetParentMatrix", f"{self.module.out_parentGuide_input}.offsetParentMatrix")
        except:
            print("Parent Module connection not possible, manual connection requiered")
        

class SpineModule:
    def __init__(self, name:str = "spine", bind_jnts=10, com_guide_pos:tuple = (0, 14, 0), hip_guide_pos:tuple = (0, 12, 0), 
                 mid_guide_pos:tuple = (0, 0, 0), chest_guide_pos:tuple = (0, 24, 0), settings_guide_pos:tuple = (5, 16, 0)):
        
        self.name = name
        self.groups = create_groups(rig_module_name=self.name)

        self.parent_input = transform(name=f"{self.name}_parent_input")
        self.parentGuide_input = transform(name=f"{self.name}_parentGuide_input")

        com_guide = create_guide(name=f"{self.name}_com_guide", position=com_guide_pos, color=guide_color)
        hip_guide = create_guide(name=f"{self.name}_hip_guide", position=hip_guide_pos, color=guide_color)
        mid_guide = create_guide(name=f"{self.name}_mid_guide", position=mid_guide_pos, color=guide_color)
        chest_guide = create_guide(name=f"{self.name}_chest_guide", position=chest_guide_pos, color=guide_color)

        settings_guide = create_guide(name=f"{self.name}_settings_guide", position=settings_guide_pos, color=guide_color)

        com_ctrl = control.create(ctrl_type="box", name=f"{self.name}_com_ctrl", degree=1, size=[4, 1.5, 3], color=com_color)

        hip_FK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_hip_FK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_FK_color)
        mid_FK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_mid_FK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_FK_color)
        chest_FK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_chest_FK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_FK_color)

        hip_IK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_hip_IK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_IK_color)
        mid_IK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_mid_IK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_IK_color)
        chest_IK_ctrl = control.create(ctrl_type="box", name=f"{self.name}_chest_IK_ctrl", degree=1, size=[4, 0.5, 3], color=spine_IK_color)
        
        hip_tangent_ctrl = control.create_circle_ctrl(name=f"{self.name}_hip_tangent_ctrl", ctrl_size=1, color=guide_color, normal=(0, 1, 0))
        chest_tangent_ctrl = control.create_circle_ctrl(name=f"{self.name}_chest_tangent_ctrl",ctrl_size=1, color=guide_color, normal=(0, 1, 0))

        mid_start_ctrl = control.create(ctrl_type="square", name=f"{self.name}_mid_start_ctrl", normal=(0, 1, 0), color=guide_color)
        mid_end_ctrl = control.create(ctrl_type="square", name=f"{self.name}_mid_end_ctrl", normal=(0, 1, 0), color=guide_color)

        hip_tangent_offset = transform(name=f"{self.name}_hip_tangent_offset")
        chest_tangent_offset = transform(name=f"{self.name}_chest_tangent_offset")

        for ctrl in [hip_IK_ctrl, chest_IK_ctrl]:
            ctrl.node.addAttr(attr="tangent_factor", attributeType="float", minValue=1, defaultValue=1, hidden=False, keyable=True)
            ctrl.node.addAttr(attr="show_tangent", attributeType="bool", defaultValue=0, hidden=False, keyable=True)

        pm.connectAttr(hip_IK_ctrl.node.show_tangent, hip_tangent_ctrl.visibility)
        pm.connectAttr(chest_IK_ctrl.node.show_tangent, chest_tangent_ctrl.visibility)

        com_output = transform(name=f"{self.name}_com_output")
        mid_output = transform(name=f"{self.name}_FK_mid_output")
        
        self.settings_ctrl = control.create(ctrl_type="gear", degree=3, name=f"{self.name}_settings_ctrl", normal=(0, 0, 1), color=com_color)
        self.settings_ctrl.node.addAttr(attr="use_IK", attributeType="float", minValue=0, maxValue=1, defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="ribbon", niceName="RIBBON", attributeType="enum", enumName="----------", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="show_additional_ribbon_ctrl", attributeType="bool", defaultValue=0, hidden=False, keyable=True)
        self.settings_ctrl.node.addAttr(attr="visibility_grps", niceName="VISIBILITY", attributeType="enum", enumName="----------", hidden=False, keyable=True)
        setup_visibility_controls(settings_ctrl=self.settings_ctrl, groups=self.groups)

        pm.setAttr(self.settings_ctrl.node.ribbon, lock=True)
        pm.setAttr(self.settings_ctrl.node.visibility_grps, lock=True)

        mid_guide_WM = blendMatrix(name=f"{self.name}_mid_guide_WM")
        pm.connectAttr(hip_guide.worldMatrix[0], mid_guide_WM.inputMatrix)
        pm.connectAttr(chest_guide.worldMatrix[0], mid_guide_WM.target[0].targetMatrix)
        mid_guide_WM.target[0].weight.set(0.5)
        
        mid_guide_outWM = aimMatrix(name=f"{self.name}_mid_guide_outWM")
        pm.connectAttr(mid_guide.worldMatrix[0], mid_guide_outWM.inputMatrix)
        mid_guide_outWM.primaryInputAxis.set(0, 1, 0)
        pm.connectAttr(chest_guide.worldMatrix[0], mid_guide_outWM.primaryTargetMatrix)

        pm.connectAttr(mid_guide_WM.outputMatrix, mid_guide.offsetParentMatrix)

        mid_IK_pom = multMatrix(name=f"{self.name}_mid_IK_pom")
        pm.connectAttr(mid_guide_outWM.outputMatrix, mid_IK_pom.matrixIn[0])
        pm.connectAttr(self.parentGuide_input.worldInverseMatrix[0], mid_IK_pom.matrixIn[1])

        mid_IK_baseWM = multMatrix(name=f"{self.name}_mid_IK_baseWM")
        pm.connectAttr(mid_IK_pom.matrixSum, mid_IK_baseWM.matrixIn[0])
        pm.connectAttr(self.parent_input.worldMatrix[0], mid_IK_baseWM.matrixIn[1])

        chest_guide_outWM = blendMatrix(name=f"{self.name}_chest_guide_outWM")
        pm.connectAttr(mid_guide.worldMatrix[0], chest_guide_outWM.inputMatrix)
        pm.connectAttr(chest_guide.worldMatrix[0], chest_guide_outWM.target[0].targetMatrix)
        for attr in ["scaleWeight", "rotateWeight", "shearWeight"]:
            pm.setAttr(f"{chest_guide_outWM.target[0]}.{attr}", 0)

        hierarchies = {
            "com_hierarchy": {
                "name": "com",
                "guide": com_guide.worldMatrix[0],
                "parent": self.parent_input.offsetParentMatrix,
                "parentGuide": self.parentGuide_input.worldInverseMatrix[0]
            },
            "hip_FK_hierarchy": {
                "name": "hip_FK",
                "guide": hip_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0]
            },
            "mid_FK_hierarchy": {
                "name": "mid_FK",
                "guide":mid_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0]
            },
            "chest_FK_hierarchy": {
                "name": "chest_FK",
                "guide": chest_guide_outWM.outputMatrix,
                "parent": mid_FK_ctrl.worldMatrix[0],
                "parentGuide": mid_guide.worldInverseMatrix[0]
            },
            "hip_IK_hierarchy": {
                "name": "hip_IK",
                "guide": hip_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0]
            },
            "chest_IK_hierarchy": {
                "name": "chest_IK",
                "guide": chest_guide_outWM.outputMatrix,
                "parent": com_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0]
            }
        }

        all_hierarchies = {}

        for key, item in hierarchies.items():
            main_hierarchy = hierarchy_prep(module_name=self.name, name=item["name"], guide=item["guide"], parent=item["parent"], parentGuide=item["parentGuide"])
            pm.connectAttr(f"{main_hierarchy['wm'].node}.matrixSum", f"{self.name}_{item['name']}_ctrl.offsetParentMatrix")

            all_hierarchies[item["name"]] = main_hierarchy

        settings_ctrl_hierarchy = hierarchy_prep(module_name=self.name, name="settings", guide=settings_guide.worldMatrix[0], 
                                                       parent=com_ctrl.worldMatrix[0], parentGuide=com_guide.worldInverseMatrix[0])
        
        pm.connectAttr(settings_ctrl_hierarchy["wm"].matrixSum, self.settings_ctrl.offsetParentMatrix)

        mid_IK_tempWM = blendMatrix(name=f"{self.name}_mid_IK_tempWM")
        pm.connectAttr(mid_IK_baseWM.matrixSum, mid_IK_tempWM.inputMatrix)
        pm.connectAttr(hip_IK_ctrl.worldMatrix[0], mid_IK_tempWM.target[0].targetMatrix)
        pm.connectAttr(chest_IK_ctrl.worldMatrix[0], mid_IK_tempWM.target[1].targetMatrix)
        mid_IK_tempWM.target[1].weight.set(0.5)

        mid_IK_WM = multMatrix(name=f"{self.name}_mid_IK_WM")
        pm.connectAttr(mid_guide.xformMatrix, mid_IK_WM.matrixIn[0])
        pm.connectAttr(mid_IK_tempWM.outputMatrix, mid_IK_WM.matrixIn[1])

        pm.connectAttr(mid_IK_WM.matrixSum, mid_IK_ctrl.offsetParentMatrix)

        hip_localMatrix = create_ik_fk_blend(
            module_name=self.name,
            blend_name=f"{self.name}_hip_localMatrix",
            fk_source=hip_FK_ctrl.worldMatrix[0],
            ik_source=hip_IK_ctrl.worldMatrix[0],
            blend_attr=self.settings_ctrl.node.use_IK
        )

        mid_localMatrix = create_ik_fk_blend(
            module_name=self.name,
            blend_name=f"{self.name}_mid_localMatrix",
            fk_source=mid_FK_ctrl.worldMatrix[0],
            ik_source=mid_IK_ctrl.worldMatrix[0],
            blend_attr=self.settings_ctrl.node.use_IK
        )

        chest_localMatrix = create_ik_fk_blend(
            module_name=self.name,
            blend_name=f"{self.name}_chest_localMatrix",
            fk_source=chest_FK_ctrl.worldMatrix[0],
            ik_source=chest_IK_ctrl.worldMatrix[0],
            blend_attr=self.settings_ctrl.node.use_IK
        )

        chest_WM = multMatrix(name=f"{self.name}_chest_WM")
        pm.connectAttr(chest_localMatrix.outputMatrix, chest_WM.matrixIn[0])
        pm.connectAttr(mid_localMatrix.outputMatrix, chest_WM.matrixIn[1])

        com_ctrl.worldMatrix[0] >> com_output.offsetParentMatrix
        mid_localMatrix.outputMatrix >> mid_output.offsetParentMatrix

        self.hip_output = transform(f"{self.name}_hip_output")
        hip_localMatrix.outputMatrix >> self.hip_output.offsetParentMatrix
        self.hipGuide_output = transform(f"{self.name}_hipGuide_output")
        hip_guide.worldMatrix[0] >> self.hipGuide_output.offsetParentMatrix
        self.chest_output = transform(f"{self.name}_chest_output")
        chest_localMatrix.outputMatrix >> self.chest_output.offsetParentMatrix
        self.chestGuide_output = transform(f"{self.name}_chestGuide_output")
        chest_guide.worldMatrix[0] >> self.chestGuide_output.offsetParentMatrix

        pm.connectAttr(hip_localMatrix.outputMatrix, hip_tangent_offset.offsetParentMatrix)
        pm.connectAttr(chest_localMatrix.outputMatrix, chest_tangent_offset.offsetParentMatrix)

        chest_tangent_negate = negate(name=f"{self.name}_chest_tangent_negate")
        pm.connectAttr(chest_IK_ctrl.node.tangent_factor, chest_tangent_negate.input_)

        pm.connectAttr(hip_IK_ctrl.node.tangent_factor, hip_tangent_offset.translateY)
        pm.connectAttr(chest_tangent_negate.output, chest_tangent_offset.translateY)
        pm.connectAttr(hip_tangent_offset.worldMatrix[0], hip_tangent_ctrl.offsetParentMatrix)
        pm.connectAttr(chest_tangent_offset.worldMatrix[0], chest_tangent_ctrl.offsetParentMatrix)

        mid_start_point = blendMatrix(name=f"{self.name}_mid_start_point")
        pm.connectAttr(hip_localMatrix.outputMatrix, mid_start_point.inputMatrix)
        pm.connectAttr(mid_localMatrix.outputMatrix, mid_start_point.target[0].targetMatrix)
        mid_start_point.target[0].weight.set(0.5)

        mid_start_aim = aimMatrix(name=f"{self.name}_mid_start_aim")
        pm.connectAttr(mid_start_point.outputMatrix, mid_start_aim.inputMatrix)
        pm.connectAttr(mid_localMatrix.outputMatrix, mid_start_aim.primaryTargetMatrix)
        mid_start_aim.primaryMode.set(2)

        mid_end_point = blendMatrix(name=f"{self.name}_mid_end_point")
        pm.connectAttr(mid_localMatrix.outputMatrix, mid_end_point.inputMatrix)
        pm.connectAttr(chest_localMatrix.outputMatrix, mid_end_point.target[0].targetMatrix)
        mid_end_point.target[0].weight.set(0.5)

        mid_end_aim = aimMatrix(name=f"{self.name}_mid_end_aim")
        pm.connectAttr(mid_end_point.outputMatrix, mid_end_aim.inputMatrix)
        pm.connectAttr(chest_localMatrix.outputMatrix, mid_end_aim.primaryTargetMatrix)
        pm.connectAttr(mid_end_point.outputMatrix, mid_end_aim.secondaryTargetMatrix)
        mid_end_aim.primaryMode.set(2)

        pm.connectAttr(mid_start_aim.outputMatrix, mid_start_ctrl.offsetParentMatrix)
        pm.connectAttr(mid_end_aim.outputMatrix, mid_end_ctrl.offsetParentMatrix)

        for roundness_ctrl in [mid_start_ctrl, mid_end_ctrl]:
            pm.connectAttr(self.settings_ctrl.node.show_additional_ribbon_ctrl, roundness_ctrl.visibility)

        curve_dict = setup_ribbon_system(
            module_name=self.name,
            groups=self.groups,
            hip_ctrl=hip_localMatrix.outputMatrix,
            hip_tangent=hip_tangent_ctrl.worldMatrix[0],
            mid_start=mid_start_ctrl.worldMatrix[0],
            mid_ctrl=mid_localMatrix.outputMatrix,
            mid_end=mid_end_ctrl.worldMatrix[0],
            chest_tangent=chest_tangent_ctrl.worldMatrix[0],
            chest_ctrl=chest_localMatrix.outputMatrix
        )

        upper_bezier_curve = curve_dict["top_curve"]
        middle_bezier_curve = curve_dict["middle_curve"]
        down_bezier_curve = curve_dict["down_curve"]

        upper_bezier_curveShape = upper_bezier_curve.node.getShape()
        middle_bezier_curveShape = middle_bezier_curve.node.getShape()
        down_bezier_curveShape = down_bezier_curve.node.getShape()

        ribbon_loft = loft(name=f"{self.name}_ribbon_loft")
        pm.connectAttr(upper_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[0])
        pm.connectAttr(middle_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[1])
        pm.connectAttr(down_bezier_curveShape.worldSpace[0], ribbon_loft.inputCurve[2])
        ribbon_loft.uniform.set(1)
        ribbon_loft.autoReverse.set(1)
        ribbon_loft.degree.set(3)
        ribbon_loft.sectionSpans.set(1)
        ribbon_loft.reverseSurfaceNormals.set(True)

        old_ribbon = pm.nurbsPlane(name=f"{self.name}_old_ribbon")[0]
        old_ribbonShape = old_ribbon.getShape()

        pm.connectAttr(ribbon_loft.outputSurface, old_ribbonShape.create, force=True)

        ribbon, ribbonShape = rebuild_nurbsPlane(
            module_name=self.name,
            input_plane=old_ribbonShape, 
            spans_U=60, 
            spans_V=4, 
            degree_U=1, 
            degree_V=3)
        
        ribbon_pin_grp = transform(name=f"{self.name}_ribbon_pin_grp")
        ribbon_joints_grp = transform(name=f"{self.name}_ribbon_joints_grp")

        ribbon_pins, ribbon_joints = add_pin_joints(module_name=self.name, name="ribbon", ribbon=ribbon, number_of_pins=self.bind_jnts, scale_parent=com_ctrl.worldMatrix[0])
        
        for pin, jnt in zip(ribbon_pins, ribbon_joints):
            pm.parent(pin, ribbon_pin_grp.node)
            pm.parent(jnt.node, ribbon_joints_grp.node)

        order = {
            "inputs": [self.parent_input, self.parentGuide_input],
            "controls": [com_ctrl, hip_IK_ctrl, chest_IK_ctrl, mid_IK_ctrl, self.settings_ctrl, hip_FK_ctrl, mid_FK_ctrl, chest_FK_ctrl, hip_tangent_ctrl, chest_tangent_ctrl, mid_start_ctrl, mid_end_ctrl],
            "guides": [com_guide, hip_guide, chest_guide, mid_guide, settings_guide],
            "joints": [ribbon_joints_grp],
            "rigNodes": [ribbon_pin_grp, hip_tangent_offset, chest_tangent_offset, ribbon, upper_bezier_curve, middle_bezier_curve, down_bezier_curve],
            "outputs": [self.hip_output, self.hipGuide_output, self.chest_output, self.chestGuide_output, com_output, mid_output]
        }

        for key, items in order.items():
            for item in items:
                try:
                    pm.parent(item.node, self.groups[key].node)
                except:
                    pm.parent(item, self.groups[key].node)

        visibility_neg = subtract(name=f"{self.name}visibility_neg")
        visibility_neg.input1.set(1)
        pm.connectAttr(self.settings_ctrl.node.use_IK, visibility_neg.input2)

        for FK_c in [hip_FK_ctrl, mid_FK_ctrl, chest_FK_ctrl]:
            pm.connectAttr(visibility_neg.output, FK_c.visibility)

        for IK_c in [hip_IK_ctrl, mid_IK_ctrl, chest_IK_ctrl]:
            pm.connectAttr(self.settings_ctrl.node.use_IK, IK_c.visibility)

    @property
    def rig_module(self):
        return self.groups
    
    @property
    def module_name(self):
        return str(self.groups)
    
    @property
    def out_parent_input(self):
        return self.parent_input

    @property
    def out_parentGuide_input(self):
        return self.parentGuide_input
    
    @property
    def out_chest_output(self):
        return self.chest_output

    @property
    def out_chestGuide_output(self):
        return self.chestGuide_output

    @property
    def out_hip_output(self):
        return self.hip_output

    @property
    def out_hipGuide_output(self):
        return self.hipGuide_output