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

class FxsMotionBlurDeformer(OpenMayaMPx.MPxDeformerNode):
    type_id = OpenMaya.MTypeId(0x00000006)
    type_name = "FxsMotionBlurDeformer"

    # global scale multiplicator
    aGlobal_scaler = None

    # distance falloff attributes
    aMin_distance = None
    aMax_distance = None
    aDistance_falloff = None

    # blur shape attribute
    aShape_falloff = None

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)
        self._initialized = False
        self._previousPosition = OpenMaya.MPointArray()

    @classmethod
    def initialize(cls):
        numeric_attr_fn = OpenMaya.MFnNumericAttribute()
        ramp_attr_fn = OpenMaya.MRampAttribute()
        typedAttr = OpenMaya.MFnTypedAttribute()

        cls.aGlobal_scaler = numeric_attr_fn.create(
            "globalScaler",
            "gs",
            OpenMaya.MFnNumericData.kFloat,
            1
        )
        cls.addAttribute(cls.aGlobal_scaler)

        cls.aMin_distance = numeric_attr_fn.create(
            "minimumDistance",
            "mind",
            OpenMaya.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.aMin_distance)

        cls.aMax_distance = numeric_attr_fn.create(
            "maximumDistance",
            "maxd",
            OpenMaya.MFnNumericData.kFloat
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.aMax_distance)

        cls.aDistance_falloff = ramp_attr_fn.createCurveRamp(
            "falloffRamp",
            "fr"
        )
        cls.addAttribute(cls.aDistance_falloff)

        cls.aShape_falloff = ramp_attr_fn.createCurveRamp(
            "shapeRamp",
            "sr"
        )
        cls.addAttribute(cls.aShape_falloff)

        cls.attributeAffects(cls.aMin_distance, kOutputGeom)
        cls.attributeAffects(cls.aMax_distance, kOutputGeom)
        cls.attributeAffects(cls.aDistance_falloff, kOutputGeom)
        cls.attributeAffects(cls.aShape_falloff, kOutputGeom)


    @classmethod
    def creator(cls):
        """Create instance of this class.

        Returns:
            FxsMotionBlurDeformer: New class instance.
        """
        return cls()


    def postConstructor(self):
        
        node = self.thisMObject()
        motionBlurDistance_handle = OpenMaya.MRampAttribute(node, self.aDistance_falloff)

        distance_positions = OpenMaya.MFloatArray()
        distance_values = OpenMaya.MFloatArray()
        distance_interps = OpenMaya.MIntArray()

        distance_positions.append(float(0.0))
        distance_positions.append(float(1.0))

        distance_values.append(float(0.0))
        distance_values.append(float(1.0))

        distance_interps.append(OpenMaya.MRampAttribute.kSpline)
        distance_interps.append(OpenMaya.MRampAttribute.kSpline)

        motionBlurDistance_handle.addEntries(distance_positions, distance_values, distance_interps)


        # shape settings
        shapeDistance_handle = OpenMaya.MRampAttribute(node, self.aShape_falloff)

        shape_positions = OpenMaya.MFloatArray()
        shape_values = OpenMaya.MFloatArray()
        shape_interps = OpenMaya.MIntArray()

        shape_positions.append(float(0.0))
        shape_positions.append(float(1.0))

        shape_values.append(float(0.0))
        shape_values.append(float(1.0))

        shape_interps.append(OpenMaya.MRampAttribute.kSpline)
        shape_interps.append(OpenMaya.MRampAttribute.kSpline)

        shapeDistance_handle.addEntries(shape_positions, shape_values, shape_interps)



    def deform(
            self,
            data_block,
            geometry_iterator,
            local_to_world_matrix,
            geometry_index
    ):
        envelope_attribute = kEnvelope
        envelope_value = data_block.inputValue(envelope_attribute).asFloat()

        global_scaler_handle = data_block.inputValue(self.aGlobal_scaler).asFloat()

        aMin_distance_handle = data_block.inputValue(self.aMin_distance).asFloat()

        aMax_distance_handle = data_block.inputValue(self.aMax_distance).asFloat()

        input_geometry_object = self.getDeformerInputGeometry(
            data_block,
            geometry_index
        )

        mesh_fn = OpenMaya.MFnMesh(input_geometry_object)
        mesh_vertex_iterator = OpenMaya.MItMeshVertex(input_geometry_object)

        input_points = OpenMaya.MPointArray()
        mesh_fn.getPoints(input_points, OpenMaya.MSpace.kWorld)

        scaler_ramp_handle = OpenMaya.MRampAttribute(
                        self.thisMObject(),
                        self.aDistance_falloff
                    )

        shape_ramp_handle = OpenMaya.MRampAttribute(
                        self.thisMObject(),
                        self.aShape_falloff
                    )

        if not self._initialized:
            self._previousPosition = input_points
            self._initialized = True

        """
        Get Direction Vecto per point
        Determine if normal and vector align -> if not deform points
        """

        while not mesh_vertex_iterator.isDone():
            vertex_index = mesh_vertex_iterator.index()

            point = mesh_vertex_iterator.position(OpenMaya.MSpace.kWorld)
            previous_point = self._previousPosition[vertex_index]

            distance_vector = (point - previous_point)
            distance = distance_vector.length()

            new_point = OpenMaya.MPoint(point)

            point_normal = OpenMaya.MVector()
            mesh_vertex_iterator.getNormal(point_normal, OpenMaya.MSpace.kWorld)

            distance_vector_normalized = distance_vector.normal()
            point_normal_vector_normalized = point_normal.normal()

            #vertex_direction_value = distance_vector * point_normal
            vertex_direction_value = distance_vector_normalized * point_normal_vector_normalized

            inv_distance_vector = distance_vector * -1

            if vertex_direction_value < 0:
                
                shape_pos = vertex_direction_value * -1

                """
                Determine multiplication factor based on vertex direction in relation to direction vector:
                the bigger the angle the bigger the shape scaler value
                """
                if shape_ramp_handle:
                    shape_ramp_util = OpenMaya.MScriptUtil()
                    shape_ramp = shape_ramp_util.asFloatPtr()

                    try:
                        shape_ramp_handle.getValueAtPosition(
                            shape_pos,
                            shape_ramp
                        )
                    except:
                        shape_ramp = None
                    if shape_ramp:
                        shape_value = OpenMaya.MScriptUtil().getFloat(shape_ramp)

                else:
                    shape_value = (-1 * shape_pos + 1)
                    print("Not using shape scaler ramp")

                # all points faster than max velocity get fully transformed
                if distance > aMax_distance_handle:

                    new_point = point + OpenMaya.MVector(inv_distance_vector * envelope_value * global_scaler_handle * shape_value)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)

                # all points which are in between min velocity and max velocity get weighted by ramp attribute
                elif aMax_distance_handle > distance > aMin_distance_handle:

                    scaler_range = (aMax_distance_handle - aMin_distance_handle)
                    scaler_position = (distance - aMin_distance_handle) / scaler_range

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
                    
                    else:
                        scaler_value = (-1 * scaler_position + 1)
                        print("Not using distance scaler ramp")

                    if scaler_value > 1:
                        scaler_value = 1
                    elif scaler_value < 0:
                        scaler_value = 0

                    new_point = point + OpenMaya.MVector((inv_distance_vector * envelope_value) * scaler_value * global_scaler_handle * shape_value)
                    mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kWorld)
                    mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kWorld)

            else:
                pass

            input_points.set(new_point, vertex_index)
            mesh_vertex_iterator.next()

        self._previousPosition = OpenMaya.MPointArray(input_points)
        #mesh_fn.updateSurface()




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
            FxsMotionBlurDeformer.type_name,
            FxsMotionBlurDeformer.type_id,
            FxsMotionBlurDeformer.creator,
            FxsMotionBlurDeformer.initialize,
            OpenMayaMPx.MPxNode.kDeformerNode
        )
    except:
        print("failed to register node {0}".format(FxsMotionBlurDeformer.type_name))
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
        plugin_fn.deregisterNode(FxsMotionBlurDeformer.type_id)
    except:
        print( "failed to deregister node {0}".format(
            FxsMotionBlurDeformer.type_name
        ))
        raise


#  Custom attribute editor gui template
gui_template = '''
    global proc AEFxsMotionBlurDeformerTemplate( string $nodeName )
    {
        editorTemplate -beginScrollLayout;
            // Add attributes to show in attribute editor.
            editorTemplate -beginLayout "Motion Blur Deformer Attributes" -collapse 0;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "envelope" ;
                editorTemplate -addControl  "globalScaler";
                editorTemplate -addControl "minimumDistance" ;
                editorTemplate -addControl "maximumDistance" ;
                AEaddRampControl "falloffRamp" ;
                AEaddRampControl "shapeRamp" ;
            editorTemplate -endLayout;
            // Add base node attributes
            AEdependNodeTemplate $nodeName;
            // Add extra atttributes
            editorTemplate -addExtraControls;
        editorTemplate -endScrollLayout;
    }
'''