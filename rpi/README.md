## Home Network Statistics on a pi or nano

### Cooking a pi
* Using: raspberry pi 4 with 8 GB of RAM, and a 32 GB microSD card.
* Download Ubuntu 20.04 for pi from [Canonical](https://ubuntu.com/download/raspberry-pi).
* Make the bootable medium -- check `of` with `df -h`, then `sudo dd if=your.iso of=/dev/mmcblk0p1 bs=1M status=progress` 
  * Low-stress alternative: use raspberry pi imager.
  
### Configuring the software

programs: speedtest-cli, dig, nslookup, ifconfig, iperf3, nmap, arp, 
python packages: speedtest, influx, selenium 

sudo apt-get update
sudo apt install dnsutils dnsperf install iperf3 chromium-chromedriver tshark

### Configure the switch (optional)

In order to watch consumption, we need to either mirror traffic over a switch, or sniff it over wifi.
Wifi/Kismet is less accurate for the activity of a single device, since we need to see all possible channels.
Kismet could hop for us (in which case we'd miss in time), and tshark could listen to a single channel -- in which case we'd likely miss in frequency.
