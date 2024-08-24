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
    platemapInfo = platemapInfo[plateMapCol].values[0]

    humReadName = infoFile[infoFile["SignalsUUID"] == uuid]
    humReadName = humReadName["Human_Readable_Name"].values[0]
    print(platemapInfo, file=sys.stdout)  # print to stdout for bash script to use
    print(humReadName, file=sys.stdout)

    return 0


if __name__ == "__main__":
    main()
