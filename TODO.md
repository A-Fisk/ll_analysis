# TODO List

## 02_preprocessing/01_crop_edfs.py File Structure Updates

- [x] Replace hardcoded absolute path with relative path from git repository root
- [x] Update input_edf_dir to use current file structure (01_data_files/01_edf_raw)
- [x] Update output_edf_dir to use current file structure (01_data_files/02_edf_cropped)
- [ ] Test the updated paths work correctly from repository root

## 02_preprocessing/01_crop_edfs.py AIDER.md Guidelines Refactoring

- [x] Create main function structure with clear pseudo-code flow
- [x] Reorganize function order (main function after imports, supporting functions after)
- [x] Remove global variables and pass paths as function parameters
- [x] Add directory setup function to ensure output directory exists
- [x] Add file discovery function for cleaner main function
- [x] Update main function logic to follow step-by-step structure
- [x] Ensure proper function naming conventions (underscore for utility functions)

## 02_preprocessing/01_convert_to_edf.sh Bash Script Refactoring

- [x] Create main function structure with clear pseudo-code flow
- [x] Reorganize function order (main function at top, supporting functions after)
- [x] Remove hardcoded absolute paths and use relative paths from git root
- [x] Add setup_environment function to change to git repository root
- [x] Add setup_directories function to ensure output directory exists
- [x] Clean up variable names with proper naming conventions
- [x] Remove dead code and commented-out sections
- [x] Add function documentation with clear descriptions

## 02_preprocessing/03_fft_autoscore.py AIDER.md Guidelines Refactoring

- [x] Create main function structure with clear pseudo-code flow
- [x] Reorganize function order (main function after imports, supporting functions after)
- [x] Remove global variables and convert to function parameters
- [x] Convert hardcoded absolute paths to relative paths from git root
- [x] Add directory setup function to ensure output directory exists
- [x] Add file discovery function for cleaner main function
- [x] Add git root setup function for consistent execution location
- [x] Add NumPy style docstrings to all functions
- [x] Break down processing into modular functions with clear separation of concerns
