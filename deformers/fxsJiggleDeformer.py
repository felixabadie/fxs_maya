import math
from maya import cmds
import maya.OpenMaya as OpenMaya
from maya.mel import eval as mel_eval
import maya.OpenMayaMPx as OpenMayaMPx

# Set globals to the proper cpp cvars. (compatible from maya 2016)
kInput = OpenMayaMPx.cvar.MPxGeometryFilter_input
kInputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
kOutputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom
kEnvelope = OpenMayaMPx.cvar.MPxGeometryFilter_envelope
kGroupId = OpenMayaMPx.cvar.MPxGeometryFilter_groupId


class FxsJiggleDeformer(OpenMayaMPx.MPxDeformerNode):
    type_id = OpenMaya.MTypeId(0x00000004)
    type_name = "FxsJiggleDeformer"

    # multiplier to amplify deformation
    debug_scaler = None

    min_distance_attr = None
    max_distance_attr = None
    falloff_attr = None

    # vertex positions get saved on node attribute
    previous_vertex_matrix = OpenMaya.MObject()

    @classmethod
    def initialize(cls):
        numeric_attr_fn = OpenMaya.MFnNumericAttribute()
        ramp_attr_fn = OpenMaya.MRampAttribute()
        typedAttr = OpenMaya.MFnTypedAttribute()

        cls.debug_scaler = numeric_attr_fn.create(
            "debugScaler",
            "dS",
            OpenMaya.MFnNumericData.kFloat,
            1
        )
        cls.addAttribute(cls.debug_scaler)

        cls.previous_vertex_matrix = typedAttr.create(
            "previousVertexMatrix",
            "pvm",
            OpenMaya.MFnData.kPointArray
        )
        typedAttr.setStorable(True)
        typedAttr.setHidden(True)
        typedAttr.setKeyable(False)
        cls.addAttribute(cls.previous_vertex_matrix)

        cls.min_distance_attr = numeric_attr_fn.create(
            "minimumDistance",
            "mind",
            OpenMaya.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.min_distance_attr)

        cls.max_distance_attr = numeric_attr_fn.create(
            "maximumDistance",
            "maxd",
            OpenMaya.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.max_distance_attr)

        cls.falloff_attr = ramp_attr_fn.createCurveRamp(
            "falloffRamp",
            "fr"
        )
        cls.addAttribute(cls.falloff_attr)

        cls.attributeAffects(cls.min_distance_attr, kOutputGeom)
        cls.attributeAffects(cls.max_distance_attr, kOutputGeom)
        cls.attributeAffects(cls.falloff_attr, kOutputGeom)
        
        #cls.attributeAffects(cls.previous_vertex_matrix, kOutputGeom)

    @classmethod
    def creator(cls):
        """Create instance of this class.

        Returns:
            FxsJiggleDeformer: New class instance.
        """
        return cls()

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)

    def postConstructor(self):
        
        node = self.thisMObject()
        jiggleDistance_handle = OpenMaya.MRampAttribute(node, self.falloff_attr)

        positions = OpenMaya.MFloatArray()
        values = OpenMaya.MFloatArray()
        interps = OpenMaya.MIntArray()

        positions.append(float(0.0))
        positions.append(float(1.0))

        values.append(float(0.0))
        values.append(float(1.0))

        interps.append(OpenMaya.MRampAttribute.kSpline)
        interps.append(OpenMaya.MRampAttribute.kSpline)

        jiggleDistance_handle.addEntries(positions, values, interps)


    def deform(
            self,
            data_block,
            geometry_iterator,
            local_to_world_matrix,
            geometry_index
    ):
        envelope_attribute = kEnvelope
        envelope_value = data_block.inputValue(envelope_attribute).asFloat()

        debug_scaler_handle = data_block.inputValue(self.debug_scaler).asFloat()

        min_distance_handle = data_block.inputValue(self.min_distance_attr).asFloat()

        max_distance_handle = data_block.inputValue(self.max_distance_attr).asFloat()

        previous_vertex_handle = data_block.inputValue(self.previous_vertex_matrix)
        previousVertexPointData = previous_vertex_handle.data()
        

        input_geometry_object = self.getDeformerInputGeometry(
            data_block,
            geometry_index
        )

        current_deformer_node = self.thisMObject()

        fnNode = OpenMaya.MFnDependencyNode(current_deformer_node)
        node_name = fnNode.name()

        if previousVertexPointData.isNull():
            previousPoints = None
        else:
            fnPointArray = OpenMaya.MFnPointArrayData(previousVertexPointData)
            previousPoints = fnPointArray.array()

        mesh_fn = OpenMaya.MFnMesh(input_geometry_object)
        mesh_vertex_iterator = OpenMaya.MItMeshVertex(input_geometry_object)
        #global vertexIncrement

        point_array = OpenMaya.MPointArray()

        scaler_ramp_handle = OpenMaya.MRampAttribute(
                        self.thisMObject(),
                        self.falloff_attr
                    )

        """
        Current deform logic:

        For every vertex, take current position
        get previous vertex position (if available) -> if not use current

        calculate distance vector

        based on distance create new point (current + vector)

        save new point
        """

        if previousPoints is None:
            while not mesh_vertex_iterator.isDone():
                vertex_index = mesh_vertex_iterator.index()

                current_vertex_point = mesh_vertex_iterator.position(OpenMaya.MSpace.kWorld)
                previous_point = OpenMaya.MPoint(current_vertex_point)

                new_point = OpenMaya.MPoint(current_vertex_point)

                direction_vector = current_vertex_point - previous_point
                distance = direction_vector.length()

                if distance > max_distance_handle:
                    new_point = new_point + OpenMaya.MVector(direction_vector * envelope_value * debug_scaler_handle)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)

                elif max_distance_handle > distance > min_distance_handle:
                    
                    scaler_range = (max_distance_handle - min_distance_handle)
                    scaler_position = (distance - min_distance_handle) / scaler_range
                    
                    if scaler_ramp_handle:
                        scaler_ramp_util = OpenMaya.MScriptUtil()
                        scaler_ramp = scaler_ramp_util.asFloatPtr()
                        try:
                            scaler_ramp_handle.getValueAtPosition(
                                scaler_position,
                                scaler_ramp
                            )
                        except:
                            scaler_ramp = None
                        if scaler_ramp:
                            scaler_value = OpenMaya.MScriptUtil().getFloat(scaler_ramp)

                    if not scaler_ramp_handle:
                        scaler_value = (-1 * scaler_position +1)
                        print("NOT USING SCALER RAMP!!!!!!!!")

                    if scaler_value > 1:
                        scaler_value = 1
                    elif scaler_value < 0:
                        scaler_value = 0

                    new_point = new_point + OpenMaya.MVector((direction_vector * envelope_value) * scaler_value * debug_scaler_handle)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)

                #point_array.append(current_vertex_point)
                point_array.append(new_point)
                mesh_vertex_iterator.next()

        else:
            while not mesh_vertex_iterator.isDone():
                vertex_index = mesh_vertex_iterator.index()

                current_vertex_point = mesh_vertex_iterator.position(OpenMaya.MSpace.kWorld)
                previous_point = previousPoints[vertex_index]

                new_point = OpenMaya.MPoint(current_vertex_point)

                direction_vector = current_vertex_point - previous_point
                distance = direction_vector.length()

                if distance > max_distance_handle:
                    new_point = new_point + OpenMaya.MVector(direction_vector * envelope_value * debug_scaler_handle)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)

                elif max_distance_handle > distance > min_distance_handle:
                    
                    scaler_range = (max_distance_handle - min_distance_handle)
                    scaler_position = (distance - min_distance_handle) / scaler_range
                    
                    if scaler_ramp_handle:
                        scaler_ramp_util = OpenMaya.MScriptUtil()
                        scaler_ramp = scaler_ramp_util.asFloatPtr()
                        try:
                            scaler_ramp_handle.getValueAtPosition(
                                scaler_position,
                                scaler_ramp
                            )
                        except:
                            scaler_ramp = None
                        if scaler_ramp:
                            scaler_value = OpenMaya.MScriptUtil().getFloat(scaler_ramp)

                    if not scaler_ramp_handle:
                        scaler_value = (-1 * scaler_position +1)
                        print("NOT USING SCALER RAMP!!!!!!!!")

                    if scaler_value > 1:
                        scaler_value = 1
                    elif scaler_value < 0:
                        scaler_value = 0
                    
                    new_point = new_point + OpenMaya.MVector((direction_vector * envelope_value) * scaler_value * debug_scaler_handle)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)
                
                #point_array.append(current_vertex_point)
                point_array.append(new_point)
                mesh_vertex_iterator.next()
        

        point_array_data = OpenMaya.MFnPointArrayData()
        dataObject = point_array_data.create(point_array)

        previous_vertex_handle_out = data_block.outputValue(self.previous_vertex_matrix)
        previous_vertex_handle_out.setMObject(dataObject)
        previous_vertex_handle_out.setClean()

        
    def getDeformerInputGeometry(self, data_block, geometry_index):
            """Obtain a reference to the input mesh. 
            
            We use MDataBlock.outputArrayValue() to avoid having to recompute the 
            mesh and propagate this recomputation throughout the Dependency Graph.
            
            OpenMayaMPx.cvar.MPxGeometryFilter_input and 
            OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom (Maya 2016) 
            are SWIG-generated variables which respectively contain references to 
            the deformer's 'input' attribute and 'inputGeom' attribute.

            Args:
                data_block (MDataBlock): the node's datablock.
                geometry_index (int): 
                    the index corresponding to the requested output geometry.
            """
            inputAttribute = OpenMayaMPx.cvar.MPxGeometryFilter_input
            inputGeometryAttribute = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
            
            inputHandle = data_block.outputArrayValue( inputAttribute )
            inputHandle.jumpToElement( geometry_index )
            inputGeometryObject = inputHandle.outputValue().child(
                inputGeometryAttribute
            ).asMesh()
            
            return inputGeometryObject



