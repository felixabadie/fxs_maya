import control
import pymel.core as pm
from prox_node_setup.generated_nodes import *
from manual_node_classes import create_guide, colorize, create_groups, create_groups_


# Matrix-Ketten Datenstruktur
def _create_matrix_chain(self, chain_config):
    """
    chain_config = {
        'name': 'upper_base',
        'operations': [
            {'type': 'pom', 'source': guide.worldMatrix[0], 'parent': parentGuide.worldInverseMatrix[0]},
            {'type': 'mult', 'inputs': [0, parent_input.worldMatrix[0]]},  # 0 = result from previous
            {'type': 'remove_main_scale', 'main_input': main_input.worldInverseMatrix[0]},
            {'type': 'remove_scale_shear'},
            {'type': 'mult', 'inputs': [0, main_input.offsetParentMatrix]}
        ]
    }
    """
    results = []
    
    for i, op in enumerate(chain_config['operations']):
        op_name = f"{chain_config['name']}_{i}"
        
        if op['type'] == 'pom':
            node = self._create_pom(op_name, op['source'], op['parent'])
        elif op['type'] == 'mult':
            node = multMatrix(name=f"{self.name}_{op_name}")
            for j, inp in enumerate(op['inputs']):
                source = results[inp].matrixSum if isinstance(inp, int) else inp
                pm.connectAttr(source, node.matrixIn[j])
        elif op['type'] == 'remove_main_scale':
            node = self._remove_main_scale(op_name, results[-1].matrixSum, op['main_input'])
        elif op['type'] == 'remove_scale_shear':
            node = pickMatrix(name=f"{self.name}_{op_name}")
            pm.connectAttr(results[-1].outputMatrix if hasattr(results[-1], 'outputMatrix') 
                          else results[-1].matrixSum, node.inputMatrix)
            node.useScale.set(0)
            node.useShear.set(0)
        
        results.append(node)
    
    return results

# Verwendung:
upper_chain = self._create_matrix_chain({
    'name': 'upper_base',
    'operations': [
        {'type': 'pom', 'source': self.upper_FK_guide_outWM.outputMatrix, 
         'parent': parent_moduleGuide_input.worldInverseMatrix[0]},
        {'type': 'mult', 'inputs': [0, parent_module_input_WM.matrixSum]},
        {'type': 'remove_main_scale', 'main_input': main_input.worldInverseMatrix[0]},
        {'type': 'remove_scale_shear'},
        {'type': 'mult', 'inputs': [0, main_input.offsetParentMatrix]}
    ]
})

upper_base_POM = upper_chain[0]
upper_baseWM = upper_chain[1]
upper_baseWM_noMainScale = upper_chain[2]
upper_baseWM_noScaleM = upper_chain[3]
upper_WM_test = upper_chain[4]



#Space Switch Batch Processing
def _setup_space_switches(self):
    """Richtet alle Space Switches auf einmal ein"""
    
    # Definition aller Space Switches
    space_switch_configs = [
        {
            'ctrl_name': 'upper_FK_ctrl',
            'parent_matrix_node': self.upper_FK_ctrl_rotWM,
            'guide_matrix': self.upper_FK_guide_outWM.outputMatrix,
            'spaces': ['parent_module', 'main', 'world']
        },
        {
            'ctrl_name': 'hand_IK_ctrl',
            'parent_matrix_node': self.hand_IK_ctrl_WM,
            'guide_matrix': self.hand_FK_guide_outWM.outputMatrix,
            'spaces': ['parent_module', 'main', 'world']
        },
        {
            'ctrl_name': 'elbow_IK',
            'parent_matrix_node': self.elbow_IK_baseWM,
            'guide_matrix': self.orientPlane_guide.outputMatrix,
            'spaces': ['parent_module', 'main', 'world']
        }
    ]
    
    # Inputs vorher erstellt
    guide_inputs = {
        'parent_module': parent_moduleGuide_input,
        'main': mainGuide_input,
        'world': None
    }
    
    world_inputs = {
        'parent_module': parent_module_input_WM.matrixSum,
        'main': main_input.offsetParentMatrix,
        'world': None
    }
    
    for config in space_switch_configs:
        for idx, space in enumerate(config['spaces']):
            if space == 'world':
                # World space hat kein POM
                pm.connectAttr(
                    self._get_space_enable(config['ctrl_name'], space, idx).output,
                    config['parent_matrix_node'].target[idx].enableTarget
                )
                pm.connectAttr(
                    config['guide_matrix'],
                    config['parent_matrix_node'].target[idx].offsetMatrix
                )
            else:
                pom = self._create_pom(
                    f"{config['ctrl_name']}_{space}SpacePOM",
                    config['guide_matrix'],
                    guide_inputs[space].worldInverseMatrix[0]
                )
                
                pm.connectAttr(
                    self._get_space_enable(config['ctrl_name'], space, idx).output,
                    config['parent_matrix_node'].target[idx].enableTarget
                )
                pm.connectAttr(
                    world_inputs[space],
                    config['parent_matrix_node'].target[idx].targetMatrix
                )
                pm.connectAttr(
                    pom.matrixSum,
                    config['parent_matrix_node'].target[idx].offsetMatrix
                )

