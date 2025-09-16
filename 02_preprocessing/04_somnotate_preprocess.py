#!/usr/bin/env python

"""
Example script demonstrating how to preprocess a set of datasets and saving out the results.

TODO:
- provide different entry point by command line argument parsing using argparse
- fix plotting (`time` encapsulated at the moment...)
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess

try:
    # Ideally, we use a multitaper approach to compute LFP/EEG/EMG spectrograms.
    # An implementation is available on github and can be installed using:
    # pip install git+https://github.com/hbldh/lspopt.git#egg=lspopt
    from lspopt import spectrogram_lspopt
    from functools import partial

    get_spectrogram = partial(spectrogram_lspopt, c_parameter=20.0)

except ImportError:
    import warnings

    message = "Falling back to scipy.signal.spectrogram to compute the spectrogram,"
    message += "\nwhich computes the standard Baum-Welch spectrogram."
    message += "\nA multitaper approach may yield better results, "
    message += "\nfor which an implementation is available on github and can be installed with:"
    message += "\npip install git+https://github.com/hbldh/lspopt.git#egg=lspopt"
    warnings.warn(message)
    from scipy.signal import spectrogram as get_spectrogram

from _data_io import (
    ArgumentParser,
    load_dataframe,
    check_dataframe,
    load_raw_signals,
    export_preprocessed_signals,
)

from somnotate._utils import (
    robust_normalize,
)

from _configuration import (
    time_resolution,
    state_annotation_signals,
    plot_raw_signals,
)


def main():
    """
    Main function to preprocess electrophysiological signals for sleep analysis.

    Follows clear pseudo-code flow:
    1. Setup execution environment
    2. Parse command line arguments
    3. Load and validate datasets from spreadsheet
    4. Filter datasets if specific indices requested
    5. Process all datasets
    """
    setup_environment()

    args = parse_arguments()

    datasets = load_and_validate_datasets(args.spreadsheet_file_path)

    datasets = filter_datasets(datasets, args.only)

    process_all_datasets(datasets, args.show)


def setup_environment():
    """
    Setup execution environment by changing to git repository root and validating dependencies.
    """
    _change_to_git_root()
    _validate_dependencies()


def parse_arguments():
    """
    Parse command line arguments for preprocessing script.

    Returns
    -------
    args : argparse.Namespace
        Parsed command line arguments containing spreadsheet_file_path, show, and only.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "spreadsheet_file_path",
        help="Use datasets specified in /path/to/spreadsheet.csv",
    )
    parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Plot the output figures of the script.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        type=int,
        help="Indices corresponding to the rows to use (default: all). Indexing starts at zero.",
    )
    args = parser.parse_args()
    return args


def load_and_validate_datasets(spreadsheet_file_path):
    """
    Load and validate datasets from spreadsheet file.

    Parameters
    ----------
    spreadsheet_file_path : str
        Path to CSV file containing dataset information.

    Returns
    -------
    datasets : pandas.DataFrame
        Validated dataframe containing dataset information.
    """
    # load spreadsheet / data frame
    datasets = load_dataframe(spreadsheet_file_path)

    # check contents of spreadsheet
    check_dataframe(
        datasets,
        columns=[
            "file_path_raw_signals",
            "sampling_frequency_in_hz",
            "file_path_preprocessed_signals",
        ]
        + state_annotation_signals,
        column_to_dtype={
            "file_path_raw_signals": str,
            "sampling_frequency_in_hz": (int, float),
            "file_path_preprocessed_signals": str,
        },
    )
    return datasets


def filter_datasets(datasets, only_indices):
    """
    Filter datasets to specified indices if provided.

    Parameters
    ----------
    datasets : pandas.DataFrame
        Full dataset dataframe.
    only_indices : list of int or None
        Specific row indices to process, or None for all rows.

    Returns
    -------
    datasets : pandas.DataFrame
        Filtered dataset dataframe.
    """
    if only_indices:
        datasets = datasets.loc[np.in1d(range(len(datasets)), only_indices)]
    return datasets


def process_all_datasets(datasets, show_plots):
    """
    Process all datasets in the spreadsheet.

    Parameters
    ----------
    datasets : pandas.DataFrame
        Dataframe containing dataset information.
    show_plots : bool
        Whether to display plots of raw signals and spectrograms.
    """
    for ii, (idx, dataset) in enumerate(datasets.iterrows()):
        print(
            "{} ({}/{})".format(dataset["file_path_raw_signals"], ii + 1, len(datasets))
        )
        process_single_dataset(dataset, show_plots)

    if show_plots:
        plt.show()


def process_single_dataset(dataset, show_plots):
    """
    Process a single dataset row.

    Parameters
    ----------
    dataset : pandas.Series
        Single row from datasets dataframe containing file paths and parameters.
    show_plots : bool
        Whether to display plots for this dataset.
    """
    # determine edf signals to load
    signal_labels = [dataset[column_name] for column_name in state_annotation_signals]

    # load data
    raw_signals = load_raw_signals(dataset["file_path_raw_signals"], signal_labels)

    # preprocess all signals
    preprocessed_signals, time, frequencies = preprocess_signals(
        raw_signals, dataset["sampling_frequency_in_hz"], time_resolution
    )

    # show input and outputs for quality control
    if show_plots:
        display_plots(
            raw_signals,
            preprocessed_signals,
            time,
            frequencies,
            dataset["sampling_frequency_in_hz"],
        )

    # concatenate spectrograms into one set of features and save out
    concatenated_signals = np.concatenate(
        [signal.T for signal in preprocessed_signals], axis=1
    )
    export_preprocessed_signals(
        dataset["file_path_preprocessed_signals"], concatenated_signals
    )


