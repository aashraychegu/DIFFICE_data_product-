import rioxarray as rxr
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

raster = rxr.open_rasterio("/oak/stanford/groups/cyaolai/AashrayChegu/data-product/data/interp_thickness_2020-2022.nc")
thickness = raster["thickness"]

# bbox = [max_x, min_x, max_y, min_y]
bbox = [397750.0, -593250.0, -434750.0, -1352250.0]
max_x, min_x, max_y, min_y = bbox

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# --- Subplot 1: Full thickness with bbox drawn as a rectangle ---
thickness.plot(ax=axes[0], cmap="viridis", robust=True)
axes[0].set_title("Thickness with Bounding Box")

# Rectangle(xy=(lower-left corner), width, height)
rect = Rectangle(
    (min_x, min_y),           # lower-left corner
    max_x - min_x,            # width
    max_y - min_y,            # height
    linewidth=2,
    edgecolor="red",
    facecolor="none",
)
axes[0].add_patch(rect)
axes[0].set_aspect("equal")

# --- Subplot 2: Thickness cropped to bbox ---
cropped = thickness.rio.clip_box(minx=min_x, miny=min_y, maxx=max_x, maxy=max_y)

cropped.plot(ax=axes[1], cmap="viridis", robust=True)
axes[1].set_title("Thickness Cropped to Bounding Box")
axes[1].set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
plt.close()

print(thickness)
print(cropped)