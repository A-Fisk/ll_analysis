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
