import sys

file = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: countRows.py <filename>")

try:
    with open(file, "r") as f:
        lines = f.readlines()
except FileNotFoundError:
    print("File not found.")
    sys.exit(1)

counts = [0] * 1601  # 384*4+1
for line in lines:
    data = line.strip().split(",")
    for i in range(len(data)):
        if len(data[i]) > 0:
            counts[i] += 1

with open(file, "r") as f:
    lines = f.readlines()

for line in lines:
    data = line.strip().split(",")
    if len(data) > 10:
        for i in range(len(data)):
            if counts[i] > 1600:
                print(data[i], end=",")
        print()
