import json
import pymel.core as pm

_module_registry = {}
_currently_reconstructing = set()
_MODULE_CLASSES = {}

def register_class(name:str, cls):
    """Einmalig beim Import aufrufen: registry.register_class("ClavicleModule", ClavicleModule)"""
    _MODULE_CLASSES[name] = cls

def register(name, instance):
    _module_registry[name] = instance

def get(name):
    if name in _module_registry:
        return _module_registry[name]
    if name in _currently_reconstructing:
        return None
    return _reconstruct_from_scene(name)

def _reconstruct_from_scene(name:str):
    setup_node_name = f"{name}_SETUP"
    if not pm.objExists(setup_node_name):
        pm.warning(f"Registry: Node '{setup_node_name}' not in scene")
        return None
    
    node = pm.PyNode(setup_node_name)
    
    if not node.hasAttribute("moduleType"):
        pm.warning(f"Registry: No 'moduleType' attribute in '{setup_node_name}'")
        return None
    
    module_type = node.attr("moduleType").get()

    print(f"Module Type (progress check): {module_type}")

    cls = _MODULE_CLASSES.get(module_type)
    if not cls:
        pm.warning(f"Registry: Class '{module_type}' not registered")
        return None
    
    _currently_reconstructing.add(name)

    print("Print _currently_reconstructing: ", _currently_reconstructing)

    try:
        kwargs = {"_reconstruct": True}

        str_attr_map = ["name", "limb_type", "limb_side", "parent_module", "main_module"]

        for attr in str_attr_map:
            if node.hasAttribute(attr):
                kwargs[attr] = str(node.attr(attr).get())
        
        print("Print Kwargs str_attr: ", kwargs)

        optional_int_attrs = ["bind_jnts", "ctrl_size"]
        for attr in optional_int_attrs:
            if node.hasAttribute(attr):
                kwargs[attr] = int(node.attr(attr).get())

        if node.hasAttribute("upperGuideRotX"):
            kwargs["upper_guide_rot"] = (
                float(node.attr("upperGuideRotX").get()),
                0,
                0,
            )

        if node.hasAttribute("inputList"):
            kwargs["input_list"] = json.loads(node.attr("inputList").get())

        if node.hasAttribute("elbowLockList"):
            kwargs["elbow_lock_list"] = json.loads(node.attr("elbowLockList").get())

        print("Kwargs after input list: ", kwargs)

        return cls(**kwargs)
    
    except Exception as e:
        pm.warning(f"Registry: Reconstruction of '{name}' failed: {e}")
        return None
    
    finally:
        _currently_reconstructing.discard(name)

def get_all():
    return _module_registry

def remove_module(name):
    if name in _module_registry:
        del _module_registry[name]

def remove_all():
    pm.warning("registry empty")
    return _module_registry.clear()