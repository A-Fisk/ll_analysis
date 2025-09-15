import pyedflib
import pdb
import numpy as np
import pandas as pd
import os
import subprocess
from pathlib import Path

# main function
def main():
    """
    Main function to process EDF files and generate FFT analysis.
    """
    setup_environment()
    parameters = setup_parameters()
    input_dir, output_dir = setup_directories()
    file_list = discover_edf_files(input_dir)
    process_all_files(file_list, parameters, output_dir)

def setup_environment():
    """
    Set up the environment by changing to git repository root.
    """
    _change_to_git_root()

def setup_parameters():
    """
    Set up FFT analysis parameters.
    
    Returns
    -------
    dict
        Dictionary containing all FFT parameters.
    """
    parameters = {
        'sampling_rate': 256,  # Sampling rate in Hz
        'window_length': 4,    # Length of the window in seconds
        'freq_bin_size': 0.25, # Size of frequency bins in Hz
        'freq_limit': 20,      # frequency limit in Hz
        'channel_name_mapping': {0: "fro", 1: "occ", 2: "foc"}
    }
    
    # Calculate window samples
    parameters['window_samples'] = parameters['window_length'] * parameters['sampling_rate']
    
    return parameters

def setup_directories():
    """
    Set up input and output directories and ensure output directory exists.
    
    Returns
    -------
    tuple
        A tuple containing (input_dir, output_dir) as Path objects.
    """
    input_dir = Path("01_data_files/02_edf_cropped")
    output_dir = Path("01_data_files/06_fft_files")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return input_dir, output_dir

def discover_edf_files(input_dir):
    """
    Discover all EDF files in the input directory.
    
    Parameters
    ----------
    input_dir : Path
        The input directory to search for EDF files.
        
    Returns
    -------
    list
        List of Path objects for all EDF files found.
    """
    file_list = list(input_dir.glob("*.edf"))
    return file_list

def process_all_files(file_list, parameters, output_dir):
    """
    Process all EDF files with FFT analysis.
    
    Parameters
    ----------
    file_list : list
        List of Path objects for EDF files to process.
    parameters : dict
        Dictionary containing FFT parameters.
    output_dir : Path
        The output directory for FFT results.
    """
    total_files = len(file_list)
    
    for count, edf_file in enumerate(file_list, start=1):
        process_single_edf_file(edf_file, parameters, output_dir)
        print(f"Processed {count}/{total_files} files.")
    
    print("FFT processing complete for all files.")

def process_single_edf_file(edf_file_path, parameters, output_dir):
    """
    Process a single EDF file and generate FFT analysis.
    
    Parameters
    ----------
    edf_file_path : Path
        Path to the EDF file to process.
    parameters : dict
        Dictionary containing FFT parameters.
    output_dir : Path
        The output directory for FFT results.
    """
    signals_data = read_edf_signals(edf_file_path, parameters)
    all_results = process_all_channels(signals_data, parameters)
    save_results_to_csv(all_results, edf_file_path, output_dir)

def read_edf_signals(edf_file_path, parameters):
    """
    Read EDF file and return signal data for processing.
    
    Parameters
    ----------
    edf_file_path : Path
        Path to the EDF file to process.
    parameters : dict
        Dictionary containing FFT parameters.
        
    Returns
    -------
    list
        List of signal arrays from the EDF file.
    """
    signals_data = []
    
    with pyedflib.EdfReader(str(edf_file_path)) as f:
        n_channels = f.signals_in_file
        num_channels_to_process = min(3, n_channels)
        
        for channel_index in range(num_channels_to_process):
            signal = f.readSignal(channel_index)
            signals_data.append((channel_index, signal))
    
    return signals_data

def process_all_channels(signals_data, parameters):
    """
    Process all channels and return aggregated results.
    
    Parameters
    ----------
    signals_data : list
        List of tuples containing (channel_index, signal_array).
    parameters : dict
        Dictionary containing FFT parameters.
        
    Returns
    -------
    list
        List of dictionaries containing processed results for all channels.
    """
    all_results = []
    
    for channel_index, signal in signals_data:
        channel_results = process_single_channel(signal, channel_index, parameters)
        all_results.extend(channel_results)
    
    return all_results

