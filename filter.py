import os
import json
import folium
from shapely.geometry import Point, Polygon

# transform DMS(Degrees, Minutes, Seconds) to DD(Decimal Degrees)
def DMS_to_DD(pos: str):
    dms, _ = pos[:-1], pos[-1] # remove direction
    d, m, s = dms.replace('°', ' ').replace("'", ' ').replace('"', ' ').split()
    return float(d) + float(m) / 60 + float(s) / 3600

# make boundary
def make_boundary(region:str):
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

# filter
def in_region(flight:dict, polygon:Polygon):
    point = Point(flight["lon"], flight["lat"])
    return polygon.contains(point)

# test
if __name__ == "__main__":
    polygon = make_boundary("Taiwan_ADIZ.json")
    #polygon = make_boundary("Taiwan_manual_edges.json")
    test_point = Point(121.50963962666523, 24.79577412867427) # 24°47'43.9"N 121°30'34.6"E
    if polygon.contains(test_point):
        print("In region")
    else:
        print("Not in region")