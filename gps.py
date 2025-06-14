import os
import json
import folium
from shapely.geometry import Point, Polygon
import asyncio
import platform

# DMS and DD conversion
def DMS_to_DD(pos: str) -> float: # transform DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees)
    dms, _ = pos[:-1], pos[-1] # remove direction
    d, m, s = dms.replace('°', ' ').replace("'", ' ').replace('"', ' ').split()
    return float(d) + float(m) / 60 + float(s) / 3600

def DD_to_DMS(dd: float, is_lat: bool = True) -> str: # transform DD (Decimal Degrees) to DMS (Degrees, Minutes, Seconds)
    direction = ""
    if is_lat:
        direction = "N" if dd >= 0 else "S"
    else:
        direction = "E" if dd >= 0 else "W"

    dd = abs(dd)
    degrees = int(dd)
    minutes_float = (dd - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return f"{degrees}°{minutes:02d}'{seconds:05.2f}\"{direction}"

# gps region
def make_boundary(region: str) -> Polygon:
    with open(f"./data./filter_regions./{region}", "r", encoding = "utf-8") as f:
        boundary_DMS = json.load(f)
    # transform into DD
    boundary_DD = []
    center_lon = 0
    center_lat = 0
    for coordinate in boundary_DMS:
        center_lon += DMS_to_DD(coordinate["longitude"])
        center_lat += DMS_to_DD(coordinate["latitude"])
        boundary_DD.append((DMS_to_DD(coordinate["longitude"]), DMS_to_DD(coordinate["latitude"]))) # boundary is in DD form here
    
    # get center point
    center_lon /= len(boundary_DD)
    center_lat /= len(boundary_DD)
    # draw on map
    map = folium.Map(location = [center_lat, center_lon], zoom_start = 12)
    # link with lines
    folium.PolyLine([(coord[1], coord[0]) for coord in boundary_DD], color = "green").add_to(map)
    for coord in boundary_DD:
        folium.Marker(location = [coord[1], coord[0]], icon = folium.Icon(color = "green", icon_color = "green", prefix = "fa", icon = "male")).add_to(map)
    os.makedirs("./filtered_region_maps", exist_ok = True)
    map.save(f"./filtered_region_maps./{region[:-5]}.html")

    return Polygon(boundary_DD)

def in_region(lon:float, lat:float, polygon:Polygon) -> bool: # filter by region
    point = Point(lon, lat)
    return polygon.contains(point)

# get user's location
class NotSupportedError(Exception):
    def __init__(self, platform_name):
        super().__init__(f"ERROR: Platform '{platform_name}' not supported.")
        self.platform_name = platform_name

class PermissionError(Exception):
    def __init__(self):
        super().__init__("ERROR: You need to allow applications to access your location.")

async def getCoords():
    system_name = platform.system()
    match system_name:
        case 'Windows':
            import winsdk.windows.devices.geolocation as wdg
            locator = wdg.Geolocator()
            pos = await locator.get_geoposition_async()
            return [pos.coordinate.point.position.latitude, pos.coordinate.point.position.longitude]
        case _:
            raise NotSupportedError(system_name)

def getLoc():
    try:
        return asyncio.run(getCoords())
    except PermissionError as e:
        return e
    except NotSupportedError as e:
        return e