import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import pymel.core as pm

def get_u_param(pnt = [], crv = None):
	point = om.MPoint(pnt[0],pnt[1],pnt[2])
	curve_fn = om.MFnNurbsCurve(get_dag_path(crv))
	param_util=om.MScriptUtil()
	param_ptr=param_util.asDoublePtr()
	is_on_curve = curve_fn.isPointOnCurve(point)
	if is_on_curve:
		curve_fn.getParamAtPoint(point , param_ptr,0.001,om.MSpace.kObject )
	else:
		point = curve_fn.closestPoint(point,param_ptr,0.001,om.MSpace.kObject)
		curve_fn.getParamAtPoint(point , param_ptr,0.001,om.MSpace.kObject )
	param = param_util.getDouble(param_ptr)
	return param

def get_dag_path(object_name):
	if isinstance(object_name, list):
		o_node_list=[]

		for o in object_name:
			selection_list = om.MSelectionList()
			selection_list.add(o)
			o_node = om.MDagPath()
			selection_list.getDagPath(0, o_node)
			o_node_list.append(o_node)
		return o_node_list

	else:
		selection_list = om.MSelectionList()
		selection_list.add(object_name)
		o_node = om.MDagPath()
		selection_list.getDagPath(0, o_node)

		return o_node


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
				self.prefix = pm.textFieldGrp(label="Curve and Joint prefix", text="prefix")
				pm.text(label="Select the desired edge before launching the tool")
				with pm.horizontalLayout():
					pm.button(label="Cancel")
					pm.button(label="OK", command=self.execute)


	def execute(self, *args):
		
		sel = pm.ls(selection=1)
		curve = pm.polyToCurve(name=f"{self.prefix}_curve")

		pm.delete(curve, constructionHistory=True)

		om_sel = om.MSelectionList()
		om_sel.add(curve.name())
		mobj = om_sel.getDependNode(0)

		om_curve = om.MFnNurbsCurve(mobj)

		curve_point_array = om.MPointArray()
		om_curve.getCVs(curve_point_array, om.MSpace.kWorld)

		for i, cv in enumerate(curve_point_array):

		


sel = pm.ls(sl=1)
crv = "test_curveShape"

curve_jnt_grp = pm.createNode("transform", name="curve_jnt_grp")

for s in sel:
    pos = pm.xform(s, q=1, ws=1, t=1)
    u_parm = get_u_param(pos, crv)
    name = s.replace("_loc", "_pci")
    pci = pm.createNode("pointOnCurveInfo", name=name)

    joint = pm.joint(name=f"{crv}_joint")
    
    pm.connectAttr(f"{crv}.worldSpace", f"{pci}.inputCurve")
    pm.setAttr(f"{pci}.parameter", u_parm)
    pm.connectAttr(f"{pci}.position", f"{s}.t")

    s.worldMatrix >> joint.offsetParentMatrix

    pm.parent(joint, curve_jnt_grp)