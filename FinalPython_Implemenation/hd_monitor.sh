#!/usr/bin/env bash

# Change directory to the script's directory
cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline" || exit

WATCH_DIR="/csc/data/halo384/cyto_process/temp/hd_dumps"
PROCESSED_FILES="${WATCH_DIR}/.fileLog"

LOCKFILE="${WATCH_DIR}/.hdlock"

if [ -f "$LOCKFILE" ]; then
    echo "Instance of script is already running!"
    exit 1
fi

touch "$LOCKFILE"

cleanup() {
    rm -f "$LOCKFILE"
}

trap 'cleanup' EXIT

#TEMP_ENTRY_FILES="/csc/data/halo384/cyto_process/temp/hd_entries/TM_secondRerun.csv"
cytoRunContents="/csc/data/halo384/cyto_process/temp/hd_entries"
CYTO_RUN_CONTENTS=$(ls -t1 $cytoRunContents | grep -v '^\.' | head -n 1)

# TODO: ADD SOME PROGRAM/SCRIPT TO HANDLE/FETCH UUID ENTRIES
# NOTE: The above todo will require deleting entries and such

MAX_PROCESS=4

if [ ! -f "$PROCESSED_FILES" ]; then
    touch "$PROCESSED_FILES"
fi

# Loop through files using a safer method than parsing ls
find "$WATCH_DIR" -type f ! -name '.*' -print0 | while IFS= read -r -d '' file; do
    if [ -f "$file" ]; then
        echo "New file: $(basename "$file")"

        # Check the number of running processes and limit to MAX_PROCESS
        while [ "$(pgrep -c -f runHistDiff.sh)" -ge "$MAX_PROCESS" ]; do
            sleep 10
        done

        # Execute scripts
        (
            ./runHistDiff.sh "$file" "$cytoRunContents/$CYTO_RUN_CONTENTS" "$PROCESSED_FILES"
        ) &

        # if ! grep -q -Fx "$(basename "$file")" "$PROCESSED_FILES"; then
        #     echo "New file: $(basename "$file")"

        #     # Check the number of running processes and limit to MAX_PROCESS
        #     while [ "$(pgrep -c -f runHistDiff.sh)" -ge "$MAX_PROCESS" ]; do
        #         sleep 10
        #     done

        #     # Execute scripts
        #     (
        #         ./runHistDiff.sh "$file" "$cytoRunContents/$CYTO_RUN_CONTENTS" "$PROCESSED_FILES"
        #     ) &

        # fi
    fi
done

wait
