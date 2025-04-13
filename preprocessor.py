import os
import filter
import get_data

def preprocess():
    # download data
    if (not os.path.exists("./data./historical_adsbex_sample")) or \
        input("Do you want to download (or update) data?\nIf no then use current data (y/n): ").lower() == "y":
        get_data.get_data()
    
    # let user choose a region file to filter
    region_dict = {}
    print("Please choose a region to filter data: ")
    print("  0: No filter")
    for i, region in enumerate(os.listdir("./data./filter_regions"), start = 1):
        region_dict[i] = region
        print(f"  {i}: {region}")
    while True:
        try:
            idx = int(input("Enter the serial number: "))
            if idx == 0:
                region = None
            else:
                region = region_dict[idx]
            break
        except ValueError:
            print("Invalid input, try again.")
        except KeyError:
            print("No such file, try again.")
    
    filter.filter_readsb_hist(region)

if __name__ == "__main__":
    preprocess()