import pathlib
import subprocess
import sys

import PySimpleGUI as gui

import common
import soft_polytwisters
import hard_polytwisters

all_polytwisters = (
    soft_polytwisters.ALL_SOFT_POLYTWISTERS
    + hard_polytwisters.ALL_HARD_POLYTWISTERS
)

polytwister_names = [polytwister["names"][0].capitalize() for polytwister in all_polytwisters]


def main():
    layout = [
        [gui.Text("Polytwister"), gui.Combo(polytwister_names, readonly=True, key="polytwister")],
        [
            gui.Frame("Cross section", [
                [
                    gui.Text("Cross section W-coordinate:"),
                    gui.Slider((-1.0, 1.0), 0.0, resolution=0.0, orientation="horizontal", key="w"),
                ],
                [
                    gui.Checkbox("Normalize size", default=True, key="normalize"),
                ],
                [
                    gui.Button("Open section in Blender"),
                    gui.In(key="mesh_file", visible=False, enable_events=True),
                    gui.FileSaveAs(
                        "Export mesh...",
                        initial_folder=str(pathlib.Path(__file__).parent),
                        file_types=[("STL", ".stl")],
                    ),
                ]
            ])
        ],
        [
            gui.Frame("Render animation", [
                [
                    gui.Text("Duration (s):"),
                    gui.Slider((1.0, 10.0), 100 / 24, resolution=0.0, orientation="horizontal", key="duration"),
                ],
                [
                    gui.Checkbox("Export video when done", default=True, key="export_video_when_done"),
                ],
                [
                    gui.Checkbox("Send SMS when done", default=True, key="send_sms_when_done"),
                ],
                [
                    gui.Button("Render animation"),
                ],
            ]),
        ],
        [
            gui.Frame("Video export", [
                [
                    gui.Text("Animation folder:"),
                    gui.In(size=20, key="animation_folder"),
                    gui.FolderBrowse(
                        "Browse...",
                        initial_folder=str(pathlib.Path(__file__).parent),
                    ),
                ],
                [
                    gui.In(size=20, key="video_file", visible=False, enable_events=True),
                    gui.SaveAs(
                        "Export video...",
                        initial_folder=str(pathlib.Path(__file__).parent),
                        file_types=[("MP4", ".mp4")],
                    ),
                ],
            ]),
        ],
    ]

    window = gui.Window("Polytwister Studio", layout)

    while True:
        event, values = window.read()
        if event == gui.WINDOW_CLOSED:
            break
        polytwister = all_polytwisters[polytwister_names.index(values["polytwister"])]
        polytwister_name = polytwister["names"][0]
        w = values["w"]
        mesh_file = values["mesh_file"]
        num_frames = int(round(values["duration"] * 24))
        animation_folder = values["animation_folder"]
        if event == "Open section in Blender":
            window.close()
            options = ["--normalize"] if values["normalize"] else []
            common.run_blender_script(
                common.BLENDER_SCRIPT,
                [],
                [polytwister_name, str(w)] + options,
                interactive=True,
            )
            break
        elif event == "mesh_file":
            window.close()
            common.run_blender_script(
                common.BLENDER_SCRIPT,
                [],
                [polytwister_name, str(w), "--mesh-out", mesh_file],
                interactive=False,
            )
            break
        elif event == "Render animation":
            window.close()
            subprocess.run([
                sys.executable, common.RENDER_ANIMATION_SCRIPT, polytwister_name, num_frames
            ], check=True)
            if values["export_video_when_done"]:
                subprocess.run([
                    sys.executable,
                    common.MAKE_VIDEO_SCRIPT,
                    str(common.ROOT / "out" / polytwister_name)
                ], check=True)
            if values["send_sms_when_done"]:
                subprocess.run([
                    sys.executable,
                    common.NOTIFY_SCRIPT,
                ], check=True)
            break
        elif event == "video_file":
            window.close()
            command = [sys.executable, common.MAKE_VIDEO_SCRIPT, animation_folder]
            subprocess.run(command, check=True)
            break

    window.close()

if __name__ == "__main__":
    main()