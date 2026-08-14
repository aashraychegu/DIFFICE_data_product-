import pathlib as pl
from pathlib import Path
# pyrefly: ignore [missing-import]
import rioxarray as rxr
# pyrefly: ignore [missing-import]
import xarray as xr
# pyrefly: ignore [missing-import]
import numpy as np
import tqdm

direct_time_subsets = [(1995,2001),(2007,2009),(2014,2017)]
extrapolated_time_subsets = [(2020,2022)]


cwd = Path(".").resolve()
data = cwd / "data"
file_path = data / "historical_thickness.nc"
historical = rxr.open_rasterio(file_path, lock = False)
thickness = historical["thickness"].rio.write_crs("EPSG:3031")
thickness = thickness.where(thickness != -32767.0).rio.write_crs("EPSG:3031")

fit = thickness.polyfit(dim="time", deg=1, skipna=True)

times = thickness.time.values
step = times[-1] - times[-2]

vals = [times[-1] + step * (i) for i in range(2*4,2*4+1+4*3+1)]
future_times = xr.DataArray(vals, dims="time", coords={"time": vals})

predicted = xr.polyval(future_times, fit.polyfit_coefficients)
predicted = predicted.rio.write_crs("EPSG:3031")

def subset_year(data, start_year, end_year):
    def _clean_attrs(da):
        da = da.copy()
        da.attrs = {
            k: v for k, v in da.attrs.items()
            if not (k.startswith("NETCDF_DIM") or "time" in k.lower())
        }
        return da

    subset = data.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    mean_thickness = subset.mean(dim="time") 
    mean_thickness = _clean_attrs(mean_thickness)
    return mean_thickness, subset.time.values

def build_dataset(mean_thickness):
    mean_thickness = mean_thickness.drop_vars("time", errors="ignore")
    surface = xr.full_like(mean_thickness, fill_value=np.nan)
    ds = xr.Dataset(
        {
            "thickness": mean_thickness,
            "surface": surface,
        }
    )
    return ds.rio.write_crs("EPSG:3031")

for start_time, end_time in direct_time_subsets:
    save_path = data / f"thickness_{start_time}-{end_time}.nc"
    mean_thickness, values = subset_year(thickness,start_time,end_time)
    mean_thickness = mean_thickness.rio.write_crs("EPSG:3031")
    build_dataset(mean_thickness).to_netcdf(save_path)
    print(f"Saved {start_time} to {end_time} with {len(values)} time slices averaged to {save_path}")

for start_time, end_time in extrapolated_time_subsets:
    save_path = data / f"interp_thickness_{start_time}-{end_time}.nc"
    mean_thickness, values = subset_year(predicted,start_time,end_time)
    mean_thickness = mean_thickness.rio.write_crs("EPSG:3031")
    build_dataset(mean_thickness).to_netcdf(save_path)
    print(f"Saved {start_time} to {end_time} with {len(values)} time slices averaged to {save_path}")

