import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
from maya.mel import eval as mel_eval
 
class FxsMatrixNode(OpenMayaMPx.MPxNode):
    kPluginNodeId = OpenMaya.MTypeId(0x00000003)
    type_name = "FxsMatrixNode"

    aInput = OpenMaya.MObject()

    aBasisXOutput0 = None
    aBasisXOutput1 = None
    aBasisXOutput2 = None
    aBasisXOutput3 = None

    aBasisYOutput0 = None
    aBasisYOutput1 = None
    aBasisYOutput2 = None
    aBasisYOutput3 = None

    aBasisZOutput0 = None
    aBasisZOutput1 = None
    aBasisZOutput2 = None
    aBasisZOutput3 = None

    aBasisWOutput0 = None
    aBasisWOutput1 = None
    aBasisWOutput2 = None
    aBasisWOutput3 = None

    aOutput = OpenMaya.MObject()
 
    @classmethod
    def initialize(cls):
        nAttr = OpenMaya.MFnNumericAttribute()
        mAttr = OpenMaya.MFnMatrixAttribute()
    
        cls.aBasisXOutput0 = nAttr.create(
            "basisVectorX Output0",
            "bvx0",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisXOutput0)

        cls.aBasisXOutput1 = nAttr.create(
            "basisVectorX Output1",
            "bvx1",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisXOutput1)

        cls.aBasisXOutput2 = nAttr.create(
            "basisVectorX Output2",
            "bvx2",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisXOutput2)

        cls.aBasisXOutput3 = nAttr.create(
            "basisVectorX Output3",
            "bvx3",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisXOutput3)

        #====================================

        cls.aBasisYOutput0 = nAttr.create(
            "basisVectorY Output0",
            "bvy0",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisYOutput0)

        cls.aBasisYOutput1 = nAttr.create(
            "basisVectorY Output1",
            "bvy1",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisYOutput1)

        cls.aBasisYOutput2 = nAttr.create(
            "basisVectorY Output2",
            "bvy2",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisYOutput2)

        cls.aBasisYOutput3 = nAttr.create(
            "basisVectorY Output3",
            "bvy3",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisYOutput3)
        
        #======================================

        cls.aBasisZOutput0 = nAttr.create(
            "basisVectorZ Output0",
            "bvz0",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisZOutput0)

        cls.aBasisZOutput1 = nAttr.create(
            "basisVectorZOutput1",
            "bvz1",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisZOutput1)

        cls.aBasisZOutput2 = nAttr.create(
            "basisVectorZOutput2",
            "bvz2",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisZOutput2)

        cls.aBasisZOutput3 = nAttr.create(
            "basisVectorZOutput3",
            "bvz3",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisZOutput3)

        #========================================
    
        cls.aBasisWOutput0 = nAttr.create(
            "basisVectorWOutput0",
            "bvw0",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisWOutput0)

        cls.aBasisWOutput1 = nAttr.create(
            "basisVectorWOutput1",
            "bvw1",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisWOutput1)

        cls.aBasisWOutput2 = nAttr.create(
            "basisVectorWOutput2",
            "bvw2",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisWOutput2)

        cls.aBasisWOutput3 = nAttr.create(
            "basisVectorWOutput3",
            "bvw3",
            OpenMaya.MFnNumericData.kDouble
        )
        nAttr.writable = False
        nAttr.storable = False
        cls.addAttribute(cls.aBasisWOutput3)

        #=====================================

        cls.aInput = mAttr.create(
            "matrixIn",
            "mIn",
            OpenMaya.MFnMatrixAttribute.kDouble
        )
        nAttr.setKeyable = True
        cls.addAttribute(cls.aInput)
        cls.attributeAffects(cls.aInput, cls.aBasisXOutput0)
        cls.attributeAffects(cls.aInput, cls.aBasisXOutput1)
        cls.attributeAffects(cls.aInput, cls.aBasisXOutput2)
        cls.attributeAffects(cls.aInput, cls.aBasisXOutput3)

        cls.attributeAffects(cls.aInput, cls.aBasisYOutput0)
        cls.attributeAffects(cls.aInput, cls.aBasisYOutput1)
        cls.attributeAffects(cls.aInput, cls.aBasisYOutput2)
        cls.attributeAffects(cls.aInput, cls.aBasisYOutput3)

        cls.attributeAffects(cls.aInput, cls.aBasisZOutput0)
        cls.attributeAffects(cls.aInput, cls.aBasisZOutput1)
        cls.attributeAffects(cls.aInput, cls.aBasisZOutput2)
        cls.attributeAffects(cls.aInput, cls.aBasisZOutput3)

        cls.attributeAffects(cls.aInput, cls.aBasisWOutput0)
        cls.attributeAffects(cls.aInput, cls.aBasisWOutput1)
        cls.attributeAffects(cls.aInput, cls.aBasisWOutput2)
        cls.attributeAffects(cls.aInput, cls.aBasisWOutput3)


    @classmethod
    def creator(cls):
        
        #return OpenMayaMPx.asMPxPtr(FxsMatrixNode())
        return cls()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)
 
    def compute(self, plug, data):
        """if plug != FxsMatrixNode.aOutput:
            return OpenMaya.MStatus.kUnknownParameter"""
 
        inputMatrix = data.inputValue(FxsMatrixNode.aInput).asMatrix()

        # get output values from matrix
        aBasisXoutput0_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[0], 0)
        aBasisXoutput1_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[0], 1)
        aBasisXoutput2_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[0], 2)
        aBasisXoutput3_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[0], 3)

        aBasisYoutput0_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[1], 0)
        aBasisYoutput1_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[1], 1)
        aBasisYoutput2_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[1], 2)
        aBasisYoutput3_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[1], 3)

        aBasisZoutput0_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[2], 0)
        aBasisZoutput1_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[2], 1)
        aBasisZoutput2_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[2], 2)
        aBasisZoutput3_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[2], 3)

        aBasisWoutput0_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[3], 0)
        aBasisWoutput1_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[3], 1)
        aBasisWoutput2_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[3], 2)
        aBasisWoutput3_value = OpenMaya.MScriptUtil.getDoubleArrayItem(inputMatrix[3], 3)

        # get outputs and set corresponding value
        outputX0 = data.outputValue(FxsMatrixNode.aBasisXOutput0)
        outputX0.setDouble(aBasisXoutput0_value)
        outputX1 = data.outputValue(FxsMatrixNode.aBasisXOutput1)
        outputX1.setDouble(aBasisXoutput1_value)
        outputX2 = data.outputValue(FxsMatrixNode.aBasisXOutput2)
        outputX2.setDouble(aBasisXoutput2_value)
        outputX3 = data.outputValue(FxsMatrixNode.aBasisXOutput3)
        outputX3.setDouble(aBasisXoutput3_value)

        outputY0 = data.outputValue(FxsMatrixNode.aBasisYOutput0)
        outputY0.setDouble(aBasisYoutput0_value)
        outputY1 = data.outputValue(FxsMatrixNode.aBasisYOutput1)
        outputY1.setDouble(aBasisYoutput1_value)
        outputY2 = data.outputValue(FxsMatrixNode.aBasisYOutput2)
        outputY2.setDouble(aBasisYoutput2_value)
        outputY3 = data.outputValue(FxsMatrixNode.aBasisYOutput3)
        outputY3.setDouble(aBasisYoutput3_value)

        outputZ0 = data.outputValue(FxsMatrixNode.aBasisZOutput0)
        outputZ0.setDouble(aBasisZoutput0_value)
        outputZ1 = data.outputValue(FxsMatrixNode.aBasisZOutput1)
        outputZ1.setDouble(aBasisZoutput1_value)
        outputZ2 = data.outputValue(FxsMatrixNode.aBasisZOutput2)
        outputZ2.setDouble(aBasisZoutput2_value)
        outputZ3 = data.outputValue(FxsMatrixNode.aBasisZOutput3)
        outputZ3.setDouble(aBasisZoutput3_value)

        outputW0 = data.outputValue(FxsMatrixNode.aBasisWOutput0)
        outputW0.setDouble(aBasisWoutput0_value)
        outputW1 = data.outputValue(FxsMatrixNode.aBasisWOutput1)
        outputW1.setDouble(aBasisWoutput1_value)
        outputW2 = data.outputValue(FxsMatrixNode.aBasisWOutput2)
        outputW2.setDouble(aBasisWoutput2_value)
        outputW3 = data.outputValue(FxsMatrixNode.aBasisWOutput3)
        outputW3.setDouble(aBasisWoutput3_value)

        data.setClean(plug)
        #return OpenMaya.MStatus.kSuccess
 
 
def initializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj, 'Felix Abadie', '1.0', 'Any')
    try:
        plugin.registerNode(
            FxsMatrixNode.type_name,
            FxsMatrixNode.kPluginNodeId, 
            FxsMatrixNode.creator, 
            FxsMatrixNode.initialize)
    except:
        raise RuntimeError('Failed to register node')
    
    mel_eval( gui_template )
 

def uninitializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj)
    try:
        plugin.deregisterNode(FxsMatrixNode.kPluginNodeId)
    except:
        raise RuntimeError('Failed to register node')
    
gui_template = '''
    global proc AEFxsMatrixNodeTemplate( string $nodeName )
    {
        editorTemplate -beginScrollLayout;
            // Add attributes to show in attribute editor.
            editorTemplate -beginLayout "Matrix 4x4 Attributes" -collapse 0;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "basisVectorXOutput0" ;
                editorTemplate -addControl  "basisVectorXOutput1" ;
                editorTemplate -addControl  "basisVectorXOutput2" ;
                editorTemplate -addControl  "basisVectorXOutput3" ;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "basisVectorYOutput0" ;
                editorTemplate -addControl  "basisVectorYOutput1" ;
                editorTemplate -addControl  "basisVectorYOutput2" ;
                editorTemplate -addControl  "basisVectorYOutput3" ;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "basisVectorZOutput0" ;
                editorTemplate -addControl  "basisVectorZOutput1" ;
                editorTemplate -addControl  "basisVectorZOutput2" ;
                editorTemplate -addControl  "basisVectorZOutput3" ;
                editorTemplate -addSeparator;
                editorTemplate -addControl  "basisVectorWOutput0" ;
                editorTemplate -addControl  "basisVectorWOutput1" ;
                editorTemplate -addControl  "basisVectorWOutput2" ;
                editorTemplate -addControl  "basisVectorWOutput3" ;     
            editorTemplate -endLayout;
            // Add base node attributes
            AEdependNodeTemplate $nodeName;
            // Add extra atttributes
            editorTemplate -addExtraControls;
        editorTemplate -endScrollLayout;
    }
'''