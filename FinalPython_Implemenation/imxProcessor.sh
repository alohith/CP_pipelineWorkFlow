#!/usr/bin/env bash

files="/home/halo384/cyto_process/temp/hd_entries/.imx_temp"
cytoDir="/csc/data/halo384/cyto"

dumpDir="/csc/data/halo384/cyto/cytoDumps"

while IFS= read -r file; do
    if [ -f "$cytoDir/$file.zip" ]; then
        unzip "$cytoDir/$file.zip" -d "$dumpDir"
        echo "unzipped $cytoDir/$file.zip to $dumpDir"
    else
        echo "can't find $cytoDir/$file.zip"
    fi
done <"$files"
