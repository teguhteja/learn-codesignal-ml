#!/bin/bash

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

# Function to finish and save the current notebook
finish_notebook() {
    if [[ $lesson_started == true ]]; then
        # Close the JSON structure of the notebook
        echo '   ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}' >> "$current_file"
        echo "Generated notebook: $current_file"
    fi
}

# Read through the text file line by line
while IFS= read -r line; do
    # Check if the line starts with "Unit", indicating a new file and new markdown cell
    if [[ $line == Unit* ]]; then
        # Finish the previous notebook if any
        finish_notebook

        # Create a new filename based on the lesson name. 
        lesson_name=$(echo "$line" )  # Get text before the colon
        current_file=$(echo "$lesson_name" ).ipynb  

        # Start a new notebook JSON structure
        echo '{
            "cells": [' > "$current_file"
                    
                    # Add the lesson name as a heading 1
                    echo '  {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# '"$lesson_name"'"
            ]
            }' >> "$current_file"
        
        lesson_started=true
    elif  [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]]; then
        # Skip lines that do not match any condition
        continue
    else 
        # Add the subsequent lines as markdown content
        echo ' ,{
            "cell_type": "markdown",
            "metadata": {},
            "source": [' >> "$current_file"
                    echo ' "## '$(echo "$line" | sed 's/"/\\"/g')'" ' >> "$current_file"
                    echo '   ]
            }' >> "$current_file"
    fi
done < "$INPUT_FILE"

# Finish the last notebook
finish_notebook
