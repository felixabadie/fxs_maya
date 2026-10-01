import maya.api.OpenMaya as om2
import pymel.core as pm

def get_u_param(pnt = [], crv = None):
	point = om2.MPoint(*pnt)

	dag_path = get_dag_path(crv)
	#dag_path.extendToShape()
	curve_fn = om2.MFnNurbsCurve(dag_path)
	is_on_curve = curve_fn.isPointOnCurve(point)

	if is_on_curve:
		param = curve_fn.getParamAtPoint(point, 0.001, om2.MSpace.kObject)

	else:
		point_tuple = curve_fn.closestPoint(point, None, 0.001, om2.MSpace.kObject) #None necessary because else tolerance gets used as guess-attr
		param = curve_fn.getParamAtPoint(point_tuple[0], 0.001, om2.MSpace.kObject)

	return param


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
				pm.text(label="Select the desired edge before launching the tool")
				with pm.horizontalLayout():
					pm.button(label="Cancel")
					pm.button(label="OK", command=self.execute)


	def execute(self, *args):

		sel = pm.ls(selection=1)
		prefix = self.prefix.control.getText()

		ribbon_offset = 1

		#check if selection is edge
		if isinstance(sel[0], pm.general.MeshEdge):
			for s in sel:
				if isinstance(s, pm.general.MeshEdge):
					continue

				else:
					pm.error("Selection contains not just edges")

			middle_curve = pm.polyToCurve(name=f"{prefix}_middle_curve", form=0)
			pm.delete(middle_curve, constructionHistory=True)
			middle_curve_name = middle_curve[0]


		elif isinstance(sel[0], pm.nodetypes.Transform):
			if isinstance(sel[0].getShape(), pm.nodetypes.NurbsCurve):
				middle_curve_name = sel[0].name(long=False)
				pm.delete(sel[0], constructionHistory=True)
			else:
				pm.error("Selection is neither edge nor curve.")

		else:
			pm.error("Selection is neither edge nor curve.")

		om_sel = om2.MSelectionList()
		om_sel.add(middle_curve_name)

		dag_path = om_sel.getDagPath(0)

		middle_curve_test = pm.PyNode(dag_path)
		middle_curve_test_shape = middle_curve_test.getShape()

		om_middle_curve = om2.MFnNurbsCurve(dag_path)
		middle_cv_array = om_middle_curve.cvPositions(om2.MSpace.kObject)

		upper_cv_array = []
		lower_cv_array = []

		#duplicate curve points with offset to new MPointArrays. Later create Curves out of said Arrays
		for cv in middle_cv_array:
			upper_point = (cv.x, cv.y + ribbon_offset, cv.z)
			upper_cv_array.append(upper_point)
			
			lower_point = (cv.x, cv.y - ribbon_offset, cv.z)
			lower_cv_array.append(lower_point)

		upper_curve = pm.curve(p=upper_cv_array, name=f"{prefix}_upper_curve")
		lower_curve = pm.curve(p=lower_cv_array, name=f"{prefix}_lower_curve")

		upper_curve_shape = upper_curve.getShape()
		lower_curve_shape = lower_curve.getShape()

		ribbon_loft = pm.createNode("loft", name=f"{prefix}_ribbon_loft")
		upper_curve_shape.worldSpace[0] >> ribbon_loft.inputCurve[0]
		middle_curve_test_shape.worldSpace[0] >> ribbon_loft.inputCurve[1]
		lower_curve_shape.worldSpace[0] >> ribbon_loft.inputCurve[2]
		ribbon_loft.uniform.set(1)
		ribbon_loft.autoReverse.set(1)
		ribbon_loft.degree.set(3)
		ribbon_loft.sectionSpans.set(1)
		ribbon_loft.reverseSurfaceNormals.set(True)

		ribbon = pm.nurbsPlane(name=f"{prefix}_ribbon")[0]
		ribbon_shape = ribbon.getShape()

		ribbon_loft.outputSurface >> ribbon_shape.create




JointsToSurfaceFromEdge()	