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
        # save clusterings
        os.makedirs(f"{path}./{eval_method}", exist_ok = True)
        sub_path = f"{path}./{eval_method}"
        print(f"{clustering_num} clusters with {eval_mode} {eval_method.replace('_', ' ')} = {scores[clustering_num]}")
        pd.DataFrame({"cluster": clusterings}).to_csv(f"{sub_path}./clustered.csv", index = False)

        clustered_df["cluster"] = clusterings
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

    # save evaluation
    sses_list = list(sses.values())
    silhouette_scores_list = list(silhouette_scores.values())
    evaluation = pd.DataFrame({"k": K_range, "SSE": sses_list, "Silhouette": silhouette_scores_list})
    print("evaluating (first 5 rows):")
    print(evaluation.head(5))
    evaluation.to_csv(f"{path}./evaluation.csv", index = False)

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

# HDBSCAAN or OPTICS
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
    clustering_num = len(np.unique(clusterer.labels_))
    print(f"Number of clusters: {clustering_num}")
    pd.DataFrame({"cluster": clusterer.labels_}).to_csv(f"{path}./clustered.csv", index = False)

    # merge with the original data
    original_df["cluster"] = clusterer.labels_

    # save distribution
    distribution = original_df["cluster"].value_counts().reset_index()
    distribution.columns = ["cluster", "count"]
    print("Distribution (first 5 rows):")
    print(distribution.head(5))
    distribution.to_csv(f"{path}./distribution.csv", index = False)

    visualizer.draw_distribution(distribution, path)
    visualizer.draw_3D(filtered_df, clusterer.labels_, clustering_num, method, path)
    visualizer.draw_map(original_df, path)

# fine-tune HDBSCAN and OPTICS
def fine_tune(x, filename: str):
    # clusterers
    methods = {
        "hdbscan": lambda min_points, epsilon: HDBSCAN(min_cluster_size = min_points, cluster_selection_epsilon = epsilon, metric = "euclidean"),
        "optics": lambda min_points, epsilon: OPTICS(min_samples = min_points, max_eps = epsilon, metric = "euclidean")
    }
    
    # fine-tune hyperparameters
    min_points_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    epsilon_values = [round(e, 3) for e in np.arange(0.7, 2.01, 0.1)] # 0.7 ~ 2.0
    
    # run
    results = {}
    for method_name, clusterer_fn in methods.items():
        print(f"Fine-tuning {method_name.upper()} parameters...")
        base_path = f"./python_results./{method_name}./finetune_records./{filename[:-4]}"
        os.makedirs(base_path, exist_ok = True)

        records_df = pd.DataFrame(columns = ["min_points", "epsilon", "clustering_num", "noise_num"])

        for min_points in min_points_values:
            for epsilon in epsilon_values:
                clusterer = clusterer_fn(min_points, epsilon)
                clusterer.fit(x)

                clustering_num = len(np.unique(clusterer.labels_))
                distribution = pd.Series(clusterer.labels_).value_counts().reset_index()
                distribution.columns = ["cluster", "count"]
                noise_num = distribution[distribution["cluster"] == -1]["count"].values[0] if -1 in clusterer.labels_ else 0

                print(f"[{method_name}] min_points: {min_points}, epsilon: {epsilon}, clustering_num: {clustering_num}, noise_num: {noise_num}")
                records_df.loc[len(records_df)] = [min_points, epsilon, clustering_num, noise_num]

        # write
        records_df.to_csv(f"{base_path}./records.csv", index=False)

        # order strategy of best hyparameters: min noise_num -> max min_points -> min epsilon
        min_noise = records_df["noise_num"].min()
        filtered = records_df[records_df["noise_num"] == min_noise]
        filtered = filtered.sort_values(by = ["min_points", "epsilon"], ascending = [False, True])
        best = filtered.iloc[0]
        ideal_min_points = int(best["min_points"])
        ideal_epsilon = best["epsilon"]

        # draw heatmap
        ## cluster
        pivot_cluster = records_df.pivot(index = "min_points", columns = "epsilon", values = "clustering_num")
        plt.figure(figsize = (10, 6))
        sns.heatmap(pivot_cluster, annot = True, fmt = ".0f", cmap = "YlGnBu")
        plt.title(f"Number of clusters (best: min_points = {ideal_min_points}, epsilon = {ideal_epsilon})")
        plt.xlabel("epsilon")
        plt.ylabel("min_points")
        plt.tight_layout()
        plt.savefig(f"{base_path}./heatmap_clustering.png")
        plt.close()
        ## noise
        pivot_noise = records_df.pivot(index = "min_points", columns = "epsilon", values = "noise_num")
        plt.figure(figsize = (10, 6))
        sns.heatmap(pivot_noise, annot = True, fmt = ".0f", cmap = "Reds")
        plt.title(f"Number of noise (best: min_points = {ideal_min_points}, epsilon = {ideal_epsilon})")
        plt.xlabel("epsilon")
        plt.ylabel("min_points")
        plt.tight_layout()
        plt.savefig(f"{base_path}./heatmap_noise.png")
        plt.close()

        results[method_name] = (ideal_min_points, ideal_epsilon)
        print(f"{method_name.upper()} best hyperparameters: min_points = {results[method_name][0]}, epsilon = {results[method_name][1]}\n")

    return (
        results["hdbscan"][0], results["hdbscan"][1],
        results["optics"][0], results["optics"][1]
    )

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

    # K-Mean
    for min_cluster, max_cluster in [(2, 40), (2, 125), (7, 20)]:
        run_KMeans(df, filtered_df, x, filename, min_cluster, max_cluster)

    # HDBSCAN & OPTICS
    ## fine-tune and run the highest density
    hdbscan_ideal_min_points, hdbscan_ideal_epsilon, optics_ideal_min_points, optics_ideal_epsilon = fine_tune(x, filename)
    run_HDBSCANorOPTICS(df, filtered_df, x, filename, "hdbscan", hdbscan_ideal_min_points, hdbscan_ideal_epsilon)
    run_HDBSCANorOPTICS(df, filtered_df, x, filename, "optics", optics_ideal_min_points, optics_ideal_epsilon)
    ## must-run combinations
    for min_points, epsilon in zip([7, 20], [0.07, 0.6]):
        if not (min_points == hdbscan_ideal_min_points and epsilon == hdbscan_ideal_epsilon):
            run_HDBSCANorOPTICS(df, filtered_df, x, filename, "hdbscan", min_points, epsilon)
        if not (min_points == optics_ideal_min_points and epsilon == optics_ideal_epsilon):
            run_HDBSCANorOPTICS(df, filtered_df, x, filename, "optics", min_points, epsilon)

if __name__ == "__main__":
    run()