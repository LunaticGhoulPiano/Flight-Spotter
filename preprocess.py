import os
import gzip
import json
import shutil
import get_data
import filter_Taiwan_ADIZ

def filter_readsb_hist_by_Taiwan_ADIZ():
    original_path = "./data./historical_adsbex_sample./readsb-hist"
    new_path = f"./data./Taiwan./filtered_by_Taiwan_ADIZ"
    if os.path.exists(new_path):
        shutil.rmtree(new_path)
    os.makedirs(new_path)

    # download data
    get_data.get_data()
    
    # filter by Taiwan ADIZ
    adiz_polygon = filter_Taiwan_ADIZ.make_boundary()
    for year in os.listdir(original_path):
        for month in os.listdir(f"{original_path}./{year}"):
            for day in os.listdir(f"{original_path}./{year}./{month}"):
                for file_by_time in os.listdir(f"{original_path}./{year}./{month}./{day}"):
                    # unzip and load as a dict
                    if file_by_time.endswith(".json.gz"):
                        with gzip.open(f"{original_path}./{year}./{month}./{day}./{file_by_time}", "rb") as f_in:
                            
                            # unzipped file
                            unzipped_json = json.load(f_in)
                            
                            # fetch time
                            hour = file_by_time[:2]
                            minute = file_by_time[2:4]
                            second = file_by_time[4:6]
                            
                            # filtered file
                            file_path = f"{new_path}./{year}_{month}_{day}_{hour}_{minute}_{second}.json"
                            
                            # iterate each item
                            first_entry = True  # Flag to check if it's the first entry to write
                            for flight in unzipped_json.get("aircraft", []):
                                if "lat" in flight and "lon" in flight and filter_Taiwan_ADIZ.in_Taiwan_ADIZ(flight, adiz_polygon):
                                    # create the file if the first filtered flight exist
                                    if first_entry:
                                        with open(file_path, "w", encoding = "utf-8") as f_out:
                                            f_out.write("[\n")  # start with the opening bracket
                                    
                                    # append into the file with a comma at the end (except the first entry)
                                    with open(file_path, "a", encoding = "utf-8") as f_out:
                                        # pretty write with correct indent without using json.dump and 
                                        if not first_entry:
                                            f_out.write(",\n")  # add a comma before each entry except the first one
                                        json_str = json.dumps(flight, indent = 8).replace("{", "    {").replace("}", "    }")
                                        f_out.write(json_str)
                                        first_entry = False
                            # ensure the file ends with a closing bracket
                            with open(file_path, "a", encoding="utf-8") as f_out:
                                f_out.write("\n]")  # add the closing bracket after all entries are written
                        
                        # debug: only process two files
                        #if minute == "01":
                        #    exit()

def preprocess():
    filter_readsb_hist_by_Taiwan_ADIZ()

if __name__ == "__main__":
    preprocess()