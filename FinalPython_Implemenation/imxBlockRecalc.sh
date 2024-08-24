#!/usr/bin/env bash
cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline" || exit
source ~/miniconda3/bin/activate histdiff

imxFile=$1
platemap=$2
outPath=$3
file=$imxFile

cytoDir="/csc/data/halo384/cyto"
dumpDir="/csc/data/halo384/cyto/cytoDumpsRecalc" # change this

blocks=$(python ./pipelineCore/genBlocks.py -i A C E G I K M O)

cleanup() {
    echo "removing ${dumpDir}/${file}.txt"
    rm "${dumpDir}/${file}.txt"
}

trap 'cleanup' EXIT

if [ -f "$cytoDir/$file.zip" ]; then
    unzip "$cytoDir/$file.zip" -d "$dumpDir"
    echo "unzipped $cytoDir/$file.zip to $dumpDir"
else
    echo "can't find $cytoDir/$file.zip"
    exit 1
fi

python ./pipelineCore/histdiff_pipelineV2.py -i "$dumpDir/$file.txt" -o "${outPath}_HD" -c "$platemap" -cs -b $blocks
