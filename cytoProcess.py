import glob
import subprocess
import sys
import os

semaphore = "cytoProcess.lock"


def mylog(s):
    print(s, file=sys.stderr)


if os.path.exists(semaphore):
    with open(semaphore, "r") as f:
        pid = f.readline().strip()
    try:
        count = int(
            subprocess.check_output(
                [
                    "ps",
                    "-ef",
                    "|",
                    "grep",
                    pid,
                    "|",
                    "grep",
                    "-v",
                    "grep",
                    "|",
                    "wc",
                    "-l",
                ],
                shell=True,
            )
        )
    except subprocess.CalledProcessError:
        count = 0

    if count > 0:
        sys.exit()

with open(semaphore, "w") as f:
    f.write(f"{os.getpid()}\n")

new_run_contents = sorted(glob.glob("/home/halo384/cyto/CytoRunContents*"))[-1]

# Check for updated platemaps
plate_maps = glob.glob("/home/halo384/cyto/CytoPlateMaps/*.csv")
for plate_map in plate_maps:
    plate_map_base = os.path.basename(plate_map)
    output_plate_map = os.path.join("PlateMaps", plate_map_base)

    if os.path.getmtime(plate_map) > os.path.getmtime(output_plate_map):
        with open(new_run_contents, "r") as f:
            lines = f.readlines()

        for line in lines:
            if plate_map_base in line:
                parts = line.strip().split(",")
                mylog(f"removing {parts[1]}.histdiff.csv")
                os.unlink(f"{parts[1]}.histdiff.csv")

# Check for new or updated zip files
zip_files = glob.glob("/home/halo384/cyto/*.zip")
for zip_file in zip_files:
    base_name = os.path.basename(zip_file).replace(".zip", "")
    hist_diff_file = f"{base_name}.histdiff.csv"
    if not os.path.exists(hist_diff_file) or os.path.getmtime(
        zip_file
    ) > os.path.getmtime(hist_diff_file):
        plate_map_path = os.path.join(
            "/home/halo384/cyto/CytoPlateMaps", f"{base_name}.csv"
        )
        mylog(f"./flip -u {plate_map_path}")
        subprocess.run(["./flip", "-u", plate_map_path])

        mylog(f"./fixPlateMap.pl {plate_map_path} > PlateMaps/{base_name}.csv")
        subprocess.run(
            ["./fixPlateMap.pl", plate_map_path, f"> PlateMaps/{base_name}.csv"]
        )

        mylog(f"./fixZip.pl {zip_file}")
        subprocess.run(["./fixZip.pl", zip_file])

        mylog(f"./runCommand.pl {new_run_contents} {zip_file}")
        subprocess.run(["./runCommand.pl", new_run_contents, zip_file])

with open("lastRunContents.txt", "r") as f:
    last_run_contents = f.readline().strip()

if new_run_contents != last_run_contents:
    subprocess.run(["./flip", "-u", new_run_contents])
    subprocess.run(["cp", "-p", new_run_contents, "./runcontents.csv"])
    subprocess.run(["cp", "-p", new_run_contents, "../cyto_output/runcontents.csv"])
    subprocess.run(["touch", "/var/www/html/cyto/runcontents.csv"])
    subprocess.run(["rm", "-f", "/var/www/html/cyto/runcontents.csv"])
    subprocess.run(["cp", "-p", new_run_contents, "/var/www/html/cyto/runcontents.csv"])

    diff_output = subprocess.check_output(
        ["diff", last_run_contents, new_run_contents]
    ).decode("utf-8")
    lines = diff_output.split("\n")

    for line in lines:
        if line.startswith("> "):
            _, base_name, _ = line.split(",")
            mylog(f"./flip -u /home/halo384/cyto/CytoPlateMaps/{base_name}.csv")
            subprocess.run(
                ["./flip", "-u", f"/home/halo384/cyto/CytoPlateMaps/{base_name}.csv"]
            )

            mylog(
                f"./fixPlateMap.pl /home/halo384/cyto/CytoPlateMaps/{base_name}.csv > PlateMaps/{base_name}.csv"
            )
            subprocess.run(
                [
                    "./fixPlateMap.pl",
                    f"/home/halo384/cyto/CytoPlateMaps/{base_name}.csv",
                    f"> PlateMaps/{base_name}.csv",
                ]
            )

            mylog(f"./fixZip.pl {base_name}")
            subprocess.run(["./fixZip.pl", base_name])

            mylog(f"./runCommand.pl {new_run_contents} {base_name}")
            subprocess.run(["./runCommand.pl", new_run_contents, base_name])

with open("lastRunContents.txt", "w") as f:
    f.write(new_run_contents)

os.unlink(semaphore)
