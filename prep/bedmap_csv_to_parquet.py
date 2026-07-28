import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
from datetime import date

def average_year_to_date(y1: int, y2: int) -> str:
    d1, d2 = date(y1, 1, 1), date(y2, 1, 1)
    avg_ordinal = (d1.toordinal() + d2.toordinal()) // 2
    return date.fromordinal(avg_ordinal).isoformat()

data = Path("./data")
csvs = list((data / "bedmap_csv").glob("*.csv"))

drop_cols = ['trajectory_id', 'trace_number', 'time_UTC',
             'two_way_travel_time (m)', 'aircraft_altitude (m)',
             'along_track_distance (m)']

rename_map = {
    'surface_altitude (m)': "surface",
    'land_ice_thickness (m)': "thickness",
    'bedrock_altitude (m)': "bedrock",
}

gdfs = []
for csv in tqdm(csvs):
    df = (pd.read_csv(csv, skiprows=18, low_memory=False)
            .drop(columns=drop_cols)
            .rename(columns=rename_map))

    # filter early to drop fill rows
    df = df[df["thickness"] != -9999]

    # downcast to save memory
    for col in ["surface", "thickness", "bedrock",
                "longitude (degree_east)", "latitude (degree_north)"]:
        df[col] = pd.to_numeric(df[col], downcast="float")

    date_col = df["date"]
    valid_date = date_col[date_col != -9999]
    valid_prop = len(valid_date) / len(date_col)

    if valid_prop < 0.001:
        csv_metadata = pd.read_csv(csv, nrows=18, sep = ': ', engine='python', header= None)
        start = int(csv_metadata[csv_metadata[0] == "#time_coverage_start"][1].iloc[0])
        end = int(csv_metadata[csv_metadata[0] == "#time_coverage_end"][1].iloc[0])
        diff = start-end
        if diff > 2:
            if start in [1995,1996,1997,1998,1999, 2000,2001,2007,2008,2009,2014,2015,2016,2017,2020,2021,2022]:
                df["date"] = start
            elif end in [1995,1996,1997,1998,1999, 2000,2001,2007,2008,2009,2014,2015,2016,2017,2020,2021,2022]:
                df["date"] = end
            else:
                avg_val = average_year_to_date(start,end)
                df["date"] = avg_val 
        else:
            avg_val = average_year_to_date(start,end)
            df["date"] = avg_val 

    # build + reproject this file's GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df['longitude (degree_east)'], df['latitude (degree_north)'])
    ).drop(columns=['longitude (degree_east)', 'latitude (degree_north)'])

    gdf = gdf.set_crs("EPSG:4326").to_crs("EPSG:3031")


    gdfs.append(gdf)

# combine all reprojected GeoDataFrames
combined = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True), crs="EPSG:3031"
)
invalid_dates = (combined["date"] == -9999).sum()

print(invalid_dates, combined.size, invalid_dates/combined.size)
combined["date"] = combined["date"].astype("string")

combined.to_parquet(data / "bedmap3.parquet")