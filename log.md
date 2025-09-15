# Log

## 2025-09-15

### File Structure Updates for 01_crop_edfs.py
- Replaced hardcoded absolute path `/Users/angusfisk/Documents/01_personal_files/01_work/11_LL_paper/02_analysis/01_data_files/01_edf/01_script` with relative path `data/edf/raw`
- Updated output directory from `input_edf_dir.parent / "02_cropped"` to relative path `data/edf/cropped`
- Corrected directory paths: input_edf_dir to `01_data_files/01_edf_raw` and output_edf_dir to `01_data_files/02_edf_cropped`
- Both paths now work from git repository root as specified in AIDER.md guidelines
- Marked first three TODO items as completed

### Added Git Root Directory Function
- Added `_change_to_git_root()` function to ensure script always runs from git repository root
- Function uses `git rev-parse --show-toplevel` to find git root directory
- Added error handling for cases where git is not available or not in a git repository
- Updated main execution to call this function first
- Marked "Verify script follows AIDER.md guidelines" as completed

### TODO List Cleanup
- Removed three TODO items: error handling for input directory, output directory creation, and missing EDF files
- Focused TODO list on testing the updated paths

## 2025-09-16

### AIDER.md Guidelines Refactoring for 01_crop_edfs.py
- Refactored script structure to align with AIDER.md guidelines (commit 411facf)
- Created proper main() function with clear pseudo-code flow: setup_environment() → setup_directories() → discover_edf_files() → process_all_files()
- Reorganized function order: main function placed after imports, supporting functions defined after main
- Removed global variables input_edf_dir and output_edf_dir, now handled within functions with proper parameters
- Added setup_directories() function that ensures output directory exists using mkdir(parents=True, exist_ok=True)
- Added discover_edf_files() function to handle EDF file discovery separately from main logic
- Added setup_environment() function to handle git root directory change
- Updated process_all_files() function to handle the file processing loop with proper parameters
- Maintained proper function naming: _change_to_git_root() keeps underscore (utility function not called from main)
- All functions now have NumPy style docstrings with proper Parameters and Returns sections
- Script now follows the example structure from AIDER.md with clear separation of concerns
