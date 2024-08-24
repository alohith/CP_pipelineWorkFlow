#!/usr/bin/env python
"""
A simple script thet organizes nocodb entried for IMX and signals

(signals and IMX are 2 different pipeline processes)

by Derfel Terciano
version 1.0
"""
import pandas as pd
import sys, os
import multiprocessing as mp


def signalsWorker(entries, outDir):
    fileName = ".signals_temp"
    with open(os.path.join(outDir, fileName), "w") as f:
        f.write(f">> Signals Input\n")
        for entry in entries:
            print(entry, file=f)
    return


def imxWorker(entries, outDir):
    fileName = ".imx_temp"
    with open(os.path.join(outDir, fileName), "w") as f:
        for entry in entries:
            print(entry, file=f)

    return


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: python organizeEntries.py <inputCSV> <output directory>",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = pd.read_csv(sys.argv[1])
    outputDir = sys.argv[2]

    entries = entries["SignalsUUID"].dropna().to_list()

    signals = []
    imx = []
    for id in entries:
        if "MX" in str(id):
            imx.append(id)
        else:
            signals.append(id)

    threadProcess = []

    if len(signals) > 0:
        thread = mp.Process(
            target=signalsWorker, kwargs={"entries": signals, "outDir": outputDir}
        )
        thread.start()
        threadProcess.append(thread)

    if len(imx) > 0:
        thread = mp.Process(
            target=imxWorker, kwargs={"entries": imx, "outDir": outputDir}
        )
        thread.start()
        threadProcess.append(thread)

    for thread in threadProcess:
        thread.join()

    return


if __name__ == "__main__":
    main()
