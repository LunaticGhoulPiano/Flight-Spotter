import os
import pandas as pd
import numpy as np
from gps import make_boundary
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box
from sklearn.neighbors import KernelDensity
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from collections import defaultdict

from libpysal.weights import Queen
from esda import G_Local

def get_cluster_num_by_continuous_icao(df, timeout_in_sec: int = 1800):
    # timeout_in_sec: how long a cluster should be considered as a single cluster
    # i.e. if the time interval between two data points of the same hex is larger than timeout_in_sec
    # then they are considered as different clusters
    timestamps = pd.to_datetime(df[["year", "month", "day", "hour", "minute", "second"]])
    hexes = df["hex"].values
    temp_df = pd.DataFrame({"hex": hexes, "timestamp": timestamps})
    temp_df = temp_df.sort_values(by = ["hex", "timestamp"])

    cluster_count = 0
    last_time_by_hex = {}
    for row in temp_df.itertuples(index = False):
        hex_val = row.hex
        curr_time = row.timestamp

        if hex_val not in last_time_by_hex:
            cluster_count += 1
        else:
            time_diff = (curr_time - last_time_by_hex[hex_val]).total_seconds()
            if time_diff > timeout_in_sec:
                cluster_count += 1

        last_time_by_hex[hex_val] = curr_time

    return cluster_count

def draw_grid(gdf, grid, map, path):
    grid_nonzero = grid[grid["count"] > 0].copy()
    grid_nonzero = grid_nonzero.to_crs("EPSG:4326") # TWD97 to WGS84

    _, ax = plt.subplots(figsize = (10, 10), dpi = 300)
    map.plot(ax = ax, facecolor = "None")
    grid_nonzero.plot(
        column = "count",
        cmap = "coolwarm",
        legend = True,
        edgecolor = "none",
        ax = ax
    )

    plt.axis("off")
    plt.savefig(f"{path}./grid_by_count.png", bbox_inches = "tight", pad_inches = 0)
    plt.close()

    for column_name in ["hex", "flight"]:
        # draw by each attribute
        for legend_on in [True, False]:
            _, ax = plt.subplots(figsize = (10, 10), dpi = 300)
            gdf.to_crs(4326).plot(ax = ax, column = column_name, legend = legend_on)
            map.plot(ax = ax, facecolor = "None")
            ax.axis("off")
            legend_on_str = "on" if legend_on else "off"
            plt.savefig(f"{path}./grid_by_{column_name}_legend_{legend_on_str}.png", bbox_inches = "tight", pad_inches = 0)
            plt.close()
        
        # count
        stat = gdf.sjoin(grid, how = "inner", predicate = "within")
        group = stat.groupby("index_right")[column_name].nunique()
        count_col = f"{column_name}_count"
        grid[count_col] = group
        grid[count_col] = grid[count_col].fillna(0)
        grid_nonzero = grid[grid[count_col] > 0].copy().to_crs("EPSG:4326")
        # draw by count of each attribute
        _, ax = plt.subplots(figsize = (10, 10), dpi = 300)
        map.to_crs("EPSG:4326").plot(ax = ax, facecolor = "None")
        grid_nonzero.plot(
            column = count_col,
            cmap = "coolwarm",
            legend = True,
            edgecolor = "none",
            ax = ax
        )
        ax.axis("off")
        plt.savefig(f"{path}./grid_by_{column_name}_count.png", bbox_inches = "tight", pad_inches = 0)
        plt.close()

