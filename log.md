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

### Bash Script Refactoring for 01_convert_to_edf.sh
- Refactored bash script structure to follow similar principles as Python guidelines (commit f57be8e)
- Created main() function with clear pseudo-code flow: setup_environment → setup_directories → convert_all_files
- Reorganized function order: main function at top, supporting functions defined after
- Removed hardcoded absolute paths and converted to relative paths from git repository root
- Added setup_environment() function that changes to git root using `cd "$(git rev-parse --show-toplevel)"`
- Added setup_directories() function that sets up directory paths and ensures output directory exists with `mkdir -p`
- Added convert_all_files() function to handle the main conversion loop
- Added convert_single_file() function to process individual files with proper parameters
- Cleaned up variable names using proper bash conventions (UPPERCASE for constants, lowercase for local variables)
- Removed all commented-out code and unused variables for cleaner script
- Added function documentation with clear descriptions of what each function does
- Added proper error handling structure with meaningful error messages

### FFT Processing Script Refactoring for 03_fft_autoscore.py
- Refactored script structure to align with AIDER.md guidelines (commit 4e3a9e0)
- Created proper main() function with clear pseudo-code flow: setup_environment() → setup_parameters() → setup_directories() → discover_edf_files() → process_all_files()
- Reorganized function order: main function placed after imports, supporting functions defined after main
- Removed all global variables (input_directory, output_directory, sampling_rate, etc.) and converted to function parameters
- Converted hardcoded absolute path to relative paths from git root: input "01_data_files/02_edf_cropped", output "01_data_files/06_fft_files"
- Added setup_parameters() function that returns dictionary with all FFT analysis parameters
- Added setup_directories() function that ensures output directory exists using mkdir(parents=True, exist_ok=True)
- Added discover_edf_files() function to handle EDF file discovery separately from main logic
- Added setup_environment() function with _change_to_git_root() for consistent execution location
- Added process_all_files() function to handle the main processing loop with progress tracking
- Renamed process_edf_file() to process_single_edf_file() for clarity and updated to use parameter dictionary
- Added NumPy style docstrings to all functions with proper Parameters and Returns sections
- Added _change_to_git_root() utility function with proper error handling for git operations
- Script now follows the example structure from AIDER.md with clear separation of concerns and modular design
