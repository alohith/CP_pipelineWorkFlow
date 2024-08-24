import sys
import pandas as pd

cutoff = 20
bad_wells = set()

if len(sys.argv) < 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

file = sys.argv[1]

try:
    df = pd.read_csv(file)
except FileNotFoundError:
    print("File not found.")
    sys.exit(1)

if (
    "WellName" not in df.columns
    or "Total_Cells_Micronuclei" not in df.columns
    or "Total_Cells_MultiWaveScoring" not in df.columns
):
    print(
        "WellName, Total_Cells_Micronuclei, or Total_Cells_MultiWaveScoring not found in header"
    )
    sys.exit(1)

for index, row in df.iterrows():
    if (
        row["Total_Cells_Micronuclei"] < cutoff
        or row["Total_Cells_MultiWaveScoring"] < cutoff
    ):
        bad_wells.add(row["WellName"])

filtered_df = df[~df["WellName"].isin(bad_wells)]

print(filtered_df)