def KDE(grid, grid_length, map, path):
    grid_nonzero = grid[grid["count"] > 0].copy()
    coords = np.vstack([grid_nonzero.geometry.centroid.x, grid_nonzero.geometry.centroid.y]).T # center to coordinates
    weights = grid_nonzero["count"].values # use the count as weights

    # run
    kde = KernelDensity(bandwidth = grid_length, kernel = "gaussian")
    kde.fit(coords, sample_weight = weights)

    # generate density of grid
    xmin, ymin, xmax, ymax = grid_nonzero.total_bounds
    xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j] # 100 * 100
    grid_coords = np.vstack([xx.ravel(), yy.ravel()]).T

    # get density of each grid
    zz = np.exp(kde.score_samples(grid_coords)).reshape(xx.shape) # use exp() to restore the original scale in log
    
    # filter the sparse points
    threshold = 1e-11
    zz = np.ma.masked_where(zz < threshold, zz)

    # draw
    _, ax = plt.subplots(figsize = (10, 10), dpi = 300)
    im = ax.imshow(zz.T, origin = "lower", extent = (xmin, xmax, ymin, ymax), cmap = "coolwarm")
    map.to_crs(grid_nonzero.crs).plot(ax = ax, facecolor = "none", edgecolor = "black", linewidth = 0.5) # add layers
    plt.colorbar(im, ax = ax)
    ax.axis("off")
    plt.savefig(f"{path}./KDE.png", bbox_inches = "tight", pad_inches = 0) # lower case will cause error, can't open image on Windows
    plt.close()

def GETIS_ORD_G_i_star(grid, map, path, epsg):
    values = grid[grid["count"] > 0]["count"]
    w = Queen.from_dataframe(grid[grid["count"] > 0].to_crs(epsg), use_index = False)
    w.transform = "r"
    g_star = G_Local(values, w)
    grid_re = grid[grid["count"] > 0].copy()
    grid_re["G_stat"] = g_star.Gs
    grid_re["p_value"] = g_star.p_sim

    # probability density value < 0.05 -> significant grid
    grid_re["sig"] = grid_re["p_value"] < 0.05

    # draw
    _, ax = plt.subplots(figsize=(10, 10), dpi=300)
    grid_re[grid_re["sig"]].plot(column = "G_stat", cmap = "coolwarm", legend = True, ax = ax, edgecolor = "gray", linewidth = 0)
    map.to_crs(epsg).plot(facecolor = "None", ax = ax)
    ax.axis("off")
    plt.savefig(f"{path}./GETIS_ORD_Gstar.png", bbox_inches = "tight", pad_inches = 0)

def build_directional_graph(gdf):
    # build edges
    edges = defaultdict(int)
    for hex_id, group in gdf.groupby("hex"): # build fly through path of each hex
        fly_through_path = group["grid_idx"].tolist() # fly through path by grid
        fly_through_path = [pt for i, pt in enumerate(fly_through_path) if i == 0 or pt != fly_through_path[i - 1]] # avoid duplicate
        for i in range(len(fly_through_path) - 1):
            u, v = fly_through_path[i], fly_through_path[i + 1] # view neighbor grid and current grid as a directed edge
            if u != v:
                edges[(u, v)] += 1 # weight = number of fly through
    
    # build directional graph
    directional_graph = nx.DiGraph()
    for (u, v), w in edges.items():
        directional_graph.add_edge(u, v, weight = w) # weight = number of fly through of each pair of grid
    
    return directional_graph

def draw_social_network(map, grid, path: str, method: str):
    _, ax = plt.subplots(figsize = (16,9), dpi = 600)
    grid.plot(column = method, cmap = "Blues", legend = True, ax = ax)
    map.to_crs(3826).plot(facecolor = "None", ax=ax)
    ax.axis("off")
    # upper case the first letter in method
    plt.savefig(f"{path}./{method}.png", bbox_inches = "tight", pad_inches = 0) # upper case will cause error, can't open image on Windows
    plt.close()

def community_detection(path:str, epsg: int, grid, map, directional_graph):
    G_undirected = directional_graph.to_undirected()
    communities = list(greedy_modularity_communities(G_undirected))

    node2comm = {}
    for i, comm in enumerate(communities):
        for node in comm:
            node2comm[node] = i

    _, ax = plt.subplots(figsize = (10, 10), dpi = 300)
    grid["community"] = grid["grid_idx"].map(node2comm)
    grid.plot(column = "community", cmap = "tab20", legend = True, ax = ax)
    map.to_crs(epsg).plot(facecolor = "None", ax = ax)
    ax.axis("off")
    plt.savefig(f"{path}./community_detection.png", bbox_inches = "tight", pad_inches = 0)

