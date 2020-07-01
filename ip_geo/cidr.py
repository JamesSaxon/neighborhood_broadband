#!/usr/bin/env python 

import pandas as pd
import numpy as np
from ipaddress import ip_address, ip_network

import re
import requests

cidr_df = pd.read_csv("cidr.csv")


dba_refs = \
{"AT&T" : "ATT", "Verizon" : "Verizon", "Comcast" : "Comcast", 
 "University of Chicago" : "UChicago", 
 "Wide Open West" : "WOW",
 "T-Mobile" : "T-Mobile", "Sprint" : "Sprint",
 "Illinois Century Network" : "ICN",
 "ALPINE" : "Alpine", "Cox" : "Cox", "Google" : "Google",
 "Illinois Institute of Technology" : "IIT",
 "Internet Assigned Numbers Authority" : "IANA",
 "Windstream Communications": "Windstream",
 "City of Chicago" : "City of Chicago",
 "Everywhere Wireless" : "Everywhere",
 "JOHN NAPOLITANO" : "John Napolitano",
 "Qwest Communications" : "Qwest",
 "Remax" : "Remax", "Hughes Network Systems" : "Hughes",
 "OSI Group" : "OSI", "SilverIP" : "SilverIP", 
 "Synergy Internet" : "Synergy Internet",
 "Webpass" : "Webpass", "Network Device" : "Access One", ## See parent
 "OnShore" : "OnShore", "RCN" : "RCN", 
 "Wayport" : "Wayport", "rback8c.akrnoh" : "ATT" ## See parent
}


def address_in_cidr(net, ip):
    
    return ip_address(ip) in ip_network(net)



def find_cidr(ip):

    global cidr_df

    if ip is np.nan: return ""

    ip_orig = ip
    if "." in ip: ip = ip + '.0'
    if ":" in ip: ip = re.sub(":$", ":0000:0000:0000:0000:0000:0000", ip)

    ## First check if we've already cached the result.
    mask = cidr_df.CIDR.apply(address_in_cidr, args = (ip,))
    if mask.any(): return cidr_df[mask].CIDR.iloc[0]

    ## Otherwise go to ARIN to get the IP block.
    j = requests.get("http://whois.arin.net/rest/ip/{}".format(ip),
                     headers = {'Accept': 'application/json'}).json()

    try: 

        if "orgRef" in j["net"]:
            org = j["net"]["orgRef"]["@name"]
        elif "customerRef" in j["net"]:
            org = j["net"]["customerRef"]["@name"]

        net_block = j["net"]["netBlocks"]["netBlock"]
        if type(net_block) is dict:
            net_block = [net_block]

        for nb in net_block:

            new_cidr = nb["startAddress"]["$"] + "/" + nb["cidrLength"]["$"]

            new_dba = ""
            for ref, dba in dba_refs.items():
                if ref in org: new_dba = dba

            print(ip, org, new_cidr)
            cidr_df = cidr_df.append({"DBA" : new_dba, "Organization" : org, "CIDR" : new_cidr},
                              ignore_index = True)
            
        ## Then try it again -- should work now!
        mask = cidr_df.CIDR.apply(address_in_cidr, args = (ip,))
        if mask.any(): return cidr_df[mask].CIDR.iloc[0]

    except: pprint(j)

    return ""

   
 
def cache_cidr(): 

    cidr_df.sort_values(by = ["DBA", "CIDR"], inplace = True)
    cidr_df.to_csv("cidr.csv", index = False)

