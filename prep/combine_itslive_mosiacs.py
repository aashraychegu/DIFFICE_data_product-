from pathlib import Path

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import rasterio
# pyrefly: ignore [missing-import]
from rasterio.windows import Window

from tqdm import tqdm

aux_dir = Path("./data/itslive_mosaic_aux")
output_dir = Path("./data/itslive_mean")
nodata_value = -32767.0


def tiled_windows(width, height, size=1024):
    for row in range(0, height, size):
        for col in range(0, width, size):
            yield Window(col, row,
                         min(size, width - col),
                         min(size, height - row))

year_groups = {
    "1995-2001": [1994,1995,1996,1997,1998,1999,2000,2001,2002],
    "2007-2009": [2006,2007,2008,2009,2010],
    "2014-2017": [2013,2014,2015,2016,2017, 2018],
    "2020-2022": [2020,2021,2022],
}
data_variables = ["vx", "vy"]


def average_variable(var, name, years):
    inputs = [aux_dir / str(year) / f"{var}.tif" for year in years]
    srcs = [rasterio.open(f) for f in inputs]

    profile = srcs[0].profile | {
        "dtype": "float32",
        "count": 1,
        "nodata": np.nan,
        "driver": "GTiff",
        "tiled": True,
        "compress": "deflate",
    }

    out_path = output_dir / f"{var}_mean_{name}.tif"
    with rasterio.open(out_path, "w", **profile) as dst:
        w, h = srcs[0].width, srcs[0].height
        windows = list(tiled_windows(w, h, size=1024*4))
        for window in tqdm(windows, desc=out_path.name):
            stack = np.stack([s.read(1, window=window).astype("float32") for s in srcs])
            stack[stack <= nodata_value] = np.nan

            count = np.sum(~np.isnan(stack), axis=0)
            summed = np.nansum(stack, axis=0)
            mean = np.full(count.shape, np.nan, dtype="float32")
            np.divide(summed, count, out=mean, where=count > 0)

            dst.write(mean, 1, window=window)

    for s in srcs:
        s.close()
    print(f"Wrote {out_path}")


output_dir.mkdir(parents=True, exist_ok=True)
for name, years in year_groups.items():
    for var in data_variables:
        average_variable(var, name, years)