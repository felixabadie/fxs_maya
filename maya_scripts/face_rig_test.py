import maya.OpenMaya as om
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