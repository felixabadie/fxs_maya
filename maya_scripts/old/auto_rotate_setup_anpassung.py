from typing import List
import pymel.core as pc
from pymel.core.general import Attribute
from pymel.core.nodetypes import FrameCache, Transform


def create_delay_caches(from_attributes: List[Attribute], to_attributes: List[Attribute], delay: int=1) -> List[FrameCache]:
    for fa, ta in zip(from_attributes, to_attributes):
        cache_node = pc.createNode("frameCache", name=f"{fa.name().replace('.', '_')}_fc")
        fa >> cache_node.stream
        cache_node.attr(f"past[{delay}]") >> ta
        

def create_measure_setup(ctrl: Transform, relevant_dir="tz"):
    name = ctrl.name()

    # Create locators and group
    on_time_loc = pc.spaceLocator(n=f"{name}_ontime_loc")
    delay_loc = pc.spaceLocator(n=f"{name}_delay_loc")
    dist_loc = pc.spaceLocator(n=f"{name}_dist_loc")
    pc.parent(dist_loc, on_time_loc)
    measure_grp = pc.group(on_time_loc, delay_loc, n=f"{name}_measure_grp")

    pc.parentConstraint(ctrl, on_time_loc, mo=False)
    pc.parentConstraint(delay_loc, dist_loc, mo=False)
    
    # Add attributes for measure_grp
    measure_grp.addAttr("start_frame", at="double", k=True, dv=1)
    measure_grp.addAttr("wheel_radius", at="double", k=True, dv=1)
    measure_grp.addAttr("rotation", at="double", k=True, dv=0)
    measure_grp.addAttr("sign", at="long", k=True, dv=1)

    # Create the frameCache setup
    attrs = ["tx","ty","tz","rx","ry","rz"]
    on_time_attrs = [on_time_loc.attr(a) for a in attrs]
    delay_loc_attrs = [delay_loc.attr(a) for a in attrs]

    create_delay_caches(on_time_attrs, delay_loc_attrs, 1)

    # Create the expression that just accumulates the traveled distance and calculates the rotation
    # 57.295 is precalculated 180 / PI
    exp = """if(frame == {mgn}.start_frame){{{mgn}.rotation = 0;}}
    {mgn}.rotation = {mgn}.rotation + 2.0825 * {dln}.{relevant_dir} * {mgn}.sign;
    """.format(
        mgn=measure_grp.name(),
        dln=dist_loc.name(),
        relevant_dir=relevant_dir
    )

    pc.expression(s=exp, ae=1, uc="all")


# mit ausgewähltem ketten-controller könnte das schon funktionieren...
# vorraussetzung ist, dass die vorgeschlagene Richtung (tz) stimmt.
animated_controller = pc.selected()[0]
create_measure_setup(animated_controller, relevant_dir="tz")