def analyze_the_original_data(df, path, filename: str, map_folder_name: str, epsg: int):
    map_folder_path = f"./data./{map_folder_name}"
    
    # basic infos
    print("Number of unique ICAO Hexes:", len(df["hex"].unique()))
    print("Number of unique flights:", len(df["flight"].unique()))
    #print("Number of clusters by unique ICAO Hex:", get_cluster_num_by_continuous_icao(df))

    # sort and convert to geo-df data points
    df["timestamp"] = pd.to_datetime(df[["year", "month", "day", "hour", "minute", "second"]])
    df = df.sort_values(by = ["hex", "timestamp"])
    gdf = gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.lon, df.lat), crs = 4326) # WGS84
    gdf = gdf.to_crs(epsg)

    # build single grid (lattice)
    xmin, ymin, xmax, ymax = gdf.total_bounds
    grid_length = 5000 # 1 grid = 5000 * 5000 (meters)
    cols = np.arange(xmin, xmax + grid_length, grid_length)
    rows = np.arange(ymin, ymax + grid_length, grid_length)
    
    # build layer of grids
    polygons = []
    for x in cols:
        for y in rows:
            polygons.append(box(x, y, x + grid_length, y + grid_length))
    grid = gpd.GeoDataFrame({"geometry": polygons}, crs = f"EPSG:{epsg}") # TWD97 == EPSG:3826

    # add data points into layer with count
    joined = gpd.sjoin(gdf, grid, how = "inner", predicate = "within")
    counts = joined.groupby("index_right").size()
    grid["count"] = counts # number of data points in each grid
    grid["count"] = grid["count"].fillna(0)

    # get filtered map by boundary
    region_name = filename.replace("readsb-hist_filtered_by_", "").replace(".csv", "")
    boundary = make_boundary(f"{region_name}.json", False)
    shp_path = [f for f in os.listdir(map_folder_path) if f.endswith(".shp")][0] # the map file in SHP format
    map = gpd.read_file(f"{map_folder_path}./{shp_path}")
    map = gpd.clip(map, boundary) # get the cliped map by boundary

    draw_grid(gdf, grid, map, path)

    # Traditional geographic analysis
    KDE(grid, grid_length, map, path)
    GETIS_ORD_G_i_star(grid, map, path, epsg)
    
    # Social network analysis
    grid["grid_idx"] = np.arange(grid.shape[0])
    gdf = gdf.sjoin(grid[["geometry", "grid_idx"]])
    
    # build directional graph
    directional_graph = build_directional_graph(gdf)
    
    # draw results of social network analysis
    social_networks = {
        "in_degree": dict(directional_graph.in_degree(weight = "weight")),
        "out_degree": dict(directional_graph.out_degree(weight = "weight")),
        "betweenness": nx.betweenness_centrality(directional_graph, weight = "weight", normalized = True),
        "closeness": nx.closeness_centrality(directional_graph, distance = "weight"),
        "pagerank": nx.pagerank(directional_graph, weight = "weight")
    }
    for method, arrtibute in social_networks.items():
        # set and append attributes to grid
        nx.set_node_attributes(directional_graph, arrtibute, method)
        grid[method] = grid["grid_idx"].map(arrtibute)
        # draw
        draw_social_network(map, grid, path, method)
    
    # community detection
    community_detection(path, epsg, grid, map, directional_graph)
    
    # get node attributes for visualization
    #pos = {row["grid_idx"]: row["geometry"].centroid.coords[0] for idx, row in gdf.iterrows()}
    
    # get top 10 max s-t flow of edges
    #top_edges = sorted(directional_graph.edges(data = True), key = lambda x: x[2]["weight"], reverse = True)[:10]

