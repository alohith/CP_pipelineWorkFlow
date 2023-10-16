import pandas as pd
import sys


def transpose_table(input_file, delimiter):
    df = pd.read_csv(input_file, sep=delimiter, header=None)
    transposed_df = df.T
    transposed_df.to_csv(sys.stdout, sep=delimiter, index=False, header=False)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py DELIMITER input_file")
        sys.exit(1)

    delimiter = sys.argv[1]
    input_file = sys.argv[2]

    transpose_table(input_file, delimiter)
