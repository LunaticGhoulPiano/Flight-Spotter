import eval_and_draw_weka_results
import clusterer
import analyzer

def run(data_name: str = "readsb-hist_filtered_by_Taiwan_manual_edges.csv", shp_map_folder_name: str = "直轄市、縣(市)界線1140318", epsg: int = 3826):
    # shp_map_folder_name: put the folder that contains the shapefile that corresponds to the selected dataset (readsb-hist_filtered_by_{name of region filter file with no ".json"}.csv)
    # EPSG:3826 = TWD97, central meridian 121°E
    eval_and_draw_weka_results.run(data_name)
    clusterer.run(data_name)
    analyzer.analyze(data_name, shp_map_folder_name, epsg)