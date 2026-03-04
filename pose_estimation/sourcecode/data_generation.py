import random
import json
import os
import subprocess
import shutil
import logging
from contextlib import contextmanager
from pathlib import Path
from maya import cmds

training_data_path = Path(r"D:\fa026_Bachelor\Training_data")

total_start_frame = int(cmds.playbackOptions(q=True, min=True))
total_end_frame = int(cmds.playbackOptions(q=True, max=True))

print("total_end_frame: ", total_end_frame)


#Paths to Exported Data

#dict_export_path = Path(training_data_path + r"\Dicts\tmp")
dict_export_path = training_data_path / r"Dicts\tmp"
#image_export_path = Path(training_data_path + r"\Rendered_Images\tmp")
image_export_path = training_data_path / r"Rendered_Images\tmp"

#classification_overview_path = Path(training_data_path + r"\Classification_overview")
classification_overview_path = training_data_path / r"Classification_overview"

#data_generation_scene_temp = Path(training_data_path + r"\copy_scene\data_generation_temp")
data_generation_scene_temp = training_data_path / r"copy_scene\data_generation_temp"



#Rotation Limits als Python Dictionary
joint_rotation_ranges = {
    "root_jnt": [(-15, 15), (0, 0), (-15, 15)],
    "spine_01_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "spine_02_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "spine_03_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "neck_jnt": [(-10, 10), (-10, 10), (-10, 10)],
    "l_clavicle_jnt": [(0, 0), (-70, 0), (0, 0)],
    "l_shoulder_jnt": [(0, 0), (-65, 0), (0, 0)],
    "l_ellbow_jnt": [(0, 0), (0, 0), (-110, 110)],
    "r_clavicle_jnt": [(0, 0), (-70, 0), (0, 0)],
    "r_shoulder_jnt": [(0, 0), (-65, 0), (0, 0)],
    "r_ellbow_jnt": [(0, 0), (0, 0), (-110, 110)],
    "l_leg_jnt": [(-65, 65), (0, 20), (-50, 90)],
    "l_knee_jnt": [(0, 0), (0, 90), (0, 0)],
    "r_leg_jnt": [(-65, 65), (0, 20), (-50, 90)],
    "r_knee_jnt": [(0, 0), (0, 90), (0, 0)],
}

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def get_joint_chain_from_dict(rotation_dict):
    
    """
    Instead of rig traversal joints are taken out of joint_rotation_ranges (was hotfix but stuck)
    """

    joints = []
    missing = []
    for name in rotation_dict.keys():
        if cmds.objExists(name):
            joints.append(name)
        else:
            missing.append(name) 
    if missing:
        print("Felhlende Joints im Rig: {missing}")
    return joints


def export_json_data(data, dict_export_path):

    """Exports all Rotations in a Python Dictionary inside a JSON  file for readability"""

    current_frame = int(cmds.currentTime(q=True))
    filename = f"image_{current_frame:06}.json"
    full_path = os.path.join(dict_export_path, filename)
    
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)


def export_classification_as_json(joint_chain, export_path):

    """Exports additional file to see which index equals which joint (useful overwiew)"""

    classification_overview = {}

    for index, joint in enumerate(joint_chain):
        classification_overview[joint] = [index]

    filename = "classification_overview.json"
    full_path = os.path.join(export_path, filename)
    with open(full_path, "w") as f:
        json.dump(classification_overview, f, indent=2)


def save_custom_copy(source_path, destination):

    """creates a copy of scene as a precaution"""

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source filoe not found: {source_path}")
    
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copy2(source_path, destination)


