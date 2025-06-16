import ecef
import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import random

def draw_3D(filtered_df, clustering, num_of_clusters, mode, path):
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
        plt.savefig(f"{path}./3D.png")
        plt.close()

def draw_distribution(distribution, save_path):
    distribution["cluster"] = distribution["cluster"].apply(lambda x: "noise" if x == -1 else str(x))
    plt.figure(figsize = (8, 6))
    plt.bar(distribution["cluster"], distribution["count"], color = "skyblue", edgecolor = "black")
    plt.xlabel("Cluster")
    plt.ylabel("Count")
    plt.title(f"Cluster Distribution")
    plt.xticks(distribution["cluster"])
    plt.tight_layout()
    plt.savefig(f"{save_path}./distribution.png")
    plt.close()

def draw_map(df, folder_path: str, data_num: int, threshold: int = 20000):
    if data_num > threshold:
        print(f"The current dataset size ({data_num}) is too big (larger than {threshold}), the html map file may not be created successfully. Please use the dataset size that is smaller than {threshold} for better visualization.")
        return
    # load data
    df["timestamp"] = pd.to_datetime(df[["year", "month", "day", "hour", "minute", "second"]])
    df["timestamp_str"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["ts_unix"] = (df["timestamp"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")

    # draw clusters
    unique_clusters = df["cluster"].unique()
    cluster_colors = {}
    for cluster in unique_clusters:
        if cluster == -1: # noise must use gray
            cluster_colors[cluster] = [128, 128, 128]
        else: # assign random color
            while True:
                color = [random.randint(0, 255) for _ in range(3)]
                if color not in cluster_colors.values():
                    cluster_colors[cluster] = color
                    break
    df["color"] = df["cluster"].map(cluster_colors)

    # build layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position = "[lon, lat, alt_geom]",
        get_fill_color = "color",
        get_radius = 300,
        pickable = True,
        auto_highlight = True,
        get_line_color = [255, 255, 255],
    )

    # map view settings
    view_state = pdk.ViewState(
        latitude = df["lat"].mean(),
        longitude = df["lon"].mean(),
        zoom = 9,
        pitch = 1000
    )

    # build map
    r = pdk.Deck(
        layers = [layer],
        initial_view_state = view_state,
        tooltip = {
            "html": """
                <b>Cluster:</b> {cluster} <br/>
                <b>Time:</b> {timestamp_str} <br/>
                <b>ICAO hex:</b> {hex} <br/>
                <b>Flight:</b> {flight} <br/>
                <b>Type:</b> {t} <br/>
                <b>Barometric / Geometric altitude:</b> {alt_baro} / {alt_geom} feets<br/>
                <b>Ground speed:</b> {gs} knots<br/>
                <b>Track:</b> {track} degrees<br/>
                <b>Geometric rate:</b> {geom_rate} feet/minute<br/>
                <b>Squawk:</b> {squawk} <br/>
                <b>Altimeter setting (QFE or QNH/QNE):</b> {nav_qnh} hPa<br/>
                <b>selected altitude from the Mode Control Panel / Flight Control Unit (MCP/FCU) or equivalent equipment:</b> {nav_altitude_mcp} feet<br/>
                <b>selected altitude from the Flight Manaagement System (FMS):</b> {nav_altitude_fms} feet<br/>
                <b>Selected heading:</b> {nav_heading} degrees<br/>
                <b>Latitude:</b> {lat} degrees<br/>
                <b>Longitude:</b> {lon} degrees <br/>
                <b>Navigation Integrity Category:</b> {nic} <br/>
                <b>Radius of Containment:</b> {rc} meters <br/>
                <b>Navigation Integrity Category for Barometric Altitude:</b> {nic_baro} <br/>
                <b>Navigation Accuracy for Position:</b> {nac_p} <br/>
                <b>Navigation Accuracy for Velocity:</b> {nac_v} <br/>
                <b>Source Integity Level:</b> {sil} <br/>
                <b>Interpretation of SIL:</b> {sil_type}
            """
        }
    )

    # output
    r.to_html(f"{folder_path}./clustered.html", notebook_display = False)
    print(f"{folder_path}./clustered.html generated.")