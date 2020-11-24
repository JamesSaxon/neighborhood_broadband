#!/bin/bash 

declare -A months=( ["01"]="jan" ["02"]="feb" ["03"]="mar" ["04"]="apr" ["05"]="may" ["06"]="jun" ["07"]="jul" ["08"]="aug" ["09"]="sept" ["10"]="oct" ["11"]="nov" ["12"]="dec")

url=http://data.fcc.gov/download/measuring-broadband-america

#  for y in 2017 2018 2019 2020; do
for y in 2020; do
  for m in $(seq -w 1 12); do 
 
    mdec=$(echo $m | sed "s/0//g")

    if [[ $y -lt 2020 || $mdec -lt 10 ]]; then 
      wget -nv $url/${y}/data-raw-${y}-${months[$m]}.tar.gz -O ${y}${m}.tar.gz
    fi

  done
done

