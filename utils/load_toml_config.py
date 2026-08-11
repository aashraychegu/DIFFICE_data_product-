import tomllib
from pathlib import Path

def load_shelf_toml(path: Path):
    with open(path,"rb") as f:
        data = tomllib.load(f)
    out = {}
    for i in data:
        out[i] = tuple(data[i]["bbox"])
    return out

def load_mappings_toml(mapping_path):
    with open(mapping_path, "rb") as f:
        data = tomllib.load(f)

    data_product_name = data["data_product_name"]
    time_mappings = data["time_mappings"]
    boundary_smoothing = data.get("boundary_smoothing",2000)
    return data_product_name, time_mappings, data["template"], boundary_smoothing, data["data_dir"], data["shelves"]