# Kali / Kismet Approach 

## HW

### Parts
1. Compute: raspberry pi 4 w/ 4 GB RAM
2. GPS: GlobalSat BU-353-S4 USB dongle
3. Wifi: Alfa AWUS036ACH -- Long-Range / Dual Band
4. USB: AUKEY powered hub
   * The Alfa munches power and interferes with the GPS!
5. Power: Omni 20+
   * This is not a cheap or sustainable solution, but it makes the power problem "trivial"
     for once, which is a blessing...

### Cabling -- 
* pi draws power directly from the omni USB C
* GPS plugs directly to the pi
* Hub uses the Omni "wall plug"
* Wifi uses the Hub -- this isolates it from the GPS, which otherwise just loses its fix continuously!

## OS / Software

* Get the rpi4 64 bit Kali install from Offensive Security.
* Use dd or etcher (lower stress!) to write the medium.
* Update and isntall stuff:
  ```
  sudo rm /etc/apt/sources.list.d/re4son.list # GPG key fucked up
  sudo apt update
  sudo apt install sqlite3 kismet kismet-doc kismet-plugins gpsd gpsd-clients
  ```
* Copy the `gpsd.conf` file to `/etc/default/gpsd`
  * Do `sudo systemctl stop gpsd.socket` and `sudo systemctl disable gpsd.socket`
  * Necessary?
* Start it this time using `sudo gpsd /dev/ttyUSB0`
  * Test using `cpgs -s`.
  * In the future, this should boot at launch if the USB is plugged in.
* Use `airmon-ng check kill` to turn off services that interfere with scanning.
* Try `sudo airodump-ng wlan1 -b abg -w piscan -e` to hop on A/B/G and write to `piscan-*`
  * This seems really great, but it `airodump-ng` doesn't write the radiotap to the pcap file.
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
* Add yourself (`kali`) to the kismet user group.
* Then do `kismet -s` and check out the status of the new html gui at `localhost:2501`.  (Now go for a walk)
* Finally, we can extract the data from the `Kismet*.kismet` file (actually just sqlite), using the [`kismet.sql`](kismet.sql) file, 
  or by running `kismetdb_to_wiglecsv -i Kismet-*.kismet -o kismet_wigle.csv`.



