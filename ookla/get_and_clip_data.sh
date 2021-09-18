#!/bin/bash

ookla_s3_dest="s3://ookla-open-data/shapefiles/performance"

cities="new_york los_angeles chicago houston phoenix philadelphia san_antonio san_diego dallas san_jose austin jacksonville san_francisco columbus fort_worth indianapolis charlotte seattle denver washington"

mkdir -p zip clipped temp

##  Y=2020
##  for Q in 1 2 3; do
##    for T in mobile fixed; do
##      let M=(Q-1)*3+1
##      aws s3 cp $ookla_s3_dest/type=$T/year=2020/quarter=$Q/$Y-0$M-01_performance_${T}_tiles.zip zip/${Y}_q${Q}_${T}.zip
##    done
##  done
##  cd ../

for x in $(ls zip/); do 

  z=$(echo $x | sed "s/.zip//g")
  echo $f $z

  cd temp
  unzip ../zip/${z}.zip
  for f in gps_*_tiles.*; do 
    o=$(echo $f | sed "s/fixed_//" | sed "s/mobile_//")
    echo $f $o
    mv $f $o
  done
  cd ../

  for city in $cities; do 
    echo $z $city
    /usr/bin/ogr2ogr -clipsrc places/${city}_10km.geojson -f GeoJSON clipped/${city}_${z}.geojson temp/gps_tiles.shp
  done 

done
rm -rf temp