def read_distribution(tool, method, folder_name, experiment) -> dict:
    distributions = {}
    if not (tool == "python" and method == "kmeans"): # normal cases
        csv_path = f"./{tool}_results./{method}./{folder_name}./{experiment}./distribution.csv"
        if not os.path.exists(csv_path):
            return distributions

        df = pd.read_csv(csv_path)
        noise_count = df[df["cluster"] == -1]["count"].sum() if (-1 in df["cluster"].values) else 0
        num_clusters = df.shape[0]
        num_clusters_wo_noise = df[df["cluster"] != -1].shape[0]
        label = f"({tool}, {method}, {experiment})"
        distributions[label] = {
            "x_value": num_clusters,
            "x_label": f"(clusters: {num_clusters_wo_noise}, noise: {noise_count})"
        }
    else: # special cases: python-kmeans
        experiment_path = f"./{tool}/{method}/{folder_name}/{experiment}"
        if not os.path.exists(experiment_path):
            return distributions

        for evaluate_methods in os.listdir(experiment_path):
            sub_path = os.path.join(experiment_path, evaluate_methods)
            for evaluate_method in os.listdir(sub_path):
                csv_path = f"{sub_path}./{evaluate_method}./distribution.csv"
                if not os.path.exists(csv_path):
                    continue

                df = pd.read_csv(csv_path)
                noise_count = df[df["cluster"] == -1]["count"].sum() if (-1 in df["cluster"].values) else 0
                num_clusters = df.shape[0]
                num_clusters_wo_noise = df[df["cluster"] != -1].shape[0]
                label = f"({tool}, {method}, {experiment}, {evaluate_methods}, {evaluate_method})"
                distributions[label] = {
                    "x_value": num_clusters,
                    "x_label": f"(clusters: {num_clusters_wo_noise}, noise: {noise_count})"
                }

    return distributions

def analyze_the_clustered_data(df, path: str, filename: str):
    folder_name = filename[:-4]
    distributions = {}
    for tool in ["weka", "python"]:
        for method in os.listdir(f"./{tool}_results"):
            for experiment in os.listdir(f"./{tool}_results./{method}./{folder_name}"):
                if experiment == "fine_tune_records":
                    continue
                result = read_distribution(tool, method, folder_name, experiment)
                distributions.update(result)
    
    # draw
    labels = list(distributions.keys())
    x_values = [distributions[k]["x_value"] for k in labels]
    x_labels = [distributions[k]["x_label"] for k in labels]

    _, ax = plt.subplots(figsize=(12, len(labels) * 0.6))
    bars = ax.barh(labels, x_values, color='skyblue')

    # x-axis title
    ax.set_xlabel(f"(number of clusters without noise, number of noise)")
    ax.set_ylabel("(tool, method, hyper parameters)")
    ax.set_title("Analysis of clustered distributions")

    # informations of each bar
    x_center = ax.get_xlim()[1] / 2 # center the x-axis content to the whole figure
    for bar, xlbl in zip(bars, x_labels):
        y_center = bar.get_y() + bar.get_height() / 2
        ax.text(
            x_center, y_center, xlbl,
            va = "center", ha = "center",
            fontsize = 8, color = "black",
            weight = "bold"
        )

    plt.tight_layout()
    plt.savefig(f"{path}./cluster_distribution_analysis.png", dpi = 300)
    plt.close()

def analyze(filename: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv", map_folder_name: str = "直轄市、縣(市)界線1140318", epsg: int = 3826):
    df = pd.read_csv(f"./data./preprocessed./{filename}")
    path = f"./analyzed_results./{filename[:-4]}"
    os.makedirs(path, exist_ok = True)

    analyze_the_original_data(df, path, filename, map_folder_name, epsg)
    analyze_the_clustered_data(df, path, filename)

if __name__ == "__main__":
    analyze()