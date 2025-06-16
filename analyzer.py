import pandas as pd


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

def analyze(filename: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv"):
    df = pd.read_csv(f"./data./preprocessed./{filename}")
    
    print(df["hex"].unique())
    print(len(df["hex"].unique()))
    print(df["flight"].unique())
    print(len(df["flight"].unique()))
    print(get_cluster_num_by_continuous_icao(df, 1800))

if __name__ == "__main__":
    analyze()