def _get_space_enable(self, ctrl_name, space_name, index):
    """Erstellt oder holt Space Enable Node"""
    node_name = f"{ctrl_name}_{space_name}SpaceEnable"
    
    enable = equal(name=f"{self.name}_{node_name}")
    pm.connectAttr(self.settings_ctrl.node.space, enable.input1)
    enable.input2.set(index)
    
    return enable



#Soft IK als separate Klasse
class SoftIKSolver:
    def __init__(self, limb_name, settings_ctrl):
        self.name = limb_name
        self.settings = settings_ctrl
        
    def create(self, upper_length, lower_length, clamped_length, clamped_length_squared):
        """Erstellt komplettes Soft IK System"""
        
        # Basis IK Solver
        base_ik = self._create_base_ik_nodes(upper_length, lower_length, 
                                              clamped_length, clamped_length_squared)
        
        # Blend Curves
        blend_curve = self._create_blend_curve_system(base_ik['upper_cosValue_remapped'])
        
        # Height Calculations
        heights = self._calculate_heights(
            base_ik['upper_cosValue'],
            base_ik['upper_cosValue_squared'],
            blend_curve,
            upper_length,
            lower_length
        )
        
        # Final Scalers
        scalers = self._calculate_scalers(heights, base_ik['upper_cosValue_squared'])
        
        return {
            'upper_scaler': scalers['upper_scaler_enable'],
            'lower_scaler': scalers['lower_scaler_enable']
        }
    
    def _create_base_ik_nodes(self, upper_length, lower_length, 
                              clamped_length, clamped_length_squared):
        # Dein existing IK solver code
        ik_solver = self._create_ik_solver_setup(...)
        
        # Remap
        upper_cosValue_remapped = remapValue(name=f"{self.name}_upper_softIK_cosValueRemapped")
        pm.connectAttr(self.settings.node.softIkStart, upper_cosValue_remapped.inputMin)
        pm.connectAttr(ik_solver['upper_cosValue'].output, upper_cosValue_remapped.inputValue)
        
        return {
            'upper_cosValue': ik_solver['upper_cosValue'],
            'upper_cosValue_squared': ik_solver['upper_cosValueSquared'],
            'upper_cosValue_remapped': upper_cosValue_remapped
        }
    
    def _create_blend_curve_system(self, remapped_value):
        """Erstellt die 3 Blend Curve Optionen"""
        
        # Cubic
        cubic = multiply(name=f"{self.name}_softIK_cubic")
        for i in range(3):
            pm.connectAttr(remapped_value.outValue, cubic.input_[i])
        
        # Smoothstep
        smoothstep = smoothStep(name=f"{self.name}_softIK_smoothstep")
        pm.connectAttr(remapped_value.outValue, smoothstep.input_)
        smoothstep.rightEdge.set(1)
        
        # Ease in/out (Custom)
        ease = self._create_ease_curve(remapped_value.outValue)
        
        # Selector
        selector = choice(name=f"{self.name}_softIK_blendcurve_selector")
        pm.connectAttr(self.settings.node.softIkCurve, selector.selector)
        pm.connectAttr(ease, selector.input_[0])
        pm.connectAttr(smoothstep.output, selector.input_[1])
        pm.connectAttr(cubic.output, selector.input_[2])
        
        return selector
    
    def _create_ease_curve(self, input_value):
        """Erstellt Ease In/Out Kurve - komprimiert"""
        # Condition für < 0.5 oder >= 0.5
        condition = condition(name=f"{self.name}_ease_condition")
        pm.connectAttr(input_value, condition.firstTerm)
        condition.secondTerm.set(0.5)
        condition.operation.set(4)
        
        # Branch 1: x < 0.5 -> 4x³
        branch1 = multiply(name=f"{self.name}_ease_branch1")
        pm.connectAttr(input_value, branch1.input_[0])
        pm.connectAttr(input_value, branch1.input_[1])
        pm.connectAttr(input_value, branch1.input_[2])
        branch1.input_[3].set(4)
        
        # Branch 2: x >= 0.5 -> 1 - ((2-2x)³)/2
        temp1 = multiply(name=f"{self.name}_ease_temp1")
        temp1.input_[0].set(-2)
        pm.connectAttr(input_value, temp1.input_[1])
        
        temp2 = sum_(name=f"{self.name}_ease_temp2")
        pm.connectAttr(temp1.output, temp2.input_[0])
        temp2.input_[1].set(2)
        
        temp3 = power(name=f"{self.name}_ease_temp3")
        pm.connectAttr(temp2.output, temp3.input_)
        temp3.exponent.set(3)
        
        temp4 = divide(name=f"{self.name}_ease_temp4")
        pm.connectAttr(temp3.output, temp4.input1)
        temp4.input2.set(2)
        
        branch2 = subtract(name=f"{self.name}_ease_branch2")
        branch2.input1.set(1)
        pm.connectAttr(temp4.output, branch2.input2)
        
        pm.connectAttr(branch2.output, condition.colorIfFalseR)
        pm.connectAttr(branch1.output, condition.colorIfTrueR)
        
        return condition.outColorR

