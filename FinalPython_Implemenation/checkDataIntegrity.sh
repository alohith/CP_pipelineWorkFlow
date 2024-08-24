#!/bin/bash

file=$1

if [ ! -f "$file" ]; then
    echo "File not found!"
    echo "Usage: $0 <cell by cell data>"
    exit 1
fi

tempFile="/home/halo384/cyto_process/temp/tempData_$$.tmp"
touch "$tempFile"

trap "rm -f $tempFile" EXIT

python3 ./pipelineCore/verifyIntegrity.py "$file" "$tempFile"

mv "$tempFile" "$file"
