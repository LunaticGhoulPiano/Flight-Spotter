import os
import json
import folium
import pandas as pd
from tqdm import tqdm
from datetime import datetime
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

# filter by region
def in_region(lon:float, lat:float, polygon:Polygon):
    point = Point(lon, lat)
    return polygon.contains(point)

def filter_readsb_hist(region:str = None):
    # check output path
    data_path = "./data./historical_adsbex_sample./readsb-hist"
    os.makedirs("./data./preprocessed", exist_ok = True)

    # filter
    if region:
        polygon = make_boundary(region)
    else:
        polygon = None

    all_rows = []
    in_region_rows = []
    for snapshot_json in tqdm(os.listdir(data_path), desc = "Filtering readsb-hist", unit = " snapshots"):
        # file of a specific time
        json_file = json.load(open(f"{data_path}./{snapshot_json}", "r", encoding="utf-8"))

        # time features
        year, month, date, time = snapshot_json[:-5].split("_")
        hour, minute, second = time[:2], time[2:4], time[4:]

        # headers
        time_headers = ["year", "month", "date", "hour", "minute", "second"]
        feature_headers = [
            "hex", "flight", "t", "alt_baro", "alt_geom", "gs", "track", "geom_rate", "squawk", \
            "nav_qnh", "nav_altitude_mcp", "nav_altitude_fms", "nav_heading", \
            "lat", "lon", "nic", "rc", "track", "nic_baro", "nac_p", "nac_v", "sil", "sil_type"
        ]
        full_headers = time_headers + feature_headers

        # collect valid aircraft rows
        for aircraft in json_file["aircraft"]:
            if all(feature in aircraft for feature in feature_headers):
                row = [year, month, date, hour, minute, second] + \
                    [aircraft[feature].strip() if isinstance(aircraft[feature], str) else aircraft[feature] \
                     for feature in feature_headers]
                all_rows.append(row)
                if polygon and in_region(aircraft["lon"], aircraft["lat"], polygon):
                    in_region_rows.append(row)

    # make DataFrame once
    if all_rows:
        df = pd.DataFrame(all_rows, columns = full_headers)
        df.to_csv(f"./data./preprocessed./readsb-hist_merged.csv", index = False)
        if in_region_rows:
            df = pd.DataFrame(in_region_rows, columns = full_headers)
            df.to_csv(f"./data./preprocessed./readsb-hist_filtered_by_{region[:-5]}.csv", index = False)
    else:
        print("No data matched the filter. File not saved.")

    # log
    with open(f"./logs./readsb-hist.txt", "a", encoding = "utf-8") as f:
        f.write(f"> Update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total number of aircrafts: {len(all_rows)}\n")
        if in_region_rows:
            f.write(f"Number of aircrafts in {region[:-5]}: {len(in_region_rows)}\n")
        else:
            f.write("\n")

def reduce_traces(hires:bool = False):
    return
    res = "hires-traces" if hires else "traces"
    # check output path
    data_path = f"./data./historical_adsbex_sample./{res}"
    file_path = f"./data./filtered./{res}.csv" # ".json" -> ".csv"
    #if os.path.exists(file_path):
    #    shutil.rmtree(file_path)
    os.makedirs("./data./filtered", exist_ok = True)

    # calculate max the number of traces
    trace_count = []
    for aircraft in tqdm(os.listdir(data_path), desc = "Calculating num of max tracees", unit = " aircrafts"):
        jf = json.load(open(f"{data_path}./{aircraft}", "r", encoding = "utf-8"))
        trace_count.append(len(jf["trace"]))
    max_trace_count = max(trace_count) # use this for padding null traces

    # check aircraft
    k = 0
    for aircraft in tqdm(os.listdir(data_path), desc = "Reducing traces", unit = " aircrafts"):
        # file of a specific time
        json_file = json.load(open(f"{data_path}./{aircraft}", "r", encoding = "utf-8"))
        
        # features
        year, month, date, _ = aircraft[:-5].split("_")
        hex = json_file["icao"]
        timestamp = json_file["timestamp"] # start time: unix timestamp in seconds since epoch (1970)
        timeline = {}

        print(aircraft)

        for trace in json_file["trace"]:
            # index meanings: see "Trace File Fields" at https://www.adsbexchange.com/version-2-api-wip/
            # 0: seconds after timestamp,
            # 1: lat,
            # 2: lon,
            # 3: altitude in ft or "ground" or null
            # 4: ground speed in knots or null
            # 5: track in degrees or null (if altitude == "ground", this will be true heading instead of track)
            # 6: flags as a bitfield: (use bitwise and to extract data)
            #    (flags & 1 > 0): position is stale (no position received for 20 seconds before this one)
            #    (flags & 2 > 0): start of a new leg (tries to detect a separation point between landing and takeoff that separates fligths)
            #    (flags & 4 > 0): vertical rate is geometric and not barometric
            #    (flags & 8 > 0): altitude is geometric and not barometric
            # 7: vertical rate in fpm or null
            # 8: aircraft object with extra details or null (see aircraft.json documentation,
            #    note that not all fields are present as lat and lon for example already in the values above)
            # -- the following fields only in files generated 2022 and later: --
            # 9: type / source of this position or null
            # 10: geometric altitude or null
            # 11: geometric vertical rate or null
            # 12: indicated airspeed or null
            # 13: roll angle or null
            
            # padding null traces
            if not trace[8]:
                pass
            else:
                # filter: if these keys not in trace[8] or is null
                required_keys = ["alt_geom", "gs", "track"]
                if not trace[8][0] or not trace[8][1] or not trace[8][2]: # time interval by second, latitude, longitude
                    continue

            
            
            # build feature table by time
            # timeline[float]: {lat, lon, alt_geom, gs, track}
            timeline[str(trace[0])] = {
                "lat": trace[1],
                "lon": trace[2],
                "alt_ft": trace[3],
                "alt_geom": trace[8]["alt_geom"] if trace[8] else 0,
                "gs": trace[4],
                "track": trace[5]
            }

        print(timeline)
# test
if __name__ == "__main__":
    #polygon = make_boundary("Taiwan_ADIZ.json")
    #polygon = make_boundary("Taiwan_manual_edges.json")
    #test_point = Point(120.006663, 22.999459) # 22°59'58.1"N 120°00'24.0"E
    #if polygon.contains(test_point):
    #    print("In region")
    #else:
    #    print("Not in region")
    reduce_traces()