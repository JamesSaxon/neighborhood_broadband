## Home Network Statistics on a pi or nano

### Cooking a pi
* Using: raspberry pi 4 with 8 GB of RAM, and a 32 GB microSD card.
* For inexplicable reasons, I decided to try the Ubuntu 20.04 64-bit Server.  It's a lot easier to just use the pi OS, for which the user and networking defaults are better.  Nevertheless, you download this from from [Canonical](https://ubuntu.com/download/raspberry-pi).  Kali Linux would seem like an appealing choice -- Kismet, dsniff, arpspoof etc. are all included by default -- but Kali is secure at the price of robustness.  In my experience most unplanned shutdowns corrupt Kali so badly that it's easier to just rewrite the boot medium.  Since I will inevitably unplug something, it's a bad choice.
* Make the bootable medium -- check the `of` to write to with `df -h`, then `sudo dd if=your.iso of=/dev/[MY_DEVICE] bs=1M status=progress` 
  * Low-stress alternative: use raspberry pi imager.
* The Ubuntu set-ups is messier and so -- as I say -- probably a worse choice.  First, it only sets up the ubuntu:ubuntu user and calls the computer ubuntu.  You can change this on the bootable medium before inserting it into the pi.  But it also needs to run a _ton_ of updates, has crappy default packages, and you _must_ install avahi-daemon to be able to find it through anything but nmap and then the numeric IP!  So something like this, just to function normally:

```
sudo apt update
# wait and intermittently ps aux | grep apt, until it's done the auto updates!

sudo apt full-upgrade

sudo apt install avahi-daemon # so we can log in to words instead of (dynamic) numbers.
sudo hostnamectl set-hostname netrics # change the hostname
sudo service avahi-daemon restart

sudo groupadd jsaxon
sudo useradd jsaxon -g jsaxon -m -G sudo -s /bin/bash
```

Then log back in as the new user, get rid of the other account, and set up ssh.
```
sudo userdel ubuntu 
sudo rm -rf /home/ubuntu/
ssh-keygen 
sudo vi /etc/ssh/sshd_config # PasswordAuthentication -> no
vi ~/.ssh/authorized_keys # get rid of password log-ins
```
It was still not always getting found for me, so I fixed the IP address -- 
```
>> sudo vi /etc/netplan/50-cloud-init.yaml
network:
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.4/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
  version: 2
>> sudo netplan apply
```
and froze this in `~/.ssh/config`
```
Host netrics
  HostName 192.168.1.4
```

### Configuring the software

Install these packages / dependencies:
```
sudo apt install speedtest-cli net-tools iperf3 chromium-chromedriver nmap traceroute dsniff tshark kismet aircrack-ng airodump-ng wirless-tools
pip3 install pandas speedtest-cli influxdb_client selenium pynetgear_enhanced 
```

To simplify things with `tshark`, add yourself to the wireshark user group `sudo adduser jsaxon wireshark`.

And for now, just clone this gist:
```
git clone https://gist.github.com/JamesSaxon/a7ddb11d5fe78ab0f91c22500af13778 netrics
```

It contains a python script of measurements, following along with the google doc.  Most of these are "fairly straightforward," although they do require a bit of care.  For example, you must run nmap before you run `arp` or the results of the cache will be meaningless.  You should also check `/etc/resolv.conf`.  Different OS's do this differently: pi OS points to `192.168.1.1` while Ubuntu Server symlinks to a system service, resulting in 0 DNS latency.  We _could_ say that the 0 ms response times are "real," but lets instead point them to the router, so it actually gets resolved off-device -- that is, set it to: 
```
>> sudo vi /etc/resolv.conf
nameserver 192.168.1.1
```

Finally, `cat` out `z_crontab` to check that each line works.  There are some absolute paths in there that I need to fix -- search for `saxon`.  I also store my passwords in `~/.netc`, so you'll have to add that as well.

I should make the `install` tag configurable to each device.


### Measuring consumption.

Most of the measurements are just active measurements from the pi, though the `arp` count watches locally.  Measuring consumption or looking at application performance requires us to intercept traffic in one way or another.  I've tried four strategies for this: (1) wired, (2) wireless, (3) software, and (4) router.  Each of these has advantages and disadvantages.  They all work fairly well

#### 1. Wired