# Verwendung im Limb __init__:
soft_ik_solver = SoftIKSolver(self.name, self.settings_ctrl)
soft_ik_result = soft_ik_solver.create(
    upper_length.output,
    lower_length.output, 
    clampedLength.output,
    clampedLength_squared.output
)

upper_softIK_scaler_enable = soft_ik_result['upper_scaler']
lower_softIK_scaler_enable = soft_ik_result['lower_scaler']




#Controller Setup Batch
def _create_fk_chain(self, segments):
    """
    segments = [
        {'name': 'upper', 'guide_wm': upper_FK_ctrl_WM.outputMatrix},
        {'name': 'lower', 'guide_wm': lower_FK_ctrl_WM.matrixSum, 'parent': upper_FK_ctrl},
        {'name': 'hand', 'guide_wm': hand_FK_ctrl_WM.matrixSum, 'parent': lower_FK_ctrl}
    ]
    """
    ctrls = []
    
    for segment in segments:
        ctrl = control.create_circle_ctrl(
            name=f"{self.name}_{segment['name']}_FK_ctrl",
            ctrl_size=2,
            normal=(1, 0, 0)
        )
        colorize(ctrl.node, self.fk_color)
        
        pm.connectAttr(segment['guide_wm'], ctrl.offsetParentMatrix)
        ctrls.append(ctrl)
    
    return ctrls

# Verwendung:
fk_ctrls = self._create_fk_chain([
    {'name': 'upper', 'guide_wm': upper_FK_ctrl_WM.outputMatrix},
    {'name': 'lower', 'guide_wm': lower_FK_ctrl_WM.matrixSum},
    {'name': 'hand', 'guide_wm': hand_FK_ctrl_WM.matrixSum}
])

upper_FK_ctrl, lower_FK_ctrl, hand_FK_ctrl = fk_ctrls



#Axis Extraction Helper
def _extract_matrix_axes(self, name, matrix_attr):
    """Extrahiert alle 3 Achsen aus einer Matrix"""
    axes = {}
    
    for i, axis_name in enumerate(['X', 'Y', 'Z']):
        axis = rowFromMatrix(name=f"{self.name}_{name}_axis{axis_name}")
        pm.connectAttr(matrix_attr, axis.matrix)
        axis.input_.set(i)
        axes[axis_name] = axis
    
    return axes

# Verwendung:
lower_FK_ctrl_POM = self._create_pom(...)
lower_axes = self._extract_matrix_axes('lower_FK_ctrl_POM', lower_FK_ctrl_POM.matrixSum)

lower_FK_ctrl_POM_manualScale = self._create_fourByFourMatrix(
    name="lower_FK_ctrl_POM_manualScale",
    inputs=[
        [lower_axes['X'].outputX, lower_axes['X'].outputY, 
         lower_axes['X'].outputZ, lower_axes['X'].outputW],
        [lower_axes['Y'].outputX, lower_axes['Y'].outputY, 
         lower_axes['Y'].outputZ, lower_axes['Y'].outputW],
        [lower_axes['Z'].outputX, lower_axes['Z'].outputY, 
         lower_axes['Z'].outputZ, lower_axes['Z'].outputW],
        [upper_length_manualScale.output]
    ])



#IK/FK Blending as Helper
def _create_ikfk_blend(self, name, fk_source, ik_source, blend_attr):
    """Erstellt IK/FK Blend für Position oder Rotation"""
    
    blend = blendMatrix(name=f"{self.name}_{name}_blend")
    pm.connectAttr(fk_source, blend.inputMatrix)
    pm.connectAttr(ik_source, blend.target[0].targetMatrix)
    pm.connectAttr(blend_attr, blend.target[0].weight)
    
    return blend

