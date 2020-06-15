SELECT 
  json_extract(device, '$."dot11.device"."dot11.device.last_beaconed_ssid_record"."dot11.advertisedssid.ssid"') ssid, 
  devmac, 
  strongest_signal signal, 
  (first_time + last_time) / 2 time, 
  avg_lat lat, avg_lon lon 
FROM
  devices 
WHERE 
  avg_lat > 0 AND 
  type = 'Wi-Fi AP' 
ORDER BY 
  signal DESC
;
