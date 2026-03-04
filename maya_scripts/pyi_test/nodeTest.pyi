import pymel.core as pm


class RemapvalueValueSlot(object):
    '''One element of remapValue.value[i]'''
    value_Position: pm.Attribute
    value_FloatValue: pm.Attribute
    value_Interp: pm.Attribute

class RemapvalueValueArray(object):
    '''Provides autocompletion for array of RemapvalueValueSlot'''
    def __getitem__(self, idx: int) -> RemapvalueValueSlot: ...
    def __iter__(self): ...
    def __len__(self) -> int: ...

class RemapValueColorSlotColor(object):
    """
    Docstring for RemapValueColorSlotColor
    """
    color_colorR: pm.Attribute
    color_colorG: pm.Attribute
    color_colorB: pm.Attribute

class RemapvalueColorSlot(object):
    '''One element of remapValue.color[i]'''
    color_Position: pm.Attribute
    color_Color: RemapValueColorSlotColor
    color_Interp: pm.Attribute

class RemapvalueColorArray(object):
    '''Provides autocompletion for array of RemapvalueColorSlot'''
    def __getitem__(self, idx: int) -> RemapvalueColorSlot: ...
    def __iter__(self): ...
    def __len__(self) -> int: ...


class __remapValue(object):
    '''Remap Value
is a utility node that allows you to take an input
 scalar value and remap its value using a gradient. One can remap this to a new output
 scalar value and/or color.
The input value is used to select a point along the gradient to use for the output value.
 The value specified by the Min attribute determines the input value that indexes the far left of
 the ramp while the Max attribute determines the value at far right.
The outColor is determined by the color gradient and the outValue by the value gradient. If one only uses
 the outValue, for example, then the color gradient is ignored.'''
    _node: pm.nodetypes.RemapValue

    def __init__(self, name: str = 'remapValue', n: str = '', parent: str | pm.PyNode | None = None, p: str | pm.PyNode | None = None, shared: bool = False, s: bool = False, skipSelect: bool = False, ss: bool = False, **kwargs) -> None: ...
    message: pm.Attribute
    caching: pm.Attribute
    frozen: pm.Attribute
    isHistoricallyInteresting: pm.Attribute
    nodeState: pm.Attribute
    binMembership: pm.Attribute
    inputValue: pm.Attribute
    inputMin: pm.Attribute
    inputMax: pm.Attribute
    outputMin: pm.Attribute
    outputMax: pm.Attribute
    value: RemapvalueValueArray
    color: RemapvalueColorArray
    outValue: pm.Attribute
    outColor: pm.Attribute
    outColorR: pm.Attribute
    outColorG: pm.Attribute
    outColorB: pm.Attribute

    def node(self) -> pm.nodetypes.RemapValue: ...