import pdb
import pyedflib
import numpy as np
import os
import subprocess
from datetime import timedelta
from pathlib import Path

input_edf_dir = Path("data/edf/raw")
output_edf_dir = Path("data/edf/cropped")


def _change_to_git_root():
    """
    Change the current working directory to the git repository root.
    
    This ensures the script runs from the correct location regardless of
    where it's executed from.
    """
    try:
        # Get the git root directory
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'], 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # Change to git root directory
        os.chdir(git_root)
        print(f"Changed working directory to git root: {git_root}")
        
    except subprocess.CalledProcessError:
        print("Warning: Not in a git repository or git not available")
    except Exception as e:
        print(f"Warning: Could not change to git root: {e}")


def crop_edf_to_24_hours(
        input_edf_path,
        output_edf_path,
        file_num,
        total_files):
    """
    Crop the EDF file to the first 24 hours of data and save it.

    Parameters:
    - input_edf_path (path): The path to the input EDF file.
    - output_edf_path (path): The path to save the cropped EDF file.
    - file_num (int): Current file index (for progress tracking).
    - total_files (int): Total number of files being processed.
    """
    # Read the EDF file using high-level functions
    signals, signal_headers, header = pyedflib.highlevel.read_edf(
        str(input_edf_path)
    )

    # Determine the sampling frequency from the first signal
    sample_rate = signal_headers[0]['sample_rate']

    # Calculate the number of samples corresponding to 24 hours
    max_samples = int(24 * 60 * 60 * sample_rate)

    # Crop the signals to 24 hours (or total available samples if fewer)
    cropped_signals = [signal[:max_samples] for signal in signals]

    # Adjust the header to reflect the cropped duration
    header['record_duration'] = 24 * 60 * 60  # 24 hours in seconds

    # Write the cropped EDF file
    pyedflib.highlevel.write_edf(
        str(output_edf_path), cropped_signals, signal_headers, header
    )

    print(f"Processed file {file_num}/{total_files}: {input_edf_path.name}")


if __name__ == "__main__":
    # Ensure we're running from git repository root
    _change_to_git_root()
    
    # List all edf files in input dir
    file_list = list(input_edf_dir.glob("*.edf"))
    total_files = len(file_list)

    for i, file in enumerate(file_list):
        input_edf_path = file
        output_edf_path = output_edf_dir / str(file.stem + ".edf")

        crop_edf_to_24_hours(input_edf_path, output_edf_path, i, total_files)
