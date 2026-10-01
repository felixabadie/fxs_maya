import maya.api.OpenMaya as om2
import pymel.core as pm


"""
To do, add functionality of custom joint number
"""


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


class JointsToCurveFromEdge:
	"""Working title"""

	def __init__(self):
		self.win_id = "fxs_joints_to_curve_from_edge"

		if pm.window(self.win_id, query=True, exists=True):
			pm.deleteUI(self.win_id)

		with pm.window(self.win_id, title="Joints to Curve from Edge") as win:
			with pm.columnLayout(adj=True):
				pm.text(
					label="This tool will work by taking an edge, " \
					"converting this edge to a curve and then place joints on that curve", 
					align="left")
				self.prefix = TextFieldHelper("Type or select Prefix: ")
				pm.text(label="Select the desired edge before launching the tool")
				with pm.horizontalLayout():
					pm.button(label="Cancel")
					pm.button(label="OK", command=self.execute)


	def execute(self, *args):

		sel = pm.ls(selection=1)
		prefix = self.prefix.control.getText()

		# check if selection is edge
		if isinstance(sel[0], pm.general.MeshEdge):
			for s in sel:
				if isinstance(s, pm.general.MeshEdge):
					continue

				else:
					pm.error("Selection contains not just edges")

			curve = pm.polyToCurve(name=f"{prefix}_curve")
			pm.delete(curve, constructionHistory=True)
			curve_name = curve[0]
		

		# check if transform and if nurbscurve
		elif isinstance(sel[0], pm.nodetypes.Transform):
			if isinstance(sel[0].getShape(), pm.nodetypes.NurbsCurve):
				pm.delete(sel[0], constructionHistory=True)
				curve_name = sel[0].name(long=False)
			else:
				pm.error("Selection is neither edge nor curve.")

		else:
			pm.error("Selection is neither edge nor curve.")

		loc_array = []
		curve_jnt_grp = pm.createNode("transform", name=f"{prefix}_curve_jnt_grp")
		curve_loc_grp = pm.createNode("transform", name=f"{prefix}_curve_loc_grp")

		om_sel = om2.MSelectionList()
		om_sel.add(curve_name)

		dag_path = om_sel.getDagPath(0)
		#dag_path.extendToShape()

		om_curve = om2.MFnNurbsCurve(dag_path)
		cv_array = om_curve.cvPositions(om2.MSpace.kObject)

		for cv in cv_array:
			loc = pm.spaceLocator(name=f"{prefix}_loc")
			loc.setTranslation((cv.x, cv.y, cv.z), space='world')
			loc_array.append(loc)

		
		for l in loc_array:
			pos = pm.xform(l, q=1, os=1, t=1)
			u_parm = get_u_param(pos, curve_name)
			name = l.replace("_loc", "_pci")
			pci = pm.createNode("pointOnCurveInfo", name=name)

			joint = pm.joint(name=f"{curve_name}_joint")

			pm.connectAttr(f"{curve_name}.worldSpace", f"{pci}.inputCurve")
			pm.setAttr(f"{pci}.parameter", u_parm)
			pm.connectAttr(f"{pci}.position", f"{l}.t")

			l.worldMatrix >> joint.offsetParentMatrix
			pm.parent(l, curve_loc_grp)
			pm.parent(joint, curve_jnt_grp)

			
JointsToCurveFromEdge()