#!/bin/bash

# Function to format and display messages in a box
function box_echo() {
    local message="$1"
    local box_width=80
    local padding="|  "
    local end_padding="  |"
    local line_length=$((box_width - ${#padding} - ${#end_padding}))

    # Split the message into lines of the specified length
    while IFS= read -r line; do
        printf "%s%-${line_length}s%s\n" "$padding" "$line" "$end_padding"
    done <<< "$(echo "$message" | fold -sw $line_length)"
}
