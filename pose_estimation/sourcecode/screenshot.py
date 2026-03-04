"""Utility to capture the current Maya viewport."""
from maya import cmds
import contextlib
import os


@contextlib.contextmanager
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
    original_color = cmds.displayRGBColor("background", query=True)
    original_multi_sampling = cmds.getAttr(
        "hardwareRenderingGlobals.multiSampleEnable"
    )
    original_sample_count = cmds.getAttr(
        "hardwareRenderingGlobals.multiSampleCount"
    )

    cmds.displayRGBColor("background", *color)
    cmds.setAttr(
        "hardwareRenderingGlobals.multiSampleEnable", multi_sampling
    )
    cmds.setAttr(
        "hardwareRenderingGlobals.multiSampleCount", sample_count
    )
    try:
        yield
    finally:
        cmds.displayRGBColor("background", *original_color)
        cmds.setAttr(
            "hardwareRenderingGlobals.multiSampleEnable",
            original_multi_sampling
        )
        cmds.setAttr(
            "hardwareRenderingGlobals.multiSampleCount",
            original_sample_count
        )

def create(output_path, width=1920, height=1080, **kwargs):
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
    with viewport_overrides(**kwargs):
        cmds.refresh(force=True),
        cmds.playblast(
            format="image",
            filename=output_path,
            forceOverwrite=True,
            showOrnaments=False,
            width=width,
            height=height,
            percent=100,
            compression=extension,
            viewer=False,
            frame=cmds.currentTime(q=1),
            completeFilename=output_path
        )

    print(f"Viewport image saved to: {output_path}")

output_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Abbildungen_für_Bachelorarbeit\test.png"

create(
    output_path=output_dir,
    width=1920,
    height=1080,
    )