For the wired setup, we use a switch to mirror traffic to the pi.  This requires rather a lot of gear.  I have, sequences
* [Netgear CM500 Cable Modem](https://www.amazon.com/gp/product/B06XH46MWW/)
* [Linksys LRT214 Gigabit VPN Router](https://www.amazon.com/gp/product/B07P9SR8WB/) -- 4 LAN + WAN + DMZ
  * The TP-Link TL-R600VPN is cheaper, and probably a better choice; this is just what I had available.
* [Netgear GS105Ev2 Smart Managed Plus Switch](https://www.amazon.com/NETGEAR-Gigabit-Lifetime-Protection-GS105Ev2/dp/B00HGLVZLY/): the only trick here is that its default port is `192.168.0.239`, and you have to move this to the subnet of your router.  To do this, I connected to it alone, and forced my ethernet to that subnet:
  ```
  sudo ipconfig set en7 INFORM 192.168.0.123
  ```
  
  Then you can log in and change the static IP of the switch.  (You'll come back to the same interface, to turn on port mirroring.
* [NETGEAR Nighthawk Smart WiFi Router (R6900P)](https://www.amazon.com/gp/product/B07C65K9H9/) used in this case in "access point mode."  This is a great router -- the signal quality is excellent and it is easy to configure -- but it was really a pain to find this and get it working.  The setup wizard for the AP mode made the whole setup virtually unusuable several times.  So eventually I set it up as its own router (on `10.0.0.1`) and then moved it afterwards to the AP mode.  This is at "Advanced > Advanced Settings > Router / AP / Bridge Mode > AP Mode" and I did "Enable fixed IP settings" because it was driving me crazy to nmap to find my router.  The ethernet cable from the switch IS going into the "Internet" port (not one of the LAN ports).

and of course also
* The pi, also attached to the switch.  The ports for both the router and wifi AP are mirrored to the pi.

This works great, though the internal limit of this system will be 1/2 Gbps.  But -- it's not in the path, and we know the switch can keep up.  

Then, the command is something like

```
tshark -f "not broadcast and not multicast and not (ip src 192.168.1.4 or ip dst 192.168.1.4 or ip src 192.168.1.1 or ip dst 192.168.1.1)" -i eth0 -a duration:60 -Q -z io,stat,100 -z conv,ip 
```
I don't want to write the capture file, because the microSD card probably can't handle it (that was my most-common failure when war-driving).  So we keep it to memory.  The `io,stat,100` is just because `io,stat` requires an interval, so I make it longer than the duration (60 seconds).  I drop everything as a capture filter instead of as a display filter, which could do the same thing.

#### 2. Wireless

Using wireless, we are also "out of the path."  This requires two wireless antennas, to capture the 2.4 and 5 GHz bands, but we still risk missing packets if the AP is set to auto-select packets.  On the plus side, this could give us a direct measurement of spectrum congestion, or the activities of other people in the neighborhood, etc.  I used:
* [Alfa AWUS036ACH](https://www.amazon.com/gp/product/B00VEEBOPG/) for 5 GHz and 
* [AWUS036NEH](https://www.amazon.com/gp/product/B0035OCVO6/) for 2.4 GHz
The former required me to install the driver from this [aircrack-ng repo](https://github.com/aircrack-ng/rtl8812au).
```
sudo apt-get install dkms
cd rtl8812au
sudo make dkms_install
```
The [driver for the 2.4 GHz antenna](https://github.com/art567/mt7601usta0) should be included in the kernel.
Then you can set them to monitor and set the channels:
```
sudo ip link set wlan1 down
sudo ip link set wlan2 down
sudo iw dev wlan1 set type monitor
sudo iw dev wlan2 set type monitor
sudo iwconfig wlan1 channel 11
sudo iwconfig wlan2 channel 157
sudo ip link set wlan1 up
sudo ip link set wlan2 up
```

Note that some of the programs will over-ride the channel.  I ultimately decided against Kismet, because I did not want to record the data, but to test, I set the relevant lines in my `/etc/kismet/kismet.conf` to
```
ncsource=wlan1:name=a2,hop=false,channel=11
ncsource=wlan2:name=a5,hop=false,channel=157
```
(You may also want to do `airmon-ng check kill`, to get things running smoothly.)

Anyway, then you can do
```
tshark -f "not broadcast and not multicast and (wlan src 10:0c:6b:62:59:e9 || wlan src 10:0c:6b:62:59:ea || wlan dst 10:0c:6b:62:59:e9 || wlan dst 10:0c:6b:62:59:ea)" -i wlan1 -i wlan2 -a duration:10
```
Just for kicks, note that you could do similar things with display filters
```
tshark -i wlan1 -f "not broadcast and not multicast" -i wlan2 -f "not broadcast and not multicast" -a duration:100 -Q -z conv,wlan,'wlan.fc.type == 2 && wlan.sa != th:em:ac:ad:dr:pi && wlan.da != th:em:ac:ad:dr:pi && other requirements ...'
```

or something equivalent with `airomon-ng` or `kismet`.  Then you can do 


#### 3. Software

ARP spoofing is possibly the easiest and cheapest method, though Nick has warned about performance.  In my experience, my video chats were all fine when running through the pi.  In this case, the wireless router runs as a router, and we drop the Linksys router and the switch.  Then assuming you've installed dsniff, it's
```
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
sudo arpspoof -i eth0 -t 192.168.1.1 192.168.1.9 >/dev/null 2>&1 > router_to_mac &
sudo arpspoof -i eth0 -t 192.168.1.9 192.168.1.1 >/dev/null 2>&1 > mac_to_router &
```
Note that Danny Huang wrote an [ARP spoofing package](https://github.com/nyu-mlab/iot-inspector-client/blob/master/src/arp_spoof.py) in python, for IoT inspector.

#### 4. Router

The Netgear wireless router -- if it is _not_ set up as an AP -- also records consumption.  The [pynetgear_enhanced](https://github.com/roblandry/pynetgear_enhanced) exposes the API really nicely, and so from _within the LAN_ one can query consumption and number of devices.  The router stores consumption per day, week, and month, but it is "up to date" so trivial to keep track down to the minute.

The router even has consumption by device (if QoS is on), though this is not in the API (should verify that it's the API and not just the package that is missing it).


#### Other packages

This guy runs `tshark` as a [daemon](https://gist.github.com/sepastian/5d793612e7adf288712287899619f661), which is smart but might kill the microSD card and probably would not be able to keep up in terms of write -- better to keep to memory.  `iftop` is also really nice, but _requires_ sudo, whereas tshark doesn't _really_.

