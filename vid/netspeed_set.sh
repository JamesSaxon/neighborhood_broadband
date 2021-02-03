#!/bin/bash 

# wlp59s0 enxcc483a9d3920
IFACE=$1
VIRT=ifb0

DL_SPEED=$2
UL_SPEED=$3

if [ "$#" -eq 2 ]; then 
  UL_SPEED=$DL_SPEED
fi

BURST=50kbit

# Careful -- of the meaning of the 
#  "latency" in the tbf qdisc.
MAX_DELAY=20ms


function reset_interfaces() {

  echo Resetting interfaces: $IFACE $VIRT

  sudo tc qdisc del dev $IFACE ingress
  sudo tc qdisc del dev $IFACE root
  sudo tc qdisc del dev $VIRT root
  sudo ip link set dev $VIRT down

}


function set_speed() {

  echo Set speed to: ${DL_SPEED}/${UL_SPEED}

  # Create virtual interface
  sudo modprobe ifb numifbs=1
  sudo ip link set dev $VIRT up
  
  # Redirect all
  sudo tc qdisc  add dev $IFACE handle ffff: ingress
  sudo tc filter add dev $IFACE parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev $VIRT
  
  sudo tc qdisc  add dev $VIRT  root tbf rate $DL_SPEED burst 50kbit latency $MAX_DELAY
  sudo tc qdisc  add dev $IFACE root tbf rate $UL_SPEED burst 50kbit latency $MAX_DELAY

}


# If there are no arguments, we will reset.
# This obviates the need for replace etc.
# So everything is clean if we just want to change.
if [[ -n `ifconfig -s | grep ifb0` ]]; then
  reset_interfaces
fi

if [ "$#" -gt 1 ]; then 
  set_speed
fi


