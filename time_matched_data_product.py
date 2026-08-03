from sys import argv
from pathlib import Path
from itertools import product
from tqdm import tqdm
tout = tqdm.write
import datetime
from utils import load_netcdf, flatten_netcdf, load_parquet, flatten_parquet,  process_one_data_product, patch_config, load_shelf_toml, load_mappings_toml
# pyrefly: ignore [missing-import]
import rioxarray as rxr
# pyrefly: ignore [missing-import]
import argparse
import shutil

print("All Configs:")
cwd = Path(".").resolve()
template_dir = cwd / "configs"
for filepath in sorted(list(template_dir.glob("*.toml"))):
    print(f" > {filepath.stem:<50} | {filepath.name}")

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, help="Config file name (without .toml extension)")
parser.add_argument("--yaml-only", action="store_true", help="Only regenerate YAML files")
parser.add_argument("--copy-from", help="Source to copy from", default = None)
args = parser.parse_args()

config_file_name = args.config
mapping_path = template_dir / f"{config_file_name}.toml"
data_product_name, time_mappings, template = load_mappings_toml(mapping_path)

config_path = template_dir / "shelves.toml"
data_folder = cwd / "data" 
product_location = cwd / "product"
output_location = product_location / data_product_name
output_location.mkdir(exist_ok=True, parents = True)
imgs_dir = cwd  / "imgs"
imgs_dir.mkdir(exist_ok=True)
imgs_save_dir = imgs_dir / data_product_name
imgs_save_dir.mkdir(exist_ok=True)

config_only = args.yaml_only
if config_only:
    for file in output_location.glob("*.yaml"):
        file.unlink(missing_ok = True)
    copy_dir = Path(product_location / args.copy_from)
    if copy_dir.exists():
        for pattern in ("*.mat", "*.wkt"):
            for file in copy_dir.glob(pattern):
                shutil.copy2(file, output_location / file.name)
    else:
        print(f"Copy from directory {copy_dir} not found")
        exit(67)

if not config_only:
    for file in output_location.iterdir():
        file.unlink(missing_ok = True)

    for file in imgs_save_dir.iterdir():
        file.unlink(missing_ok = True)

time_str = datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S")

shelf_to_bbox = load_shelf_toml(config_path)
shelf_names = list(shelf_to_bbox.keys())

method_reference = dict(
        netcdf = dict(load = load_netcdf,  flatten = flatten_netcdf),
        parquet = dict(load = load_parquet, flatten = flatten_parquet)
    )

filetype_mapping = {"nc":"netcdf","parquet":"parquet"}
def get_dataset_type(name):
    return filetype_mapping[name.split(".")[1]]

def get_name(filepath):
    return filepath.split(".")[0]

velocity_files = set()
thickness_files = set()
for name, data_files in time_mappings.items():
    velocity_files.update(set(data_files["velocity"]))
    thickness_files.update(set(data_files["thickness"]))

velocity_files = sorted(velocity_files)
thickness_files = sorted(thickness_files)

thickness_datasources = {}
velocity_ncs = {}

if not config_only:
    # pyrefly: ignore [invalid-syntax]
    for thickness_file in (pbar:=tqdm(thickness_files)):
        pbar.set_description(f"Loading Thickness: {thickness_file}")
        thickness_file_path = data_folder / thickness_file
        source_type = get_dataset_type(thickness_file)
        source = method_reference[source_type]["load"](thickness_file_path)
        thickness_datasources[thickness_file] = dict(source = source, function = method_reference[source_type]["flatten"])
    else:
        pbar.set_description("All thickness files loaded.")
    # pyrefly: ignore [invalid-syntax]
    for velocity_filename in (pbar := tqdm(velocity_files)):
        pbar.set_description(f"Loading Velocity: {velocity_filename}")
        velocity_name = get_name(velocity_filename)
        velocity_path = data_folder / velocity_filename
        velocity_nc = rxr.open_rasterio(velocity_path)[["VX","VY","MASK"]]
        velocity_nc["VX"] = velocity_nc["VX"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
        velocity_nc["VY"] = velocity_nc["VY"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
        velocity_nc["MASK"] = velocity_nc["MASK"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
        velocity_ncs[velocity_name] = velocity_nc.rio.write_crs("EPSG:3031")
    else:
        pbar.set_description("All velocity files loaded.")

triplets = []
for shelf_name, time_mapping in tqdm(product(shelf_names,time_mappings.values())):
    for velocity_file, thickness_file in product(time_mapping["velocity"],time_mapping["thickness"]):
        triplets.append((shelf_name, velocity_file, thickness_file))

print(f"Generated {len(triplets)} triplets \n{'---'*30}")

# pyrefly: ignore [invalid-syntax]
for (shelf_name, velocity_file, thickness_source_key) in (pbar := tqdm(triplets, desc = f"Processing {len(triplets)} triplets:")):
    velocity_name = get_name(velocity_file)
    thickness_name = get_name(thickness_source_key)
    name = f"{shelf_name}__{velocity_name}__{thickness_name}"
    pbar.set_description(f"Processing {name}:")
    
    if not config_only:
        if not process_one_data_product(
            name = name, 
            bbox = shelf_to_bbox[shelf_name], 
            output_location = output_location, 
            velocity_nc = velocity_ncs[velocity_name],
            thickness_source = thickness_datasources[thickness_source_key]["source"],
            thickness_flatten_function = thickness_datasources[thickness_source_key]["function"],
            imgs_path = imgs_save_dir,
            ):
            continue
    
    patches = {
        "artifacts.output_dir" : f"/oak/stanford/groups/cyaolai/AashrayChegu/DIFFICE_out/{data_product_name}__configGen_{time_str}/{name}/",
        "data.source" : f"/oak/stanford/groups/cyaolai/AashrayChegu/data-product/product/{data_product_name}/{name}.mat",
        "name" : f"{name}",
    }
    if Path(patches["data.source"]).exists():
        patch_config(template = template_dir / template, patches = patches, save_path=output_location / f"{name}.yaml", )