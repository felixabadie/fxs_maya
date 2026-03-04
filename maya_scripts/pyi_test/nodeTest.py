import pymel.core as pm

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
    
    def __init__(
        self,
        name: str = "remapValue",
        n: str = "",
        parent=None,
        p=None,
        shared: bool = False,
        s: bool = False,
        skipSelect: bool = False,
        ss: bool = False,
        **kwargs
    ):
                               
        node_name = n if n else name
        node_parent = p if p else parent

        create_kwargs = {
            'name': node_name,
            'shared': shared or s,
            'skipSelect': skipSelect or ss
        }
                               
        if node_parent is not None:
            create_kwargs['parent'] = node_parent
        
        # add additional kwargs
        create_kwargs.update(kwargs)
        
        self._node: pm.nodetypes.RemapValue = pm.createNode("remapValue", **create_kwargs)
        self.message = self._node.attr('message')
        self.caching = self._node.attr('caching')
        self.frozen = self._node.attr('frozen')
        self.isHistoricallyInteresting = self._node.attr('isHistoricallyInteresting')
        self.nodeState = self._node.attr('nodeState')
        self.binMembership = self._node.attr('binMembership')
        self.inputValue = self._node.attr('inputValue')
        self.inputMin = self._node.attr('inputMin')
        self.inputMax = self._node.attr('inputMax')
        self.outputMin = self._node.attr('outputMin')
        self.outputMax = self._node.attr('outputMax')
        self.value = self._node.attr('value')
        self.color = self._node.attr('color')
        self.outValue = self._node.attr('outValue')
        self.outColor = self._node.attr('outColor')
        self.outColorR = self._node.attr('outColorR')
        self.outColorG = self._node.attr('outColorG')
        self.outColorB = self._node.attr('outColorB')
    
    @property
    def node(self):
        return self._node