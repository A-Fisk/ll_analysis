# Log

## 2025-09-15

### File Structure Updates for 01_crop_edfs.py
- Replaced hardcoded absolute path `/Users/angusfisk/Documents/01_personal_files/01_work/11_LL_paper/02_analysis/01_data_files/01_edf/01_script` with relative path `data/edf/raw`
- Updated output directory from `input_edf_dir.parent / "02_cropped"` to relative path `data/edf/cropped`
- Both paths now work from git repository root as specified in AIDER.md guidelines
- Marked first three TODO items as completed
