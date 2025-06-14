import os
from tqdm import tqdm
import pandas as pd
import numpy as np
import visualize
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.metrics import silhouette_score

# K-Means
def run_KMeans(original_df, filtered_df, x, filename: str, min_cluster: int, max_cluster: int):
    if max_cluster < min_cluster:
        print(f"Error: max_cluster {max_cluster} < min_cluster {min_cluster}")
        return
    elif min_cluster < 2:
        print(f"Error: min_cluster {min_cluster} < 2")
        return
    os.makedirs("./python_results./kmeans", exist_ok = True)
    path = f"min_{min_cluster}_max_{max_cluster}_{filename[:-4]}"
    os.makedirs(f"./python_results./kmeans./{path}", exist_ok = True)
    lowest_sse_cluster_num = -1
    sses = {}
    lowest_sse_clusterings = []
    highest_silhouette_score_cluster_num = -1
    silhouette_scores = {}
    highest_silhouette_score_clusterings = []
    K_range = range(min_cluster, max_cluster + 1) # silhouette requires at least 2 clusters
    # run
    progress_bar = tqdm(K_range)
    for k in progress_bar:
        progress_bar.set_description(f"Running K-Means - {k} clusters")
        kmeans = KMeans(n_clusters = k, random_state = 0, n_init = 10)
        kmeans.fit(x)

        # evaluate
        cur_sse = kmeans.inertia_
        cur_silhouette_score = silhouette_score(x, kmeans.labels_)

        # ranking and storing
        if lowest_sse_cluster_num == -1: # first
            lowest_sse_cluster_num = k
            lowest_sse_clusterings = kmeans.labels_
            highest_silhouette_score_cluster_num = k
            highest_silhouette_score_clusterings = kmeans.labels_
        else: # rank sse and silhouette
            # ranking
            if cur_sse < sses[lowest_sse_cluster_num]:
                lowest_sse_cluster_num = k
                lowest_sse_clusterings = kmeans.labels_
            if cur_silhouette_score > silhouette_scores[highest_silhouette_score_cluster_num]:
                highest_silhouette_score_cluster_num = k
                highest_silhouette_score_clusterings = kmeans.labels_
        
        # append
        sses[k] = cur_sse
        silhouette_scores[k] = cur_silhouette_score
    # save results
    ## save lowest SSE
    temp_df = original_df.copy()
    temp_df["cluster"] = lowest_sse_clusterings
    print(f"lowest SSE: {lowest_sse_cluster_num} clusters with SSE = {sses[lowest_sse_cluster_num]}")
    # Save lowest SSE cluster distribution
    lowest_sse_distribution = temp_df["cluster"].value_counts().reset_index()
    lowest_sse_distribution.columns = ["cluster", "count"]
    print("Distribution (first 5 rows):")
    print(lowest_sse_distribution.head(5))
    lowest_sse_distribution.to_csv(f"./python_results./kmeans./{path}./lowest_sse_distribution.csv", index = False)
    temp_df.to_csv(f"./python_results./kmeans./{path}./lowest_sse.csv", index = False)
    ## save highest silhouette score
    temp_df['cluster'] = highest_silhouette_score_clusterings
    print(f"Highest Silhouette score: {highest_silhouette_score_cluster_num} clusters with silhouette score = {silhouette_scores[highest_silhouette_score_cluster_num]}")
    # Save highest Silhouette cluster distribution
    highest_silhouette_distribution = temp_df["cluster"].value_counts().reset_index()
    highest_silhouette_distribution.columns = ["cluster", "count"]
    print("Distribution (first 5 rows):")
    print(highest_silhouette_distribution.head(5))
    highest_silhouette_distribution.to_csv(f"./python_results./kmeans./{path}./highest_silhouette_distribution.csv", index = False)
    temp_df.to_csv(f"./python_results./kmeans./{path}./highest_silhouette.csv", index = False)
    # save
    sses_list = list(sses.values())
    silhouette_scores_list = list(silhouette_scores.values())
    ranking = pd.DataFrame({"k": K_range, "SSE": sses_list, "Silhouette": silhouette_scores_list})
    print("Ranking (first 5 rows):")
    print(ranking.head(5))
    ranking.to_csv(f"./python_results./kmeans./{path}./ranking.csv", index = False)

    # draw
    _, ax1 = plt.subplots()
    color = "tab:blue"
    ax1.set_xlabel("Number of clusters (k)")
    ax1.set_ylabel("SSE (Elbow)", color = color)
    ax1.plot(K_range, sses_list, marker = "o", color = color)
    ax1.tick_params(axis = "y", labelcolor = color)
    ax2 = ax1.twinx()
    color = "tab:green"
    ax2.set_ylabel("Silhouette Score", color = color)
    ax2.plot(K_range, silhouette_scores_list, marker = "s", color = color)
    ax2.tick_params(axis = "y", labelcolor = color)
    plt.title("K-Means: Elbow Method and Silhouette Analysis")
    plt.grid(True)
    plt.savefig(f"./python_results./kmeans./{path}./evaluation.png")
    visualize.draw_3D(filtered_df, lowest_sse_clusterings, lowest_sse_cluster_num, "Lowest SSE", "lowest_sse", f"./python_results./kmeans./{path}")
    visualize.draw_3D(filtered_df, highest_silhouette_score_clusterings, highest_silhouette_score_cluster_num, "Highest Silhouette Score", "highest_silhouette", f"./python_results./kmeans./{path}")

