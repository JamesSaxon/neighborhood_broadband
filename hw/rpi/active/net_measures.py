#!/usr/bin/env python3

import os
import sys
import re
import json 
import time 

from datetime import datetime

from netrc import netrc

from subprocess      import Popen, PIPE

from influxdb_client import InfluxDBClient 
from influxdb_client.client.write_api import SYNCHRONOUS

import argparse

reference_site_dict = {
    "google"    : "google.com",
    "youtube"   : "youtube.com",
    "facebook"  : "facebook.com",
    "amazon"    : "amazon.com",
    "wikipedia" : "wikipedia.org",
    "tribune"   : "www.chicagotribune.com",
    "suntimes"  : "chicago.suntimes.com",
    "uchicago"  : "cs.uchicago.edu"
}

reference_sites = list(reference_site_dict.values())

render_site_dict = {
    "nytimes" : "nytimes.com",
    "google"  : "google.com"
}
    

def ping_latency(site = "google.com", i = 0.25, n = 10, timeout = 5, 
                 label = "", measurements = {}):

    print("ping", site)

    ping_cmd = "ping -i {:.2f} -c {:d} -w {:d} {:s}".format(i, n, timeout, site)
    ping_res = Popen(ping_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')
    
    ping_packet_loss = re.findall(', ([0-9.]*)% packet loss', ping_res, re.MULTILINE)[0]
    ping_packet_loss = float(ping_packet_loss)
    
    ping_rtt_ms = re.findall('rtt [a-z/]* = ([0-9.]*)/([0-9.]*)/([0-9.]*)/([0-9.]*) ms', ping_res)[0]
    ping_rtt_ms = [float(v) for v in ping_rtt_ms]
    
    if not label: label = site

    measurements[label + "_packet_loss_pct"] = ping_packet_loss
    measurements[label + "_rtt_min_ms"]      = ping_rtt_ms[0]
    measurements[label + "_rtt_max_ms"]      = ping_rtt_ms[2]
    measurements[label + "_rtt_avg_ms"]      = ping_rtt_ms[1]
    measurements[label + "_rtt_mdev_ms"]     = ping_rtt_ms[3]

    return measurements


def dns_dig_latency(sites = reference_sites, measurements = {}):
    
    print("dns latency")

    with open("/tmp/dns_sites.txt", "w") as f: f.write("\n".join(sites))

    dig_cmd = "dig @8.8.8.8 -f /tmp/dns_sites.txt"
    dig_res = Popen(dig_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    dig_res = re.findall('Query time: ([0-9]*) msec', dig_res, re.MULTILINE)
    dig_res = [int(v) for v in dig_res]

    measurements["dns_query_avg_ms"] = sum(dig_res) / len(dig_res)
    measurements["dns_query_max_ms"] = max(dig_res) 

    return measurements

def hops_to_backbone(measurements = {}, site = "google.com", backbone = "ibone"):

    print("hops to backbone")
    
    tr_cmd = "traceroute -m 15 -N 32 -w3 {} | grep -m 1 {}".format(site, backbone)
    tr_res = Popen(tr_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    tr_res = tr_res.strip().split(" ")
    if len(tr_res): hops = int(tr_res[0])
    else:           hops = -1

    measurements["hops_to_backbone"] = hops

    return measurements

def hops_to_target(measurements = {}, site = "google.com", label = "google"):

    print("hops to {}".format(site))
    
    tr_cmd = "traceroute -m 20 -q 5 -w 2 {} | tail -1 | awk -e '{{print $1}}'".format(site)
    tr_res = Popen(tr_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    tr_res = tr_res.strip().split(" ")
    if len(tr_res): hops = int(tr_res[0])
    else:           hops = -1

    measurements["hops_to_{}".format(label)] = hops

    return measurements


def connected_devices_arp(measurements = {}, 
                          device_file = "/home/pi/chalk/unique_mac_addr.csv"):

    import pandas as pd

    print("connected devices")

    ts = int(time.time())

    nmap_cmd = "/usr/bin/nmap -sn 192.168.1.0/24" 
    Popen(nmap_cmd, shell = True, stdout = PIPE)

    arp_cmd = "/usr/sbin/arp -e -i eth0 | grep : | grep -v '192.168.1.1 ' | tr -s ' ' | cut -f3 -d' ' | sort | uniq"
    arp_res = Popen(arp_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    devices = set(arp_res.strip().split("\n"))
    new_devices = [[dev, ts, 1] for dev in devices]
    new_devices = pd.DataFrame(columns = ["mac_addr", "last_seen", "N"],
                               data = new_devices)

    if not os.path.exists(device_file):
        with open(device_file, "w") as out:
            out.write("mac_addr,last_seen,N\n")

    existing_devices = pd.read_csv(device_file)

    devices = pd.concat([existing_devices, new_devices])
    devices = devices.groupby("mac_addr").agg({"N" : sum, "last_seen" : max})
    devices[["last_seen", "N"]].to_csv(device_file, index = True)

    measurements["devices_active"] = new_devices.shape[0]
    measurements["devices_total"]  = devices.shape[0]
    measurements["devices_1day"]   = devices.query("last_seen > {:d}".format(ts - 86400)).shape[0]
    measurements["devices_1week"]  = devices.query("last_seen > {:d}".format(ts - 86400 * 7)).shape[0]

    return measurements

def connected_devices_iw(measurements = {}, 
                         device_file = "/root/netrics/unique_mac_addr.csv"):

    print("connected devices")

    now_ts = int(time.time())

    iw_cmd = "{ iwinfo wlan0 assoclist && iwinfo wlan1 assoclist; } | grep ago | awk '{print tolower($1)}' | sort | uniq"
    iw_res = Popen(iw_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    new_devices = set(iw_res.strip().split("\n"))

    devices = {}
    if os.path.exists(device_file):
        for line in open(device_file):
            
            if not line: continue
            
            spline = line.split(",")
            
            device = spline[0]
            ts     = int(spline[1])
            N      = int(spline[2])
            
            devices[device] = [ts, N]
            

    for d in new_devices:
        if d in devices:
            devices[d][0]  = now_ts
            devices[d][1] += 1
        else:
            devices[d] = [now_ts, 1]

    print(devices)

    with open(device_file, "w") as out:
    	for d, vals in devices.items():
            out.write("{},{},{}\n".format(d, vals[0], vals[1]))


    measurements["devices_active"] = len(new_devices)
    measurements["devices_total"]  = len(devices)
    measurements["devices_1day"]   = sum([v[0] > now_ts - 86400     for d, v in devices.items()])
    measurements["devices_1week"]  = sum([v[0] > now_ts - 86400 * 7 for d, v in devices.items()])
    
    return measurements



def render_site(label = "nytimes", site = "https://nytimes.com", measurements = {}):

    print("rendering", site)

    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.add_argument("window-size=1200x600")
    options.add_argument("headless")
    driver = webdriver.Chrome(options = options)

    start = time.time()
    driver.get(site)
    end   = time.time()

    measurements[label + "_render_s"] = end - start

    driver.close()
    time.sleep(3)
    driver.quit()


def ookla_bandwidth(measurements = {}):

    print("ookla speedtest")

    from speedtest       import Speedtest

    s = Speedtest()
    s.get_best_server()
    s.download()
    s.upload()
    speedtest_results = s.results.dict()

    measurements["speedtest_download"] = speedtest_results["download"] / 1e6
    measurements["speedtest_upload"]   = speedtest_results["upload"]   / 1e6 

    return measurements

def iperf3_bandwidth(measurements = {}, bandwidth = 30,
                     protocol = "udp", reverse = False):

    print("iperf3 bandwidth measurment")

    UDP = protocol.lower() == "udp"

    iperf_cmd = "iperf3 -c tigerteam.io -p 33001 -i 0 -b {}M {} {}"\
                .format(bandwidth, "-u" if UDP else "", "-R" if reverse else "")

    iperf_res = Popen(iperf_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    iperf_rate = re.findall(' ([0-9.]*) Mbits/sec .*  receiver', iperf_res, re.MULTILINE)[0]
    iperf_rate = float(iperf_rate)

    iperf_jitter = re.findall(' ([0-9.]*) ms .*  receiver', iperf_res, re.MULTILINE)[0]
    iperf_jitter = float(iperf_jitter)

    ul_dl = "download" if reverse else "upload"

    measurements["iperf_{}_{}".format(protocol, ul_dl)] = iperf_rate
    if protocol == "udp": measurements["iperf_{}_{}_jitter_ms".format(protocol, ul_dl)] = iperf_jitter

    return measurements


def get_total_consumption(bmon_file):
    
    dl, ul = 0, 0

    update_time = os.path.getmtime(bmon_file)

    for line in open(bmon_file):
        
        if line[0] == "#": continue
        if not line.strip(): continue
        
        if "192.168.1" not in line: continue
        
        i, o = line.strip().split(",")[3:5]
        
        dl += int(i)
        ul += int(o)

    return dl, ul, update_time
    

def consumption_wrt(measurements = {}, bmon_file = "/tmp/usage.db"): 

    print("consumption measurment on router")

    old_dl, old_ul, old_time = get_total_consumption(bmon_file)

    bmon_cmd = "/opt/wrtbwmon/wrtbwmon update {}".format(bmon_file)
    bmon_res = Popen(bmon_cmd, shell = True, stdout = PIPE).stdout.read().decode('utf-8')

    new_dl, new_ul, new_time = get_total_consumption(bmon_file)
    
    time_diff  = new_time - old_time
    bw_dl_diff = (new_dl - old_dl) * 8 / time_diff / 1e6
    bw_ul_diff = (new_ul - old_ul) * 8 / time_diff / 1e6

    measurements["consumption_download"] = bw_dl_diff
    measurements["consumption_upload"]   = bw_ul_diff

    return measurements



def submit_measurements_to_influx(measurements):

    print(" >> uploading to influx")

    influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com/"
    influx_orgID, _, influx_token = netrc().authenticators("influx")
    influx_client = InfluxDBClient(url = influx_url, orgID = influx_orgID, token = influx_token)
    influx_write = influx_client.write_api(write_options = SYNCHRONOUS).write

    # https://www.influxdata.com/blog/getting-started-with-python-and-influxdb-v2-0/
    influx_write("burnham", "jsaxon@uchicago.edu", ## bucket / org
                 [{"measurement": "networks", 
                   "tags": {"install": "oberlin"}, 
                   "fields": measurements,
                   "time" : datetime.utcnow()
                 }])

   
    from influx_credentials import uc_cred
    uc_cred.client.write_points([{"measurement": "networks", 
                                  "tags": {"install": "oberlin"}, 
                                  "fields": measurements,
                                  "time" : datetime.utcnow()
                                 }])


def run(submit, ping, dns, hops, ookla, iperf, render, ndev, consumption,
	udp_ul, udp_dl, TURRIS):

    measurements = {}

    if ping: 
        for label, site in reference_site_dict.items():

            ping_latency(site = site, label = label, 
                         measurements = measurements)

    if dns:   dns_dig_latency (measurements = measurements)
    if hops:
    	if not TURRIS: hops_to_backbone(measurements = measurements)
    	else:          hops_to_target(measurements = measurements)

    if ndev:
    	if not TURRIS: connected_devices_arp(measurements = measurements)
    	else:          connected_devices_iw (measurements = measurements)

    if ookla: ookla_bandwidth (measurements = measurements)

    if iperf:
        iperf3_bandwidth(bandwidth = udp_dl, reverse = True,  measurements = measurements)
        iperf3_bandwidth(bandwidth = udp_ul, reverse = False, measurements = measurements)

    if consumption:
        if TURRIS: consumption_wrt(measurements = measurements)

    if render: 
        for label, site in render_site_dict.items():
            render_site(site = site, label = label, measurements = measurements)

    if submit: submit_measurements_to_influx(measurements)

    print(measurements)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run some network measurements and upload them to influx.')
    parser.add_argument("--no_submit", dest = "submit", default = True, action = 'store_false')
    parser.add_argument("-p", "--ping",   default = False, action = 'store_true')
    parser.add_argument("-d", "--dns",    default = False, action = 'store_true')
    parser.add_argument("-t", "--hops",   default = False, action = 'store_true')
    parser.add_argument("-n", "--ndev",   default = False, action = 'store_true')
    parser.add_argument("-s", "--ookla",  default = False, action = 'store_true')
    parser.add_argument("-i", "--iperf",  default = False, action = 'store_true')
    parser.add_argument("--udp_dl",  default = 35, type = int)
    parser.add_argument("--udp_ul",  default = 3, type = int)

    parser.add_argument("-c", "--consumption", default = False, action = 'store_true')
    parser.add_argument("-r", "--render", default = False, action = 'store_true')
    parser.add_argument("-T", "--TURRIS", default = False, action = 'store_true')
    args  = parser.parse_args()

    print(args)
    run(**vars(args))


