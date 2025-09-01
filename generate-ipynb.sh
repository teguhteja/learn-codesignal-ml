#!/bin/bash

# Check if an input file argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

# Define the input text file from the first argument
INPUT_FILE="$1"

# Variables to hold current notebook content
current_file=""
lesson_started=false
unit_number=""
next_valid_line=""
skip_next=0
last_line=""

# Function to check if line should be skipped
should_skip_line() {
    local line="$1"
    # Skip lines containing "practices" or "min" or "Preview" (case insensitive)
    if [[ $line =~ [0-9]+[[:space:]]*practices ]] || [[ $line =~ [0-9]+[[:space:]]*min ]] || [[ $line =~ [Pp]review ]]; then
        return 0  # true - should skip
    fi
    return 1  # false - should not skip
}

# Function to finish and save the current notebook
finish_notebook() {
    if [[ $lesson_started == true ]]; then
        # Add the last line as a heading if it exists
        if [[ -n "$last_line" ]]; then
            echo ' ,{
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## '"$(echo "$last_line" | sed 's/"/\\"/g')"'"
            ]
            }' >> "$current_file"
        fi
        
        # Close the JSON structure of the notebook
        echo '   ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}' >> "$current_file"
        echo "Generated notebook: $current_file"
    fi
}

# Read all lines into an array first to handle last line properly
mapfile -t lines < "$INPUT_FILE"

# Process each line
for i in "${!lines[@]}"; do
    line="${lines[$i]}"
    
    # Check if the line starts with "Unit", indicating a new file and new markdown cell
    if [[ $line == Unit* ]]; then
        # Finish the previous notebook if any
        finish_notebook

        # Extract unit number
        unit_number=$(echo "$line" | grep -o '[0-9]\+')
        
        # Find the next valid line (skip practices, min, preview)
        next_valid_line=""
        for ((j=i+1; j<${#lines[@]}; j++)); do
            if ! should_skip_line "${lines[$j]}" && [[ -n "${lines[$j]// /}" ]]; then
                next_valid_line="${lines[$j]}"
                break
            fi
        done
        
        # Create filename: Unit number + next valid line
        if [[ -n "$next_valid_line" ]]; then
            filename="${unit_number}.${next_valid_line// /-}"
        else
            filename="$unit_number"
        fi
        current_file="${filename}.ipynb"

        # Start a new notebook JSON structure
        echo '{
            "cells": [' > "$current_file"
                    
        # Add the lesson name as a heading 1
        echo '  {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# '"$line"'"
            ]
            }' >> "$current_file"
        
        lesson_started=true
        
    elif should_skip_line "$line"; then
        # Skip this line
        continue
    elif [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]]; then
        # Skip empty lines
        continue
    elif [[ $lesson_started == true ]]; then
        # Store this line as potential last line
        last_line="$line"
        
        # Check if this is the actual last line of the file
        is_last_content_line=true
        for ((k=i+1; k<${#lines[@]}; k++)); do
            if [[ -n "${lines[$k]// /}" ]] && ! [[ "${lines[$k]}" == Unit* ]]; then
                is_last_content_line=false
                break
            fi
        done
        
        # If not the last content line, add as heading now
        if [[ $is_last_content_line == false ]]; then
            echo ' ,{
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## '"$(echo "$line" | sed 's/"/\\"/g')"'"
            ]
            }' >> "$current_file"
        fi
    fi
done

# Finish the last notebook
finish_notebook
