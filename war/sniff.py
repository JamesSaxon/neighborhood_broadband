#!/usr/bin/env python 

import pyshark, datetime, sys

cap = pyshark.FileCapture('/tmp/airportSniff8NfELH.cap')

# cap = pyshark.LiveCapture(interface = 'en0')
# cap.sniff(timeout = 5)

bssids = set()

for pi, packet in enumerate(cap):

  if "WLAN" not in packet: continue
  if "_WS.MALFORMED" in packet: continue

  w  = packet['WLAN']

  if int(w.fc_type_subtype) != 8: continue # Beacon only
  if not int(w.fcs_good): continue # bad packet

  r  = packet['RADIOTAP']

  if "WLAN_MGT" not in packet:
    print(pi, w.fcs_good)
    sys.exit() 

  wm = packet['WLAN_MGT']

  dbm_signal = None
  try: dbm_signal = r.dbm_antsignal
  except: pass


  # try: 
  #   print(packet.sniff_timestamp, wm.ssid, w.bssid, r.dbm_antnoise, dbm_signal, r.channel_freq, r.channel_type)
  # except: 
  #   print(pi)
  #   sys.exit()

  print(packet.sniff_timestamp, wm.ssid, w.bssid, r.dbm_antnoise, dbm_signal, r.channel_freq, r.channel_type)

  if w.bssid not in bssids: bssids.add(w.bssid)

  #  if w.bssid == 'c0:a0:0d:cb:8c:5a':
  #    print(packet.sniff_timestamp, wm.ssid, w.bssid, r.dbm_antnoise, dbm_signal, r.channel_freq, r.channel_type)

print("Observed {} total.".format(len(bssids)))
print(bssids)

