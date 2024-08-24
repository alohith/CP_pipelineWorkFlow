#!/usr/bin/env bash
cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline" || exit

# act="$(which activate)"
source ~/miniconda3/bin/activate histdiff

if [ $# -lt 3 ]; then
    echo "usage: $0 <cellByCellData> <entryInfoFile> <fileLog path>"
    exit 1
fi

cellByCellData=$1
entryInfo=$2
fileLog=$3

if [ ! -f "$cellByCellData" ]; then
    echo "File: $cellByCellData not found!"
    exit 1
fi

# clean cell by cell data
./checkDataIntegrity.sh "$cellByCellData" || {
    echo "checkDataIntegrity script failed to execute"
    exit 1
}

res=$(python ./pipelineCore/grabPlateMap.py "$1" "$2")

platemap=$(echo "$res" | head -n 1)
humReadName=$(echo "$res" | tail -n 1)

echo "$platemap"
echo "$humReadName"

# TODO: CHANGE OUTPUT DESTINATION
plateMapDirectory="/home/halo384/cyto/CytoPlateMaps"
dest="/csc/data/halo384/cyto_output/hd_outputs"

python ./pipelineCore/histdiff_pipelineV2.py -i $cellByCellData -o "${dest}/${humReadName}_HD" -c "$plateMapDirectory/$platemap.csv" -cs || {
    echo "hist diff failed to execute"
    exit 1
}

moveDir="/csc/data/halo384/cyto_process/merged/hd_cellbycell"

cellFileName=$(basename -- "$cellByCellData")
echo "$cellFileName" >>"$fileLog"

gzip -c "$cellByCellData" >"$moveDir/$cellFileName.gz"
rm "$cellByCellData"

conda deactivate
