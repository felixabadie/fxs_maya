from contextlib import contextmanager
from pathlib import Path
import pymel.core as pm
import numpy as np
import os


tpose_ref = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss\tpose_ref.jpg"
export_dir = Path(r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss")


#Rotation Limits als Python Dictionary
joint_rotation_ranges = {
    "root_jnt_x": (-15, 15),
    "root_jnt_z": (-15, 15),
    "spine_01_jnt_x": (-10, 10),
    "spine_01_jnt_z": (-10, 10),
    "spine_02_jnt_x": (-10, 10),
    "spine_02_jnt_z": (-10, 10),
    "spine_03_jnt_x": (-10, 10),
    "spine_03_jnt_z": (-10, 10),
    "neck_jnt_x": (-10, 10),
    "neck_jnt_y": (-10, 10),
    "neck_jnt_z": (-10, 10),
    "l_clavicle_jnt_y": (-70, 0),
    "l_shoulder_jnt_y": (-65, 0),
    "l_ellbow_jnt_z": (-110, 110),
    "r_clavicle_jnt_y": (-70, 0),
    "r_shoulder_jnt_y": (-65, 0),
    "r_ellbow_jnt_z": (-110, 110),
    "l_leg_jnt_x": (-65, 65),
    "l_leg_jnt_y": (0, 20),
    "l_leg_jnt_z": (-50, 90),
    "l_knee_jnt_y": (0, 90),
    "r_leg_jnt_x": (-65, 65),
    "r_leg_jnt_y": (0, 20),
    "r_leg_jnt_z": (-50, 90),
    "r_knee_jnt_y": (0, 90)
}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


@contextmanager
def viewport_overrides(
        color=(0.0, 0.0, 0.0), multi_sampling=True, sample_count=16
):
    """Temporarily overrides viewport settings for screenshot capture.

    Args:
        color (tuple): RGB color for the viewport background.
        multi_sampling (bool): Enable or disable multi-sampling.
        sample_count (int): Number of samples for multi-sampling.

    Yields:
        None: Context manager to apply viewport settings.
    """
    original_color = pm.displayRGBColor("background", query=True)
    original_multi_sampling = pm.getAttr(
        "hardwareRenderingGlobals.multiSampleEnable"
    )
    original_sample_count = pm.getAttr(
        "hardwareRenderingGlobals.multiSampleCount"
    )

    pm.displayRGBColor("background", *color)
    pm.setAttr(
        "hardwareRenderingGlobals.multiSampleEnable", multi_sampling
    )
    pm.setAttr(
        "hardwareRenderingGlobals.multiSampleCount", sample_count
    )
    try:
        yield
    finally:
        pm.displayRGBColor("background", *original_color)
        pm.setAttr(
            "hardwareRenderingGlobals.multiSampleEnable",
            original_multi_sampling
        )
        pm.setAttr(
            "hardwareRenderingGlobals.multiSampleCount",
            original_sample_count
        )


def create(output_path, width=256, height=256, **kwargs):
    """Capture the current Maya viewport and save it as an image.

    Args:
        output_path (str): Path where the screenshot will be saved.
        width (int): Width of the screenshot.
        height (int): Height of the screenshot.
        **kwargs: Additional arguments for viewport overrides.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    extension = os.path.splitext(output_path)[-1].strip(".")
    print("Creating Screenshot")

    current_frame = pm.currentTime(q=True)

    with viewport_overrides(**kwargs):
        pm.refresh(force=True)
        pm.playblast(
            format="image",
            filename=output_path,
            forceOverwrite=True,
            showOrnaments=False,
            width=width,
            height=height,
            percent=100,
            compression=extension,
            viewer=False,
            startTime=current_frame,
            endTime=current_frame,
            completeFilename=output_path
        )


def set_joint_rotation(joint_axis, value):
    """ joint_axis z.B. 'spine_01_jnt_x', value in Grad """
    joint_name, axis = joint_axis.rsplit("_", 1)
    joint = pm.PyNode(joint_name)
    attr = f"rotate{axis.upper()}"
    joint.setAttr(attr, value)


if __name__ == "__main__":

    steps_per_axis = 10
    frame = 1

    # === Reset aller definierten Achsen ===
    for joint_axis in joint_rotation_ranges.keys():
        set_joint_rotation(joint_axis, 0)

    #axis_influence = {}

    #Create 10 Poses per active joint axis
    for joint_axis, (min_val, max_val) in joint_rotation_ranges.items():
        values = np.linspace(min_val, max_val, steps_per_axis)
        
        #ssim_scores = []

        output_dir = os.path.join(export_dir, joint_axis)
        ensure_dir(Path(output_dir))

        for val in values:
            pm.currentTime(frame)
            set_joint_rotation(joint_axis, val)

            # Keyframe setzen (nur die Achse, die sich bewegt)
            joint_name = joint_axis.rsplit("_", 1)[0]
            pm.setKeyframe(joint_name, attribute="rotate" + joint_axis[-1].upper())
            
            image_name = os.path.join(output_dir, f"{joint_axis}_{val}.jpg")
            create(
                output_path=image_name,
                width=1024,
                height=1024
            )

            for reset_axis in joint_rotation_ranges.keys():
                set_joint_rotation(reset_axis, 0)
                pm.setKeyframe(joint_name, attribute="rotate" + reset_axis[-1].upper())

            frame += 1