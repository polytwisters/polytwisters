from . import common


def render_all_sections_as_objs(
        polytwister,
        num_frames,
        out_dir,
        *,
        soft_resolution=common.DEFAULT_SOFT_POLYTWISTER_RESOLUTION,
        hard_tolerance=common.DEFAULT_HARD_POLYTWISTER_TOLERANCE,
        hard_angular_tolerance=common.DEFAULT_HARD_POLYTWISTER_ANGULAR_TOLERANCE,
        progress_bar=True,
):
    type_ = polytwister["type"]
    if type_ == "soft":
        from . import soft_polytwister_section
        soft_polytwister_section.render_all_sections_as_objs(
            polytwister,
            num_frames,
            out_dir,
            progress_bar=progress_bar,
            resolution=soft_resolution,
        )
    elif type_ == "hard":
        # Prevent extra loading time if polytwister is hard.
        # Modules are imported exactly once so this does not slow down repeated calls, see:
        # https://stackoverflow.com/a/296062
        from . import hard_polytwister_section
        hard_polytwister_section.render_all_sections_as_objs(
            polytwister,
            num_frames,
            out_dir,
            progress_bar=progress_bar,
            tolerance=hard_tolerance,
            angular_tolerance=hard_angular_tolerance,
        )
    else:
        raise ValueError(f"Unrecognized polytwister type: '{type_}'")
