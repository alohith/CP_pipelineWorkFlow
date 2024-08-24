#!/usr/bin/env bash
cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline" || exit

WATCH_DIR="/csc/data/halo384/cyto/cytoDumps"
LOCKFILE="${WATCH_DIR}/.hdlock"
PROCESSED_FILES="${WATCH_DIR}/.fileLog"

if [ -f "$LOCKFILE" ]; then
    echo "Instance of script is already running!"
    exit 1
fi

touch "$LOCKFILE"

cleanup() {
    rm -f "$LOCKFILE"
}

trap 'cleanup' EXIT

cytoRunContents="/csc/data/halo384/cyto_process/temp/hd_entries"
CYTO_RUN_CONTENTS=$(ls -t1 $cytoRunContents | grep -v '^\.' | head -n 1)

MAX_PROCESS=4

if [ ! -f "$PROCESSED_FILES" ]; then
    touch "$PROCESSED_FILES"
fi

find "$WATCH_DIR" -type f ! -name '.*' -print0 | while IFS= read -r -d '' file; do
    if [ -f "$file" ]; then
        while [ "$(pgrep -c -f runHistDiff.sh)" -ge "$MAX_PROCESS" ]; do
            sleep 10
        done
        (
            ./runHistDiff.sh "$file" "$cytoRunContents/$CYTO_RUN_CONTENTS" "$PROCESSED_FILES"
        ) &
    fi
done

wait
