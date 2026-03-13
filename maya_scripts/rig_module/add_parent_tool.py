import pymel.core as pm


from maya_scripts import registry

def get_module_from_selection():
    selection = pm.selected()
    for node in selection:
        current = node
        while current:
            if current.hasAttr("moduleRegistryKey"):
                key = current.moduleRegistryKey.get()
                return registry.get(key)
            
            
module = get_module_from_selection()

try:
    module.mirror()
except Exception as e:
    print(e)