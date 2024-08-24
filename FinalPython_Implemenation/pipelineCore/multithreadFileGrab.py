#!/usr/bin/env python
"""
This script multithreads all UUID requests from
a list of UUIDs from a given text file.

by Derfel Terciano
version 1.0
"""
import multiprocessing as mp, os, sys
import cellBycellCall as cbc
from time import sleep

import pandas as pd


def fetchUUIDs(filePath):
    """
    Input a text file containing all the UUIDs
    """
    uuids = []
    with open(filePath, "r") as file:
        for i, line in enumerate(file):
            currLine = line.strip()

            if i == 0:
                header = currLine.replace(">>", "").strip()
                print(f"DATASETS: {header}", file=sys.stderr)
            else:
                uuids.append(currLine)
    return uuids


class CommandLine:
    def __init__(self, inOpts=None):
        import argparse

        self.parser = argparse.ArgumentParser(
            description="Downloads CellbyCell data from SImA. (Multithread process using a text file of UUIDs)",
            prog="multithreadFileGrab.py",
            add_help=True,
            prefix_chars="-",
        )
        self.parser.add_argument(
            "-i",
            "--uuid",
            action="store",
            required=True,
            nargs="?",
            type=str,
            help="File input for UUID Text file",
        )
        self.parser.add_argument(
            "-u",
            "--user",
            action="store",
            required=True,
            nargs="?",
            type=str,
            help="Signals Server Username",
        )
        self.parser.add_argument(
            "-p",
            "--password",
            action="store",
            required=True,
            nargs="?",
            type=str,
            help="Signals Server password",
        )
        self.parser.add_argument(
            "-c",
            "--chunksize",
            action="store",
            required=False,
            nargs="?",
            type=int,
            default=10240000,
            help="chunksize for writing tsv file (def: 10240000)",
        ),
        self.parser.add_argument(
            "--attempts",
            action="store",
            required=False,
            default=3,
            type=int,
            help="Number of connection re-attemps (def: 3)",
        )

        self.parser.add_argument(
            "-o",
            "--outPath",
            action="store",
            nargs="?",
            type=str,
            required=True,
            help="Specifies the file path where tsv file will be place (not file name)",
        )

        self.parser.add_argument(
            "-t",
            "--threads",
            action="store",
            required=False,
            default=1,
            type=int,
            help="Decides how many threads will be used for proces. -1 allows for the use of ALL threads. (default: 1)",
        )

        self.parser.add_argument(
            "--csv",
            action="store_true",
            default=False,
            required=False,
            help="If this flag is enabled, then a csv will be parsed instead",
        )

        if inOpts is None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(inOpts)


def uuidWorker(uuidList, **kwargs):
    if not isinstance(uuidList, list):
        uuidList = [uuidList]

    user = kwargs["user"]
    pwd = kwargs["password"]
    chunkSize = kwargs["chunkSize"]
    attempts = kwargs["attempts"]
    outPath = kwargs["outPath"]

    for uuid in uuidList:
        cbc.main(
            inOpts=[
                f"--user={user}",
                f"--password={pwd}",
                f"--chunksize={chunkSize}",
                f"--attempts={attempts}",
                f"--outPath={outPath}",
                f"--uuid={uuid}",
                # "-d",  # this disables actualy downloading
            ]
        )
        sleep(1)


def main(inOpts=None):
    cl = CommandLine(inOpts=inOpts)

    user = cl.args.user
    pwd = cl.args.password
    uuid = cl.args.uuid
    chunkSize = cl.args.chunksize
    attempts = cl.args.attempts
    outPath = cl.args.outPath

    threads = cl.args.threads
    if threads == -1:
        threads = mp.cpu_count() - 2  # you do not want to accidentally kill the system

    if not cl.args.csv:
        uuids = fetchUUIDs(filePath=uuid)
    else:
        uuidCsv = pd.read_csv(uuid)
        uuids = uuidCsv["SignalsUUID"].to_list()

    fileChunks = None
    if len(uuids) > threads:
        chunks = len(uuids) // threads
        fileChunks = [uuids[i : i + chunks] for i in range(0, len(uuids), chunks)]

    groups = uuids if fileChunks is None else fileChunks

    print(f"Threads to use: {threads}", file=sys.stderr)
    print(f"Groups size: {len(groups)}", file=sys.stderr)

    threadProcess = []
    for group in groups:
        thread = mp.Process(
            target=uuidWorker,
            kwargs={
                "uuidList": group,
                "user": user,
                "password": pwd,
                "chunkSize": chunkSize,
                "attempts": attempts,
                "outPath": outPath,
            },
        )
        thread.start()
        threadProcess.append(thread)

    for thread in threadProcess:
        thread.join()

    return 0


if __name__ == "__main__":
    main()
