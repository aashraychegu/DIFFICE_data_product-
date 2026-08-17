import pathlib as pl
from pathlib import Path
from itertools import product
from collections import namedtuple
from tqdm import tqdm
from typing import List
from utils.read_exp import read_exp
from utils.compute_normals import compute_normals
from utils.plotting_helpers import plot_data_product_summary, plot_contours

from shapely import Polygon, MultiPolygon, make_valid
from shapely.geometry import LineString
from shapely.ops import unary_union

# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore [missing-import]
import rioxarray as rxr
# pyrefly: ignore [missing-import]
import xarray as xr
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import geopandas as gpd
# pyrefly: ignore [missing-import]
from scipy.io import savemat
# pyrefly: ignore [missing-import]
from scipy.interpolate import RBFInterpolator
# pyrefly: ignore [missing-import]
from scipy.spatial import cKDTree
# pyrefly: ignore [missing-import]
from skimage import measure

def sample_rbf_velocity(da_vx, da_vy, query_pts, neighbors=16,
                        kernel="thin_plate_spline", max_distance=5000.0):
						
    xs, ys = np.meshgrid(da_vx.x.values, da_vy.y.values)

    vx_vals = da_vx.values
    vy_vals = da_vy.values

    valid = (
        np.isfinite(vx_vals) & np.isfinite(vy_vals)
        & ~((vx_vals == 0) & (vy_vals == 0))
    )

    valid_pts = np.column_stack([xs[valid], ys[valid]])
    if len(valid_pts) < neighbors:
        nan_out = np.full(len(query_pts), np.nan)
        return nan_out, nan_out

    tree = cKDTree(query_pts)
    dist, _ = tree.query(valid_pts, k=1)  
    near = dist <= max_distance

    if near.sum() < neighbors:
        nan_out = np.full(len(query_pts), np.nan)
        return nan_out, nan_out

    src_pts = valid_pts[near]
    vals2d = np.column_stack([vx_vals[valid][near], vy_vals[valid][near]])

    rbf = RBFInterpolator(src_pts, vals2d, neighbors=neighbors, kernel=kernel)
    result = rbf(query_pts)  # (M, 2)

    return result[:, 0], result[:, 1]

