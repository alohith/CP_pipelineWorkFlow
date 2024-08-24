#!/usr/bin/env bash

var=$(python grabPlateMap.py "/Users/dterciano/Desktop/LokeyLabFiles/TargetMol/XMLexamples/cellbycellTSV/bfbe6900-005a-11ee-9416-02420a00012a_cellbycell.tsv" "/Users/dterciano/Desktop/LokeyLabFiles/TargetMol/hd_pipeline files/PhoenixRunContents_exported_1.csv")

platemap=$(echo "$var" | head -n 1)
humReadName=$(echo "$var" | tail -n 1)

echo "$platemap"
echo "$humReadName"
