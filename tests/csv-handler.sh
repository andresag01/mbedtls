#!/bin/sh

CSV_HANDLER_OUTFILE=""
CSV_HANDLER_SEPARATOR=""

csv_handler_init() {
    CSV_HANDLER_OUTFILE="$1"
    CSV_HANDLER_SEPARATOR="${2:-,}"

    if [ "${CSV_HANDLER_SEPARATOR}" = "\"" ]; then
        echo "csv file separator cannot be '\"'"
        return 1
    elif [ ${#CSV_HANDLER_OUTFILE}  -eq 0 ]; then
        echo "Output csv filename cannot be '$CSV_HANDLER_OUTFILE'"
        return 1
    elif [ ! -f "$CSV_HANDLER_OUTFILE" ]; then
        echo "Creating output csv file '$CSV_HANDLER_OUTFILE'"
        csv_handler_add_header
    else
        echo "Output csv file '$CSV_HANDLER_OUTFILE' already exists"
    fi
    return 0
}

# At the moment it is not possible to configure the quote character, which is
# always set to '
csv_handler_quote_string() {
    echo "'$( python -c "print '$1'.encode('unicode_escape')" )'"
}

csv_handler_add_header() {
    csv_handler_add_record "Number" "Name" "Dependencies" "Result" "Reason" \
        "Log file" "Test script"
}

csv_handler_add_record() {
    local INDEX=0
    local ITEM QUOTED_ITEM

    for ITEM in "$@"; do
        QUOTED_ITEM="$( csv_handler_quote_string "$ITEM" )"
        if [ $INDEX -eq 0 ]; then
            printf "%s" "$QUOTED_ITEM" >> "$CSV_HANDLER_OUTFILE"
        else
            printf "%s%s" "$CSV_HANDLER_SEPARATOR" "$QUOTED_ITEM" >> "$CSV_HANDLER_OUTFILE"
        fi
        INDEX=$(( INDEX + 1 ))
    done
    printf "\n" >> "$CSV_HANDLER_OUTFILE"
}
