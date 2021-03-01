#!/bin/bash 

SPEEDS="20.0 10.0 5.0 3.0 2.0 1.5 1.4 1.3 1.2 1.1 1.0 0.9 0.8 0.7 0.6 0.5 0.4 0.3 0.2"

SLEEP=300

BURST=50kbit
MAX_DELAY=20ms

# enxcc483a9d3920 wlp59s0
IFACE=$1
# IFACE=enxcc483a9d3920
# IFACE=wlp59s0
VIRT=ifb0


reset_interfaces() {

  echo Resetting interfaces: $IFACE $VIRT

  sudo tc qdisc del dev $IFACE ingress
  sudo tc qdisc del dev $IFACE root
  sudo tc qdisc del dev $VIRT root
  sudo ip link set dev $VIRT down

}


create_interfaces() {

  echo Creating ingress interface for $IFACE

  # Create virtual interface
  sudo modprobe ifb numifbs=1
  sudo ip link set dev $VIRT up
  
  # Redirect all
  sudo tc qdisc  add dev $IFACE handle ffff: ingress
  sudo tc filter add dev $IFACE parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev $VIRT
  
  sudo tc qdisc  add dev $VIRT  root tbf rate 1000mbit burst 50kbit latency $MAX_DELAY
  sudo tc qdisc  add dev $IFACE root tbf rate 1000mbit burst 50kbit latency $MAX_DELAY

}



replace_speed() {

  DL_SPEED=$1
  UL_SPEED=$2
  TS=$(/bin/date +%s)

  echo $DL_SPEED,$UL_SPEED,$TS | tee -a speed_cycle.csv
  tc qdisc replace dev $VIRT  root tbf rate ${DL_SPEED}mbit burst 50kbit latency $MAX_DELAY
  tc qdisc replace dev $IFACE root tbf rate ${UL_SPEED}mbit burst 50kbit latency $MAX_DELAY

  tcpdump -i $IFACE -w pcap/${TS}

}


# If there are no arguments, we will reset.
# This obviates the need for replace etc.
# So everything is clean if we just want to change.
if [[ -n `ifconfig -s | grep ifb0` ]]; then reset_interfaces; fi

# The re-create them.
create_interfaces

echo "dl,ul,ts" > speed_cycle.csv
for s in ${SPEEDS}; do replace_speed ${s} 100; sleep $SLEEP; done
for s in ${SPEEDS}; do replace_speed 100 ${s}; sleep $SLEEP; done


