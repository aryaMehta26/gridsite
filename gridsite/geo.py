"""Distance math with plain numpy (no GIS stack required)."""

import numpy as np

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Inputs broadcast like numpy arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def distance_matrix_km(lat_a, lon_a, lat_b, lon_b):
    """Pairwise distances: rows are points in A, columns are points in B."""
    lat_a = np.asarray(lat_a, dtype=float)[:, None]
    lon_a = np.asarray(lon_a, dtype=float)[:, None]
    lat_b = np.asarray(lat_b, dtype=float)[None, :]
    lon_b = np.asarray(lon_b, dtype=float)[None, :]
    return haversine_km(lat_a, lon_a, lat_b, lon_b)


def nearest(lat_a, lon_a, lat_b, lon_b, chunk: int = 2000):
    """For each point in A, return (index into B, distance km) of its nearest B.

    Processed in chunks so a few thousand x few thousand stays in memory.
    """
    lat_a = np.asarray(lat_a, dtype=float)
    lon_a = np.asarray(lon_a, dtype=float)
    idx = np.empty(len(lat_a), dtype=int)
    dist = np.empty(len(lat_a), dtype=float)
    for start in range(0, len(lat_a), chunk):
        stop = start + chunk
        d = distance_matrix_km(lat_a[start:stop], lon_a[start:stop], lat_b, lon_b)
        idx[start:stop] = d.argmin(axis=1)
        dist[start:stop] = d.min(axis=1)
    return idx, dist


def within_radius(lat_a, lon_a, lat_b, lon_b, radius_km: float, chunk: int = 2000):
    """Boolean matrix chunks are summed per row: how many B lie within radius."""
    lat_a = np.asarray(lat_a, dtype=float)
    lon_a = np.asarray(lon_a, dtype=float)
    out = []
    for start in range(0, len(lat_a), chunk):
        d = distance_matrix_km(lat_a[start:start + chunk], lon_a[start:start + chunk], lat_b, lon_b)
        out.append(d <= radius_km)
    return np.vstack(out) if out else np.zeros((0, len(lat_b)), dtype=bool)
