# Kali / Kismet Approach 

* Get the rpi4 64 bit Kali install from Offensive Security.
* Use dd or etcher (lower stress!) to write the medium.
* `sudo apt install sqlite3 kismet gpsd gpsd-clients`
  * Test using `cpgs -s`.
* Copy the `gpsd.conf` file to `/etc/defaults/gpsd`
  * Do `sudo systemctl stop gpsd.socket` and `sudo systemctl disable gpsd.socket`
  * Necessary?
* Use `airmon-ng check kill` to turn off services that interfere with scanning.
* Try `sudo airodump-ng wlan1 -b abg -w piscan -e` to hop on A/B/G and write to `piscan-*`
  * This seems really great, but it `airodump-ng` doesn't right the radiotap to the pcap file.
  * Nevertheless, you could extract the beacon packets like so:
    ```
    tshark -r piscan-01.cap -Y "wlan.fc.type_subtype == 0x8" -T fields -e frame.time -e wlan.bssid -e wlan.ssid -E separator=,`
    ```
  * You could also just use tshark directly, but this is going to stick to a single channel, and 
    people seem to scoff at the idea that `tshark` itself would hop.
    ```
    sudo tshark -i wlan1 -I -Y "wlan.fc.type_subtype == 0x8" -T fields -e frame.time -e wlan.bssid -e wlan.ssid -E separator=,
    ```
  * So we use Kismet.
* In `/etc/kismet/kismet.conf` set the default device to `wlan1` and set the `gpsd` parameters (uncomment gpsd).
* Then do `kismet -s` and check out the status of the new html gui at `localhost:2501`.  (Now go for a walk)
* Finally, we can extract the data from the `Kismet*.kismet` file (actually just sqlite), using the [`kismet.sql`](kismet.sql) file, 
  or by running `kismetdb_to_wiglecsv -i Kismet-*.kismet -o kismet_wigle.csv`.



