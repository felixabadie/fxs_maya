import pymel.core as pm


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


class NodeToCode:
    """
    Interface for node to code
    """
    def __init__(self):
        self.win_id = "fa_node_to_code"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Node to Code exporter") as win:
            with pm.columnLayout(adj=True):
                pm.text(label="Select whatever you want to export. \nIf nothing is selected everything gets exported")
                self.module_name = TextFieldHelper("Node module name: ")
                pm.text(label="Please input a valid and unique name")
                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

        """
        Buttons
        """

    def execute(self, *args):

        deselect = [
            "persp", 
            "top", 
            "front", 
            "side", 
            "lightLinker1", 
            "shapeEditorManager", 
            "poseInterpolatorManager", 
            "layerManager", 
            "defaultLayer", 
            "renderLayerManager", 
            "defaultRenderLayer",
            "defaultArnoldRenderOptions",
            "defaultArnoldFilter",
            "defaultArnoldDriver",
            "defaultArnoldDisplayDriver",
            "defaultArnoldDenoiser",
            "uiConfigurationScriptNode",
            "sceneConfigurationScriptNode",
            "MayaNodeEditorSavedTabsInfo"
        ]

        sel = pm.selected()
        if not sel:
            pm.select(all=True)

            for node in deselect:
                try:
                    pm.select(deselect=node)
                except Exception as e:
                    print(f"Cannot deselect {node}, reason: {e}")
                    continue

        pm.exportSelected(exportPath=None, constraints=True, expressions=True, shader=True, preserveReferences=True, type="mayaAscii")

            



NodeToCode()