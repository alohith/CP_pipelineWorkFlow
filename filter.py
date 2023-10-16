import sys
import re
import pandas as pd

if len(sys.argv) != 3:
    print("Usage: python script.py input.csv output.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

df = pd.read_csv(input_file)
header = df.columns.tolist()
print(",".join(header))

cell_ID_column = -1
series_ID_column = -1
site_ID_column = -1

for i in range(len(header)):
    if header[i] == "Cell_ID":
        cell_ID_column = i
    elif header[i] == "Series_ID":
        series_ID_column = i
    elif header[i] == "Site_ID":
        site_ID_column = i

for index, row in df.iterrows():
    cell_ID = row["Cell_ID"]
    if "e" in cell_ID:
        cell_ID = re.sub(r'"[\d.]+[eE][+-]\d+"', "", cell_ID)
        cell_ID = cell_ID.replace('"', "")
        cell_ID = cell_ID.replace("+", r"\+")
        parts = cell_ID.split("_")
        new_cell_ID = f"{parts[0]}_{row['Site_ID']}_{row['Series_ID']}_{parts[3]}"
        df.at[index, "Cell_ID"] = re.sub(cell_ID, new_cell_ID, row["Cell_ID"])

df.to_csv(output_file, index=False)
