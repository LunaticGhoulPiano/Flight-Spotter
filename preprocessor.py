import os
import gzip
import json
import filter
import get_data
from tqdm import tqdm

def preprocess():
    # let user choose a region file to filter
    region_dict = {}
    print("Please choose a region to filter data: ")
    for i, region in enumerate(os.listdir("./data./filter_regions"), start = 1):
        region_dict[i] = region
        print(f"  {i}: {region}")
    while True:
        try:
            region = region_dict[int(input("Enter the serial number: "))]
            break
        except ValueError:
            print("Invalid input, try again.")
        except KeyError:
            print("No such file, try again.")
    
    # data path
    original_path = "./data./historical_adsbex_sample./readsb-hist"
    
    # download data
    if (not os.path.exists(original_path)) or input("Do you want to download / update data?\nIf no then use current data (y/n): ").lower() == "y":
        get_data.get_data()

    # check path
    new_path = f"./data./filtered./filtered_by_{region[:-5]}" # remove ".json"
    #if os.path.exists(new_path):
    #    shutil.rmtree(new_path)
    #os.makedirs(new_path)
    os.makedirs(new_path, exist_ok = True)
    
    # filter
    polygon = filter.make_boundary(region)
    for year in os.listdir(original_path):
        print(year)
        for month in os.listdir(f"{original_path}./{year}"):
            for day in os.listdir(f"{original_path}./{year}./{month}"):
                for file_by_time in os.listdir(f"{original_path}./{year}./{month}./{day}"):
                    # unzip and load as a dict
                    if file_by_time.endswith(".json.gz"):
                        with gzip.open(f"{original_path}./{year}./{month}./{day}./{file_by_time}", "rb") as f_in:
                            # unzipped file
                            unzipped_dicts = json.load(f_in)
                            
                            # fetch time
                            hour = file_by_time[:2]
                            minute = file_by_time[2:4]
                            second = file_by_time[4:6]
                            
                            # filtered file
                            file_path = f"{new_path}./{year}_{month}_{day}_{hour}_{minute}_{second}.json"
                            
                            # get size
                            size = len(unzipped_dicts["aircraft"])
                            filtered = []
                            
                            # filter
                            for i, aircraft in tqdm(enumerate(unzipped_dicts["aircraft"]), total = size, desc = f"Filtering {file_path} ..."):
                                if "lat" in aircraft and "lon" in aircraft and filter.in_region(aircraft["lon"], aircraft["lat"], polygon):
                                    filtered.append(aircraft)
                            
                            # write only if has data
                            if filtered:
                                with open(file_path, "w", encoding = "utf-8") as f_out:
                                    json.dump(filtered, f_out, indent = 4)

if __name__ == "__main__":
    preprocess()