import pymel.core as pm


class NodeToCode:
    """
    Interface for node to code
    """
    def __init__(self):
        self.win_id = "fa_node_to_code"

        if pm.window(self.win_id, query=True, exists=True):
            pm.deleteUI(self.win_id)

        """
        Buttons
        """

    def execute(self, *args):
        pass



NodeToCode()