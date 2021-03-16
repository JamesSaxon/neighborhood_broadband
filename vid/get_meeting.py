#!/usr/bin/env python 

import os, sys
import base64 as b64
import requests
import urllib.parse
import argparse
import json
import netrc
import time

from dateutil.parser import parse
from pprint import pprint


install_url = "https://zoom.us/oauth/authorize?response_type=code&client_id={}&redirect_uri={}"
auth_url    = "https://zoom.us/oauth/token?grant_type=authorization_code&redirect_uri={}&code={}"
refresh_url = "https://zoom.us/oauth/token?grant_type=refresh_token&refresh_token={}"

user_url         = "https://api.zoom.us/v2/users/{}"
meeting_url      = "https://api.zoom.us/v2/past_meetings/{}/instances"
participants_url = "https://api.zoom.us/v2/metrics/meetings/{}/participants"

# qos_url        = "https://api.zoom.us/v2/metrics/meetings/{}/participants/qos"     ##  All users
qos_url          = "https://api.zoom.us/v2/metrics/meetings/{}/participants/{}/qos"  ##  Single user
my_url           = "https://saxon.cdac.uchicago.edu/"


def get_token_auth(code, token_cache):

    if os.path.exists(token_cache):

        with open(token_cache, "r") as token_file:
            j = json.load(token_file)

            token   = j["access_token"]
            refresh = j["refresh_token"]

            if int(time.time()) < j["ts"] + j["expires_in"]:
                return {'authorization': 'Bearer ' + token}

    else: refresh = False


    client_id, _, passwd = netrc.netrc().authenticators("zoom")

    if not code and not refresh:
        print("Go get a code from the redirect url here:",
              install_url.format(client_id, urllib.parse.quote_plus(my_url)))

        sys.exit()
    
    auth       = "{}:{}".format(client_id, passwd)
    auth_enc64 = b64.b64encode(auth.encode("utf-8")).decode("utf-8")
    header     = {'authorization' : 'Basic ' + auth_enc64}

    if refresh: j = requests.post(refresh_url.format(refresh), headers = header).json()
    else:       j = requests.post(auth_url.format(my_url, code), headers = header).json()

    j["ts"] = int(time.time())

    with open(token_cache, "w") as out: json.dump(j, out)

    token = j["access_token"]
    token_auth = {'authorization': 'Bearer ' + token}

    return token_auth


def get_qos(code, token_cache, meeting, user_email, output):

    token_auth = get_token_auth(code, token_cache)

    j = requests.get(user_url.format(user_email), headers = token_auth).json()
    user_id = j["id"]

    j = requests.get(meeting_url.format(meeting), headers = token_auth).json()
    meetings = j["meetings"]
    meetings.sort(key = lambda v: parse(v["start_time"]), reverse = True)
    meeting_uuid = meetings[0]["uuid"]
    
    query = {"page_size" : "30", "type" : "past"} # page_size only for *all* participants...

    j = requests.get(participants_url.format(meeting_uuid, user_id), headers = token_auth, params = query).json()

    participant_id = None
    for p in j["participants"]:

        if not "id" in p: continue
        if p["id"] != user_id: continue

        participant_id = p["user_id"]

    if not participant_id:
        print("participant {} not found in meeting".format(user_email))
        sys.exit()
    
    j = requests.get(qos_url.format(meeting_uuid, participant_id), headers = token_auth, params = query).json()
    
    with open(output, "w") as out: json.dump(j, out)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = 'Meeting stats.')
    parser.add_argument("-c", "--code",    type = str, default = "")
    parser.add_argument("-m", "--meeting", type = int, required = True)
    parser.add_argument("-t", "--token_cache", type = str, default = "zoom_token_video_analytics.json")
    parser.add_argument("-u", "--user_email", type = str, default = "jsaxon@uchicago.edu") 
    parser.add_argument("-o", "--output", type = str, default = "meeting_metrics.json")
    args  = parser.parse_args()

    get_qos(**vars(args))