def preprocess_signals(raw_signals, sampling_frequency, time_resolution):
    """
    Preprocess all signals for a dataset.

    Parameters
    ----------
    raw_signals : numpy.ndarray
        Raw signal data with shape (samples, channels).
    sampling_frequency : float
        Sampling frequency in Hz.
    time_resolution : int
        Time resolution in seconds.

    Returns
    -------
    preprocessed_signals : list of numpy.ndarray
        List of preprocessed spectrograms for each signal.
    time : numpy.ndarray
        Time vector for spectrograms.
    frequencies : numpy.ndarray
        Frequency vector for spectrograms.
    """
    preprocessed_signals = []
    time = None
    frequencies = None

    for signal in raw_signals.T:
        time, frequencies, preprocessed_signal = preprocess_single_signal(
            signal,
            sampling_frequency,
            time_resolution_in_sec=time_resolution,
            low_cut=1.0,
            high_cut=90.0,
            notch_low_cut=45.0,
            notch_high_cut=55.0,
        )
        preprocessed_signals.append(preprocessed_signal)

    return preprocessed_signals, time, frequencies


def display_plots(
    raw_signals, preprocessed_signals, time, frequencies, sampling_frequency
):
    """
    Display plots of raw signals and preprocessed spectrograms.

    Parameters
    ----------
    raw_signals : numpy.ndarray
        Raw signal data.
    preprocessed_signals : list of numpy.ndarray
        List of preprocessed spectrograms.
    time : numpy.ndarray
        Time vector for spectrograms.
    frequencies : numpy.ndarray
        Frequency vector for spectrograms.
    sampling_frequency : float
        Sampling frequency in Hz.
    """
    fig, axes = plt.subplots(1 + len(preprocessed_signals), 1, sharex=True)
    plot_raw_signals(
        raw_signals,
        sampling_frequency=sampling_frequency,
        ax=axes[0],
    )
    for signal, ax in zip(preprocessed_signals, axes[1:]):
        ax.imshow(
            signal,
            aspect="auto",
            origin="lower",
            extent=[time[0], time[-1], frequencies[0], frequencies[-1]],
        )
        ax.set_ylabel("Frequency")
    ax.set_xlabel("Time [seconds]")


def preprocess_single_signal(
    raw_signal,
    sampling_frequency_in_hz,
    time_resolution_in_sec=1,
    low_cut=1.0,
    high_cut=90.0,
    notch_low_cut=45.0,
    notch_high_cut=55.0,
):
    """
    Preprocess a single electrophysiological signal using spectrogram analysis.

    Wrapper around get_spectrogram that:
    1) computes the spectrogram for the given LFP/EEG/EMG trace,
    2) normalizes it such that the power in a given frequency band is
    approximately normally distributed, and
    3) excludes frequencies that are contaminated by noise using the equivalent
    of a notch filter.

    Parameters
    ----------
    raw_signal : numpy.ndarray, shape (total_samples,)
        The electrophysiological signal.
    sampling_frequency_in_hz : float
        The sampling frequency of `raw_signals`.
    time_resolution_in_sec : int, default 1
        The time resolution of the output array.
    low_cut : float, default 1.
        The minimum frequency for which to compute the power.
    high_cut : float, default 90.
        The maximum frequency for which to compute the power.
    notch_low_cut : float, default 45.
        The lower bound of frequency band to exclude (50 Hz noise filter).
    notch_high_cut : float, default 55.
        The upper bound of frequency band to exclude (50 Hz noise filter).

    Returns
    -------
    time : numpy.ndarray
        Time vector for the spectrogram.
    frequencies : numpy.ndarray
        Frequency vector for the spectrogram.
    preprocessed_signal : numpy.ndarray, shape (total_frequencies, total_time_points)
        The normalized spectrogram of the given signal.
    """
    # compute spectrogram
    frequencies, time, spectrogram = get_spectrogram(
        raw_signal,
        fs=sampling_frequency_in_hz,
        nperseg=sampling_frequency_in_hz * time_resolution_in_sec,
        noverlap=0,
    )

    # exclude ill-determined frequencies
    mask = (frequencies >= low_cut) & (frequencies < high_cut)
    frequencies = frequencies[mask]
    spectrogram = spectrogram[mask]

    # exclude noise-contaminated frequencies around 50 Hz;
    # this improves performance (generally, 0.1-0.5%, but 3% in at least one case)
    mask = (frequencies >= notch_low_cut) & (frequencies <= notch_high_cut)
    frequencies = frequencies[~mask]
    spectrogram = spectrogram[~mask]

    # the power in each frequency band tends to be log-normally distributed, and
    # taking the log hence transforms the distribution of power values to a normal distribution;
    # shift power values by +1 such that values close to zero remain close to zero
    # (and do not become large, negative values after log transformation)
    spectrogram = np.log(spectrogram + 1)

    # normalize the data by de-meaning and rescaling by the standard deviation
    spectrogram = robust_normalize(spectrogram, p=5.0, axis=1, method="standard score")

    return time, frequencies, spectrogram


def _validate_dependencies():
    """
    Validate that required modules are available.

    Raises
    ------
    RuntimeError
        If required modules are missing.
    """
    try:
        import _data_io
        import _configuration
        import somnotate._utils
    except ImportError as e:
        raise RuntimeError(f"Missing required module: {e}")


def _change_to_git_root():
    """
    Change working directory to git repository root.

    Raises
    ------
    RuntimeError
        If not in a git repository or git command fails.
    """
    try:
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.STDOUT
            )
            .decode("utf-8")
            .strip()
        )
        os.chdir(git_root)
    except subprocess.CalledProcessError:
        raise RuntimeError("Not in a git repository or git command failed")
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not available in PATH")


if __name__ == "__main__":
    main()
