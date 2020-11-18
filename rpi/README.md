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

#### Wired

For the wired setup, we use a switch to mirror traffic to the pi.  This requires rather a lot of gear, actually.  I have:
* [Netgear CM500 Cable Modem](https://www.amazon.com/gp/product/B06XH46MWW/)
* [Linksys LRT214 Gigabit VPN Router](https://www.amazon.com/gp/product/B07P9SR8WB/) -- 4 LAN + WAN + DMZ
  * The TP-Link TL-R600VPN is cheaper, and probably a better choice; this is just what I had available.
* [Netgear GS105Ev2 Smart Managed Plus Switch](https://www.amazon.com/NETGEAR-Gigabit-Lifetime-Protection-GS105Ev2/dp/B00HGLVZLY/): the only trick here is that its default port is `192.168.0.239`, and you have to move this to the subnet of your router.  To do this, I connected to it alone, and forced my ethernet to that subnet:
  ```
  sudo ipconfig set en7 INFORM 192.168.0.123
  ```
  
  Then you can log in and change the static IP of the switch.  (You'll come back to the same interface, to turn on port mirroring.
* 
* The pi

#### Wireless

#### Software

#### Router

In order to watch consumption, we need to either mirror traffic over a switch, or sniff it over wifi.
Wifi/Kismet is less accurate for the activity of a single device, since we need to see all possible channels.
Kismet could hop for us (in which case we'd miss in time), and tshark could listen to a single channel -- in which case we'd likely miss in frequency.
Of course, you could watch your neighbors with Kismet, but let's not get into that.

\[Instructions coming.\]

### tshark

```
sudo apt install tshark

tshark -i eth0 -a duration:10 -w shark.pcap

capinfos shark.pcap | grep Data
```

Alternatively, we could run tshark in ring mode, and then just pull of the stats...
```
tshark -r shark_00001_20201114024130.pcap -q -z io,stat,10 -z io,phs
tshark -i eth0 -b files:5 -b duration:60 -q -w shark.pcap
```
This guy runs it as a [daemon](https://gist.github.com/sepastian/5d793612e7adf288712287899619f661), which is smart but might kill the microSD card and probably would not be able to keep up in terms of write -- better to keep to memory.


Note -- `iftop` is also really nice, but _requires_ sudo, whereas tshark doesn't _really_.