def process_single_channel(signal, channel_index, parameters):
    """
    Process a single channel's signal data.
    
    Parameters
    ----------
    signal : numpy.ndarray
        Signal data for the channel.
    channel_index : int
        Index of the channel being processed.
    parameters : dict
        Dictionary containing FFT parameters.
        
    Returns
    -------
    list
        List of dictionaries containing processed results for the channel.
    """
    channel_results = []
    n_windows = len(signal) // parameters['window_samples']
    
    for window_index in range(n_windows):
        start_sample = window_index * parameters['window_samples']
        end_sample = start_sample + parameters['window_samples']
        signal_window = signal[start_sample:end_sample]
        
        binned_magnitude = perform_fft_analysis(signal_window, parameters)
        
        # Convert binned results to data records
        frequency_bins = np.arange(len(binned_magnitude)) * parameters['freq_bin_size']
        for bin_freq, bin_mag in zip(frequency_bins, binned_magnitude):
            channel_results.append({
                'Channel': parameters['channel_name_mapping'].get(
                    channel_index, f"Channel {channel_index}"
                ),
                'Frequency (Hz)': bin_freq,
                'Magnitude': bin_mag,
                'Window': window_index + 1
            })
    
    return channel_results

def perform_fft_analysis(signal_window, parameters):
    """
    Perform FFT analysis on a signal window.
    
    Parameters
    ----------
    signal_window : numpy.ndarray
        Signal data for a single window.
    parameters : dict
        Dictionary containing FFT parameters.
        
    Returns
    -------
    numpy.ndarray
        Binned magnitude values for the frequency range.
    """
    # Perform FFT
    fft_result = np.fft.fft(signal_window)
    magnitude = np.abs(fft_result[:parameters['window_samples'] // 2])
    
    # Create frequency array
    frequencies = np.fft.fftfreq(
        parameters['window_samples'], d=1 / parameters['sampling_rate']
    )[:parameters['window_samples'] // 2]
    
    # Filter frequencies to keep only those within the limit
    valid_indices = frequencies <= parameters['freq_limit']
    valid_frequencies = frequencies[valid_indices]
    valid_magnitude = magnitude[valid_indices]
    
    # Bin the results
    num_bins = int(parameters['freq_limit'] / parameters['freq_bin_size']) + 1
    binned_magnitude = np.zeros(num_bins)
    
    for j in range(len(valid_frequencies)):
        bin_index = int(valid_frequencies[j] // parameters['freq_bin_size'])
        binned_magnitude[bin_index] += valid_magnitude[j]
    
    return binned_magnitude

def save_results_to_csv(all_results, edf_file_path, output_dir):
    """
    Save processed results to CSV file.
    
    Parameters
    ----------
    all_results : list
        List of dictionaries containing all processed results.
    edf_file_path : Path
        Path to the original EDF file (for naming output).
    output_dir : Path
        The output directory for FFT results.
    """
    filename_stem = edf_file_path.stem
    output_file_path = output_dir / f"{filename_stem}.csv"
    
    # Convert all results to a DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Pivot the DataFrame to have frequencies as columns
    pivoted_df = results_df.pivot_table(
        index=['Channel', 'Window'],
        columns='Frequency (Hz)',
        values='Magnitude', fill_value=0
    )
    
    # Save the pivoted DataFrame to a single CSV file
    pivoted_df.to_csv(output_file_path)
    
    print(f"Saved all binned FFT results to {output_file_path}")

def _change_to_git_root():
    """
    Change the current working directory to the git repository root.
    """
    try:
        # Get the git repository root directory
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True
        )
        git_root = result.stdout.strip()
        
        # Change to the git root directory
        os.chdir(git_root)
        print(f"Changed to git repository root: {git_root}")
        
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository or git not available")
        exit(1)
    except FileNotFoundError:
        print("Error: git command not found")
        exit(1)

if __name__ == "__main__":
    main()
