import os
from scipy.io import arff
import pandas as pd
import numpy as np
import visualize

def get_clustering(filename: str, path: str):
    with open(f"{path}./{filename}", "r", encoding = "utf-8") as f:
        data, _ = arff.loadarff(f)
    clustering = pd.DataFrame(data)["Cluster"]
    
    # b'?' -> noise -> -1
    # b'cluster0' -> 0
    def convert(label):
        label = label.decode("utf-8")
        if label == "?":
            return -1
        return int(label.replace("cluster", ""))
    return clustering.apply(convert)

def run(original_dataset: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv"):
    path = f"./data./preprocessed./{original_dataset}"
    original_df = pd.read_csv(path)
    for method in os.listdir("./weka_results"):
        for arff_file in os.listdir(f"./weka_results./{method}"):
            if arff_file.endswith(".arff"):
                clustered_df = original_df.copy()
                # store the clustered data
                clustered_df["cluster"] = get_clustering(arff_file, f"./weka_results./{method}")
                clustered_df.to_csv(f"./weka_results./{method}./{arff_file[:-5]}.csv", index = False)
                # draw 3D
                filtered_df = clustered_df[["t", "gs", "track", "squawk", "nav_heading", "ecef_x", "ecef_y", "ecef_z"]]
                m = method.replace("clusterers.", "")
                visualize.draw_3D(filtered_df, clustered_df["cluster"], len(np.unique(clustered_df["cluster"])), m, f"{arff_file[:-5]}", f"./weka_results./{method}")

if __name__ == "__main__":
    run()