def process_one_data_product(name, output_location, velocity_nc, thickness_source, thickness_flatten_function, exp_path = None, bbox = None, imgs_path = None, buffersize = .1, boundary_smoothing_buffer = 2500, tout = tqdm.write):

    if exp_path:
        floating_domain: List = read_exp(exp_path)[0]
        maxx, minx, maxy, miny = max(floating_domain["x"]), min(floating_domain["x"]), max(floating_domain["y"]), min(floating_domain["y"])
    else:
        maxx, minx, maxy, miny = bbox
    extent_x, extent_y = maxx - minx, maxy-miny
    buffer_x, buffer_y = extent_x * buffersize , extent_y * buffersize
    maxx, minx, maxy, miny = maxx + buffer_x, minx - buffer_x, maxy + buffer_y, miny - buffer_y
    clipped_velocity_nc = velocity_nc.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy,crs = "EPSG:3031")

    mask = clipped_velocity_nc["MASK"] == 2
    nonzero_mask = ((clipped_velocity_nc["VX"] != 0) & (clipped_velocity_nc["VY"] != 0))
    total_velocity_mask = mask & nonzero_mask
    velocity_x = clipped_velocity_nc["x"].broadcast_like(total_velocity_mask).values[total_velocity_mask.values]
    velocity_y = clipped_velocity_nc["y"].broadcast_like(total_velocity_mask).values[total_velocity_mask.values]
    velocity_vx = clipped_velocity_nc["VX"].values[total_velocity_mask.values]
    velocity_vy = clipped_velocity_nc["VY"].values[total_velocity_mask.values]

    flattened_thickness = thickness_flatten_function(thickness_source, minx=minx, miny=miny, maxx=maxx, maxy=maxy)

    x_coords = clipped_velocity_nc["x"].values
    y_coords = clipped_velocity_nc["y"].values
    contours = measure.find_contours(mask.values.astype(float), level=.99)

    boundary_contour = max(contours, key=len)

    rows, cols = boundary_contour[:, 0], boundary_contour[:, 1]
    cx = np.interp(cols, np.arange(len(x_coords)), x_coords)
    cy = np.interp(rows, np.arange(len(y_coords)), y_coords)
    cx = np.append(cx, cx[0])
    cy = np.append(cy, cy[0])

    boundary_polygon = Polygon(np.column_stack((cx, cy)))
    if not boundary_polygon.is_valid:
        boundary_polygon = boundary_polygon.buffer(0)
    if isinstance(boundary_polygon, MultiPolygon):
        boundary_polygon = max(boundary_polygon.geoms, key=lambda p: p.area)

    contour_polygons = []
    for contour in contours:
        c_rows, c_cols = contour[:, 0], contour[:, 1]
        ccx = np.interp(c_cols, np.arange(len(x_coords)), x_coords)
        ccy = np.interp(c_rows, np.arange(len(y_coords)), y_coords)
        ccx = np.append(ccx, ccx[0])
        ccy = np.append(ccy, ccy[0])
        poly = Polygon(np.column_stack((ccx, ccy)))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda p: p.area)
        contour_polygons.append(poly)

    outer_polygon = max(contour_polygons, key=lambda p: p.area)
    holes = []
    for poly in contour_polygons:
        if poly is outer_polygon:
            continue
        if outer_polygon.contains(poly):
            holes.append(list(poly.exterior.coords))

    polygon_with_holes = Polygon(outer_polygon.exterior.coords, holes)
    if not polygon_with_holes.is_valid:
        polygon_with_holes = make_valid(polygon_with_holes)
    if isinstance(polygon_with_holes, MultiPolygon):
        polygon_with_holes = max(polygon_with_holes.geoms, key=lambda p: p.area)

    clip_gdf = gpd.GeoDataFrame(geometry=[polygon_with_holes], crs="EPSG:3031")

    velocity_gdf = gpd.GeoDataFrame(
        {
            "vx": velocity_vx,
            "vy": velocity_vy,
        },
        geometry=gpd.points_from_xy(velocity_x, velocity_y),
        crs="EPSG:3031",
    )
    velocity_clipped = gpd.sjoin(velocity_gdf, clip_gdf, predicate="within", how="inner")

    velocity_x = velocity_clipped.geometry.x.values
    velocity_y = velocity_clipped.geometry.y.values
    velocity_vx = velocity_clipped["vx"].values
    velocity_vy = velocity_clipped["vy"].values

    thickness_gdf = gpd.GeoDataFrame(
        {
            "surface": flattened_thickness["surface"],
            "thickness": flattened_thickness["thickness"],
        },
        geometry=gpd.points_from_xy(flattened_thickness["x"], flattened_thickness["y"]),
        crs="EPSG:3031",
    )
    thickness_gdf = thickness_gdf.dropna(subset=["thickness"])
    thickness_gdf = thickness_gdf[thickness_gdf["thickness"] > 1e-8]
    thickness_clipped = gpd.sjoin(thickness_gdf, clip_gdf, predicate="within", how="inner")

    pt_x = xr.DataArray(thickness_clipped.geometry.x.values, dims="points")
    pt_y = xr.DataArray(thickness_clipped.geometry.y.values, dims="points")

    keep = total_velocity_mask.sel(x=pt_x, y=pt_y, method="nearest").values
    thickness_clipped = thickness_clipped[keep]

    thickness_x = thickness_clipped.geometry.x.values
    thickness_y = thickness_clipped.geometry.y.values
    thickness_surface = thickness_clipped["surface"].values
    thickness_thickness = thickness_clipped["thickness"].values
    
    original_px, original_py = boundary_polygon.exterior.xy

    closed_polygon = (
        boundary_polygon
        .buffer(boundary_smoothing_buffer,  quad_segs=8,join_style="mitre")
        .buffer(-boundary_smoothing_buffer, quad_segs=8,join_style="mitre")
    )

    combined_polygon = unary_union([boundary_polygon, closed_polygon])

    px, py = combined_polygon.exterior.xy
    px = np.asarray(px)[:-1]
    py = np.asarray(py)[:-1]
    normals = compute_normals(px, py)

    xs, ys = np.meshgrid(
        clipped_velocity_nc["VX"].x.values,
        clipped_velocity_nc["VX"].y.values,
    )
    query_pts = np.column_stack([px, py])
    
    boundary_vx, boundary_vy = sample_rbf_velocity(
        clipped_velocity_nc["VX"],
        clipped_velocity_nc["VY"],
        query_pts,
    )

    ocean_mask = clipped_velocity_nc["MASK"] == 0

    ocean_contours = measure.find_contours(ocean_mask.values.astype(float), level=.01)
    
    ocean_boundary_contour = max(ocean_contours, key=len)
    o_rows, o_cols = ocean_boundary_contour[:, 0], ocean_boundary_contour[:, 1]
    obcx = np.interp(o_cols, np.arange(len(x_coords)), x_coords)
    obcy = np.interp(o_rows, np.arange(len(y_coords)), y_coords)
    ocean_line = LineString(np.column_stack((obcx, obcy)))
    ocean_buffer = ocean_line.buffer(1000.0)

    boundary_points = gpd.GeoDataFrame(
        {
            "px": px,
            "py": py,
            "vx": boundary_vx,
            "vy": boundary_vy,
            "nx": normals[:, 0],
            "ny": normals[:, 1],
        },
        geometry=gpd.points_from_xy(px, py),
        crs="EPSG:3031",
    )
    ocean_buffer_gdf = gpd.GeoDataFrame(geometry=[ocean_buffer], crs="EPSG:3031")

    calving_front = gpd.sjoin(
        boundary_points, ocean_buffer_gdf, predicate="within", how="inner"
    ).drop(columns="index_right")

    xct = calving_front["px"].values[:, np.newaxis]
    yct = calving_front["py"].values[:, np.newaxis]
    bd_ud = calving_front["vx"].values[:, np.newaxis]
    bd_vd = calving_front["vy"].values[:, np.newaxis]
    nnct = calving_front[["nx", "ny"]].values

    if imgs_path is not None:
        # plot_contours(name, imgs_path,contours,ocean_contours,mask)
        plot_data_product_summary(
            name, px, py, xct, yct, nnct, bd_ud, bd_vd,
            velocity_x, velocity_y, velocity_vx, velocity_vy,
            thickness_x, thickness_y, thickness_thickness,
            imgs_path, original_px=original_px,original_py=original_py, tout=tout,
        )

    data_product: dict[str, np.ndarray] = dict(
            # Velocity ground truth data
            xd = velocity_x[:, np.newaxis],          # x-coordinates of FEM vertices at which velocities are calculated
            yd = velocity_y[:, np.newaxis],          # y-coordinates of FEM vertices at which velocities are calculated
            xcol = velocity_x[:, np.newaxis],        # x-coordinates of collocation points where PINNs evaluate equation residuals
            ycol = velocity_y[:, np.newaxis],        # y-coordinates of collocation points where PINNs evaluate equation residuals
            ud = velocity_vx[:, np.newaxis],         # x-component (u) of velocity corresponding to xd/yd entries
            vd = velocity_vy[:, np.newaxis],         # y-component (v) of velocity corresponding to xd/yd entries
            # Irrelevent terms
            alpha2d = np.full_like(velocity_x, 0)[:, np.newaxis],           # values of alpha^2 (not beta^2) corresponding to xd/yd entries
            mud = np.full_like(velocity_x, np.nan)[:, np.newaxis],          # values of mu corresponding to xd/yd entries
            basal_mask = np.full_like(velocity_x, False)[:, np.newaxis],    # boolean: True if region is grounded, False if floating
            ols_d = np.full_like(velocity_x, -1)[:, np.newaxis],            # ocean level-set: >0 grounded, <0 floating, =0 on grounding line
            # Thickness (+ Elevation) Ground truth data
            xd_h = thickness_x[:, np.newaxis],          # x-coordinates of FEM vertices at which thickness is calculated (same as xd)
            yd_h = thickness_y[:, np.newaxis],          # y-coordinates of FEM vertices at which thickness is calculated (same as yd)
            hd = thickness_thickness[:, np.newaxis],    # thickness at FEM vertices (xd_h/yd_h); may be artificially sparse (radar tracks)
            sd = thickness_surface[:, np.newaxis],      # surface elevation at FEM vertices corresponding to xd_h/yd_h
            # Ice shelf Boundary
            xct = xct,                                  # x-coordinates of FEM vertices on the domain boundary (relevant for floating regions)
            yct = yct,                                  # y-coordinates of FEM vertices on the domain boundary (relevant for floating regions)
            nnct = nnct,                                # outward-pointing normal vectors at each boundary vertex (relevant for floating regions)
            bd_ud = bd_ud,                              # values of u at boundary FEM vertices corresponding to xct/yct
            bd_vd = bd_vd,                              # values of v at boundary FEM vertices corresponding to xct/yct
            bd_mu = np.full_like(xct,np.nan),           # values of mu at boundary FEM vertices corresponding to xct/yct
        )

    for key, product in data_product.items():
        smallest_dim = min(product.shape)
        if smallest_dim == 0:
            tout(f"! ABORTED \t {name}\n \t {key} has shape {product.shape}")    
            return False
            
    output_path = output_location / f"{name}_polygon.wkt"
    output_path.write_text(polygon_with_holes.wkt)
    savemat(output_location / f"{name}.mat",data_product)
    tout(f"> Completed \t {name}")
    return True
