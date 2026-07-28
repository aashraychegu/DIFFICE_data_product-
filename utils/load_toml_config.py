import tomllib
from pathlib import Path

def load_toml_config(path: Path):
    with open(path,"rb") as f:
        data = tomllib.load(f)
    out = {}
    for i in data:
        out[i] = tuple(data[i]["bbox"])
    return out

