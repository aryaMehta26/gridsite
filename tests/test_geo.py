import numpy as np

from gridsite.geo import haversine_km, nearest


def test_haversine_sf_to_la():
    # San Francisco to Los Angeles is about 559 km
    d = haversine_km(37.7749, -122.4194, 34.0522, -118.2437)
    assert abs(d - 559) < 3


def test_haversine_zero():
    assert haversine_km(37.0, -121.0, 37.0, -121.0) == 0


def test_nearest_matches_brute_force():
    rng = np.random.default_rng(7)
    a_lat, a_lon = rng.uniform(37, 38, 300), rng.uniform(-122.5, -121.5, 300)
    b_lat, b_lon = rng.uniform(37, 38, 50), rng.uniform(-122.5, -121.5, 50)
    idx, dist = nearest(a_lat, a_lon, b_lat, b_lon, chunk=64)
    for i in range(len(a_lat)):
        brute = haversine_km(a_lat[i], a_lon[i], b_lat, b_lon)
        assert idx[i] == brute.argmin()
        assert np.isclose(dist[i], brute.min())
