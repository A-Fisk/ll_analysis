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