# HDBSCAN
def run_HDBSCAN(original_df, filtered_df, x, filename: str, min_points: int, epsilon: float):
    os.makedirs("./python_results./hdbscan", exist_ok = True)
    str_epsilon = str(epsilon).replace(".", "")
    path = f"min_{min_points}_epsilon_{str_epsilon}_{filename[:-4]}"
    os.makedirs(f"./python_results./hdbscan./{path}", exist_ok = True)

    clusterer = HDBSCAN(min_cluster_size = min_points, cluster_selection_epsilon = epsilon, metric = "euclidean")
    clusterer.fit(x)

    # save
    clustered_df = original_df.copy()
    clustered_df["cluster"] = clusterer.labels_
    clustering_num = len(np.unique(clusterer.labels_))
    print(f"Number of clusters: {clustering_num}")
    clustered_df.to_csv(f"./python_results./hdbscan./{path}./clustered.csv", index = False)
    distribution = clustered_df["cluster"].value_counts().reset_index()
    distribution.columns = ["cluster", "count"]
    print("Distribution (first 5 rows):")
    print(distribution.head(5))
    distribution.to_csv(f"./python_results./hdbscan./{path}./distribution.csv", index = False)
    visualize.draw_3D(filtered_df, clustered_df["cluster"], clustering_num, "HDBSCAN", "hdbscan", f"./python_results./hdbscan./{path}")

# main
def run(filename: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv", min_cluster: int = 7, max_cluster: int = 20, min_points: int = 7, epsilon: float = 0.6):
    # load
    df = pd.read_csv(f"./data./preprocessed./{filename}")

    # create output folder
    os.makedirs("./python_results", exist_ok = True)
    
    # filter and encode
    filtered_df = df[["t", "gs", "track", "squawk", "nav_heading", "ecef_x", "ecef_y", "ecef_z"]]
    df_encoded = pd.get_dummies(filtered_df, columns = ["t"]) # one-hot encoding the aircraft type

    # standardization
    scaler = StandardScaler()
    x = scaler.fit_transform(df_encoded)

    # K-Means
    #run_KMeans(df, filtered_df, x, filename, min_cluster, max_cluster)

    # HDBSCAN
    run_HDBSCAN(df, filtered_df, x, filename, min_points, epsilon)

if __name__ == "__main__":
    run()