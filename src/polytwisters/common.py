import json

VERSION = "0.1.0"


def normalize_polytwister_name(name):
    return name.replace("_", " ")


def write_metadata_file(polytwister, file_names, out_dir):
    with open(out_dir / "metadata.json", "x") as file:
        json.dump(
            {
                "software_version": VERSION,
                "polytwister_spec": polytwister,
                "file_names": file_names,
            },
            file
        )
