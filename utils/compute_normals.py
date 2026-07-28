# pyrefly: ignore [missing-import]
import numpy as np

def compute_normals(boundary_x, boundary_y, smooth_window=5):
    """Outward unit normals for an ordered closed curve, with optional smoothing."""
    x, y = np.asarray(boundary_x), np.asarray(boundary_y)

    # Tangents via central differences (np.roll wraps the closed loop)
    tx = np.roll(x, -1) - np.roll(x, 1)
    ty = np.roll(y, -1) - np.roll(y, 1)

    # Orient normals outward using signed (shoelace) area
    signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    nx, ny = (ty, -tx) if signed_area > 0 else (-ty, tx)

    # Smooth with a wrap-around moving average
    if smooth_window > 1:
        k = np.ones(smooth_window) / smooth_window
        pad = smooth_window // 2
        nx = np.convolve(np.r_[nx[-pad:], nx, nx[:pad]], k, 'same')[pad:-pad]
        ny = np.convolve(np.r_[ny[-pad:], ny, ny[:pad]], k, 'same')[pad:-pad]

    # Normalize to unit length
    length = np.hypot(nx, ny)
    length[length == 0] = 1e-12
    return np.column_stack([nx / length, ny / length])