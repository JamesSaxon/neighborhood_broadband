#!/usr/bin/env python 

import argparse
import os
import re
import requests
import json
import netrc
import glob
import pandas as pd


def scan_addresses():
    
    # Get the scan from the CLI.
    scan = os.popen("airport -s").read()

    # Regex mac address.
    mac_re = r"[0-f][0-f]" + r":[0-f][0-f]" * 5

    addresses = []
    for li, line in enumerate(scan.split("\n")):

        if "SSID BSSID"   in line: continue
        if "IBSS network" in line: continue

        ssid = re.sub(r"(.*) (" + mac_re + ").*", r"\1", line).strip()
        if not ssid: continue

        rest = re.sub(r".* (" + mac_re + ".*)", r"\1", line)
        rest = re.sub(r"  *", " ", rest).split(" ")

        bssid    = rest[0]
        strength = int(rest[1])
        channel  = int(rest[2].split(",")[0])

        addresses.append((ssid, bssid, strength, channel))

    df = pd.DataFrame(columns = ["SSID", "BSSID", "RSSI", "Ch"], data = addresses)
    df.sort_values("RSSI", ascending = False, inplace = True)
    df.reset_index(drop = True, inplace = True)

    df.rename(columns = {"BSSID" : "macAddress", "RSSI" : "signalStrength"}, inplace = True)

    addresses = df[["macAddress", "signalStrength"]].to_dict(orient = "records")

    return addresses
    
    
def get_location(addresses):

    # Get a Google API Key
    _, _, api_key = netrc.netrc().authenticators("google-location")

    payload = {"considerIp": False, "wifiAccessPoints" : addresses}

    resp = requests.post("https://www.googleapis.com/geolocation/v1/geolocate?key=" + api_key, json = payload)
    resp = resp.json()
    
    return resp


def get_scan_number(folder = "scans"):

    os.makedirs("scans/", exist_ok = True)

    scan_number = 0
    scans = glob.glob("scans/*")
    if scans:
        for f in scans:

            f = re.sub(r"scans/([0-9]{5}).json", r"\1", f)

            try: fi = int(f) 
            except: continue

            if fi + 1 > scan_number:
                scan_number = fi + 1
                
    return scan_number

def write_scan(data, scan_number = -1, folder = "scans"):
    
    # Check the max scan yet recorded.
    if scan_number < 0: scan_number = get_scan_number("scans/")

    with open("scans/{:05d}.json".format(scan_number), "w") as out:
        if "lat" in data:
            print("Recording scan {} at ({:f}, {:f}) -- {:d} APs."\
                  .format(scan_number, data["lat"], data["lon"], len(data["bssid"])))
        else:
            print("Recording scan {} -- {:d} APs.  (No location.)"\
                  .format(scan_number, len(data["bssid"])))

        out.write(json.dumps(data))


def scan(locate = False):
    
    addresses = scan_addresses()
    
    data = {"bssid" : addresses}

    if locate:

        location = get_location(addresses)

        data["acc"] = location["accuracy"]
        data["lat"] = location["location"]["lat"]
        data["lon"] = location["location"]["lng"]

    write_scan(data)
    

def locate_scans(folder = "scans"):
        
    for f in glob.glob(folder + "/[0-9][0-9][0-9][0-9][0-9].json"):

        fi = int(re.sub(r"scans/([0-9]{5}).json", r"\1", f))

        with open(f) as obj: data = json.load(obj)

        if "lat" in data.keys(): continue

        location = get_location(data["bssid"])

        data["acc"] = location["accuracy"]
        data["lat"] = location["location"]["lat"]
        data["lon"] = location["location"]["lng"]

        write_scan(data, scan_number = fi)

    
    
    
    
if __name__ == "__main__": 

    parser = argparse.ArgumentParser() 
    parser.add_argument("-l", "--locate", action = "store_true",
                        help = "Retrieve lat/lon from Google Location API")

    args = parser.parse_args()

    scan(locate = args.locate)




