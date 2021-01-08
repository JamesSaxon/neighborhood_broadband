#!/bin/bash 

SPEEDS="10 5 2 1.75 1.50 1.25 1.1 1.0 0.9 0.8 0.7 0.6 0.5 0.25"
SPEEDS="2.0 1.5 1.2 1.0 0.8 0.6"
SPEEDS="1.5 1.2 1.0 0.8 0.6"

SLEEP=300

BURST=50kbit
MAX_DELAY=20ms

# IFACE=enx00e04c01598c
IFACE=wlp59s0
VIRT=ifb0

replace_speed() {

  DL_SPEED=$1
  UL_SPEED=$2
  TS=$(/bin/date +%s)

  echo $DL_SPEED,$UL_SPEED,$TS | tee -a speed_cycle.csv
  tc qdisc replace dev $VIRT  root tbf rate ${DL_SPEED}mbit burst 50kbit latency $MAX_DELAY
  tc qdisc replace dev $IFACE root tbf rate ${UL_SPEED}mbit burst 50kbit latency $MAX_DELAY

  sleep $SLEEP

}


echo "dl,ul,ts" > speed_cycle.csv
for s in ${SPEEDS}; do replace_speed ${s} 100; done
for s in ${SPEEDS}; do replace_speed 100 ${s}; done