def render_defined_sequence(image_export_path):

    """
    Sets all important parametes (filename, fileformat, scene-range, image resolution, cameram render engine)
    and starts Render.exe as a batch render
    """

    filename = "image_"
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", filename, type="string")
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 6)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)
    cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
    cmds.setAttr("defaultRenderGlobals.animation", 1)
    cmds.setAttr("defaultRenderGlobals.animationRange", 0)
    cmds.setAttr("defaultRenderGlobals.startFrame", total_start_frame)
    cmds.setAttr("defaultRenderGlobals.endFrame", total_end_frame)
    cmds.setAttr("resolution1.width", 256)
    cmds.setAttr("resolution1.height", 256)
    cmds.setAttr("render_camShape.renderable", 1)
    cmds.setAttr("perspShape.renderable", 0)
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaHardware2", type="string")

    scenefile = cmds.file(q=True, sn=True)

    try:
        cmds.saveFile(force=True)
        print("scene saved")
    except:
        print("scene not saved")

    try:
        save_custom_copy(scenefile, data_generation_scene_temp)
        print("saved copy")
    except:
        print("save copy failed")
    
    maya_location = os.environ.get("MAYA_LOCATION", r"C:\Program Files\Autodesk\Maya2026")
    mayabatch = os.path.join(maya_location, "bin", "Render.exe")

    #cmd = [mayabatch, "-rd", str(image_export_path), scenefile]
    cmd = [
    mayabatch,
    "-s", str(total_start_frame),
    "-e", str(total_end_frame),
    "-im", "image_",  # optional
    "-rd", str(image_export_path),
    scenefile
    ]
    print(cmd)
    subprocess.Popen(cmd)


#Definiert Rotations-Regeln für Spine_joints (in Abhängigkeit voneinander)
def dynamic_spine_axis_range(parent_rotation, axis_range):
    if parent_rotation > 0:
        return (0, 10)
    elif parent_rotation < 0:
        return (-10, 0)
    else:
        return axis_range


#Definiert Rotations-Regeln für Clavicle_joints
def rotation_range_for_clavicle():
    range = random.choices(
        population=[(1, 2), (-78, -1)],
        weights=[0.8, 0.2],
        k=1
    )
    return range[0]


#Definiert Rotations-Regeln für Ellbow_joints (in Abhängigkeit zu Shoulder)
def rotation_range_for_ellbow(clavicle_rotation, shoulder_rotation):
    if clavicle_rotation < -50:
        return (-110, 100)
    if -35 < shoulder_rotation < -30:
        return (-100, 110)
    elif shoulder_rotation < -35:
        return (-43.381, 110)
    else:
        return (-110, 110)


#Definiert Rotations-Regeln für l_leg
def rotation_range_for_l_leg():
    range = random.choices(
        population=[[(-65, 0), (0, 20) ,(-10, 90)], [(0, 65), (0, 20), (-50, 10)]],
        weights=[0.6, 0.4],
        k=1
    )
    return range[0]


#Definiert Rotation für r_leg (in Abhängigkeit zu l_leg -> Vermeidet Überschneiden der Beine usw / Ist für Datenoptimierung) 
def rotation_range_for_r_leg(x_rotation, y_rotation):
    rot_range = []

    if x_rotation < 0:
        if x_rotation < -50 and y_rotation > 5:
            range = random.choices(
                population=[[(-65, 0), (0, 20) ,(-30, 50)], [(0, 50), (0, 20), (-30, 10)]],
                weights=[0.5, 0.5],
                k=1
            )
            rot_range = range[0]
        else:
            rot_range = [(-65, 0), (0, 20) ,(-10, 90)]
    else:
        if x_rotation > 50 and y_rotation > 5:
            range = random.choices(
                population=[[(-65, 0), (0, 20) ,(-30, 50)], [(0, 50), (0, 20), (-30, 10)]],
                weights=[0.5, 0.5],
                k=1
            )
            rot_range = range[0]
        else:
            rot_range = [(0, 65), (0, 20), (-50, 10)]
    
    return rot_range


