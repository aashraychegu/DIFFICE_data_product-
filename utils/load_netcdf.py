from pathlib import Path
# pyrefly: ignore [missing-import]
import rioxarray as rxr
import numpy as np

def load_netcdf(path: Path): 
    dataset = rxr.open_rasterio(path,lock=False)[["surface","thickness"]]
    dataset = dataset.rio.write_crs("EPSG:3031")
    dataset["surface"] = dataset["surface"].rio.write_crs("EPSG:3031").squeeze("band",drop = True)
    dataset["thickness"] = dataset["thickness"].rio.write_crs("EPSG:3031").squeeze("band",drop = True)
    return dataset

def flatten_netcdf(nc, minx, miny, maxx, maxy):
    nc = nc.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
    stacked = nc.stack(points=("y", "x"))
    stacked = stacked.where(stacked["thickness"] > -9998)
    # NOTE: SURFACE CAN BE ALL NAN - DO NOT ADD IT TO ```subset=[...]```
    stacked = stacked.dropna(dim="points", subset=["thickness"], how="any")
    return {
        "x": stacked["x"].values,
        "y": stacked["y"].values,
        "thickness": stacked["thickness"].values,
        "surface": stacked["surface"].values,
    }
