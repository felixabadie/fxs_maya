from maya import cmds
from maya import OpenMaya as om
from maya import OpenMayaMPx as omMPx
from maya.mel import eval as mel_eval
import math


"""
Template taken from Marieke van Neutigem
https://github.com/mvanneutigem/tutorials/blob/master/plugins/deformerTemplate.py

As this project is used only internally I am going to start from her template

"""



# Set globals to the proper cpp cvars. (compatible from maya 2016)
kInput = omMPx.cvar.MPxGeometryFilter_input
kInputGeom = omMPx.cvar.MPxGeometryFilter_inputGeom
kOutputGeom = omMPx.cvar.MPxGeometryFilter_outputGeom
kEnvelope = omMPx.cvar.MPxGeometryFilter_envelope
kGroupId = omMPx.cvar.MPxGeometryFilter_groupId


class FxsStickyLipDeformer(omMPx.MPxDeformerNode):
    """Template deformer node."""
    # Replace this with a valid node id for use in production.
    type_id = om.MTypeId(0x00000002)  
    type_name = "FxsStickyLipDeformer"

    # Add attribute variables here.
    aUpperLipIndices = om.MObject()
    aLowerLipIndices = om.MObject()
    min_distance_attr = None
    max_distance_attr = None
    falloff_attr = None
    


    @classmethod
    def initialize(cls):
        """Initialize attributes and dependencies."""
        # Add any input and outputs to the deformer here, also set up 
        # dependencies between the in and outputs. If you want to use another 
        # mesh as an input you can use an MFnGenericAttribute and add 
        # MFnData.kMesh with the addDataAccept method.
        
        numeric_attr_fn = om.MFnNumericAttribute()
        ramp_attr_fn = om.MRampAttribute()
        typedAttr = om.MFnTypedAttribute()

        # Create upper lip vertex array
        cls.aUpperLipIndices = typedAttr.create(
            "upperLipIndeces",
            "uli",
            om.MFnData.kIntArray
        )
        typedAttr.setStorable(True)
        typedAttr.setHidden(True)
        typedAttr.setKeyable(False) # gets created once and assigend at setup, no need for runtime changes
        cls.addAttribute(cls.aUpperLipIndices)

        # Create lower lip vertex array
        cls.aLowerLipIndices = typedAttr.create(
            "lowerLipIndeces",
            "lli",
            om.MFnData.kIntArray
        )
        typedAttr.setStorable(True)
        typedAttr.setHidden(True)
        typedAttr.setKeyable(False) # gets created once and assigend at setup, no need for runtime changes
        cls.addAttribute(cls.aLowerLipIndices)


        # Min Distance Threshold value (everything under gets fully attracted towards midpoint)
        cls.min_distance_attr = numeric_attr_fn.create(
            "minDistanceThreshold",
            "midt",
            om.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.min_distance_attr)

        # Distance Threshold value (everything between min and max distance gets affected by falloff)
        cls.max_distance_attr = numeric_attr_fn.create(
            "maxDistanceThreshold",
            "madt",
            om.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.max_distance_attr)

        # Create Fallof Ramp (No idea if this will work)
        cls.falloff_attr = ramp_attr_fn.createCurveRamp(
            "falloffRamp",
            "fr",
        )
        cls.addAttribute(cls.falloff_attr)

        # I have no fucking idea, probably will indluence output geometry
        cls.attributeAffects(cls.min_distance_attr, kOutputGeom)
        cls.attributeAffects(cls.max_distance_attr, kOutputGeom)
        cls.attributeAffects(cls.falloff_attr, kOutputGeom)
        cls.attributeAffects(cls.aUpperLipIndices, kOutputGeom)
        cls.attributeAffects(cls.aLowerLipIndices, kOutputGeom)


    @classmethod
    def creator(cls):
        """Create instance of this class.

        Returns:
            FxsStickyLipDeformer: New class instance.
        """
        return cls()

    def __init__(self):
        """Construction."""
        omMPx.MPxDeformerNode.__init__(self)

    def postConstructor(self):
        """This is called when the node has been added to the scene."""

        # For distance ramp attr with default values, if not working remove
        node = self.thisMObject()
        stickyDistance_handle = om.MRampAttribute(node, self.falloff_attr)

        positions = om.MFloatArray()
        values = om.MFloatArray()
        interps = om.MIntArray()
        
        positions.append(float(0.0))
        positions.append(float(1.0))

        values.append(float(1.0))
        values.append(float(0.0))
        
        interps.append(om.MRampAttribute.kSpline)
        interps.append(om.MRampAttribute.kSpline)

        stickyDistance_handle.addEntries(positions, values, interps)



    def deform(
        self, 
        data_block, 
        geometry_iterator, 
        local_to_world_matrix, 
        geometry_index
    ):
        """Deform each vertex using the geometry iterator.
        
        Args:
            data_block (MDataBlock): the node's datablock.
            geometry_iterator (MItGeometry): 
                iterator for the geometry being deformed.
            local_to_world_matrix (MMatrix): 
                the geometry's world space transformation matrix.
            geometry_index (int): 
                the index corresponding to the requested output geometry.
        """
        
        # The envelope determines the weight of the deformer on the mesh (connected to face rig)
        envelope_attribute = kEnvelope
        envelope_value = data_block.inputValue(envelope_attribute).asFloat()

        # get min distance threshold
        min_distance_handle = data_block.inputValue(self.min_distance_attr).asFloat()

        # get max distance threshold
        max_distance_handle = data_block.inputValue(self.max_distance_attr).asFloat()

        # get IntArray Handles
        upper_handle = data_block.inputValue(FxsStickyLipDeformer.aUpperLipIndices)
        upperIndicesData = upper_handle.data()
        try:
            upper_fn_IntArray = om.MFnIntArrayData(upperIndicesData)
            upper_indices = upper_fn_IntArray.array()
        except Exception as e:
            print(f"Problem in deform with upper indices: {e}")
            return

        lower_handle = data_block.inputValue(FxsStickyLipDeformer.aLowerLipIndices)
        lowerIndicesData = lower_handle.data()
        try:
            lower_fn_IntArray = om.MFnIntArrayData(lowerIndicesData)
            lower_indeces = lower_fn_IntArray.array()
        except Exception as e:
            print(f"Problem in deform with lower indices: {e}")
            return

        input_geometry_object = self.getDeformerInputGeometry(
            data_block,
            geometry_index
        )

        # normals if necessary later on
        normals = om.MFloatVectorArray()
        mesh_fn = om.MFnMesh(input_geometry_object)
        mesh_fn.getVertexNormals(True, normals, om.MSpace.kTransform)

        # original points if necessary
        orig_points = om.MPointArray()
        mesh_fn.getPoints(orig_points)

        # Iterator that goes over every single vertex
        mesh_vertex_iterator = om.MItMeshVertex(input_geometry_object)

        global vertexIncrement
       
        """
        Deform Logic:

        For every vertex in lower_indices get corresponding vertex in upper_indeces

        measure distance

        if distance under min threshold value: -> pull to midpoint
        if distance between min and max threshold value: -> pull to midpoint but weighted by falloff_attr

        """

        while not mesh_vertex_iterator.isDone():
            vertex_index = mesh_vertex_iterator.index()

            if vertex_index in lower_indeces:

                partners = {}
                for i in range(lower_indeces.length()):
                    partners[lower_indeces[i]] = upper_indices[i]

                #print(partners)

                upper_idx = partners[vertex_index]
                upper_point = om.MPoint()
                mesh_fn.getPoint(upper_idx, upper_point, om.MSpace.kWorld)

                lower_point = mesh_vertex_iterator.position(om.MSpace.kWorld)
                #print(f"For Vertex Index {vertex_index}, lower_point: {lower_point}, upper_point: {upper_point}")
                
                distance = (lower_point - upper_point).length()

                if distance < min_distance_handle:

                    # calculate mid point between upper and lower corresponding vertecies
                    midpoint = self.get_midPoint(lower_point, upper_point)

                    # calculate vector from vertecies to midpoint
                    upper_vector = midpoint - upper_point
                    lower_vector = midpoint - lower_point

                    # construct new point towards midpoint weighted by envelope value (connected to face-rig controller)
                    new_upper_point = upper_point + om.MVector(upper_vector * envelope_value)
                    new_lower_point = lower_point + om.MVector(lower_vector * envelope_value)

                    # set position of current vertex and corresponding vertex
                    mesh_vertex_iterator.setPosition(new_lower_point, om.MSpace.kWorld)
                    mesh_fn.setPoint(upper_idx, new_upper_point, om.MSpace.kWorld)


                elif min_distance_handle < distance < max_distance_handle:

                    midpoint = self.get_midPoint(lower_point, upper_point)

                    scaler_range = (max_distance_handle - min_distance_handle)
                    scaler_position = (distance - min_distance_handle) / scaler_range

                    # not sure if necessary but clamping values to range
                    if scaler_position > 1:
                        scaler_position = 1
                    elif scaler_position < 0:
                        scaler_position = 0

                    scaler_ramp_handle = om.MRampAttribute(
                        self.thisMObject(),
                        self.falloff_attr
                    )

                    if scaler_ramp_handle:
                        # get the fallof value of current distance
                        scaler_ramp_util = om.MScriptUtil()
                        scaler_ramp = scaler_ramp_util.asFloatPtr()
                        try:
                            scaler_ramp_handle.getValueAtPosition(
                                scaler_position,
                                scaler_ramp
                            )
                        except:
                            scaler_ramp = None
                        if scaler_ramp:
                            scaler_value = om.MScriptUtil().getFloat(scaler_ramp)
                    
                    if not scaler_ramp_handle:
                        scaler_value = (-1 * scaler_position +1)
                        print("NOT USING SCALER RAMP!!!!!!!!")

                    # another clamp as quickfix
                    if scaler_value > 1:
                        scaler_value = 1
                    elif scaler_value < 0:
                        scaler_value = 0

                    # calculate vector from vertecies to midpoint
                    upper_vector = midpoint - upper_point
                    lower_vector = midpoint - lower_point

                    # construct new point towards midpoint weighted by envelope value (connected to face-rig controller)
                    new_upper_point = upper_point + om.MVector((upper_vector * envelope_value) * scaler_value)
                    new_lower_point = lower_point + om.MVector((lower_vector * envelope_value) * scaler_value)

                    # set position of current vertex and corresponding vertex
                    mesh_vertex_iterator.setPosition(new_lower_point, om.MSpace.kWorld)
                    mesh_fn.setPoint(upper_idx, new_upper_point, om.MSpace.kWorld)
        
            mesh_vertex_iterator.next()


    # gets midpoint between to MPoints
    def get_midPoint(self, point1, point2):

        zero_point = om.MPoint() # dummy point to get corresponding vectors

        p1_vector = point1 - zero_point
        p2_vector = point2 - zero_point

        connection_vector = p1_vector + p2_vector # must be MVecors (cannot add MPoints)
        mid_point = zero_point + (connection_vector * 0.5)

        return mid_point


    # was already part of template file (no changens so far)
    def getDeformerInputGeometry(self, data_block, geometry_index):
        """Obtain a reference to the input mesh. 
        
        We use MDataBlock.outputArrayValue() to avoid having to recompute the 
        mesh and propagate this recomputation throughout the Dependency Graph.
        
        omMPx.cvar.MPxGeometryFilter_input and 
        omMPx.cvar.MPxGeometryFilter_inputGeom (Maya 2016) 
        are SWIG-generated variables which respectively contain references to 
        the deformer's 'input' attribute and 'inputGeom' attribute.

        Args:
            data_block (MDataBlock): the node's datablock.
            geometry_index (int): 
                the index corresponding to the requested output geometry.
        """
        inputAttribute = omMPx.cvar.MPxGeometryFilter_input
        inputGeometryAttribute = omMPx.cvar.MPxGeometryFilter_inputGeom
        
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
    plugin_fn = omMPx.MFnPlugin(plugin, "Felix Abadie", "0.0.1")

    try:
        plugin_fn.registerNode(
            FxsStickyLipDeformer.type_name,
            FxsStickyLipDeformer.type_id,
            FxsStickyLipDeformer.creator,
            FxsStickyLipDeformer.initialize,
            omMPx.MPxNode.kDeformerNode
        )
    except:
        print("failed to register node {0}".format(FxsStickyLipDeformer.type_name))
        raise

    # Load custom Attribute Editor GUI.
    mel_eval( gui_template )