def apply_custom_random_rotation(joint_chain, joint_rotation_ranges):

    """
    Assigns every Joint a random Rotation from joint_rotation_ranges. For some joints (spine, clavicle, shoulder, ellbow, leg) 
    additional Rules werde defined to overwrite rotations in relation to other joints (if necessary).

    All Rotationvalues get saved and exported and the pose is keyframed for rendering
    """

    joint_frame_data = {}

    l_leg_rot_range = []
    l_leg_x_rotation = 0
    l_leg_y_rotation = 0

    for index, joint in enumerate(joint_chain):
        joint_name = os.path.basename(joint)
        if joint_name in joint_rotation_ranges:
            axis_ranges = joint_rotation_ranges[joint_name]
            if joint_name in ["l_clavicle_jnt", "r_clavicle_jnt"]:
                clavicle_range = rotation_range_for_clavicle()
                random_rot = [
                    0.0,
                    random.uniform(*clavicle_range),
                    0.0
                ]
            elif joint_name in ["l_shoulder_jnt", "r_shoulder_jnt"]:
                parent = cmds.listRelatives(joint, parent=True)[0]
                y_rot = cmds.getAttr(f"{parent}.rotateY")
                if -10 < y_rot < 0:
                    random_rot = [
                        random.uniform(*axis_ranges[0]), 
                        0.0, 
                        random.uniform(*axis_ranges[2])
                        ]
                elif y_rot < -10:
                    random_rot = [
                        random.uniform(*axis_ranges[0]), 
                        0.0, 
                        0.0
                        ]
                else:
                    random_rot = [
                        random.uniform(*axis_ranges[0]),
                        random.uniform(*axis_ranges[1]),
                        random.uniform(*axis_ranges[2])
                        ]
            
            elif joint_name in ["l_ellbow_jnt", "r_ellbow_jnt"]:
                shoulder = cmds.listRelatives(joint, parent=True)[0]
                clavicle = cmds.listRelatives(shoulder, parent=True)[0]
                shoulder_y_rot = cmds.getAttr(f"{shoulder}.rotateY")
                clavicle_y_rot = cmds.getAttr(f"{clavicle}.rotateY")

                ellbow_z_range = rotation_range_for_ellbow(clavicle_y_rot, shoulder_y_rot)

                random_rot = [
                    random.uniform(*axis_ranges[0]),
                    random.uniform(*axis_ranges[1]),
                    random.uniform(*ellbow_z_range),
                ]

            elif joint_name in ["spine_02_jnt", "spine_03_jnt"]:
                parent = cmds.listRelatives(joint, parent=True)[0]
                x_rot = cmds.getAttr(f"{parent}.rotateX")
                y_rot = cmds.getAttr(f"{parent}.rotateY")
                z_rot = cmds.getAttr(f"{parent}.rotateZ")
                
                x_range = dynamic_spine_axis_range(x_rot, axis_ranges[0])
                #y_range = dynamic_spine_axis_range(y_rot, axis_ranges[1])
                z_range = dynamic_spine_axis_range(z_rot, axis_ranges[2])
                
                random_rot = [
                    random.uniform(*x_range),
                    random.uniform(*axis_ranges[1]),
                    random.uniform(*z_range)
                ]
            
            elif joint_name == "l_leg_jnt":
                l_leg_rot_range = rotation_range_for_l_leg()

                random_rot = [
                    random.uniform(*l_leg_rot_range[0]),
                    random.uniform(*l_leg_rot_range[1]),
                    random.uniform(*l_leg_rot_range[2])
                ]
            
            elif joint_name == "r_leg_jnt":
                
                r_leg_rot_range = rotation_range_for_r_leg(l_leg_x_rotation, l_leg_y_rotation)

                random_rot = [
                    random.uniform(*r_leg_rot_range[0]),
                    random.uniform(*r_leg_rot_range[1]),
                    random.uniform(*l_leg_rot_range[2])
                ]

            else:
                    random_rot = [
                        random.uniform(*axis_ranges[0]),
                        random.uniform(*axis_ranges[1]),
                        random.uniform(*axis_ranges[2])
                    ]    

            cmds.setAttr(f"{joint}.rotate", *random_rot)
            
            if joint_name == "l_leg_jnt":
                l_leg_x_rotation = cmds.getAttr(f"{joint}.rotateX")
                l_leg_y_rotation = cmds.getAttr(f"{joint}.rotateY")
            joint_frame_data[index] = random_rot
          
        else:
            pass
     
    cmds.setKeyframe(joint_chain)
    export_json_data(joint_frame_data, dict_export_path)


