import io

import numpy as np
import json

VERSION = "0.1.0"


def write_obj(vertices: np.ndarray, triangles: np.ndarray, file: io.FileIO):
    for row in vertices:
        file.write(f"v {row[0]} {row[1]} {row[2]}\n")
    for row in triangles:
        file.write(f"f {row[0] + 1} {row[1] + 1} {row[2] + 1}\n")


def normalize_polytwister_name(name):
    return name.replace("_", " ")


def write_manifest_file(polytwister, file_names, out_dir):
    with open(out_dir / "manifest.json", "x") as file:
        json.dump(
            {
                "directory_type": "sections",
                "software_version": VERSION,
                "polytwister_spec": polytwister,
                "file_names": file_names,
            },
            file
        )
