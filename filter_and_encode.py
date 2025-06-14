import os
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import gps
import ecef
import geohash2

def filter_readsb_hist(filter_all: bool = True, region: str = None):
    # check output path
    data_path = "./data./historical_adsbex_sample./readsb-hist"
    os.makedirs("./data./preprocessed", exist_ok = True)

    msg = ""
    all_rows = []
    in_region_rows = []
    
    # check if the file already exists
    if not os.path.exists(f"./data./preprocessed./readsb-hist_merged.csv"):
        msg = "You don't have a merged file yet, start filtering..."
    elif filter_all:
        msg = "You already have a merged file, start filtering..."
    
    # iterate all readsb-hist files
    if msg:
        print(msg)
        for snapshot_json in tqdm(os.listdir(data_path), desc = "Fetching readsb-hist", unit = " snapshots"):
            # file of a specific time
            json_file = json.load(open(f"{data_path}./{snapshot_json}", "r", encoding = "utf-8"))

            # time features
            year, month, date, time = snapshot_json[:-5].split("_")
            hour, minute, second = time[:2], time[2:4], time[4:]

            # headers
            time_headers = ["year", "month", "day", "hour", "minute", "second"]
            encoded_headers = ["geohash", "ecef_x", "ecef_y", "ecef_z"]
            feature_headers = [
                "hex", "flight", "t", "alt_baro", "alt_geom", "gs", "track", "geom_rate", "squawk", \
                "nav_qnh", "nav_altitude_mcp", "nav_altitude_fms", "nav_heading", \
                "lat", "lon", "nic", "rc", "nic_baro", "nac_p", "nac_v", "sil", "sil_type"
            ]
            full_headers = time_headers + feature_headers + encoded_headers

            # collect valid aircraft rows
            for aircraft in json_file["aircraft"]:
                if all(feature in aircraft for feature in feature_headers):
                    row = [year, month, date, hour, minute, second] + \
                        [aircraft[feature].strip() if isinstance(aircraft[feature], str) else aircraft[feature] \
                        for feature in feature_headers]
                    
                    # encode
                    geohash = geohash2.encode(aircraft["lat"], aircraft["lon"], precision = 12)
                    ecef_x, ecef_y, ecef_z = ecef.encode(aircraft["lat"], aircraft["lon"], aircraft["alt_geom"])
                    row.extend([geohash, ecef_x, ecef_y, ecef_z])
                    
                    # append
                    all_rows.append(row)

    # make full file
    if all_rows:
        print("Writing readsb-hist_merged.csv ...")
        df = pd.DataFrame(all_rows, columns = full_headers)
        df.to_csv(f"./data./preprocessed./readsb-hist_merged.csv", index = False)
    
    # filter by region
    if region:
        polygon = gps.make_boundary(region)
        # load merged file
        print("Loading readsb-hist_merged.csv ...")
        all_rows = pd.read_csv(f"./data./preprocessed./readsb-hist_merged.csv")
        # iterate all_rows to filter in_region
        for row in tqdm(all_rows.itertuples(index = False), total = len(all_rows), desc = "Filtering readsb-hist", unit = " rows"):
            if gps.in_region(row.lon, row.lat, polygon):
                in_region_rows.append(row._asdict())
        if in_region_rows:
            print(f"Writing readsb-hist_filtered_by_{region[:-5]}.csv ...")
            df = pd.DataFrame(in_region_rows)
            df.to_csv(f"./data./preprocessed./readsb-hist_filtered_by_{region[:-5]}.csv", index = False)
        else:
            print("No data matched the filter. File will not saved.")

    # log
    if not filter_all and not in_region_rows:
        return
    with open(f"./logs./readsb-hist.txt", "a", encoding = "utf-8") as f:
        f.write(f"> Update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total number of aircrafts: {len(all_rows)}\n")
        if in_region_rows:
            f.write(f"Number of aircrafts in {region[:-5]}: {len(in_region_rows)}\n")
        else:
            f.write("\n")