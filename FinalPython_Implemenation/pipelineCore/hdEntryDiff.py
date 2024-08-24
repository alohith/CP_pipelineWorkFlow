#!/usr/bin/env python

import json
import pandas as pd, sys, os
from datetime import datetime


def diff(file1: pd.DataFrame, file2: pd.DataFrame) -> pd.DataFrame:
    res = file1[~file1.apply(tuple, 1).isin(file2.apply(tuple, 1))]
    return res


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python hdEntryDiff.py <old File> <new File to compare> <output File/path>"
        )
        sys.exit(1)

    oldCSV = sys.argv[1]
    jsonPath = sys.argv[2]
    outpath = sys.argv[3]

    columnsIgnore = ["created_at", "updated_at"]

    jsonDf = pd.read_json(jsonPath)  # convert json file to df

    jsonCSVfile = f"{os.path.splitext(jsonPath)[0]}.csv"
    jsonDf.to_csv(
        jsonCSVfile, index=False
    )  # I have to output jsondf to a csv due to pandas issues

    jsonDf = pd.read_csv(jsonCSVfile)
    oldEntry = pd.read_csv(oldCSV)

    jsonDf.set_index("id", inplace=True)
    oldEntry.set_index("id", inplace=True)

    jsonDf = jsonDf[sorted(jsonDf.columns)]
    oldEntry = oldEntry[sorted(oldEntry.columns)]

    jsonDf.drop(columnsIgnore, axis=1, inplace=True, errors="ignore")
    oldEntry.drop(columnsIgnore, axis=1, inplace=True, errors="ignore")

    difference = diff(jsonDf, oldEntry)

    today = datetime.today()
    formatDate = today.strftime("%m%d%Y")

    if difference.empty:
        print("", file=sys.stdout)
    else:
        fileOutput = f"PhoenixRunContents_exported_1_{formatDate}.csv"
        path = os.path.join(outpath, fileOutput)
        print(f"{path}", file=sys.stdout)

        difference.to_csv(path, index=True)

    os.remove(jsonCSVfile)
    return


if __name__ == "__main__":
    main()
