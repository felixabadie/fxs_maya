from maya_scripts import registry
from maya_scripts.rig_module.root import RootModule
from maya_scripts.rig_module.spine import SpineModule
from maya_scripts.rig_module.clavicle import ClavicleModule
from maya_scripts.rig_module.base_limb import LimbModule
from maya_scripts.rig_module.leg import LegModule

def _register_modules():
    registry.register_class("RootModule", RootModule)
    registry.register_class("SpineModule", SpineModule)
    registry.register_class("ClavicleModule", ClavicleModule)
    registry.register_class("LimbModule", LimbModule)
    registry.register_class("LegModule", LegModule)

_register_modules()