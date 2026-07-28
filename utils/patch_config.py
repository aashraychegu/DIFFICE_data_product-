from pathlib import Path
from tqdm import tqdm
from .patch_yaml import patch_yaml

def patch_config(template, patches, save_path, print = tqdm.write):
    
    save_path.parents[0].mkdir(exist_ok=True, parents=True)
    
    patch_list = []
    for field, value in patches.items():
        patch_str = f"{field}={value}"
        patch_list.append(patch_str)
    out = patch_yaml(template, patch_list)
    save_path.write_text(out)

    return save_path