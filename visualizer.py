import ecef
import matplotlib.pyplot as plt

def draw_3D(filtered_df, clustering, num_of_clusters, mode, name, path):
        # draw 3D
        fig = plt.figure(figsize = (10, 8))
        ax = fig.add_subplot(111, projection = "3d")
        lat, lon, alt_geom = ecef.decode(filtered_df["ecef_x"], filtered_df["ecef_y"], filtered_df["ecef_z"])
        scatter = ax.scatter(lat, lon, alt_geom, c = clustering, cmap = "tab10", s = 10, alpha = 0.6)
        ax.set_xlabel("Latitude (degree)")
        ax.set_ylabel("Longitude (degree)")
        ax.set_zlabel("Geometric Altitude (feet)")
        ax.set_title(f"Clustering of {mode}: {num_of_clusters} Clusters")
        fig.colorbar(scatter, label = "Cluster")
        plt.tight_layout()
        plt.savefig(f"{path}./3D_{name}.png")

def draw_distribution(distribution, filename, save_path):
    distribution["cluster"] = distribution["cluster"].apply(lambda x: "noise" if x == -1 else str(x))
    plt.figure(figsize = (8, 6))
    plt.bar(distribution["cluster"], distribution["count"], color = "skyblue", edgecolor = "black")
    plt.xlabel("Cluster")
    plt.ylabel("Count")
    plt.title(f"Cluster Distribution")
    plt.xticks(distribution["cluster"])
    plt.tight_layout()
    plt.savefig(f"{save_path}./{filename}.png")