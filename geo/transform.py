#!/usr/bin/env python

import pandas as pd
import geopandas as gpd

from fiona.crs import from_epsg
from shapely.geometry import Point

import requests

with open("chicago_xy.csv", "w"): pass

for ip_i, ip in enumerate(pd.read_csv("chicago.csv.bz2", chunksize = 1e5,
                                      names = ["id", "datetime", "lat", "lon", "ip"])):

    geo = gpd.GeoSeries([Point(xy) for xy in ip[["lon", "lat"]].values], 
                        index = ip.index, crs = from_epsg(4326)).to_crs(epsg = 3528)

    ip_geo = gpd.GeoDataFrame(data = ip, geometry = geo, crs = geo.crs)

    ip_geo["x"] = ip_geo.geometry.x.astype(int)
    ip_geo["y"] = ip_geo.geometry.y.astype(int)

    ip_geo = ip_geo[["id", "datetime", "x", "y", "ip"]]

    ip_geo.to_csv("chicago_xy.csv", mode = "a", header = False, index = False)
    print(ip_i, end = " ", flush = True)

