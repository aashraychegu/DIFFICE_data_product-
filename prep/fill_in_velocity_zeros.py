from pathlib import Path
# pyrefly: ignore [missing-import]
import rioxarray as rxr
from tqdm import tqdm
# pyrefly: ignore [missing-import]
from rasterio.enums import Resampling
# pyrefly: ignore [missing-import]
import numpy as np
import gc

nodata_value = -32767.0

times = [(1995,2001),(2007,2009),(2014,2017),(2020,2022)]

cwd = Path(".")
data_folder = cwd / "data"
itslive_tifs_folder = data_folder/"itslive_mean"

# pyrefly: ignore [invalid-syntax]
for t1,t2 in (pbar := tqdm(times)):
    pbar.set_description(f"1/6 | Patching Velocity: {t1}-{t2}")
    velocity_name = f"velocity_{t1}-{t2}"
    velocity_path = data_folder / f"{velocity_name}.nc"
    itslive_vx_path = itslive_tifs_folder / f"vx_mean_{t1}-{t2}.tif"
    itslive_vy_path = itslive_tifs_folder / f"vy_mean_{t1}-{t2}.tif"

    pbar.set_description(f"2/6 | Loading Files for Velocity: {t1}-{t2}")
    velocity_nc = rxr.open_rasterio(velocity_path)[["VX","VY","MASK"]]
    velocity_nc = velocity_nc.drop_vars("crs")
    velocity_nc["VX"] = velocity_nc["VX"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    velocity_nc["VY"] = velocity_nc["VY"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    velocity_nc["MASK"] = velocity_nc["MASK"].rio.write_crs("EPSG:3031").squeeze("band", drop=True)
    itslive_vx = rxr.open_rasterio(itslive_vx_path, masked=True).squeeze("band")
    itslive_vy = rxr.open_rasterio(itslive_vy_path, masked=True).squeeze("band")
    
    itslive_vx = itslive_vx.rio.write_crs(None)
    itslive_vx.attrs.pop("grid_mapping", None)
    itslive_vx.encoding.pop("grid_mapping", None)
    itslive_vx = itslive_vx.drop_vars("spatial_ref", errors="ignore")
    itslive_vx = itslive_vx.rio.write_crs("EPSG:3031",grid_mapping_name="crs")
    
    itslive_vy = itslive_vy.rio.write_crs(None)
    itslive_vy.attrs.pop("grid_mapping", None)
    itslive_vy.encoding.pop("grid_mapping", None)
    itslive_vy = itslive_vy.drop_vars("spatial_ref", errors="ignore")
    itslive_vy = itslive_vy.rio.write_crs("EPSG:3031",grid_mapping_name="crs")

    pbar.set_description(f"3/6 | Reprojecting Velocity: {t1}-{t2}")
    itslive_vx_on_grid = itslive_vx.rio.reproject_match(
        velocity_nc["VX"], resampling=Resampling.average
    )
    itslive_vx.close(); del itslive_vx

    itslive_vy_on_grid = itslive_vy.rio.reproject_match(
        velocity_nc["VY"], resampling=Resampling.average
    )
    itslive_vy.close(); del itslive_vy

    pbar.set_description(f"4/6 | Masking Velocity: {t1}-{t2}")
    nonzero_mask = (velocity_nc["VX"] != 0) & (velocity_nc["VY"] != 0)

    velocity_nc["VX"] = (
        velocity_nc["VX"].where(nonzero_mask, itslive_vx_on_grid)
    )
    del itslive_vx_on_grid

    velocity_nc["VY"] = (
        velocity_nc["VY"].where(nonzero_mask, itslive_vy_on_grid)
    )
    del itslive_vy_on_grid, nonzero_mask
    
    vx_max = np.nanpercentile(np.abs(velocity_nc["VX"]),99.7)
    vy_max = np.nanpercentile(np.abs(velocity_nc["VY"]),99.7)
    velocity_nc["VX"] = velocity_nc["VX"].clip(max = vx_max)
    velocity_nc["VY"] = velocity_nc["VY"].clip(max = vy_max)


    pbar.set_description(f"5/6 | Exporting Velocity: {t1}-{t2}")
    
    velocity_nc = velocity_nc.drop_vars("crs")
    velocity_nc = velocity_nc.rio.write_crs("EPSG:3031")
    velocity_nc.to_netcdf(
        data_folder / f"patched_velocity_{t1}-{t2}.nc",)
      
    pbar.set_description(f"6/6 | Export Complete for Velocity: {t1}-{t2}")
    
    velocity_nc.close()
    del velocity_nc
    gc.collect()
else:
    pbar.set_description("All velocity files loaded.")