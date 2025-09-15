import pyedflib
import pdb
import numpy as np
import pandas as pd
from pathlib import Path

# Parameters

input_directory = Path(
    '/Users/angusfisk/Documents/01_personal_files/01_work/'
    '11_LL_paper/02_analysis/01_data_files/01_edf/03_test'
)
output_directory = input_directory.parents[1] / '06_fft_files' / '01_script'
sampling_rate = 256  # Sampling rate in Hz
window_length = 4  # Length of the window in seconds
window_samples = window_length * sampling_rate
# Number of samples in the window
freq_bin_size = 0.25  # Size of frequency bins in Hz
freq_limit = 20  # frequency limit in Hz

# Create output directory if it doesn't exist
output_directory.mkdir(exist_ok=True)

# Channel name mapping
channel_name_mapping = {0: "fro", 1: "occ", 2: "foc"}

# Function to process a single EDF file


def process_edf_file(edf_file_path):
    # Get the filename stem for output
    filename_stem = edf_file_path.stem
    output_file_path = output_directory / f"{filename_stem}.csv"

    # Read the EDF file
    with pyedflib.EdfReader(str(edf_file_path)) as f:
        n_channels = f.signals_in_file

        # Process the first three channels (or fewer if there aren't three)
        num_channels_to_process = min(3, n_channels)
        all_results = []

        for channel_index in range(num_channels_to_process):
            signal = f.readSignal(channel_index)

            # Calculate number of windows
            n_windows = len(signal) // window_samples

            # Frequency array for FFT
            frequencies = np.fft.fftfreq(
                window_samples, d=1 / sampling_rate
            )[:window_samples // 2]

            # Process each window
            for i in range(n_windows):
                start_sample = i * window_samples
                end_sample = start_sample + window_samples
                signal_window = signal[start_sample:end_sample]

                # Perform FFT
                fft_result = np.fft.fft(signal_window)
                magnitude = np.abs(fft_result[:window_samples // 2])
                # Get magnitude for positive frequencies

                # Filter frequencies and magnitudes
                # to keep only those between 0 and 20 Hz
                valid_indices = frequencies <= freq_limit
                valid_frequencies = frequencies[valid_indices]
                valid_magnitude = magnitude[valid_indices]

                # Bin the results for the valid frequencies
                num_bins = int(freq_limit / freq_bin_size) + 1
                binned_magnitude = np.zeros(num_bins)

                for j in range(len(valid_frequencies)):
                    bin_index = int(valid_frequencies[j] // freq_bin_size)
                    binned_magnitude[bin_index] += valid_magnitude[j]

                # Prepare data for aggregation
                frequency_bins = np.arange(num_bins) * freq_bin_size
                for bin_freq, bin_mag in zip(frequency_bins, binned_magnitude):
                    all_results.append({
                        'Channel': channel_name_mapping.get(
                            channel_index, f"Channel {channel_index}"
                        ),
                        'Frequency (Hz)': bin_freq,
                        'Magnitude': bin_mag,
                        'Window': i + 1
                    })

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


# Process all EDF files in the input directory
edf_files = list(input_directory.glob('*.edf'))
total_files = len(edf_files)

for count, edf_file in enumerate(edf_files, start=1):
    process_edf_file(edf_file)
    print(f"Processed {count}/{total_files} files.")

print("FFT processing complete for all files.")
