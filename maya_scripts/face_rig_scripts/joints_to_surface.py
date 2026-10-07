import maya.api.OpenMaya as om2
import pymel.core as pm
import numpy as np


def add_pin_joints(name:str, ribbon, number_of_pins):

	jnt_list = []

	pin_list = add_pins_to_ribbon_uv(
		name=name,
		ribbon_shape=ribbon.getShape(),
		number_of_pins=number_of_pins
	)

	for index, pin in enumerate(pin_list):
		jnt = pm.createNode("joint", name=f"{name}_{index}_bind_jnt")
		pm.makeIdentity(jnt, apply=True, t=0, r=1, s=0, n=0, pn=True)
		pm.xform(jnt, translation=(0, 0, 0))

		pin.worldMatrix[0] >> jnt.offsetParentMatrix
		jnt_list.append(jnt)

	return pin_list, jnt_list


def add_pins_to_ribbon_uv(name:str, ribbon_shape, number_of_pins):

	pin_list = []

	uv_pin = pm.createNode("uvPin", name=f"{name}_uvPin")
	ribbon_shape.worldSpace[0] >> uv_pin.originalGeometry
	ribbon_shape.worldSpace[0] >> uv_pin.deformedGeometry

	for i in range(number_of_pins):

		u_pos = (i/float(number_of_pins-1))
		v_pos = 0.5

		name_suf = str(i)

		pin_name = f"{name}_pin_{name_suf}"
		pin_locator = pm.spaceLocator(name=pin_name)
		pin_locatorShape = pin_locator.getShape()

		pin_locatorShape.addAttr("parameterU", at="double", keyable=True, dv=u_pos)
		pin_locatorShape.addAttr("parameterV", at="double", keyable=True, dv=v_pos)

		pin_locatorShape.parameterU.set(u_pos)
		pin_locatorShape.parameterV.set(v_pos)

		pin_locatorShape.parameterU >> uv_pin.coordinate[i].coordinateU
		pin_locatorShape.parameterV >> uv_pin.coordinate[i].coordinateV

		uv_pin.outputMatrix[i] >> pin_locator.offsetParentMatrix

		pin_list.append(pm.PyNode(pin_name))

	return pin_list


def get_dag_path(object_name):
	if isinstance(object_name, list):
		o_node_list=[]

		for o in object_name:
			selection_list = om2.MSelectionList()
			selection_list.add(o)
			o_node = selection_list.getDagPath(0)
			o_node_list.append(o_node)
		return o_node_list

	else:
		selection_list = om2.MSelectionList()
		selection_list.add(object_name)
		o_node = selection_list.getDagPath(0)
		return o_node


class TextFieldHelper:
	def __init__(self, label, buttonLabel="Set", text="Not set"):
		self.control = pm.textFieldButtonGrp(
			label=label, buttonLabel=buttonLabel, text=text,
			bc=self.set_text
		) # PEP8
				
	def set_text(self):
		sel = pm.selected()
		if not sel:
			pm.warning("Warning")
			return
		self.control.setText(sel[0].name())
		self.obj = sel[0]


