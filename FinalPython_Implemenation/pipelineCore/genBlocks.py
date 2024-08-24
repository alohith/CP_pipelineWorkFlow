#!/usr/bin/env python
import os, sys
from string import ascii_uppercase


class CommandLine:
    def __init__(self, inOpts=None) -> None:
        import argparse

        self.parser = argparse.ArgumentParser(add_help=True, description="Block gen")
        self.parser.add_argument(
            "-i",
            "--input",
            nargs="+",
            action="store",
            required=True,
            help="input selection (i.e. A..P or 1..24)",
        )
        self.parser.add_argument(
            "-c",
            "--columns",
            default=False,
            action="store_true",
            help="enables column block generation",
        )

        if inOpts is not None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(inOpts)


def main():
    cl = CommandLine()
    row = not cl.args.columns
    col = cl.args.columns

    # inBlocks = ["A", "C", "E", "G", "I", "K", "M", "O"]
    # # inBlocks = [1, 2, 3, 4]
    inBlocks = cl.args.input
    finalBlocks = []
    if row:
        for i in inBlocks:
            for j in range(1, 25):
                finalBlocks.append(f"{i}{str(j).zfill(2)}")

    if col:
        for i in inBlocks:
            for j in ascii_uppercase[:16]:
                finalBlocks.append(f"{j}{str(i).zfill(2)}")

    print(*finalBlocks, sep=" ", file=sys.stdout)


if __name__ == "__main__":
    main()
