import argparse
import pathlib

from .core import all_polytwisters
from .core.common import normalize_polytwister_name
from .blender import export_blends
from .blender import render_blends
from .blender import make_video


def main():
    parser = argparse.ArgumentParser("run_full_pipeline")
    parser.add_argument("polytwister", help="Name of polytwister.")
    parser.add_argument("n", type=int, help="Number of animation frames, not including two blank frames.")
    parser.add_argument("out_dir", help="Out directory.")
    args = parser.parse_args()

    polytwister_name = normalize_polytwister_name(args.polytwister)
    polytwister = all_polytwisters.get_polytwister(polytwister_name)
    num_frames = args.n

    if num_frames > 10_000:
        raise ValueError("Too many frames (> 10,000).")

    root_dir = pathlib.Path(args.out_dir)
    root_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = root_dir / "sections"
    blend_file = root_dir / "animation.blend"
    render_frames_dir = root_dir / "render_frames"
    animation_mp4 = root_dir / "animation.mp4"
    animation_gif = root_dir / "animation.gif"

    if not sections_dir.exists():
        # Import here to avoid an unnecessary wait when importing CadQuery, which can be slow.
        from .core import hard_polytwister_section
        hard_polytwister_section.render_all_sections_as_objs(
            polytwister, num_frames, sections_dir, progress_bar=True
        )
    if not blend_file.exists():
        export_blends.export_directory_as_blend(sections_dir, blend_file)
    if not render_frames_dir.exists():
        render_blends.render_blend(blend_file, render_frames_dir)
    if not animation_mp4.exists():
        make_video.make_mp4(render_frames_dir, animation_mp4)
    if not animation_gif.exists():
        make_video.make_gif(render_frames_dir, animation_gif)


if __name__ == "__main__":
    main()