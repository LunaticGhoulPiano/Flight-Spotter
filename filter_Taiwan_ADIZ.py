import json
from shapely.geometry import Point, Polygon

# transform DMS(Degrees, Minutes, Seconds) to DD(Decimal Degrees)
def DMS_to_DD(pos: str):
    dms, _ = pos[:-1], pos[-1] # remove direction
    d, m, s = dms.replace('°', ' ').replace("'", ' ').replace('"', ' ').split()
    return float(d) + float(m) / 60 + float(s) / 3600

# make boundary
def make_boundary():
    with open('./data/Taiwan/Taiwan_ADIZ.json', 'r', encoding = 'utf-8') as f:
        adiz_boundary_json = json.load(f)
    adiz_boundary = []
    for coordinate in adiz_boundary_json:
        adiz_boundary.append((DMS_to_DD(coordinate["longitude"]), DMS_to_DD(coordinate["latitude"])))
    return Polygon(adiz_boundary)

# filter
def in_Taiwan_ADIZ(flight:dict, adiz_polygon:Polygon):
    point = Point(flight["lon"], flight["lat"])
    return adiz_polygon.contains(point)

# test
if __name__ == "__main__":
    adiz_polygon = make_boundary()
    test_point = Point(121.50963962666523, 24.79577412867427) # 24°47'43.9"N 121°30'34.6"E
    if adiz_polygon.contains(test_point):
        print("In Taiwan ADIZ")
    else:
        print("Not in Taiwan ADIZ")