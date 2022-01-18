#!/usr/bin/env python 

# curl "https://opendata.fcc.gov/api/views/sgz3-kiqt/rows.csv?accessType=DOWNLOAD&sorting=true" -o fcc.csv

import pandas as pd

columns = {
  "Census Block FIPS Code" : "geoid",
  "Provider ID" : "provider_id", 
  "DBA Name" : "dbaname", 
  "Consumer" : "consumer",
  "Max Advertised Downstream Speed (mbps)" : "maxaddown",
  "Max Advertised Upstream Speed (mbps)" : "maxadup",
  "Max CIR Downstream Speed (mbps)" : "maxcirdown",
  "Max CIR Upstream Speed (mbps)" : "maxcirup"
}

#### Expensive!! Don't redo this all the time!!
##  fcc = pd.read_csv("data/fcc.csv.bz2", usecols = columns)
##  
##  fcc.rename(columns = columns, inplace = True)
##  fcc.sort_values(["geoid", "provider_id"], inplace = True)
##  fcc.reset_index(inplace = True, drop = True)
##  fcc = fcc[["geoid", "provider_id", "dbaname", "consumer", "maxaddown", "maxadup", "maxcirdown", "maxcirup"]]
##  
##  fcc.to_csv("data/fcc_redux.csv.bz2", index = False)

fcc = pd.read_csv("data/fcc_redux.csv.bz2")

fcc.query("consumer == 1", inplace = True)
fcc["geoid"] = (fcc.geoid // 1e4).astype(int)


nisp = fcc.groupby("geoid").provider_id.nunique().rename("nisp")

num_broadband_C_L = lambda g: g[(g.maxcirdown >= 25) & (g.maxcirup >= 3)].provider_id.nunique()
num_broadband_C = fcc.groupby("geoid").apply(num_broadband_C_L).rename("n25c")

num_broadband_C100_L = lambda g: g[(g.maxcirdown >= 100) & (g.maxcirup >= 10)].provider_id.nunique()
num_broadband_C100 = fcc.groupby("geoid").apply(num_broadband_C100_L).rename("n100c")

num_broadband_A_L = lambda g: g[(g.maxaddown >= 25) & (g.maxadup >= 3)].provider_id.nunique()
num_broadband_A = fcc.groupby("geoid").apply(num_broadband_A_L).rename("n25a")

num_broadband_A100_L = lambda g: g[(g.maxaddown >= 100) & (g.maxadup >= 10)].provider_id.nunique()
num_broadband_A100 = fcc.groupby("geoid").apply(num_broadband_A_L).rename("n100a")

cmax_down = fcc.groupby("geoid").maxcirdown.max().rename("maxdownc")
cmax_down_cat = pd.cut(cmax_down, [0, 0.5, 1, 2, 5, 25, 100, 500, 1000], include_lowest = True).rename("cmax_cat")

amax_down = fcc.groupby("geoid").maxaddown.max().rename("maxdowna")
amax_down_cat = pd.cut(amax_down, [0, 0.5, 1, 2, 5, 25, 100, 500, 1000], include_lowest = True).rename("amax_cat")


broadband = pd.concat([nisp, 
                       amax_down, num_broadband_A, num_broadband_A100, amax_down_cat,
                       cmax_down, num_broadband_C, num_broadband_C100, cmax_down_cat], axis = 1)

broadband.reset_index(inplace = True)
broadband.query("geoid / 1000000000 < 57", inplace = True) # < 57 retains US states and DC.
broadband[["geoid", "nisp", "n25a", "n100a", "maxdowna"]].to_csv("data/fcc_tract.csv.gz", index = True)


