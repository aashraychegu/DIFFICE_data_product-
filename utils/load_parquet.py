from pathlib import Path
import geopandas as gpd

def load_parquet(path: Path):
    return gpd.read_parquet(path)

def flatten_parquet(gdf, minx, miny, maxx, maxy):
    gdf = gdf.cx[minx:maxx, miny:maxy]
    x_vals = gdf.geometry.x.values
    y_vals = gdf.geometry.y.values
    thickness_vals = gdf["thickness"].values
    surface_vals = gdf["surface"].values

    return {
        "x": x_vals,
        "y": y_vals,
        "thickness": thickness_vals,
        "surface": surface_vals,
    }
