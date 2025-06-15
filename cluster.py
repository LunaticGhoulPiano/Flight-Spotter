import os
from tqdm import tqdm
import pandas as pd
import numpy as np
import visualizer
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, HDBSCAN, OPTICS
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
    os.makedirs(f"./python_results./kmeans./{filename[:-4]}", exist_ok = True)
    path = f"./python_results./kmeans./{filename[:-4]}./min_{min_cluster}_max_{max_cluster}"
    os.makedirs(path, exist_ok = True)
    
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
    
    # write the results
    clustered_df = original_df.copy()
    def run_sub(clusterings, scores, clustering_num: int, eval_method: str, eval_mode: str):
        clustered_df["cluster"] = clusterings
        os.makedirs(f"{path}./{eval_method}", exist_ok = True)
        sub_path = f"{path}./{eval_method}"
        clustered_df.to_csv(f"{sub_path}./clustered.csv", index = False)
        print(f"{clustering_num} clusters with {eval_mode} {eval_method.replace('_', ' ')} = {scores[clustering_num]}")
        
        distribution = clustered_df["cluster"].value_counts().reset_index()
        distribution.columns = ["cluster", "count"]
        print("Distribution (first 5 rows):")
        print(distribution.head(5))
        distribution.to_csv(f"{sub_path}./distribution.csv", index = False)

        visualizer.draw_distribution(distribution, sub_path)
        visualizer.draw_3D(filtered_df, clusterings, clustering_num, f"{eval_mode} {eval_method.replace('_', ' ')}", sub_path)
        visualizer.draw_map(clustered_df, sub_path)
    run_sub(lowest_sse_clusterings, sses, lowest_sse_cluster_num, "SSE", "highest")
    run_sub(highest_silhouette_score_clusterings, silhouette_scores, highest_silhouette_score_cluster_num, "Silhouette_Score", "lowest")

    # save ranking
    sses_list = list(sses.values())
    silhouette_scores_list = list(silhouette_scores.values())
    ranking = pd.DataFrame({"k": K_range, "SSE": sses_list, "Silhouette": silhouette_scores_list})
    print("Ranking (first 5 rows):")
    print(ranking.head(5))
    ranking.to_csv(f"{path}./ranking.csv", index = False)

    # draw evaluation of sse and silhouette Score
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
    plt.savefig(f"{path}./evaluation.png")

def run_HDBSCANorOPTICS(original_df, filtered_df, x, filename: str, method: str, min_points: int, epsilon: float):
    if method not in ["hdbscan", "optics"]:
        print("Method must be hdbscan or optics.")
        exit()
    os.makedirs(f"./python_results./{method}", exist_ok = True)
    os.makedirs(f"./python_results./{method}./{filename[:-4]}", exist_ok = True)
    str_epsilon = str(epsilon).replace(".", "_")
    path = f"./python_results./{method}./{filename[:-4]}./min_{min_points}_epsilon_{str_epsilon}"
    os.makedirs(path, exist_ok = True)

    # run
    clusterer = None
    if method == "hdbscan":
        clusterer = HDBSCAN(min_cluster_size = min_points, cluster_selection_epsilon = epsilon, metric = "euclidean")
    else:
        clusterer = OPTICS(min_samples = min_points, max_eps = epsilon, metric = "euclidean")
    clusterer.fit(x)

    # save clustered data
    clustered_df = original_df.copy()
    clustered_df["cluster"] = clusterer.labels_
    clustering_num = len(np.unique(clusterer.labels_))
    print(f"Number of clusters: {clustering_num}")
    clustered_df.to_csv(f"{path}./clustered.csv", index = False)

    # save distribution
    distribution = clustered_df["cluster"].value_counts().reset_index()
    distribution.columns = ["cluster", "count"]
    print("Distribution (first 5 rows):")
    print(distribution.head(5))
    distribution.to_csv(f"{path}./distribution.csv", index = False)

    visualizer.draw_distribution(distribution, path)
    visualizer.draw_3D(filtered_df, clustered_df["cluster"], clustering_num, method, path)
    visualizer.draw_map(clustered_df, path)

