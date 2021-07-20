#!/usr/bin/env python 

import os
import pandas as pd

ifile = "../data/fcc_477_jun_2020.csv.gz"
ofile = "../data/fcc_477_jun_2020_redux.csv.gz"

columns = ["BlockCode", "Provider_Id", "DBAName", "TechCode", "Consumer", "MaxAdDown", "MaxAdUp"]

col_dict = {"BlockCode" : "geoid", "Provider_Id" : "provider", 
            "DBAName" : "dba", "TechCode" : "tech", "Consumer" : "consumer", 
            "MaxAdDown" : "ad_dn", "MaxAdUp" : "ad_up"}

chunkerator = pd.read_csv(ifile, chunksize = 1000000, usecols = columns)

if os.path.exists(ofile): os.remove(ofile)

providers = []

for ci, chunk in enumerate(chunkerator):

    chunk.rename(columns = col_dict, inplace = True)
    chunk.query("consumer == 1", inplace = True)
    chunk.query("geoid < 570000000000000")
    chunk.query("tech != 60", inplace = True) # satellite
    chunk.drop("consumer", axis = 1, inplace = True)
    chunk["tech"] = chunk.tech // 10
    chunk["dba"]  = chunk.dba.str.replace(",", "")

    print(ci, end = " ", flush = True)
    chunk.to_csv(ofile, mode = "a", compression = "gzip",
                 index = False, header = (ci == 0))

