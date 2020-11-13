## Home Network Statistics on a pi or nano

### Cooking a pi
* Using: raspberry pi 4 with 8 GB of RAM, and a 32 GB microSD card.
* For inexplicable reasons, I decided to try the Ubuntu 20.04 64-bit Server.  It's a lot easier to just use the pi OS, for which the user and networking defaults are better.  Nevertheless, you download this from from [Canonical](https://ubuntu.com/download/raspberry-pi).
* Make the bootable medium -- check `of` with `df -h`, then `sudo dd if=your.iso of=/dev/mmcblk0p1 bs=1M status=progress` 
  * Low-stress alternative: use raspberry pi imager.
* The Ubuntu set ups is messier and so -- as I say -- probably a worse choice.  First, it only sets up ubuntu:ubuntu and calls the computer ubuntu.  You can change this on the bootable medium before puttingit in the pi.  But it also needs to run a _ton_ of updates, has crappy default packages, and you _must_ install avahi-daemon to be able to find it through anything but nmap and then the numeric IP!  So something like this, just to function normally:

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

### Configuring the software

```
pip3 install pandas speedtest-cli influxdb_client selenium 
sudo apt install speedtest-cli net-tools iperf3 chromium-chromedriver nmap traceroute
```

And for now, just clone this gist:
```
git clone https://gist.github.com/JamesSaxon/a7ddb11d5fe78ab0f91c22500af13778 netrics
```

`cat` out `z_crontab` to check that each line works.  There are some hard links in there that I need to fix -- search for `jsaxon`.

We should also make the `install` tag configurable to each device.


### Configure the switch (optional)

In order to watch consumption, we need to either mirror traffic over a switch, or sniff it over wifi.
Wifi/Kismet is less accurate for the activity of a single device, since we need to see all possible channels.
Kismet could hop for us (in which case we'd miss in time), and tshark could listen to a single channel -- in which case we'd likely miss in frequency.
Of course, you could watch your neighbors with Kismet, but let's not get into that.


sudo rfkill block wifi