# taken from plugin, no changes exept name
def initializePlugin(plugin):
    """Called when plugin is loaded.

    Args:
        plugin (MObject): The plugin.
    """
    plugin_fn = OpenMayaMPx.MFnPlugin(plugin, "Felix Abadie", "0.0.1")

    try:
        plugin_fn.registerNode(
            FxsJiggleDeformer.type_name,
            FxsJiggleDeformer.type_id,
            FxsJiggleDeformer.creator,
            FxsJiggleDeformer.initialize,
            OpenMayaMPx.MPxNode.kDeformerNode
        )
    except:
        print("failed to register node {0}".format(FxsJiggleDeformer.type_name))
        raise

    # Load custom Attribute Editor GUI.
    mel_eval( gui_template )


# taken from plugin, no changes exept name
def uninitializePlugin(plugin):
    """Called when plugin is unloaded.

    Args:
        plugin (MObject): The plugin.
    """
    plugin_fn = OpenMayaMPx.MFnPlugin(plugin, "Felix Abadie", "0.0.1")

    try:
        plugin_fn.deregisterNode(FxsJiggleDeformer.type_id)
    except:
        print( "failed to deregister node {0}".format(
            FxsJiggleDeformer.type_name
        ))
        raise


#  Custom attribute editor gui template
gui_template = '''
    global proc AEFxsJiggleDeformerTemplate( string $nodeName )
    {
        editorTemplate -beginScrollLayout;
            // Add attributes to show in attribute editor.
            editorTemplate -beginLayout "Jiggle Deformer Attributes" -collapse 0;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "envelope" ;
                editorTemplate -addControl  "debugScaler";
                editorTemplate -addControl "minimumDistance" ;
                editorTemplate -addControl "maximumDistance" ;
                AEaddRampControl "falloffRamp" ;
            editorTemplate -endLayout;
            // Add base node attributes
            AEdependNodeTemplate $nodeName;
            // Add extra atttributes
            editorTemplate -addExtraControls;
        editorTemplate -endScrollLayout;
    }
'''