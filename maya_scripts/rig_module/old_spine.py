import json
import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from utilities import create_guide, colorize, create_groups, add_pins_to_ribbon, add_pins_to_ribbon_uv, create_groups_

guide_color = [1, 1, 1]
pin_color = [1, 1, 0.26]
limb_connection_color = [0, 0, 0]
spine_color = [1, 0.97, 0.66]
com_color = [0, 0.85, 0]

class Spine:
    def __init__(
            self, name:str, com_guide_pos:tuple = (0, 0, 0), hip_guide_pos:tuple = (0, 0, 0), 
            mid_guide_pos:tuple = (0, 0, 0), chest_guide_pos:tuple = (0, 0, 0), settings_guide_pos:tuple = (0, 0, 0)
    ):
        
        self.name = name
        self.groups = create_groups(rig_module_name=self.name)

        self.parent_input = transform(name=f"{self.name}_parent_input")
        self.parentGuide_input = transform(name=f"{self.name}_parentGuide_input")

        com_guide = create_guide(name=f"{self.name}_com_guide", position=com_guide_pos, color=guide_color)
        hip_guide = create_guide(name=f"{self.name}_hip_guide", position=hip_guide_pos, color=guide_color)
        mid_guide = create_guide(name=f"{self.name}_mid_guide", position=mid_guide_pos, color=guide_color)
        chest_guide = create_guide(name=f"{self.name}_chest_guide", position=chest_guide_pos, color=guide_color)

        com_temp_guide = create_guide(name=f"{self.name}_com_temp_guide", position=com_guide_pos, color=guide_color)
        hip_temp_guide = create_guide(name=f"{self.name}_hip_temp_guide", position=hip_guide_pos, color=guide_color)
        mid_temp_guide = create_guide(name=f"{self.name}_mid_guide", position=mid_guide_pos, color=guide_color)
        chest_temp_guide = create_guide(name=f"{self.name}_chest_temp_guide", position=chest_guide_pos, color=guide_color)

        settings_guide = create_guide(name=f"{self.name}_settings_guide", position=settings_guide_pos, color=guide_color)

        hidden_guides = transform(name=f"{self.name}_hidden_guides")

        for g in [com_temp_guide, hip_temp_guide, mid_temp_guide, chest_temp_guide]:
            g.visibility.set(0)
            pm.parent(g.node, hidden_guides.node)

        com_ctrl = control.create(ctrl_type="box", name=f"{self.name}_com_ctrl", degree=1, size=[4, 1.5, 3], color=com_color)

        FK_hip_ctrl = control.create(ctrl_type="box", name=f"{self.name}_FK_hip_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)
        FK_mid_ctrl = control.create(ctrl_type="box", name=f"{self.name}_FK_mid_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)
        FK_chest_ctrl = control.create(ctrl_type="box", name=f"{self.name}_FK_chest_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)

        IK_hip_ctrl = control.create(ctrl_type="box", name=f"{self.name}_IK_hip_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)
        IK_mid_ctrl = control.create(ctrl_type="box", name=f"{self.name}_IK_mid_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)
        IK_chest_ctrl = control.create(ctrl_type="box", name=f"{self.name}_IK_chest_ctrl", degree=1, size=[4, 0.5, 3], color=spine_color)
        
        hip_tangent_ctrl = control.create_circle_ctrl(name=f"{self.name}_hip_tangent_ctrl", ctrl_size=1, color=spine_color)
        chest_tangent_ctrl = control.create_circle_ctrl(name=f"{self.name}_chest_tangent_ctrl",ctrl_size=1, color=spine_color)

        hip_tangent_offset = transform(name=f"{self.name}_hip_tangent_offset")
        chest_tangent_offset = transform(name=f"{self.name}_chest_tangent_offset")

        for ctrl in [IK_hip_ctrl, IK_chest_ctrl]:
            ctrl.node.addAttr(attr="tangent_factor", attributeType="float", minValue=1, defaultValue=1, hidden=False, keyable=True)
            ctrl.node.addAttr(attr="show_tangent", attributeType="bool", defaultValue=0, hidden=False, keyable=True)

        pm.connectAttr(IK_hip_ctrl.node.show_tangent, hip_tangent_ctrl.visibility)
        pm.connectAttr(IK_chest_ctrl.node.show_tangent, chest_tangent_ctrl.visibility)

        com_output = transform(name=f"{self.name}_com_output")
        mid_output = transform(name=f"{self.name}_FK_mid_output")
        
        settings_ctrl = control.create(ctrl_type="gear", degree=3, name=f"{self.name}_settings_ctrl", normal=(0, 0, 1), color=com_color)
        settings_ctrl.node.addAttr(attr="use_IK", attributeType="float", minValue=0, maxValue=1, defaultValue=0, hidden=False, keyable=True)

        """mid_IK_ctrl_WM = blendMatrix(name=f"{self.name}_mid_guide_WM")
        pm.connectAttr(IK_hip_ctrl.worldMatrix[0], mid_IK_ctrl_WM.inputMatrix)
        pm.connectAttr(IK_chest_ctrl.worldMatrix[0], mid_IK_ctrl_WM.target[0].targetMatrix)
        mid_IK_ctrl_WM.target[0].weight.set(0.5)

        pm.connectAttr(mid_IK_ctrl_WM.outputMatrix, mid_temp_guide.offsetParentMatrix)"""

        hierarchies = {
            "com_hierarchy": {
                "name": "com",
                "guide": com_guide.worldMatrix[0],
                "temp_guide": com_temp_guide.worldMatrix[0],
                "parent": self.parent_input.offsetParentMatrix,
                "temp_parent": com_ctrl.worldMatrix[0],
                "parentGuide": self.parentGuide_input.worldInverseMatrix[0],
                "temp_parentGuide": com_guide.worldInverseMatrix[0]
            },
            "hip_FK_hierarchy": {
                "name": "FK_hip",
                "guide": hip_guide.worldMatrix[0],
                "temp_guide": hip_temp_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "temp_parent": FK_hip_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0],
                "temp_parentGuide": hip_guide.worldInverseMatrix[0]
            },
            "mid_FK_hierarchy": {
                "name": "FK_mid",
                "guide": mid_guide.worldMatrix[0],
                "temp_guide": mid_temp_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "temp_parent": FK_mid_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0],
                "temp_parentGuide": mid_guide.worldInverseMatrix[0]
            },
            "chest_FK_hierarchy": {
                "name": "FK_chest",
                "guide": chest_guide.worldMatrix[0],
                "temp_guide": chest_temp_guide.worldMatrix[0],
                "parent": FK_mid_ctrl.worldMatrix[0],
                "temp_parent": FK_chest_ctrl.worldMatrix[0], 
                "parentGuide": mid_guide.worldInverseMatrix[0],
                "temp_parentGuide": chest_guide.worldInverseMatrix[0]
            },
            "hip_IK_hierarchy":{
                "name": "IK_hip",
                "guide": hip_guide.worldMatrix[0],
                "temp_guide": hip_temp_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "temp_parent": IK_hip_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0],
                "temp_parentGuide": hip_guide.worldInverseMatrix[0]
            },
            "chest_IK_hierarchy": {
                "name": "IK_chest",
                "guide": chest_guide.worldMatrix[0],
                "temp_guide": chest_temp_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "temp_parent": IK_chest_ctrl.worldMatrix[0], 
                "parentGuide": com_guide.worldInverseMatrix[0],
                "temp_parentGuide": chest_guide.worldInverseMatrix[0]
            },
            "mid_IK_hierarchy": {
                "name": "IK_mid",
                "guide": mid_guide.worldMatrix[0],
                "temp_guide": mid_temp_guide.worldMatrix[0],
                "parent": com_ctrl.worldMatrix[0],
                "temp_parent": IK_mid_ctrl.worldMatrix[0],
                "parentGuide": com_guide.worldInverseMatrix[0],
                "temp_parentGuide": mid_guide.worldInverseMatrix[0]
            },
        }

        temp_WM_dict = {}

        for key, item in hierarchies.items():
            main_hierarchy = self._hierarchy_prep(name=item["name"], guide=item["guide"], parent=item["parent"], parentGuide=item["parentGuide"])
            pm.connectAttr(f"{main_hierarchy['wm'].node}.matrixSum", f"{self.name}_{item['name']}_ctrl.offsetParentMatrix")

            sub_name = f"{item['name']}_temp"

            sub_hierarchy = self._hierarchy_prep(name=sub_name, guide=item["temp_guide"], parent=item["temp_parent"], parentGuide=item["temp_parentGuide"])

            temp_WM_dict[f"{sub_name}_WM"] = sub_hierarchy["wm"]

        settings_ctrl_hierarchy = self._hierarchy_prep(name="settings", guide=settings_guide.worldMatrix[0], 
                                                       parent=temp_WM_dict["com_temp_WM"].matrixSum, parentGuide=com_guide.worldInverseMatrix[0])
        
        pm.connectAttr(settings_ctrl_hierarchy["wm"].matrixSum, settings_ctrl.offsetParentMatrix)

        hip_localMatrix = blendMatrix(name=f"{self.name}_hip_localMatrix")
        pm.connectAttr(temp_WM_dict["FK_hip_temp_WM"].matrixSum, hip_localMatrix.inputMatrix)
        pm.connectAttr(temp_WM_dict["IK_hip_temp_WM"].matrixSum, hip_localMatrix.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.use_IK, hip_localMatrix.target[0].weight)

        mid_localMatrix = blendMatrix(name=f"{self.name}_mid_localMatrix")
        pm.connectAttr(temp_WM_dict["FK_mid_temp_WM"].matrixSum, mid_localMatrix.inputMatrix)
        pm.connectAttr(temp_WM_dict["IK_mid_temp_WM"].matrixSum, mid_localMatrix.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.use_IK, mid_localMatrix.target[0].weight)

        chest_localMatrix = blendMatrix(name=f"{self.name}_chest_localMatrix")
        pm.connectAttr(temp_WM_dict["FK_chest_temp_WM"].matrixSum, chest_localMatrix.inputMatrix)
        pm.connectAttr(temp_WM_dict["IK_chest_temp_WM"].matrixSum, chest_localMatrix.target[0].targetMatrix)
        pm.connectAttr(settings_ctrl.node.use_IK, chest_localMatrix.target[0].weight)

        chest_WM = multMatrix(name=f"{self.name}_chest_WM")
        pm.connectAttr(chest_localMatrix.outputMatrix, chest_WM.matrixIn[0])
        pm.connectAttr(mid_localMatrix.outputMatrix, chest_WM.matrixIn[1])


        hip_output = transform(f"{self.name}_hip_output")
        hip_localMatrix.outputMatrix >> hip_output.offsetParentMatrix
        hipGuide_output = transform(f"{self.name}_hipGuide_output")
        hip_guide.worldMatrix[0] >> hipGuide_output.offsetParentMatrix
        chest_output = transform(f"{self.name}_chest_output")
        chest_localMatrix.outputMatrix >> chest_output.offsetParentMatrix
        chestGuide_output = transform(f"{self.name}_chestGuide_output")
        chest_guide.worldMatrix[0] >> chestGuide_output.offsetParentMatrix


        pm.connectAttr(hip_localMatrix.outputMatrix, hip_tangent_offset.offsetParentMatrix)
        pm.connectAttr(chest_localMatrix.outputMatrix, chest_tangent_offset.offsetParentMatrix)

        chest_tangent_negate = negate(name=f"{self.name}_chest_tangent_negate")
        pm.connectAttr(IK_chest_ctrl.node.tangent_factor, chest_tangent_negate.input_)

        pm.connectAttr(IK_hip_ctrl.node.tangent_factor, hip_tangent_offset.translateY)
        pm.connectAttr(chest_tangent_negate.output, chest_tangent_offset.translateY)
        pm.connectAttr(hip_tangent_offset.worldMatrix[0], hip_tangent_ctrl.offsetParentMatrix)
        pm.connectAttr(chest_tangent_offset.worldMatrix[0], chest_tangent_ctrl.offsetParentMatrix)


        curve_dict = self._setup_ribbon_system(
            hip_ctrl=hip_localMatrix.outputMatrix,
            hip_tangent=hip_tangent_ctrl.worldMatrix[0],
            mid_ctrl=mid_localMatrix.outputMatrix,
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

        for crv in [upper_bezier_curve, middle_bezier_curve, down_bezier_curve]:
            crv.visibility.set(0)

        old_ribbon = pm.nurbsPlane(name=f"{self.name}_old_ribbon")[0]
        old_ribbonShape = old_ribbon.getShape()

        pm.connectAttr(ribbon_loft.outputSurface, old_ribbonShape.create, force=True)

        ribbon, ribbonShape = self._rebuild_nurbsPlane(input_plane=old_ribbonShape, spans_U=20, spans_V=4, degree_U=1, degree_V=3)
        
        ribbon_pin_grp = transform(name=f"{self.name}_ribbon_pin_grp")

        ribbon_pins = self._add_pin_joints(name="ribbon", ribbon=ribbon, number_of_pins=10)
        for pin in ribbon_pins:
            pm.parent(pin, ribbon_pin_grp.node)

        for thing in [ribbon_pin_grp, hip_tangent_offset, chest_tangent_offset, ribbon, upper_bezier_curve, middle_bezier_curve, down_bezier_curve]:
            try:
                pm.parent(thing.node, self.groups["rigNodes"].node)
            except:
                pm.parent(thing, self.groups["rigNodes"].node)

        order = {
            "inputs": [self.parent_input, self.parentGuide_input],
            "controls": [com_ctrl, IK_hip_ctrl, IK_chest_ctrl, IK_mid_ctrl, settings_ctrl, FK_hip_ctrl, FK_mid_ctrl, FK_chest_ctrl, hip_tangent_ctrl, chest_tangent_ctrl],
            "guides": [com_guide, hip_guide, chest_guide, mid_guide, hidden_guides, settings_guide],
            "outputs": [hip_output, hipGuide_output, chest_output, chestGuide_output, com_output, hip_output, chest_output, mid_output]
        }

        for key, items in order.items():
            for item in items:
                pm.parent(item.node, self.groups[key].node)

        visibility_neg = subtract(name=f"{self.name}visibility_neg")
        visibility_neg.input1.set(1)
        pm.connectAttr(settings_ctrl.node.use_IK, visibility_neg.input2)

        for FK_c in [FK_hip_ctrl, FK_mid_ctrl, FK_chest_ctrl]:
            pm.connectAttr(visibility_neg.output, FK_c.visibility)

        for IK_c in [IK_hip_ctrl, IK_mid_ctrl, IK_chest_ctrl]:
            pm.connectAttr(settings_ctrl.node.use_IK, IK_c.visibility)

    def _create_pom(self, name:str, source_matrix, parentGuide_input):
        """Creates a multMatrix node as a Parent ofset matrix."""
        pom = multMatrix(name=f"{self.name}_{name}_POM")
        pm.connectAttr(source_matrix, pom.matrixIn[0])
        pm.connectAttr(parentGuide_input, pom.matrixIn[1])
        return pom

    def _lock_ctrl_attrs(self, ctrl, attrs_to_lock):
        for attr in attrs_to_lock:
            pm.setAttr(f"{ctrl.node}.{attr}", lock=True)
            pm.setAttr(f"{ctrl.node}.{attr}", keyable=False)
            pm.setAttr(f"{ctrl.node}.{attr}", channelBox=False)

    def _hierarchy_prep(self, name, guide, parent, parentGuide):
        outputs = {}
        outputs["pom"] = self._create_pom(name=name, source_matrix=guide, parentGuide_input=parentGuide)
        outputs["wm"] = multMatrix(name=f"{self.name}_{name}_WM")
        outputs["pom"].matrixSum >> outputs["wm"].matrixIn[0]
        pm.connectAttr(parent, outputs["wm"].matrixIn[1])
        return outputs
    
    def _get_local_ribbon_pin_position(self, pos_name):
        positions = {"top": (0, 0, 0.5), "middle": (0, 0, 0), "down": (0, 0, -0.5)}
        return positions.get(pos_name, (0, 0, 0))

    def _setup_ribbon_system(self, hip_ctrl, hip_tangent, mid_ctrl, chest_tangent, chest_ctrl):
        pin_grp = transform(name=f"{self.name}_nurbsPin_grp")
        sections = {
            "hip": {"parent_matrix": hip_ctrl},
            "hip_tangent": {"parent_matrix": hip_tangent},
            "mid": {"parent_matrix": mid_ctrl},
            "chest_tangent": {"parent_matrix": chest_tangent},
            "chest": {"parent_matrix": chest_ctrl}
        }
        curve_points = {'top': [], 'middle': [], 'down': []}

        for section_name, config in sections.items():
            for height in ["top", "middle", "down"]:
                pin = create_guide(name=f"{self.name}_{section_name}_{height}_ribbon_pin", color=pin_color, position=self._get_local_ribbon_pin_position(height))

                tfm = translationFromMatrix(name=f"{self.name}_{section_name}_{height}_ribbon_pin_tFM")
                pm.connectAttr(pin.worldMatrix[0], tfm.input_)
                pm.connectAttr(config["parent_matrix"], pin.offsetParentMatrix)
                pm.parent(pin.node, pin_grp.node)
                pm.parent(pin_grp.node, self.groups["rigNodes"].node)
                pin_grp.visibility.set(0)
                curve_points[height].append(tfm)

        return self._create_bezier_curves(curve_points)

    def _create_bezier_curves(self, curve_points:dict):

        ribbon_curves = {}

        for crv, points in curve_points.items():
            input_nodes = []
            positions = []
            for index, p in enumerate(points):
                if index == 0 or index == len(points) - 1:
                    input_nodes.append(p)
                    input_nodes.append(p)
                    positions.append(pm.getAttr(p.node.output))
                    positions.append(pm.getAttr(p.node.output))
                else:
                    input_nodes.append(p)
                    positions.append(pm.getAttr(p.node.output))
            
            temp_bezier_curve = pm.curve(point=positions, bezier=True, name=f"temp_{crv}_curve")
            ribbon_curves[f"{crv}_curve"] = transform(name=f"{self.name}_{crv}_bezier_curve")
            shapes = pm.listRelatives(temp_bezier_curve, shapes=True, fullPath=True)
            pm.parent(shapes, ribbon_curves[f"{crv}_curve"].node, add=True, shape=True)
            pm.delete(temp_bezier_curve)

            for index, node in enumerate(input_nodes):
                pm.connectAttr(node.output, ribbon_curves[f"{crv}_curve"].node.controlPoints[index])          

        return ribbon_curves

    def _rebuild_nurbsPlane(self, input_plane, spans_U:int, spans_V:int, degree_U, degree_V):
        rebSurface = rebuildSurface(name=f"{self.name}_{input_plane.getName()}_rebuildSurface")
        pm.connectAttr(input_plane.worldSpace[0], rebSurface.inputSurface)
        rebSurface.spansU.set(spans_U)
        rebSurface.spansV.set(spans_V)
        rebSurface.degreeU.set(degree_U)
        rebSurface.degreeV.set(degree_V)

        pm.rename(input_plane, newname=f"{self.name}_oldRibbon")

        input_plane.visibility.set(0)
        newPlane = pm.nurbsPlane(name=f"{self.name}_newRibbon")[0]
        newPlaneShape = newPlane.getShape()
        pm.connectAttr(rebSurface.outputSurface, newPlaneShape.create, force=True)

        newPlane.overrideEnabled.set(1)
        newPlane.overrideDisplayType.set(1)

        return newPlane, newPlaneShape
    
    def _add_pin_joints(self, name, ribbon, number_of_pins):
            jnt_list = []

            pin_list = add_pins_to_ribbon_uv(f"{self.name}", ribbon, number_of_pins)

            for index, pin in enumerate(pin_list):
                jnt = joint(name=f"{name}_{index}_bnd_jnt")
                pm.makeIdentity(jnt.node, apply=True, t=0, r=1, s=0, n=0, pn=True)
                pm.parent(jnt.node, pin)
                pm.xform(jnt.node, translation=(0, 0, 0))
                jnt_list.append(jnt)

            return pin_list

"""a = Spine(name="spine", com_guide_pos=(0, 2, 0), hip_guide_pos=(0, 0, 0), 
          mid_guide_pos=(0, 8, 0), chest_guide_pos=(0, 16, 0), settings_guide_pos=(6, 0, 0))"""