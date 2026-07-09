import pymel.core as pm

# copied from previous projects
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

class StickyLipManager:
    def __init__(self):
        self.win_id = "fxs_sticky_lip_deformer_win"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        with pm.window(self.win_id, title="Sticky Lip Manager") as win:
            with pm.columnLayout(adj=True):
                self.mesh = TextFieldHelper("Select Mesh")
                self.upper_lip_set = TextFieldHelper("Select Upper Lip Set")
                self.lower_lip_set = TextFieldHelper("Select Lower Lip Set")

                with pm.horizontalLayout():
                    pm.button(label="Cancel")
                    pm.button(label="OK", command=self.execute)

    def execute(self, *args):
        
        mesh_name = self.mesh.control.getText()
        
        lower_set = pm.sets(self.lower_lip_set.control.getText(), query=True)
        lower_flat = pm.filterExpand((str(m) for m in lower_set), selectionMask=31, expand=True) # Gets rid of the range shit
        lower_indices = [int(m.split('[')[1].split(']')[0]) for m in lower_flat] # Gets rid of array stuff
        
        print(f"Lower Indices: {lower_indices}")

        upper_set = pm.sets(self.upper_lip_set.control.getText(), query=True)
        upper_flat = pm.filterExpand((str(m) for m in upper_set), selectionMask=31, expand=True)
        upper_indices = [int(m.split('[')[1].split(']')[0]) for m in upper_flat]

        print(f"Upper Indices: {upper_indices}")

        lower_positions = []
        for idx in lower_indices:
            vtx = pm.PyNode(f"{mesh_name}.vtx[{idx}]")
            lower_positions.append(vtx.getPosition(space="world"))

        print(f"Lower positions: {lower_positions}")

        upper_positions = []
        for idx in upper_indices:
            vtx = pm.PyNode(f"{mesh_name}.vtx[{idx}]")
            upper_positions.append(vtx.getPosition(space="world"))
        
        print(f"Upper positions: {upper_positions}")


        # assign to each lower vertex a corresponding vertex from upper set. A bit simple but probably better than doing this at runtime
        partner_indeces = []
        for i, lower_pos in enumerate(lower_positions):
            closestIdx, _ = findClosestVertex(lower_pos, upper_positions)
            partner_indeces.append(upper_indices[closestIdx]) # super important. was previously just closestIdx -> massive mismatches

        print(f"Partner Indices: {partner_indeces}")

        #deformer = pm.createNode("FxsStickyLipDeformer", name="sticky_lip_deformer")
        deformer = pm.deformer(mesh_name, type="FxsStickyLipDeformer")[0]

        pm.setAttr(
            f"{deformer}.lowerLipIndeces",  
            lower_indices,
            type="Int32Array"
        )

        print(f"lowerLipIndeces Attr: {pm.getAttr(f'{deformer}.lowerLipIndeces')}")

        pm.setAttr(
            f"{deformer}.upperLipIndeces",
            partner_indeces,
            type="Int32Array"
        )

        print(f"upperLipIndeces Attr: {pm.getAttr(f'{deformer}.upperLipIndeces')}")


# might need rework or at least a closer watch
def findClosestVertex(sourcePos, targetPositions):
    minDist = float('inf') # set to super small number
    closestIndex = -1

    for i, targetPos in enumerate(targetPositions):
        dx = sourcePos.x - targetPos.x
        dy = sourcePos.y - targetPos.y
        dz = sourcePos.z - targetPos.z
        dist = dx*dx + dy*dy + dz*dz

        if dist < minDist:
            minDist = dist
            closestIndex = i # set new index

    return closestIndex, minDist


StickyLipManager()