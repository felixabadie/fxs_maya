import math
from maya import cmds
import maya.OpenMaya as OpenMaya
from maya.mel import eval as mel_eval
import maya.OpenMayaMPx as OpenMayaMPx


"""
Some parts taken from Marieke van Neutigem
https://github.com/mvanneutigem/tutorials/blob/master/plugins/deformerTemplate.py

deformer idea derived from Inigo Quilez (Distorting space with sine waves)

f(x, y, z) = (x + sin(y), y + sin(z), z + sin(x)) base distortion function

f(f(f(f(f(p)))))

fn(x, y, z) = [(x + (sin(2^n * y)/2^n)), (y + (sin(2^n * z)/2^n)), (z + (sin(2^n * x)/2^n))] 

"""


# Set globals to the proper cpp cvars. (compatible from maya 2016)
kInput = OpenMayaMPx.cvar.MPxGeometryFilter_input
kInputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
kOutputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom
kEnvelope = OpenMayaMPx.cvar.MPxGeometryFilter_envelope
kGroupId = OpenMayaMPx.cvar.MPxGeometryFilter_groupId


class FxsDistortionDeformer(OpenMayaMPx.MPxDeformerNode):
    type_id = OpenMaya.MTypeId(0x00000010)
    type_name = "FxsDistortionDeformer"

    aDeformIterations = None
    aDeformScale = None


    def __init__(self):
        """Construction"""
        OpenMayaMPx.MPxDeformerNode.__init__(self)

    @classmethod
    def initialize(cls):
        numeric_attr_fn = OpenMaya.MFnNumericAttribute()

        cls.aDeformIterations = numeric_attr_fn.create(
            "deformIterations",
            "di",
            OpenMaya.MFnNumericData.kInt
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.aDeformIterations)

        cls.aDeformScale = numeric_attr_fn.create(
            "deformScale",
            "ds",
            OpenMaya.MFnNumericData.kInt
        )
        numeric_attr_fn.readable = False
        numeric_attr_fn.writable = True
        numeric_attr_fn.keyable = True
        cls.addAttribute(cls.aDeformScale)

        cls.attributeAffects(cls.aDeformIterations, kOutputGeom)
        cls.attributeAffects(cls.aDeformScale, kOutputGeom)


    @classmethod
    def creator(cls):
        """
        Create instance of this class
        """
        return cls()


    def postConstructor(self):
        pass


    def deform(
            self,
            data_block,
            geometry_iterator,
            local_to_world_matrix,
            geometry_index
    ):

        envelope_attribute = kEnvelope
        envelope_value = data_block.inputValue(envelope_attribute).asFloat()

        deform_iterations_value = data_block.inputValue(self.aDeformIterations).asInt()

        deform_scale_value = data_block.inputValue(self.aDeformScale).asInt()

        input_geometry_object = self.getDeformerInputGeometry(
                    data_block,
                    geometry_index
                )

        mesh_fn = OpenMaya.MFnMesh(input_geometry_object)
        mesh_vertex_iterator = OpenMaya.MItMeshVertex(input_geometry_object)

        # original points if necessary
        orig_points = OpenMaya.MPointArray()
        mesh_fn.getPoints(orig_points)


        while not mesh_vertex_iterator.isDone():
            vertex_index = mesh_vertex_iterator.index()

            current_point = OpenMaya.MPoint()
            mesh_fn.getPoint(vertex_index, current_point, OpenMaya.MSpace.kTransform)

            new_point = self.getDeformedPoint(current_point, iterations=deform_iterations_value)
            mesh_vertex_iterator.setPosition(new_point, OpenMaya.MSpace.kTransform)
            mesh_fn.setPoint(vertex_index, new_point, OpenMaya.MSpace.kTransform)

            mesh_vertex_iterator.next()

    def getDeformedPoint(self, point, iterations):
        """
        f(x, y, z) = (x + sin(y), y + sin(z), z + sin(x)) base distortion function
        """

        if iterations <= 0:
            return point

        new_point_x = point.x + math.sin(point.y)
        new_point_y = point.y + math.sin(point.z)
        new_point_z = point.z + math.sin(point.x)
        
        new_point = OpenMaya.MPoint(new_point_x, new_point_y, new_point_z)
        
        return self.getDeformedPoint(new_point, iterations - 1)



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
            FxsDistortionDeformer.type_name,
            FxsDistortionDeformer.type_id,
            FxsDistortionDeformer.creator,
            FxsDistortionDeformer.initialize,
            OpenMayaMPx.MPxNode.kDeformerNode
        )
    except:
        print("failed to register node {0}".format(FxsDistortionDeformer.type_name))
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
        plugin_fn.deregisterNode(FxsDistortionDeformer.type_id)
    except:
        print( "failed to deregister node {0}".format(
            FxsDistortionDeformer.type_name
        ))
        raise


#  Custom attribute editor gui template
gui_template = '''
    global proc AEFxsDistortionDeformerTemplate( string $nodeName )
    {
        editorTemplate -beginScrollLayout;
            // Add attributes to show in attribute editor.
            editorTemplate -beginLayout "Distortion Deformer Attributes" -collapse 0;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "envelope" ;
                editorTemplate -addControl  "deformIterations";
                editorTemplate -addControl "deformScale" ;
            editorTemplate -endLayout;
            // Add base node attributes
            AEdependNodeTemplate $nodeName;
            // Add extra atttributes
            editorTemplate -addExtraControls;
        editorTemplate -endScrollLayout;
    }
'''