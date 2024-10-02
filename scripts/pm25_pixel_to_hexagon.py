#!/usr/bin/env python

from shapely.geometry import Polygon
from shapely import wkt
import geopandas as gpd
import h3
import xarray as xa
import pandas as pd
from tqdm import tqdm
import os

def get_bounding_coordinates(lat, lon, delta_lat, delta_lon):
    half_side_lat = delta_lat/2
    half_side_lon = delta_lon/2

    point0 = (lon - half_side_lon, lat - half_side_lat)
    point1 = (lon + half_side_lon, lat - half_side_lat)
    point2 = (lon + half_side_lon, lat + half_side_lat)
    point3 = (lon - half_side_lon, lat + half_side_lat)

    return Polygon([point0, point1, point2, point3])

def h3_polyfill(unary, resolution):
	coords = [(lat, lon) for lon, lat in unary.exterior.coords]
	return h3.polygon_to_cells(h3.Polygon(coords), resolution)

def ncfile_to_h3(file, resolution):
    
    with xa.open_dataset(file) as ds:
        data = ds.to_dataframe().reset_index()

    data = data.dropna()

    data['geometry'] = data.apply(
        lambda row: get_bounding_coordinates(
            row['lat'], row['lon'], ds.Delta_Lat, ds.Delta_Lon
        ), axis = 1
    )

    hex_list = []
    for ix, row in tqdm(data.iterrows(), total = len(data)):
        hexes = list(h3_polyfill(row['geometry'], resolution = resolution))
        for h in hexes:
            newrow = [h, row['GWRPM25']]
            hex_list.append(newrow)

    hex_output = pd.DataFrame(hex_list, columns = ['hex','pm2.5'])
    output_path = os.path.join(
        os.getcwd(),
        f'h{resolution}_pm25.csv'
        )
    hex_output.to_csv(output_path, index=None)