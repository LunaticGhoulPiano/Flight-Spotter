# Flight-Spotter
## Warnings
- Currently only could run on **Windows** (only knows how to get user's gps location on Windows, also don't have other platform to test)
- Please **enable GPS** in settings ([official tutorial here](https://support.microsoft.com/en-us/windows/windows-location-service-and-privacy-3a8eee0a-5b0b-dc07-eede-2a5ca1c49088))

## Flow
![image](https://github.com/LunaticGhoulPiano/Flight-Spotter/blob/master/pics/flow.jpg?raw=true)
- See ```./flow.drawio```
- Mining:
    1. Get the historical data
    2. Set a default location (lat., lon., radius)
    3. Filter flights by location in the circle with the provided radius
    4. Mining / training routes of the flights for looking for the best place of spotting
    5. Save the result data
- Interactive:
    0. Build a discord bot([tutorial here](https://github.com/smallshawn95/Python-Discord-Bot-Course)), and buy a server (Oracle Cloud VPS, or Raspberry pi...)
    1. Get user GPS location / manually input / set a default location
    2. Search the neighbouring spotting place in the result data

## Data resources
- [ADS-B Exchange free historical data](https://www.adsbexchange.com/products/historical-data/)
- [readsb official documentation](https://github.com/wiedehopf/readsb/blob/dev/README-json.md)
- [Taiwan ADIZ](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2002-25_2025_04_17/index.html)
    ![image](https://github.com/LunaticGhoulPiano/Flight-Spotter/blob/master/pics/JADIZ_and_CADIZ_and_KADIZ_in_East_China_Sea.jpg?raw=true)
    (This picture is from [wikipedia](https://en.wikipedia.org/wiki/Air_Defense_Identification_Zone_(Taiwan)))
- [Other discussion](https://www.reddit.com/r/ADSB/comments/1gabgnf/any_free_sources_for_flight_historical_data/)
- [adsb.lol api](https://api.adsb.lol/docs) (to get live data for the interactive stage)

## Data mining Algo.
- To be continued
- Recommend methods by GhatGPT:
    - DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
        - [Tutorial 1](https://tomohiroliu22.medium.com/%E6%A9%9F%E5%99%A8%E5%AD%B8%E7%BF%92-%E5%AD%B8%E7%BF%92%E7%AD%86%E8%A8%98%E7%B3%BB%E5%88%97-84-%E5%9F%BA%E6%96%BC%E5%AF%86%E5%BA%A6%E4%B9%8B%E5%90%AB%E5%99%AA%E7%A9%BA%E9%96%93%E8%81%9A%E9%A1%9E%E6%B3%95-density-based-spatial-clustering-of-applications-with-noise-63a88275d678)
        - [Tutorial 2](https://tomohiroliu22.medium.com/%E6%A9%9F%E5%99%A8%E5%AD%B8%E7%BF%92-%E5%AD%B8%E7%BF%92%E7%AD%86%E8%A8%98%E7%B3%BB%E5%88%97-87-%E5%9F%BA%E6%96%BC%E5%AF%86%E5%BA%A6%E4%B9%8B%E5%90%AB%E5%99%AA%E7%A9%BA%E9%96%93%E9%9A%8E%E5%B1%A4%E8%81%9A%E9%A1%9E%E6%B3%95-hierarchical-density-based-spatial-clustering-of-applications-with-af6e9933bba3)
        - [Tutorial 3](https://medium.com/ai-academy-taiwan/clustering-method-1-11bcbe0fb12f)
        ```
        【基於 GPS 資料點的空間密度聚類 (Spatial Clustering)】
        方法：
        - 使用 DBSCAN（Density-Based Spatial Clustering of Applications with Noise），適合空間座標聚類。
        - 搭配 haversine 距離（球面距離）處理。
        - 可以將所有在一定高度內的飛機位置（例如 alt_geom ≤ 40000ft ≈ 12192m）集中，然後根據經緯度聚類出「常見的空中航線」或「飛機頻繁出現的區域」。

        適合場景：
        - 找出歷史上經常飛過的地點 → 這些地點對應地面點，最有潛力成為觀察點。
        ```
    - Grid-and-Heatmap-based hotspot-frequency analysis
        ```
        【網格化頻率統計 + 熵 / 熱點分析 (Grid Frequency Analysis)】
        方法：
        - 建立一個地理網格（例如 0.01° × 0.01°），每格統計有多少飛機「在半球內經過」。
        - 可結合高度條件（如在一定高度以下）。
        - 最後篩選出高頻區塊作為觀察候選地點。

        適合場景：
        - 預處理階段快速初步找出「熱點」，再進一步結合地面位置（可進一步排除海洋或山區）。

        Python 工具：
        - 使用 numpy + pandas 建立網格計數。
        - 可加上 geopandas / folium / matplotlib 做地圖視覺化。
        ```
    - Spatiotemporal weighted Analysis with Decay
        ```
        【時間維度加權的熱度分析（Temporal Heatmap with decay）】
        方法：
        - 對於每一個航班，紀錄其經過地點與時間。
        - 可考慮時間衰退權重（近期比久遠的權重大）。
        - 最終得出熱度地圖，再轉換為地面觀測點候選。

        適合場景：
        - 若想要支援近期趨勢而非歷史均值，例如現在飛機航線因疫情或戰爭改變。

        Python 工具：
        - pandas 時間處理 + 自訂權重函數
        ```
    - Backprojection by skyview
        ```
        【視野半球範圍內的反推熱區 (Skyview Backprojection)】
        方法：
        - 對每個飛機位置，反推出它能被哪個地面位置看到（使用半球幾何，地面為底）。
        - 所有飛機都這樣反推，再在地面上統計「被能看到的次數最多的點」。

        適合場景：
        - 你想要嚴格考慮視野邊界（仰角/可視半徑），而不僅是飛機在哪裡。

        實現方向：
        - 這是你描述中已經設想的核心方法，可搭配以上聚類或統計方式交叉驗證。
        ```
- Sum up
    | 方法名稱 | 特點 | 適合用途 |
    | ------- | ---- | ------- |
    | DBSCAN | 不需指定群數，找密集點 | 發現空中熱點/通道 |
    | Grid頻率分析 | 快速統計 + 熱區標記 | 建立初步地面觀察點候選 |
    | 時間加權分析 | 考慮航班時間變化 | 動態/即時熱點推薦 |
    | 半球反推分析 | 精準匹配人眼可視區域 | 面點最佳化推薦 |

## Data preprocessing
### Before running
- Set the specific data to download by time: you **SHOULD** manually add ```ENABLES_YEAR``` and ```ENABLES_MONTH``` at ```./get_data.py```, by my default this code will only download 2020/03/01, cuz too big. Just straightly add the time into these two lists.
- According to the [official description of ads-b exchange historical data](https://www.adsbexchange.com/products/historical-data/) - **readsb-hist**: **"Snapshots of all global airborne traffic are archived every 5 seconds starting April 2020, (prior data is available every 60 secs from starting in July 2016)."** (The official description says that "... every 5 seconds starting April 2020 ...", but the actucal data shows that it starts from **april**).
- The free historical data only provides **the first day of a month**, so don't modify ```ENABLES_DAY```.
### Install packages by pip
```
python -m pip install -r requirements.txt
```
### Run
```
python preprocess.py
```

## Discord bot
- To be continued
-  Used scripts and folders: ```./bot.py```
- If you want to build you own bot:
    1. Create a discord bot, get a token at ```BOT``` pgae
    2. Create an ```.env``` file and store at the root folder, set ```DISCORD_BOT_TOKEN='<YOUR_DISCORD_BOT_TOKEN>'``` into it
- Still learning from [this tutorial](https://github.com/smallshawn95/Python-Discord-Bot-Course)

## adsb.lol api testing
### Before running
-  Used scripts: ```./adsb_lol_api.py```, ```./gps.py```, ```./main.py```
- Documentations please read [this official webpage](https://api.adsb.lol/docs)
- Remember should install ```./requirements.txt```
### Run
```
python main.py
```

## Current progress
- [x] Set a specific filtering range: Taiwan ADIZ, at ```./data./Taiwan./Taiwan_ADIZ.json``` (manually create)
- [x] Get aircraft type data and readsb-hist data, store to  ```./data./aicraft``` and ```./data./historical_adsbex_sample``` (auto-created)
- [x] Filter by Taiwan ADIZ and store with a formatted file name: ```{year}_{month}_{day}_{hour}_{minute}_{second}.json``` to ```./data./Taiwan./filtered_by_Taiwan_ADIX``` folder (auto-created)

## Structure
- To be continued