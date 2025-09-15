#!/bin/bash

# Main function to convert txt files to EDF format
main() {
    setup_environment
    setup_directories
    convert_all_files
}

# Change to git repository root directory
setup_environment() {
    cd "$(git rev-parse --show-toplevel)" || {
        echo "Error: Not in a git repository or git not available"
        exit 1
    }
}

# Set up directory paths and ensure output directory exists
setup_directories() {
    TEMPLATE_FILE="02_preprocessing/_ascii_to_edf.template"
    ASCII_CONVERTER="/Users/angusfisk/Documents/github_repos/ascii2edf/ascii2edf"
    INPUT_DIR="01_data_files/01_txt_files"
    OUTPUT_DIR="01_data_files/02_edf_raw"
    
    # Ensure output directory exists
    mkdir -p "$OUTPUT_DIR"
    
    echo "Using template file: $TEMPLATE_FILE"
}

# Convert all txt files in input directory to EDF format
convert_all_files() {
    local counter=1
    
    # Loop through each file in the input directory
    for file in "$INPUT_DIR"/*; do
        if [[ -f "$file" ]]; then
            convert_single_file "$file" "$counter"
            ((counter++))
        fi
    done
}

# Convert a single txt file to EDF format
convert_single_file() {
    local input_file="$1"
    local file_counter="$2"
    local base_name
    local output_file
    
    base_name=$(basename "$input_file")
    output_file="$OUTPUT_DIR/${base_name%.txt}.edf"
    
    echo "Processing file $file_counter: $base_name"
    
    # Run ascii2edf conversion
    "$ASCII_CONVERTER" "$input_file" "$TEMPLATE_FILE" "Mouse" "date" "18" "04" "09" "00" "00" "00" "$output_file"
    
    # Check conversion result
    if [[ $? -eq 0 ]]; then
        echo "Successfully converted $input_file to $output_file"
    else
        echo "Failed to convert $input_file"
    fi
}

# Execute main function
main "$@"

