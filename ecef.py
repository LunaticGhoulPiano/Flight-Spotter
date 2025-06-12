import numpy as np

earth_radius = 6371000 # meter
unit_coefficient = 0.3048 # feet-meter

def encode(lat: float, lon: float, alt_geom: float):
    lat_rad = np.radians(lat) # degree to radian
    lon_rad = np.radians(lon) # degree to radian
    alt_m = alt_geom * unit_coefficient # feet to meter
    x = (earth_radius + alt_m) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (earth_radius + alt_m) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (earth_radius + alt_m) * np.sin(lat_rad)
    return x, y, z

def decode(x: float, y: float, z: float):
    r = np.sqrt(x**2 + y**2 + z**2)
    lat_rad = np.arcsin(z / r)
    lon_rad = np.arctan2(y, x)
    alt_m = r - earth_radius
    lat = np.degrees(lat_rad) # radian to degree
    lon = np.degrees(lon_rad) # radian to degree
    alt_geom = alt_m / unit_coefficient # feet to meter
    return lat, lon, alt_geom