# Verwendung - reduziert 30+ Zeilen auf ~10:
blends = {
    'upper': self._create_ikfk_blend(
        'upper_WM',
        upper_FK_ctrl.worldMatrix[0],
        upper_IK_WM.matrixSum,
        self.settings_ctrl.node.useIK
    ),
    'lower_local': self._create_ikfk_blend(
        'lower_localMatrix',
        lower_FK_ctrl_outLocalMatrix.matrixSum,
        lower_IK_localRotMatrix.output,
        self.settings_ctrl.node.useIK
    ),
    'hand_local': self._create_ikfk_blend(
        'hand_localMatrix',
        hand_FK_ctrl_outLocalMatrix.matrixSum,
        hand_IK_localMatrix.output,
        self.settings_ctrl.node.useIK
    )
}

upper_WM = blends['upper']
# ... etc



#Wiederholende Attr Verbindungen komprimieren
def _batch_connect_attrs(self, connections):
    """
    connections = [
        (source.attr, target.attr),
        (source2.attr, target2.attr),
        ...
    ]
    """
    for source, target in connections:
        pm.connectAttr(source, target)

# Verwendung:
self._batch_connect_attrs([
    (lower_tangent.outputMatrix, lower_ribbon_pin_transform_grp.offsetParentMatrix),
    (lower_ribbon_pin_transform_grp.worldMatrix[0], lower_ribbon_ctrl.offsetParentMatrix),
    (lower_ribbon_ctrl.worldMatrix[0], lower_ribbon_pin_start_transform_grp.offsetParentMatrix),
    (roundness_negate.output, lower_ribbon_pin_start_transform_grp.translateX),
    # ... etc
])



#Position extractor Helper
def _extract_world_positions(self, matrix_dict):
    """Extrahiert World Positions aus mehreren Matrices
    
    matrix_dict = {
        'upper': upper_WM.outputMatrix,
        'lower': lower_WM.matrixSum,
        'hand': hand_WM.matrixSum
    }
    """
    positions = {}
    
    for name, matrix in matrix_dict.items():
        tfm = translationFromMatrix(name=f"{self.name}_{name}_WPos")
        pm.connectAttr(matrix, tfm.input_)
        positions[name] = tfm
    
    return positions

# Verwendung:
world_positions = self._extract_world_positions({
    'upper': upper_WM.outputMatrix,
    'lower': lower_WM.matrixSum,
    'lower_IK': lower_IK_WM.matrixSum,
    'hand': hand_WM.matrixSum,
    'elbowLock_IK_ctrl': self.elbowLock_IK_ctrl.worldMatrix[0],
    'upper_base': upper_WM_test.matrixSum
})

# Jetzt für Helper Curves verwenden:
elbowLock_IK_helper = self._create_connection_helper(
    'elbowLock_IK',
    world_positions['elbowLock_IK_ctrl'].output,
    world_positions['lower_IK'].output,
    ik_color
)



#Settings Attributes batch creation
def _create_settings_attributes(self):
    """Erstellt alle Settings Attribute auf einmal"""
    
    attrs_config = [
        {'name': 'useIK', 'nice': 'use IK', 'type': 'float', 'default': 0, 'min': 0, 'max': 1},
        {'name': 'upperLengthScaler', 'nice': 'Upper Length Scaler', 'type': 'float', 'default': 1, 'min': 0},
        {'name': 'lowerLengthScaler', 'nice': 'Lower Length Scaler', 'type': 'float', 'default': 1, 'min': 0},
        {'name': 'elbowIkBlendpos', 'nice': 'Elbow IK Blendpos', 'type': 'float', 'default': 0.5, 'min': 0, 'max': 1},
        {'name': 'enableIkStretch', 'nice': 'Enable IK Stretch', 'type': 'float', 'default': 1, 'min': 0, 'max': 1},
        {'name': 'softIkStart', 'nice': 'Soft IK Start', 'type': 'float', 'default': 0.8, 'min': 0, 'max': 1},
        {'name': 'enableSoftIk', 'nice': 'Enable Soft IK', 'type': 'bool', 'default': 0},
        {'name': 'softIkCurve', 'nice': 'Soft IK Curve', 'type': 'enum', 
         'enum': 'custom_curve:smoothstep_curve:cubic_curve', 'default': 0},
        {'name': 'ribbonRoundness', 'nice': 'Ribbon Roundness', 'type': 'float', 
         'default': 1, 'min': 0.01, 'max': 5}
    ]
    
    for attr in attrs_config:
        kwargs = {
            'attr': attr['name'],
            'niceName': attr['nice'],
            'attributeType': attr['type'],
            'defaultValue': attr['default'],
            'hidden': False,
            'keyable': True
        }
        
        if 'min' in attr:
            kwargs['minValue'] = attr['min']
        if 'max' in attr:
            kwargs['maxValue'] = attr['max']
        if 'enum' in attr:
            kwargs['enumName'] = attr['enum']
        
        self.settings_ctrl.node.addAttr(**kwargs)