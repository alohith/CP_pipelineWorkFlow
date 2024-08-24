#!/usr/bin/env bash

cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline" || exit
source ~/miniconda3/bin/activate histdiff

files=$1
cytoDir="/csc/data/halo384/cyto"

dumpDir="/csc/data/halo384/cyto_output/medianOuts"
controls="/csc/data/halo384/cyto/CytoPlateMaps/SP20319.csv"

while IFS= read -r file; do
    if [ -f "${cytoDir}/${file}.zip" ]; then
        unzip "$cytoDir/$file.zip" -d "$dumpDir"
        echo "unzipped $cytoDir/$file.zip to $dumpDir"

        python ./pipelineCore/medianCellCount.py -i "${dumpDir}/${file}.txt" -o "$dumpDir/${file}_wellMedian.csv" -z -c "$controls" || {
            echo "error"
            exit 1
        }
        rm "${dumpDir}/${file}.txt"
    else
        echo "cannot find ${cytoDir}/${file}.zip"
    fi
done <"$files"
