# pyrefly: ignore [missing-import]
import numpy as np
from tqdm import tqdm
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt

def plot_contours(name,save_path, contours, ocean_contours, mask):
    mask_values = getattr(mask, "values", mask)
    mask_array = np.asarray(mask_values)

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(mask_array, cmap="gray", origin="lower", interpolation="nearest")

    for i, contour in enumerate(contours):
        ax.plot(
            contour[:, 1],  
            contour[:, 0],  
            linewidth=1,
            label=f"contour {i}" if i < 10 else None,
        )
    
    for i, contour in enumerate(ocean_contours):
        ax.plot(
            contour[:, 1],  
            contour[:, 0],  
            linewidth=2,
            color="blue",
            label=f"contour {i}" if i < 10 else None,
        )

    ax.set_title(f"{name} Contours ({len(contours)} found)")
    ax.set_xlabel("x index")
    ax.set_ylabel("y index")
    ax.set_aspect("equal")

    if 0 < len(contours) <= 10:
        ax.legend(loc="upper right", fontsize="small")

    fig.tight_layout()
    fig.savefig(save_path / f"{name}_boundary_plot.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    return save_path


def plot_data_product_summary(name, px, py, xct, yct, nnct, bd_ud, bd_vd,
                              velocity_x, velocity_y, velocity_vx, velocity_vy,
                              thickness_x, thickness_y, thickness_thickness,
                              imgs_path, original_px, original_py, tout=tqdm.write):
    fig, axes = plt.subplots(1, 3, figsize=(45, 15))

    speed = np.sqrt(bd_ud.ravel()**2 + bd_vd.ravel()**2)

    axes[0].plot(px, py, c="black", lw=.5, label="outer boundary")
    axes[0].scatter(original_px, original_py, s=.05, c="tab:orange",
                    label="original points")
    sc0 = axes[0].scatter(xct, yct, s=.05, c=speed, cmap="viridis", label="ice shelf points")
    fig.colorbar(sc0, ax=axes[0], label="velocity magnitude")
    axes[0].quiver(
        xct, yct, nnct[:, 0], nnct[:, 1],
        color="blue", angles="xy", scale_units="xy",
        scale=0.0003, width=0.001, label="normals",
    )
    axes[0].set_title("Outer boundary + ice shelf points + normals")
    axes[0].legend(loc="best", markerscale=5)

    axes[1].plot(px, py, c="black", lw=.05)
    vel_speed = np.sqrt(velocity_vx**2 + velocity_vy**2)
    sc1 = axes[1].scatter(velocity_x, velocity_y, s=2, c=vel_speed, cmap="viridis")
    fig.colorbar(sc1, ax=axes[1], label="velocity magnitude")
    axes[1].set_title("Velocity magnitude")

    axes[2].plot(px, py, c="black", lw=.05)
    sc2 = axes[2].scatter(thickness_x, thickness_y, s=2, c=thickness_thickness, cmap="cividis")
    fig.colorbar(sc2, ax=axes[2], label="thickness")
    axes[2].set_title("Thickness")

    for ax in axes:
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_aspect("equal")

    fig.tight_layout()
    fig.savefig(f"{imgs_path}/{name}_summary.png", dpi=512, bbox_inches="tight")
    plt.close(fig)
    plt.close()