# taken from plugin, no changes exept name
def uninitializePlugin(plugin):
    """Called when plugin is unloaded.

    Args:
        plugin (MObject): The plugin.
    """
    plugin_fn = omMPx.MFnPlugin(plugin, "Felix Abadie", "0.0.1")

    try:
        plugin_fn.deregisterNode(FxsStickyLipDeformer.type_id)
    except:
        print( "failed to deregister node {0}".format(
            FxsStickyLipDeformer.type_name
        ))
        raise


# This is a custom attribute editor gui template, if you want to display your
# attributes in a specific way you can define that here. (this is mel code)
gui_template = '''
    global proc AEFxsStickyLipDeformerTemplate( string $nodeName )
    {
        editorTemplate -beginScrollLayout;
            // Add attributes to show in attribute editor.
            editorTemplate -beginLayout "Sticky Lip Attributes" -collapse 0;
                editorTemplate -addSeparator;
                editorTemplate -addControl "minDistanceThreshold" ;
                editorTemplate -addControl "maxDistanceThreshold" ;
                editorTemplate -addControl "envelope" ;
                AEaddRampControl ($nodeName + ".falloffRamp");
            editorTemplate -endLayout;
            // Add base node attributes
            AEdependNodeTemplate $nodeName;
            // Add extra atttributes
            editorTemplate -addExtraControls;
        editorTemplate -endScrollLayout;
    }
'''