import pymel.core as pm

_module_registry = {}

def register(name, instance):
    if name in _module_registry:
        pm.warning(f"Registry: '{name}' already exists and will be overwritten")
    _module_registry[name] = instance

def get(name):
    return _module_registry.get(name)

def get_all():
    return _module_registry

def remove_module(name):
    return _module_registry.pop(name)

def remove_all():
    return _module_registry.clear()