@contextmanager
def refresh_suspended():

    """Interrupts viewport updates for increased performance (Thanks Julian)"""

    logger = logging.getLogger("Publish Context")
    logger.info("Viewport refreshing suspended.")
    cmds.refresh(suspend=True)
    try:
        yield
    finally:
        logger.info("Viewport refreshing resumed.")
        cmds.refresh(suspend=False)


class DataGeneration():

    """Datageneration class that will create GUI and start program"""

    def __init__(self):
        self.win_id = "data_generation"
        if cmds.window(self.win_id, query=True, exists=True):
            cmds.deleteUI(self.win_id)
        cmds.window(self.win_id, title="Pose Data Generation For Machine Learning", widthHeight=(400, 150), backgroundColor=(0, 0.153, 0.212))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
        cmds.text(
            label=(
                "Tool explanation:\n"
                "                                                                   \n"
                "This tool will go over the rig assuming it contains the following joints:\n"
                "- root_jnt\n"
                "- spine_01_jnt\n"
                "- spine_02_jnt\n"
                "- spine_03_jnt\n"
                "- neck_jnt\n"
                "- l_clavicle_jnt\n"
                "- l_shoulder_jnt\n"
                "- l_ellbow_jnt\n"
                "- r_clavicle_jnt\n"
                "- r_shoulder_jnt\n"
                "- r_ellbow_jnt\n"
                "- l_leg_jnt:\n"
                "- l_knee_jnt:\n"
                "- r_leg_jnt:\n"
                "- r_knee_jnt:\n"
                "Additional Joints can be added but should assigned in order\n"
                "                                                                   \n"
                "It will assign a random rotation based on defined joint rotation ranges.\n"
                "Every frame will be keyed and at the end it will start a batch render.\n"
                "The files will be rendered/saved to predetermined locations\n"
                "In order to run faster it will disable viewport actualization and will run over a limited playback range"                                                                                                        
            ), 
            align="left"
        )

        cmds.rowLayout(numberOfColumns=2)
        cmds.button(label="Start", c=self.execute)
        cmds.button(label="Cancel", c=self.cancel)
        cmds.setParent('..')

        cmds.showWindow(self.win_id)
    
    def execute(self, *args):

        """
        Starts datageneration and executes aapply_custom_random_rotation() for every frame.
        After Datageneration start render_defined_sequence()
        """        

        ensure_dir(training_data_path)
        ensure_dir(dict_export_path)
        ensure_dir(image_export_path)
        ensure_dir(classification_overview_path)
        ensure_dir(data_generation_scene_temp)

        joint_hierarchy = get_joint_chain_from_dict(joint_rotation_ranges)
        fixed_range = 500 # set size of playbackrange

        
        cmds.optionVar(iv=("CachedPlaybackEnable", 0))     #additonal performance incase needed
        cmds.optionVar(iv=("CachedPlaybackEnableGPU", 0))
        cmds.undoInfo(state=False) # turn off undo queue to make program go brrrrrrr
        try:

            with refresh_suspended():
                for epoch_start in range(total_start_frame, total_end_frame +1, fixed_range): # using epochs to minimize the time maya needs to load
                    print("epoch loop called")
                    epoch_end = min(epoch_start + fixed_range -1, total_end_frame)

                    cmds.playbackOptions(min=epoch_start, max=epoch_end) # setting new playback-range

                    for frame in range(int(epoch_start), int(epoch_end) + 1):
                        cmds.currentTime(frame)
                        apply_custom_random_rotation(joint_hierarchy, joint_rotation_ranges)
            
            
                export_classification_as_json(joint_hierarchy, classification_overview_path) 
                render_defined_sequence(image_export_path)

        finally:
            cmds.undoInfo(state=True)
            cmds.refresh(suspend=False)
            cmds.optionVar(iv=("CachedPlaybackEnable", 1))    # additonal performance incase needed
            cmds.optionVar(iv=("CachedPlaybackEnableGPU", 1))
            cmds.undoInfo(state=True)


    def cancel(self, *args):
        cmds.deleteUI(self.win_id)

if __name__ == "__main__":
    DataGeneration()