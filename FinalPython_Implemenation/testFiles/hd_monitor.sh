#!/usr/bin/env bash

cd "/csc/data/halo384/cyto_process/scripts/HistDiffPipeline"

WATCH_DIR="/csc/data/halo384/cyto_process/temp/hd_dumps"
PROCESSED_FILES="${WATCH_DIR}/.fileLog"

TEMP_ENTRY_FILES="/csc/data/halo384/cyto_process/temp/hd_entries/TM_secondRerun.csv"

CURRENT_PROCESS=0
MAX_PROCESS=2

if [ ! -f "$PROCESSED_FILES" ]; then
    touch $PROCESSED_FILES
fi

currentFiles=$(ls "$WATCH_DIR")

for file in $currentFiles; do
    if [ -f "$WATCH_DIR/$file" ]; then
        if ! grep -q "^$file$" "$PROCESSED_FILES"; then
            echo "New file: $file"

            filePath="$WATCH_DIR/$file"

            # TODO: ADD SOME PROGRAM/SCRIPT TO HANDLE/FETCH UUID ENTRIES
            # NOTE: The above todo will require deleting entries and such
            while [ "$CURRENT_PROCESS" -ge "$MAX_PROCESS" ]; do
                sleep 10
                CURRENT_PROCESS=$(pgrep -c -f runHistDiff.sh)
            done

            ((CURRENT_PROCESS++))
            #Execute scripts
            (
                ./runHistDiff.sh $filePath $TEMP_ENTRY_FILES
                echo "$file" >>"$PROCESSED_FILES"
                CURRENT_PROCESS=$((CURRENT_PROCESS - 1))
            ) &

        fi
    fi
done

# inotifywait -t 10 -q -e create --format "%f" "$WATCH_DIR" | while read newFile; do
#     echo "file: $newFile"
# done
