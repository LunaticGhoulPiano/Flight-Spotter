import os
import filter
import get_data

def preprocess():
    # download data
    if (not os.path.exists("./data./historical_adsbex_sample")) or \
        input("Do you want to download / update data?\nIf no then use current data (y/n): ").lower() == "y":
        get_data.get_data()
    
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
    
    filter.filter_readsb_hist(region)
    #filter.reduce_traces() # send True if you use hires-traces

if __name__ == "__main__":
    preprocess()