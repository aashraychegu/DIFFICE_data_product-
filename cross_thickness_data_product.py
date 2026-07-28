from pathlib import Path
from string import Template
from itertools import product
import datetime
from utils import process_one_data_product, load_netcdf, flatten_netcdf, load_parquet, flatten_parquet, patch_config

from tqdm import tqdm
# pyrefly: ignore [missing-import]
import rioxarray as rxr


tstr = datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
tout = tqdm.write

data_product_name = "cross_thickness"

cwd = Path(".").resolve()
adjoint_dir = cwd / "../adjoint-ISSM"
data_dir = cwd / "data" 
output_location = cwd / "product" / data_product_name
output_location.mkdir(exist_ok=True, parents = True)

for file in output_location.iterdir():
    file.unlink(missing_ok = True)

imgs_dir = cwd  / "imgs"
imgs_dir.mkdir(exist_ok=True)
imgs_save_dir = imgs_dir / data_product_name
for file in imgs_save_dir.iterdir():
    file.unlink(missing_ok = True)

template_dir = cwd / "templates"

thickness_dataspecs = {"bedmachine": {"path": data_dir / "thickness_bm4.nc", "type": "netcdf"}, "bedmap": {"path" : data_dir / "bedmap3.parquet", "type": "parquet"}}
velocity_paths = sorted(list(data_dir.glob("velocity_*.nc")))
shelf_names = ["Amery", "RnFlch", "LarsenC", "LarsenD", "Ross"]
buffersize = .1

method_reference = dict(
        netcdf = dict(load = load_netcdf,  flatten = flatten_netcdf),
        parquet = dict(load = load_parquet, flatten = flatten_parquet)
    )

thickness_datasources = {}
for key, thickness_dataspec in thickness_dataspecs.items():
    path = thickness_dataspec["path"]
    source_type = thickness_dataspec["type"]
    source = method_reference[source_type]["load"](path)
    thickness_datasources[key] = dict(source = source, type = source_type)
print("\n")

velocity_names = list(map(lambda velocity_path: velocity_path.stem.split(".")[0], velocity_paths))
triplets = list(product(thickness_datasources, velocity_names, shelf_names))

velocity_ncs = {}
for velocity_name, velocity_path in tqdm(zip(velocity_names, velocity_paths),desc = "Populating Velocity NetCDF files"):
    velocity_nc = rxr.open_rasterio(velocity_path)[["VX","VY","MASK"]]
    velocity_nc["VX"] = velocity_nc["VX"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    velocity_nc["VY"] = velocity_nc["VY"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    velocity_nc["MASK"] = velocity_nc["MASK"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    velocity_ncs[velocity_name] = velocity_nc.rio.write_crs("EPSG:3031")

for (thickness_datasource_key, velocity_name, shelf_name) in tqdm(triplets, desc = "Processing File:"):
    name = f"{shelf_name}__{velocity_name}__{thickness_datasource_key}"
    exp_path: Path = adjoint_dir / "out" / shelf_name / "Geometry" / f"{shelf_name}_Outline.exp"
    source_type = thickness_datasources[thickness_datasource_key]["type"]
    process_one_data_product(
        name = name,
        exp_path=exp_path, 
        output_location=output_location, 
        velocity_nc=velocity_ncs[velocity_name], 
        thickness_source=thickness_datasources[thickness_datasource_key]["source"], 
        thickness_flatten_function=method_reference[source_type]["flatten"],
        imgs_path = imgs_save_dir
    )
    
    patches = {
        "artifacts.output_dir" : f"/oak/stanford/groups/cyaolai/AashrayChegu/DIFFICE_out/{data_product_name}-{tstr}/{name}/",
        "data.source" : f"/oak/stanford/groups/cyaolai/AashrayChegu/data-product/product/{data_product_name}/{name}.mat",
        "name" : f"{name}",
    }
    patch_config(template = template_dir / "template.yaml", patches = patches, save_path=output_location / f"{name}.yaml", )

