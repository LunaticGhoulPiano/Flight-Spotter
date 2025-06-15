import os
from scipy.io import arff
import pandas as pd
import numpy as np
import visualizer

def get_clustering(filepath: str):
    with open(filepath, "r", encoding = "utf-8") as f:
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
        cur_path = f"./weka_results./{method}./{original_dataset[:-4]}"
        for folder in os.listdir(cur_path):
            for file in os.listdir(f"{cur_path}./{folder}"):
                if file == "clustered.arff":
                    output_path = f"{cur_path}./{folder}"
                    # store the clusterings
                    clusterings = get_clustering(f"{output_path}./{file}")
                    pd.DataFrame({"cluster": clusterings}).to_csv(f"{output_path}./clustered.csv", index=False)
                    # store the distribution of clusters
                    original_df["cluster"] = clusterings
                    distribution = original_df["cluster"].value_counts().reset_index()
                    distribution.columns = ["cluster", "count"]
                    distribution.to_csv(f"{output_path}./distribution.csv", index = False)
                    filtered_df = original_df[["t", "gs", "track", "squawk", "nav_heading", "ecef_x", "ecef_y", "ecef_z"]]

                    visualizer.draw_distribution(distribution, output_path)
                    visualizer.draw_3D(filtered_df, clusterings, len(np.unique(original_df["cluster"])), method, output_path)
                    visualizer.draw_map(original_df, output_path)

if __name__ == "__main__":
    run()