class JointsToSurfaceFromEdge:
	

	"""
	Takes either an egde or a curve, duplicates it twice and lofts a nurbs surface out of them
	"""

	def __init__(self):
		self.win_id = "fxs_joints_to_surface_from_edge"

		if pm.window(self.win_id, query=True, exists=True):
			pm.deleteUI(self.win_id)

		with pm.window(self.win_id, title="Joints to Curve from Edge"):
			with pm.columnLayout(adj=True):
				pm.text(
					label="This tool will take either edges or a curve/curves as input" \
					"and create a nurbssurface. It will the place joints on said nurbssurface"
				)
				self.prefix = TextFieldHelper("Type or select Prefix: ")
				self.num_pins = pm.intFieldGrp(label="Amount Joints: ", numberOfFields=1)

				pm.text(label="Select the desired edge before launching the tool")
				with pm.horizontalLayout():
					pm.button(label="Cancel")
					pm.button(label="OK", command=self.execute)


	def execute(self, *args):

		sel = pm.ls(selection=1)
		prefix = self.prefix.control.getText()

		num_pins = pm.intFieldGrp(self.num_pins, query=True, value1=True)


		#check if selection is edge
		if isinstance(sel[0], pm.general.MeshEdge):
			for s in sel:
				if isinstance(s, pm.general.MeshEdge):
					continue

				else:
					pm.error("Selection contains not just edges")

			mid_curve = pm.polyToCurve(name=f"{prefix}_mid_curve", form=0)
			pm.delete(mid_curve, constructionHistory=True)
			mid_curve_name = mid_curve[0]


		elif isinstance(sel[0], pm.nodetypes.Transform):
			if isinstance(sel[0].getShape(), pm.nodetypes.NurbsCurve):
				mid_curve_name = sel[0].name(long=False)
				pm.delete(sel[0], constructionHistory=True)
			else:
				pm.error("Selection is neither edge nor curve.")

		else:
			pm.error("Selection is neither edge nor curve.")

		om_sel = om2.MSelectionList()
		om_sel.add(mid_curve_name)

		dag_path = om_sel.getDagPath(0)

		pm_mid_curve = pm.PyNode(dag_path)
		pm_mid_curve_shape = pm_mid_curve.getShape()

		om_mid_curve = om2.MFnNurbsCurve(dag_path)
		middle_cv_array = om_mid_curve.cvPositions(om2.MSpace.kObject)

		
		midcurve_offset_x = om2.MVector(1, 0, 0)
		midcurve_offset_y = om2.MVector(0, 1, 0)
		midcurve_offset_z = om2.MVector(0, 0, 1)
	

		for offset in [midcurve_offset_x, midcurve_offset_y, midcurve_offset_z]:

			upper_cv_array = []
			lower_cv_array = []

			for cv in middle_cv_array:
				om_upper_point = cv + offset
				upper_point = (om_upper_point.x, om_upper_point.y, om_upper_point.z)
				upper_cv_array.append(upper_point)

			upper_curve = pm.curve(p=upper_cv_array, name=f"{prefix}_upper_curve")
			upper_curve_shape = upper_curve.getShape()

			result = pm.curveIntersect(pm_mid_curve, upper_curve, tolerance=0.01)

			if not result:

				for cv in middle_cv_array:
					om_lowerpoint = cv - offset
					lower_point = (om_lowerpoint.x, om_lowerpoint.y, om_lowerpoint.z)
					lower_cv_array.append(lower_point)

				lower_curve = pm.curve(p=lower_cv_array, name=f"{prefix}_lower_curve")
				lower_curve_shape = lower_curve.getShape()

				break

			else:
				pm.delete(upper_curve)


		ribbon_loft = pm.createNode("loft", name=f"{prefix}_ribbon_loft")
		upper_curve_shape.worldSpace[0] >> ribbon_loft.inputCurve[0]
		pm_mid_curve_shape.worldSpace[0] >> ribbon_loft.inputCurve[1]
		lower_curve_shape.worldSpace[0] >> ribbon_loft.inputCurve[2]
		ribbon_loft.uniform.set(1)
		ribbon_loft.autoReverse.set(1)
		ribbon_loft.degree.set(3)
		ribbon_loft.sectionSpans.set(1)
		ribbon_loft.reverseSurfaceNormals.set(True)

		ribbon = pm.nurbsPlane(name=f"{prefix}_ribbon")[0]
		ribbon_shape = ribbon.getShape()

		ribbon_loft.outputSurface >> ribbon_shape.create


		ribbon_pins, ribbon_joints = add_pin_joints(
			name=prefix,
			ribbon=ribbon,
			number_of_pins=num_pins
		)

		ribbon_pin_grp = pm.createNode("transform", name=f"{prefix}_ribbon_pin_grp")
		ribbon_joint_grp = pm.createNode("transform", name=f"{prefix}_ribbon_joint_grp")

		for pin, jnt in zip(ribbon_pins, ribbon_joints):
			pm.parent(pin, ribbon_pin_grp)
			pm.parent(jnt, ribbon_joint_grp)




JointsToSurfaceFromEdge()