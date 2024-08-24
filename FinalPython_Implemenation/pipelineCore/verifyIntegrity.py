#!/usr/bin/env python
import multiprocessing as mp, os, sys


def fixIntegrity(inFile, outFile):
    headerLen = None

    with open(inFile, "r") as f:  # file prep stage
        header = next(f)
        headerLen = len(header.split("\t"))

        with open(outFile, "w") as of:
            of.write(header)

    with open(inFile, "r") as f:
        print(f"Header length: {headerLen}", file=sys.stderr)

        next(f)  # skip the header
        with open(outFile, "a") as of:
            for line in f:
                if len(line.split("\t")) == headerLen:
                    of.write(line)

    return


def main():
    if len(sys.argv) < 3:
        print(f"Usage: python3 {sys.argv[0]} <input> <output>")
        sys.exit(1)

    inFile = sys.argv[1]
    outFile = sys.argv[2]

    fixIntegrity(inFile=inFile, outFile=outFile)


if __name__ == "__main__":
    main()
