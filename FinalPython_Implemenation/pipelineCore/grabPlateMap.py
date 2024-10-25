#!/usr/bin/env python

import pandas as pd, sys


# NEEDS COMMAND LINE INTERFACE


def main():
    # EXAMPLES
    # infoFileLoc = "/Users/dterciano/Desktop/LokeyLabFiles/TargetMol/hd_pipeline files/PhoenixRunContents_exported_1.csv"
    # dataset = "/Users/dterciano/Desktop/LokeyLabFiles/TargetMol/XMLexamples/cellbycellTSV/bfbe6900-005a-11ee-9416-02420a00012a_cellbycell.tsv"
    if len(sys.argv) > 3:
        print(
            f"Usage: python3 grabPlateMap.py <[uuid]_cellbycell.tsv> <info File>",
            file=sys.stderr,
        )
        sys.exit(1)

    dataset = sys.argv[1].strip()
    uuid = dataset.strip().split("/")[-1].split(".")[0].split("_")[0]

    plateMapCol = "CSC_Plate_ID"  # TODO: CHANGE THIS TO BE THE OFFICIAL HEADER
    infoFile = pd.read_csv(sys.argv[2])

    platemapInfo = infoFile[infoFile["SignalsUUID"] == uuid]
    platemap = platemapInfo[plateMapCol].values[0]
    expDate = platemapInfo['Experiment_Date'].values[0]
    cellLine = platemapInfo['Cell_Line'].values[0]
    timepoint = platemapInfo['Timepoint'].values[0]
    magnification = platemapInfo['Magnification'].values[0]

    # Experiment Date + Plate Map File + Cell Line + Timepoint + Magnification
    
    humReadName = infoFile[infoFile["SignalsUUID"] == uuid]
    humReadName = humReadName["Human_Readable_Name"].values[0]
    
    outName = f"{expDate:d}_{platemap}_{cellLine}_{timepoint:d}_{magnification}_{humReadName}"
    # .join([expDate,platemap,cellLine,timepoint,magnification,humReadName])
    print(platemap, file=sys.stdout)  # print to stdout for bash script to use
    print(outName, file=sys.stdout)
    
    return 0


if __name__ == "__main__":
    main()