# fine-tune
def fine_tune(x, filename: str, method: str):
    os.makedirs(f"./python_results./{method}", exist_ok = True)
    os.makedirs(f"./python_results./{method}./finetune_records", exist_ok = True)
    path = f"./python_results./{method}./finetune_records./{filename[:-4]}"
    os.makedirs(path, exist_ok = True)
    
    # OPTICS fine-tuning
    finetune_redords_df = pd.DataFrame(columns = ["min_points", "epsilon", "clustering_num", "noise_num"])
    minPoints_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    eps_values = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]

    for minPoints in minPoints_values:
        for eps in eps_values:
            eps = round(eps, 3) # avoid float error
            # run
            clusterer = OPTICS(min_samples = minPoints, max_eps = eps, metric = "euclidean")
            clusterer.fit(x)

            # find cluster numbers
            clustering_num = len(np.unique(clusterer.labels_))

            # find noise
            distribution = pd.Series(clusterer.labels_).value_counts().reset_index()
            distribution.columns = ["cluster", "count"]
            noise_rows = distribution[distribution["cluster"] == -1]
            noise_num = 0
            if not noise_rows.empty:
                noise_num = noise_rows["count"].values[0]
            print(f"min_points: {minPoints}, epsilon: {eps}, clustering_num: {clustering_num}, noise_num: {noise_num}")
            finetune_redords_df.loc[len(finetune_redords_df)] = [minPoints, eps, clustering_num, noise_num]
    
    finetune_redords_df.to_csv(f"{path}./records.csv", index = False)

    # get the highest density point: min noise, max min_points, min epsilon
    min_noise = finetune_redords_df["noise_num"].min()
    filtered = finetune_redords_df[finetune_redords_df["noise_num"] == min_noise]
    filtered = filtered.sort_values(by = ["min_points", "epsilon"], ascending=[False, True])
    best = filtered.iloc[0]
    ideal_min_points = int(best["min_points"]) # points must be int
    ideal_epsilon = best["epsilon"]

    # pivot to 2D heatmap
    pivot_cluster = finetune_redords_df.pivot(index = "min_points", columns = "epsilon", values = "clustering_num")
    pivot_noise = finetune_redords_df.pivot(index = "min_points", columns = "epsilon", values = "noise_num")

    # draw cluster heatmap
    plt.figure(figsize = (10, 6))
    sns.heatmap(pivot_cluster, annot = True, fmt = ".0f", cmap = "YlGnBu")
    plt.title(f"Number of Clusters vs. min_points & epsilon (highest density: min points = {ideal_min_points}, epsilon = {ideal_epsilon})")
    plt.xlabel("epsilon")
    plt.ylabel("min_points")
    plt.tight_layout()
    plt.savefig(f"{path}./heatmap_clustering.png")

    # draw noise heatmap
    plt.figure(figsize = (10, 6))
    sns.heatmap(pivot_noise, annot = True, fmt = ".0f", cmap = "Reds")
    plt.title(f"Number of Noise Points vs. min_points & epsilon (highest density: min points = {ideal_min_points}, epsilon = {ideal_epsilon})")
    plt.xlabel("epsilon")
    plt.ylabel("min_points")
    plt.tight_layout()
    plt.savefig(f"{path}./heatmap_noise.png")

    return ideal_min_points, ideal_epsilon

# main
def run(filename: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv"):
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
    for min_cluster, max_cluster in [(2, 40), (2, 125), (7, 20)]:
        run_KMeans(df, filtered_df, x, filename, min_cluster, max_cluster)

    # HDBSCAN & OPTICS: must-run combinations
    for min_points, epsilon in zip([7, 20], [0.07, 0.6]):
        run_HDBSCANorOPTICS(df, filtered_df, x, filename, "hdbscan", min_points, epsilon)
        run_HDBSCANorOPTICS(df, filtered_df, x, filename, "optics", ideal_min_points, ideal_epsilon)

    # HDBSCAN & OPTICS: fine-tune and run the highest density
    ideal_min_points, ideal_epsilon = fine_tune(x, filename, "hdbscan")
    run_HDBSCANorOPTICS(df, filtered_df, x, filename, "hdbscan", min_points, epsilon)
    ideal_min_points, ideal_epsilon = fine_tune(x, filename, "optics")
    run_HDBSCANorOPTICS(df, filtered_df, x, filename, "optics", ideal_min_points, ideal_epsilon)

if __name__ == "__main__":
    run("readsb-hist_filtered_by_Taiwan_ADIZ.csv")
    #run("readsb-hist_filtered_by_Taiwan_manual_edges.csv")