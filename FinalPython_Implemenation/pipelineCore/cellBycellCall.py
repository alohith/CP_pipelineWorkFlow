#!/usr/bin/env python
"""
This module handles the data retrieval of a singular singlas UUID
NOTE: On-Campus connection is needed

by Derfel Terciano
version 1.0
"""

import requests, json, os, sys
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin
from time import sleep

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
BASE_URL = "https://csc-signals.pbsci.ucsc.edu"


def getResponse(url, user, password, verify=False):
    with requests.get(
        url=url,
        verify=verify,
        auth=(user, password),
    ) as response:
        return response


def getDLLink(uuid, user, password, verify=False, attempts=3):
    for _ in range(attempts):
        try:
            datasetURL = urljoin(base=BASE_URL, url=f"api/1.1/data/dataset/{uuid}")
            datasetResponse = getResponse(
                url=datasetURL,
                verify=verify,
                user=user,
                password=password,
            )

            if datasetResponse.status_code == 200:
                jsonData = datasetResponse.json()
                results = jsonData["results"][0]
                cellData = results["celldata"]
                if cellData:
                    dlurl = results["download_cell_data"][0]["download"]
                    return dlurl
                return -1
            else:
                print(
                    f"{uuid} :: Error code: {datasetResponse.status_code}",
                    file=sys.stderr,
                )
                print("Retrying Query", file=sys.stderr)
                sleep(1)
                continue

        except Exception as e:
            print(f"<getDLLink> {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Retrying connection", file=sys.stderr)
            sleep(1)


def getFiles(
    dlLink: str, outName: str, user, password, chunksize=8192, verify=False, attempts=3
):
    for _ in range(attempts):
        try:
            fullDLLink = urljoin(base=BASE_URL, url=dlLink)
            dlResponse = getResponse(
                url=fullDLLink, verify=verify, user=user, password=password
            )

            if dlResponse.status_code == 200:
                print(
                    f"Downloading {outName} with chunk size: {chunksize}",
                    file=sys.stderr,
                )
                with open(outName, "wb") as f:
                    for chunk in dlResponse.iter_content(chunk_size=chunksize):
                        f.write(chunk)
                return 0
            else:
                print(
                    f"{dlLink} :: Error code: {dlResponse.status_code}",
                    file=sys.stderr,
                )
                print(f"Retrying connection for {dlLink}", file=sys.stderr)
                sleep(1)
                continue

            return dlResponse.status_code
        except Exception as e:
            print(f"<getFiles> {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Retrying connection")
            sleep(1)


class CommandLine:
    def __init__(self, inOpts=None):
        import argparse

        self.parser = argparse.ArgumentParser(
            description="Downloads CellbyCell data from SImA.",
            prog="cellBycellCall.py",
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
            help="Signals UUID input",
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
            default=102400,
            help="chunksize for writing tsv file (def: 102400)",
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
            "-d", "--debug", action="store_true", default=False, required=False
        )

        if inOpts is None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(inOpts)


def main(inOpts=None):
    cl = CommandLine(inOpts=inOpts)

    user = cl.args.user
    pwd = cl.args.password
    uuid = cl.args.uuid
    chunkSize = cl.args.chunksize
    attempts = cl.args.attempts
    outPath = cl.args.outPath

    for _ in range(attempts):
        try:
            tokenValidationURL = urljoin(
                base=BASE_URL, url=f"api/1.1/authentication/validate"
            )
            validToken = getResponse(
                url=tokenValidationURL,
                user=user,
                password=pwd,
            )

            ## Main Operations below ##
            if validToken.status_code == 200:
                print("Successfully connected!", file=sys.stderr)
                dlLink = getDLLink(
                    uuid=uuid, user=user, password=pwd, attempts=attempts
                )

                outName = f"{uuid}_cellbycell"
                outName = os.path.join(outPath, outName)
                print(f"File Output: {outName}.tsv", file=sys.stderr)

                if not cl.args.debug:
                    code = getFiles(
                        dlLink=dlLink,
                        outName=f"{outName}.tsv",
                        user=user,
                        password=pwd,
                        chunksize=chunkSize,
                        attempts=attempts,
                    )
                    if code != 0:
                        print(f"Status Code: {code}", file=sys.stderr)
                        sys.exit(1)
                    else:
                        return 0
            else:
                print("Invalid token!", file=sys.stderr)
                continue

        except Exception as e:
            print(f"<main> {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Retrying connection", file=sys.stderr)
            sleep(1)

    exit(1)


if __name__ == "__main__":
    main()
