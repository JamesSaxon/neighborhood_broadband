#!/usr/bin/env python 

import pandas as pd
import numpy as np
import geopandas as gpd


fcc = pd.read_csv("../data/fcc_477_jun_2020_redux.csv.gz",  
                  usecols = ["provider", "geoid", "tech", "ad_dn", "ad_up"])

blocks = fcc.geoid.drop_duplicates().sort_values().reset_index(drop = True)
blocks = pd.Series(data = np.zeros(blocks.shape[0]), index = blocks, name = "zero").astype(int)
blocks = blocks.reset_index()

fcc['tract'] = fcc['geoid'] // 10000


def get_var(query, agg_fn, name, varname):

    df_bl = fcc.query(query).groupby("geoid")[varname].apply(agg_fn).reset_index(name = name)
    df_bl = df_bl.merge(blocks, how = "outer")
    df_bl[name] = df_bl[name].fillna(0)
    df_bl["tract"] = df_bl['geoid'] // 10000
    df_tr = df_bl.groupby("tract")[name].mean()
    
    return df_tr


max_dn = get_var(name = "max_dn", varname = "ad_dn", agg_fn = pd.Series.max, query = "(ad_dn > 1)")
max_up = get_var(name = "max_up", varname = "ad_up", agg_fn = pd.Series.max, query = "(ad_dn > 1)")

dn10  = get_var(name = "dn10",  varname = "provider", agg_fn = pd.Series.count, query = "ad_dn >= 10")
dn100 = get_var(name = "dn100", varname = "provider", agg_fn = pd.Series.count, query = "ad_dn >= 100")
dn250 = get_var(name = "dn250", varname = "provider", agg_fn = pd.Series.count, query = "ad_dn >= 250")
up100 = get_var(name = "up100", varname = "provider", agg_fn = pd.Series.count, query = "ad_up >= 100")

fiber_100u = get_var(name = "fiber_100u", varname = "provider", agg_fn = pd.Series.count, 
                     query = "(ad_up >= 100) & (tech == 5)")

constr_tracts = pd.concat([max_dn, max_up, dn10, dn100, dn250, fiber_100u], axis = 1)
constr_tracts.to_csv("constructed_vars.csv")  



