# TODO List

## 02_preprocessing/01_crop_edfs.py File Structure Updates

- [x] Replace hardcoded absolute path with relative path from git repository root
- [x] Update input_edf_dir to use current file structure (01_data_files/01_edf_raw)
- [x] Update output_edf_dir to use current file structure (01_data_files/02_edf_cropped)
- [ ] Add error handling to check if input directory exists
- [ ] Add logic to create output directory if it doesn't exist
- [ ] Add error handling for missing EDF files
- [ ] Test the updated paths work correctly from repository root
- [x] Verify the script follows AIDER.md guidelines (runs from repo root)
- [ ] Add proper error messages for file/directory not found cases
