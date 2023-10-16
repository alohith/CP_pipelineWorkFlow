import sys
import pandas as pd

synonyms = {
    "UCSC CSC Plate ID": "Plate Map",
    "UCSC CSC PlateID": "Plate Map",
    "Plate Name": "Plate Map",
    "PlateName": "Plate Map",
    "384 well": "Well",
    "384 well position": "Well",
    "Well Name": "Well",
    "Molecule Name": "MoleculeID",
    "Molecule ID": "MoleculeID",
    "ID Number": "MoleculeID",
    "Molarity": "Concentration",
    "Molarity (mM)": "Concentration",
    "Stock Concentration": "Concentration",
    "Stock_Concentration": "Concentration",
    "Stock concentration": "Concentration",
    "Stock_concentration": "Concentration",
    "UCSC_CSC_Plate_ID": "Plate Map",
    "UCSC_CSC_PlateID": "Plate Map",
    "Plate_Name": "Plate Map",
    "PlateName": "Plate Map",
    "384_well": "Well",
    "384_well_position": "Well",
    "Well_Name": "Well",
    "Molecule_Name": "MoleculeID",
    "Molecule_ID": "MoleculeID",
    "ID_Number": "MoleculeID",
    "Molarity_(mM)": "Concentration",
}

if len(sys.argv) != 3:
    print("Usage: python script.py input.csv output.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

df = pd.read_csv(input_file)
header = list(df.columns)

for i in range(len(header)):
    header[i] = header[i].replace("(", "").replace(")", "")
    header[i] = synonyms.get(header[i], header[i])

for column in ["Plate Map", "Well", "MoleculeID", "Concentration"]:
    if column not in header:
        print(f"\n\n{column} column not found: {', '.join(header)}")
        sys.exit(1)

df = df[["Plate Map", "Well", "MoleculeID", "Concentration"]]
df.dropna(subset=["MoleculeID"], inplace=True)
df.to_csv(output_file, index=False)
