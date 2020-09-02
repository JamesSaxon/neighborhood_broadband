#!/usr/bin/env python 

import os
import pandas as pd
import geopandas as gpd

from cidr import *

from tqdm import tqdm
tqdm.pandas()

from fiona.crs import from_epsg
from shapely.geometry import Point

import matplotlib.pyplot as plt

chicago = gpd.read_file("data/chicago.geojson").to_crs(epsg = 3528)
chicago_shape = chicago.iloc[0].geometry

def get_data(rebuild_from_aws = False, nrows = None):

    if rebuild_from_aws:
    
        file_template = "/media/jsaxon/brobdingnag/projects/corona/data/chicago_2020_{}.csv.gz"
    
        dfs = []
    
        for h in "0123456789abcdef":
    
            print(h, end = " ")
            dfs.append(pd.read_csv(file_template.format(h), 
                                   usecols = ["identifier", 
                                              "latitude", "longitude", "local_date_time", 
                                              "duration", "bump_count", "classification", 
                                              "ip_address", "x", "y", "geoid", "out_of_home", "night"],
                                   low_memory = False)\
                         .query("~ip_address.isnull()", engine='python'))
    
        df = pd.concat(dfs).reset_index(drop = True)
    
        df["subnet"] = df.ip_address.apply(subnet)
    
        df.to_csv("data/chicago_ip_only.csv.bz2", index = False)
        
    else:
        
        df = pd.read_csv("data/chicago_ip_only.csv.bz2", nrows = nrows)
        
        
    subnets = pd.read_csv("data/chicago_subnets.csv.bz2").merge(cidr_df[["CIDR", "DBA"]])
    df = df.merge(subnets)
    df["ip_address"] = df["ip_address"].str.lower()

    print(df.shape[0], df.memory_usage().sum() / 1e9)

    return df



def get_provider(df, dba, minID = 50):

    provider = df.query("(DBA == '{}') & (classification != 'TRAVEL')".format(dba))

    provider_geo = gpd.GeoSeries([Point(xy) for xy in provider[["x", "y"]].values],
                                crs = from_epsg(3528), index = provider.index)

    provider = gpd.GeoDataFrame(data = provider, 
                                geometry = provider_geo, 
                                crs = provider_geo.crs)

    provider_subnets = provider.groupby(["subnet", "identifier"])\
                               [["x", "y"]].mean().reset_index()

    provider_subnets_geo = gpd.GeoSeries([Point(xy) for xy in 
                                          provider_subnets[["x", "y"]].values],
                                        crs = from_epsg(3528), 
                                        index = provider_subnets.index)

    provider_subnets = gpd.GeoDataFrame(data = provider_subnets, 
                                        geometry = provider_subnets_geo, 
                                        crs = provider_subnets_geo.crs)
    
    subnets_N = provider_subnets.groupby("subnet").identifier.count()
    subnets_N = subnets_N[subnets_N >= minID].copy().sort_values(ascending = False)
    high_N = list(subnets_N.index)

    return provider.query("subnet in @high_N")


def map_format(ax, on = False):

    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.margins(0,0)
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())

    if not on:
        ax.set_axis_off()
        ax.set_axis_on()
        for a in ["bottom", "top", "right", "left"]:
            ax.spines[a].set_linewidth(0)

    return ax
    
    
def plot_subnets(data, label, pdf = False):
    
    os.makedirs("figs/{}".format(label), exist_ok = True)

    chicago_bounds = chicago.buffer(10000).bounds.iloc[0].to_dict()
    
    for net in tqdm(data.subnet.value_counts().index, desc = label):
        
        fig, ax = plt.subplots(figsize = (5, 5))

        chicago.boundary.plot(lw = 1, color = "b", ax = ax)

        SN = data.query("(subnet == '{}')".format(net)).copy()

        if SN.ip_address.unique().shape[0] <= 15:
            SN.plot(column = "ip_address", cmap = "nipy_spectral", 
                    markersize = 2, linewidth = 0, 
                    alpha = max(0.1, min(1, 1000 /SN.shape[0])), ax = ax, legend = True,
                    legend_kwds = {"fontsize" : 8, "loc" : "lower left", 
                                   "bbox_to_anchor" : (0, 0.025)})
            
        else:
            SN.plot(color = "red", markersize = 2, linewidth = 0, 
                    alpha = max(0.1, min(1, 1000 /SN.shape[0])), ax = ax)

        ctr = SN.unary_union.centroid
        SN["dctr"] = SN.distance(ctr)
        SN.sort_values("dctr", inplace = True)
        SN.reset_index(drop = True, inplace = True)

        if SN[:int(SN.shape[0] * 3/4)].unary_union.convex_hull.area / chicago_shape.area < 1/4:

            ch = gpd.GeoSeries([SN[:int(SN.shape[0] * 3/4)]\
                                  .unary_union.convex_hull.buffer(500)], crs = SN.crs)
            ch.plot(color = "#FF000044", edgecolor = "red", lw = 2, zorder = -10, ax = ax)

        map_format(ax)
        ax.set_xlim(chicago_bounds["minx"], chicago_bounds["maxx"])
        ax.set_ylim(chicago_bounds["miny"], chicago_bounds["maxy"])

        fig.suptitle("{}\n{} addresses\n{} users\n"\
                     .format(net, 
                             SN.ip_address.unique().shape[0], 
                             SN.identifier.unique().shape[0]), 
                     x = 0.92, y = 0.84, ha = "right", va = "top")

        fig.savefig("figs/{}/{}.png".format(label, net), dpi = 150,
                    facecolor = "w", edgecolor='none',
                    bbox_inches = "tight", pad_inches = 0.1)

        if pdf:
            fig.savefig("figs/{}/{}.pdf".format(label, net), bbox_inches = "tight", pad_inches = 0.1)

        plt.close("all")


if __name__ == "__main__":

    df = get_data(rebuild_from_aws = True)
    for DBA in []: # "UChicago", "Northwestern", "WOW", "RCN", "Comcast", "Verizon", "T-Mobile", "Sprint" "ATT"]:
        
        label = DBA.lower().replace("-", "")
        
        provider = get_provider(df, DBA)
        plot_subnets(provider, label, pdf = True)



