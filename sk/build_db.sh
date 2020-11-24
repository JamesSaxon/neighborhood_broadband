#!/bin/bash 

# set paswword in ~/.pgpass

sk_psql="psql -d sk -U jsaxon -p 5432 -h localhost -f "


$sk_psql sql/schema

for ym in $(ls 20180[1-3].tar.gz | sed "s/.tar.gz//"); do 

  echo $ym

  cp $ym.tar.gz current_archive.tar.gz
  tar xzvf current_archive.tar.gz

  # postgres variables are messy with
  #  script + \copy 
  mv $ym curr_data/
  $sk_psql sql/copy 

  # rm current_archive.tar.gz
  mv curr_data $ym

done

# $sk_psql sql/finalize

