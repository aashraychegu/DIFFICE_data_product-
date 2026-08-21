# pyrefly: ignore [missing-import]
import numpy as np

def compute_normals(boundary_x, boundary_y, smooth_window=5):
    x, y = np.asarray(boundary_x), np.asarray(boundary_y)

    tx = np.roll(x, -1) - np.roll(x, 1)
    ty = np.roll(y, -1) - np.roll(y, 1)

    # https://en.wikipedia.org/wiki/Shoelace_formula
    signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    nx, ny = (ty, -tx) if signed_area > 0 else (-ty, tx)

    if smooth_window > 1:
        k = np.ones(smooth_window) / smooth_window
        pad = smooth_window // 2
        nx = np.convolve(np.r_[nx[-pad:], nx, nx[:pad]], k, 'same')[pad:-pad]
        ny = np.convolve(np.r_[ny[-pad:], ny, ny[:pad]], k, 'same')[pad:-pad]

    length = np.hypot(nx, ny)
    length[length == 0] = 1e-12
    return np.column_stack([nx / length, ny / length])
