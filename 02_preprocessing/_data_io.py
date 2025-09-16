#!/usr/bin/env python

"""
Data I/O utilities for EEG/sleep study data files.

This module provides functions for loading and saving various data formats
used in sleep analysis pipelines, including EDF files, hypnograms, and
review intervals.
"""

import os
import subprocess
import numpy as np
import pandas

from argparse import ArgumentParser
try:
    # python < 3.3
    from collections import Iterable
except ImportError:
    # python >= 3.3
    from collections.abc import Iterable
from pyedflib import EdfReader
from six import ensure_str

from somnotate._utils import convert_state_intervals_to_state_vector


def main():
    """
    Main function for data I/O operations.
    
    This is a utility module - main function is not typically called directly.
    Individual functions should be imported and used as needed.
    """
    setup_environment()
    print("Data I/O utilities loaded successfully")


def setup_environment():
    """
    Setup the execution environment by changing to git repository root.
    """
    _change_to_git_root()


def check_dataframe(df, columns, column_to_dtype=None):
    """
    Test if a pandas dataframe has certain columns and correct data types.

    Parameters
    ----------
    df : pandas.DataFrame
        The imported spreadsheet to validate.
    columns : list of str
        The columns whose existence should be checked.
    column_to_dtype : dict str : type, optional
        The expected type of a given column.
        Not all values in `columns` have to be present in `column_to_dtype`.

    Raises
    ------
    Exception
        If required columns are missing or have wrong data types.
    """
    missing_columns = validate_required_columns(df, columns)
    
    if missing_columns:
        raise_missing_columns_error(missing_columns)
    
    if column_to_dtype:
        wrong_types = validate_column_types(df, column_to_dtype)
        if wrong_types:
            raise_wrong_types_error(wrong_types)


def validate_required_columns(df, columns):
    """
    Check if required columns exist in dataframe.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to check.
    columns : list of str
        Required column names.
        
    Returns
    -------
    list of str
        List of missing column names.
    """
    not_present = []
    for column in columns:
        if not (column in df.columns):
            not_present.append(column)
    return not_present


def validate_column_types(df, column_to_dtype):
    """
    Check if columns have correct data types.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to check.
    column_to_dtype : dict str : type
        Expected data types for columns.
        
    Returns
    -------
    list of tuple
        List of (column, actual_dtype, expected_dtype) for wrong types.
    """
    wrong_types = []
    for column, expected_dtype in column_to_dtype.items():
        # pandas encodes all strings as objects,
        # which is not very helpful for type checking;
        # here we set the actual dtype to str, if the object is string-like.
        if pandas.api.types.is_string_dtype(df[column]):
            actual_dtype = str
        else:
            actual_dtype = df[column].dtype
            
        if isinstance(expected_dtype, type):
            if not actual_dtype == expected_dtype:
                wrong_types.append((column, actual_dtype, expected_dtype))
        elif isinstance(expected_dtype, Iterable):
            if not actual_dtype in expected_dtype:
                wrong_types.append((column, actual_dtype, expected_dtype))
        else:
            type_error_msg = "Values in column_to_dtype have to be either instances of type or an iterable thereof. Currently:"
            type_error_msg += "\ntype(column_to_dtype[{}] = {})".format(column, type(expected_dtype))
            raise TypeError(type_error_msg)
    
    return wrong_types


def raise_missing_columns_error(missing_columns):
    """
    Raise error for missing columns.
    
    Parameters
    ----------
    missing_columns : list of str
        List of missing column names.
        
    Raises
    ------
    Exception
        Error message listing missing columns.
    """
    error_msg = "The provided spreadsheet misses the following columns:"
    for column in missing_columns:
        error_msg += "\n{}".format(column)
    raise Exception(error_msg)


def raise_wrong_types_error(wrong_types):
    """
    Raise error for wrong column types.
    
    Parameters
    ----------
    wrong_types : list of tuple
        List of (column, actual_dtype, expected_dtype) tuples.
        
    Raises
    ------
    Exception
        Error message listing columns with wrong types.
    """
    error_msg = "The following columns have the wrong data type:"
    for entry in wrong_types:
        error_msg += "\n{}: dtype is {} but should be {};".format(*entry)
    raise Exception(error_msg)


def load_raw_signals(file_path, signal_labels=None):
    """
    Load LFP/EEG/EMG traces from EDF files and return a numpy array.
    
    Currently, only loading of signals with the same sampling frequency 
    and number of samples is supported.

    Parameters
    ----------
    file_path : str
        Path to the EDF file.
    signal_labels : list of str or None, optional
        Labels of the signals to load. If None, all signals are loaded.

    Returns
    -------
    signals : (total samples, total signals) ndarray
        The signals concatenated into a single numpy array.
    """
    pathlib_object = _get_pathlib_object(file_path)
    return _load_edf_file(pathlib_object, signal_labels)


def load_state_vector(file_path, mapping, time_resolution=1):
    """
    Load hypnogram and convert to a state vector.

    Parameters
    ----------
    file_path : str
        Path to the hypnogram file.
    mapping : dict str : int or None
        Mapping of state representations in the hypnogram to integers.
        If None, states returned by `get_hypnogram` must already be integers.
    time_resolution : int, optional
        Time resolution in seconds (default: 1).

    Returns
    -------
    state_vector : (total samples, ) ndarray of int
        The state vector.

    References
    ----------
    http://visbrain.org/sleep.html#save-hypnogram
    """
    states, intervals = load_hypnogram(file_path)

    state_vector = convert_state_intervals_to_state_vector(
        states, intervals, mapping=mapping, time_resolution=time_resolution)

    return state_vector


def load_hypnogram(file_path):
    """
    Load hypnogram given in visbrain Stage-duration format.

    Parameters
    ----------
    file_path : str
        Path to the hypnogram file.

    Returns
    -------
    states : list of str
        List of annotated states.
    intervals : list of (float start, float stop) tuples
        Corresponding time intervals.

    References
    ----------
    http://visbrain.org/sleep.html#save-hypnogram
    """
    pathlib_object = _get_pathlib_object(file_path)
    return _load_visbrain_hypnogram(pathlib_object)


def export_hypnogram(file_path, states, intervals, total_time=None, data_file=None):
    """
    Export hypnogram to visbrain Stage-duration format.

    Parameters
    ----------
    file_path : str
        Path to output hypnogram file.
    states : list of str
        List of annotated states.
    intervals : list of (float start, float stop) tuples
        Corresponding time intervals.
    total_time : int or None, optional
        Total time covered by the annotation.
        If None, the maximum of `intervals` is used instead.
    data_file : str or None, optional
        Path to corresponding data file or just filename.
        Optional reference to the corresponding data file.

    References
    ----------
    http://visbrain.org/sleep.html#save-hypnogram
    """
    pathlib_object = _get_pathlib_object(file_path)
    _export_visbrain_hypnogram(pathlib_object, states, intervals, total_time, data_file)


def export_review_intervals(file_path, intervals, scores=None, notes=None):
    """
    Export review intervals to CSV format.
    
    Parameters
    ----------
    file_path : str
        Path to output CSV file.
    intervals : list of (float start, float stop) tuples
        Time intervals to export.
    scores : list, optional
        Scores corresponding to each interval.
    notes : list, optional
        Notes corresponding to each interval.
    """
    pathlib_object = _get_pathlib_object(file_path)
    _export_review_intervals(pathlib_object, intervals, scores, notes)


def load_review_intervals(file_path):
    """
    Load review intervals from CSV file.
    
    Parameters
    ----------
    file_path : str
        Path to CSV file containing review intervals.
        
    Returns
    -------
    intervals : ndarray
        Array of (start, stop) time intervals.
    scores : ndarray
        Array of scores corresponding to intervals.
    """
    pathlib_object = _get_pathlib_object(file_path)
    return _load_review_intervals(pathlib_object)


def load_dataframe(file_path):
    """
    Load dataframe from CSV file.
    
    Parameters
    ----------
    file_path : str
        Path to CSV file.
        
    Returns
    -------
    pandas.DataFrame
        Loaded dataframe.
    """
    return pandas.read_csv(file_path)


def load_preprocessed_signals(file_path):
    """
    Load preprocessed signals from numpy file.
    
    Parameters
    ----------
    file_path : str
        Path to numpy file.
        
    Returns
    -------
    ndarray
        Loaded signal array.
    """
    return np.load(file_path)


def export_preprocessed_signals(file_path, signals):
    """
    Export preprocessed signals to numpy file.
    
    Parameters
    ----------
    file_path : str
        Path to output numpy file.
    signals : ndarray
        Signal array to save.
    """
    np.save(file_path, signals)


def _get_pathlib_object(file_path):
    """
    Convert file path to pathlib object (placeholder for future enhancement).
    
    Parameters
    ----------
    file_path : str
        File path to convert.
        
    Returns
    -------
    str
        Currently returns the same file path.
    """
    return file_path


def _load_edf_file(file_path, signal_labels=None):
    """
    Load EDF file and return signals as numpy array.

    Parameters
    ----------
    file_path : str
        Path to EDF file.
    signal_labels : list of str or None, optional
        Labels of the signals to load. If None, all signals are loaded.

    Returns
    -------
    signals : (total samples, total signals) ndarray
        The signals concatenated into a single numpy array.
    """
    with EdfReader(file_path) as reader:
        if signal_labels is None:
            signal_labels = reader.getSignalLabels()
        signals = _load_edf_channels(signal_labels, reader)
    return signals


def _load_edf_channels(signal_labels, edf_reader):
    """
    Load specific channels from EDF reader.
    
    Parameters
    ----------
    signal_labels : list of str
        Labels of signals to load.
    edf_reader : EdfReader
        Open EDF reader object.
        
    Returns
    -------
    ndarray
        Array of loaded signals with shape (samples, channels).
    """
    indices = find_signal_indices(signal_labels, edf_reader)
    
    validate_signal_recovery(indices, signal_labels, edf_reader)
    
    total_samples = validate_signal_lengths(indices, edf_reader)
    
    output_array = load_signal_data(indices, total_samples, edf_reader)
    
    return output_array.transpose()


def find_signal_indices(signal_labels, edf_reader):
    """
    Find indices of requested signals in EDF file.
    
    Parameters
    ----------
    signal_labels : list of str
        Labels of signals to find.
    edf_reader : EdfReader
        Open EDF reader object.
        
    Returns
    -------
    list of int
        Indices of found signals.
    """
    indices = [idx for idx in range(edf_reader.signals_in_file) 
               if ensure_str(edf_reader.signal_label(idx)).strip() in signal_labels]
    return indices


def validate_signal_recovery(indices, signal_labels, edf_reader):
    """
    Validate that all requested signals were found.
    
    Parameters
    ----------
    indices : list of int
        Found signal indices.
    signal_labels : list of str
        Requested signal labels.
    edf_reader : EdfReader
        Open EDF reader object.
        
    Raises
    ------
    Exception
        If not all requested signals were found.
    """
    if len(indices) != len(signal_labels):
        error_msg = "Could not recover all given signals. Attempted to retrieve the following signals:\n"
        for label in signal_labels:
            error_msg += "- {}\n".format(label)
        error_msg += "However, the only signals present in the file are:\n"
        for label in edf_reader.getSignalLabels():
            error_msg += "- {}\n".format(label)
        raise Exception(error_msg)


def validate_signal_lengths(indices, edf_reader):
    """
    Validate that all signals have the same length.
    
    Parameters
    ----------
    indices : list of int
        Signal indices to check.
    edf_reader : EdfReader
        Open EDF reader object.
        
    Returns
    -------
    int
        Total number of samples (validated to be same for all signals).
        
    Raises
    ------
    AssertionError
        If signals have different lengths.
    """
    total_samples = [edf_reader.samples_in_file(idx) for idx in indices]
    assert len(set(total_samples)) == 1, "All signals need to have the same length! Lengths of selected signals: {}".format(total_samples)
    total_samples, = set(total_samples)
    return total_samples


def load_signal_data(indices, total_samples, edf_reader):
    """
    Load signal data from EDF file.
    
    Parameters
    ----------
    indices : list of int
        Signal indices to load.
    total_samples : int
        Number of samples to load.
    edf_reader : EdfReader
        Open EDF reader object.
        
    Returns
    -------
    ndarray
        Array of loaded signals with shape (channels, samples).
    """
    output_array = np.zeros((len(indices), total_samples), dtype=np.int32)
    for jj, idx in enumerate(indices):
        edf_reader.read_digital_signal(idx, 0, total_samples, output_array[jj])
    return output_array


def _load_visbrain_hypnogram(file_path):
    """
    Load hypnogram given in visbrain Stage-duration format.

    Parameters
    ----------
    file_path : str
        Path to hypnogram file.

    Returns
    -------
    states : list of str
        List of annotated states.
    intervals : list of (float start, float stop) tuples
        Corresponding time intervals.

    References
    ----------
    http://visbrain.org/sleep.html#save-hypnogram
    """
    dtype = [('Stage', '|S30'), ('stop', float)]
    data = np.genfromtxt(file_path, skip_header=2, dtype=dtype, delimiter='\t')
    states = [state.astype(str).strip() for state in data['Stage']]
    transitions = np.r_[0, data['stop']]
    intervals = list(zip(transitions[:-1], transitions[1:]))
    return states, intervals


def _export_visbrain_hypnogram(file_path, states, intervals, total_time=None, data_file=None):
    """
    Export hypnogram to visbrain Stage-duration format.

    Parameters
    ----------
    file_path : str
        Path to output hypnogram file.
    states : list of str
        List of annotated states.
    intervals : list of (float start, float stop) tuples
        Corresponding time intervals.
    total_time : int or None, optional
        Total time covered by the annotation.
        If None, the maximum of `intervals` is used instead.
    data_file : str or None, optional
        Path to corresponding data file or just filename.

    References
    ----------
    http://visbrain.org/sleep.html#save-hypnogram
    """
    export_string = create_hypnogram_header(intervals, total_time, data_file)
    
    export_string += create_hypnogram_body(states, intervals)
    
    write_hypnogram_file(file_path, export_string)


def create_hypnogram_header(intervals, total_time, data_file):
    """
    Create header section for visbrain hypnogram export.
    
    Parameters
    ----------
    intervals : list of (float start, float stop) tuples
        Time intervals.
    total_time : int or None
        Total time covered by annotation.
    data_file : str or None
        Path to corresponding data file.
        
    Returns
    -------
    str
        Header string for hypnogram file.
    """
    export_string = ""
    
    if total_time:
        export_string += "*Duration_sec\t{:.1f}\n".format(total_time)
    else:
        export_string += "*Duration_sec\t{:.1f}\n".format(np.max(intervals))

    if data_file:
        export_string += "*Datafile\t{}\n".format(data_file)
    else:
        export_string += "*Datafile\tUnspecified\n"
        
    return export_string


def create_hypnogram_body(states, intervals):
    """
    Create body section for visbrain hypnogram export.
    
    Parameters
    ----------
    states : list of str
        List of annotated states.
    intervals : list of (float start, float stop) tuples
        Corresponding time intervals.
        
    Returns
    -------
    str
        Body string for hypnogram file.
    """
    # determine the length of the longest state label
    unique_states = set(states)
    string_length = max([len(s) for s in unique_states])

    # sort by interval start
    intervals = np.array(intervals)
    order = np.argsort(intervals[:, 0])
    intervals = intervals[order]
    states = [states[ii] for ii in order]

    # assert that no two intervals overlap
    assert not np.any(intervals[:-1, 1] > intervals[1:, 0]), "The hypnogram format does not support overlapping intervals!"

    # assert that there are no un-annotated gaps between intervals
    assert np.all(intervals[:-1, 1] == intervals[1:, 0]), "The hypnogram format does not support having un-annotated time intervals!"

    export_string = "".join(["{:{}}\t{:.1f}\n".format(state, string_length, stop) \
                              for state, (start, stop) in zip(states, intervals)])
    
    return export_string


def write_hypnogram_file(file_path, export_string):
    """
    Write hypnogram string to file.
    
    Parameters
    ----------
    file_path : str
        Path to output file.
    export_string : str
        Content to write to file.
    """
    with open(file_path, 'w') as f:
        f.write(export_string)


def _export_review_intervals(file_path, intervals, scores=None, notes=None):
    """
    Export review intervals to CSV file.
    
    Parameters
    ----------
    file_path : str
        Path to output CSV file.
    intervals : list of (float start, float stop) tuples
        Time intervals to export.
    scores : list, optional
        Scores corresponding to each interval.
    notes : list, optional
        Notes corresponding to each interval.
    """
    data = dict()

    data['start'] = [start for start, stop in intervals]
    data['stop'] = [stop for start, stop in intervals]

    if not (scores is None):
        data['score'] = scores

    if not (notes is None):
        data['note'] = notes

    df = pandas.DataFrame.from_dict(data)
    df.to_csv(file_path)


def _load_review_intervals(file_path):
    """
    Load review intervals from CSV file.
    
    Parameters
    ----------
    file_path : str
        Path to CSV file.
        
    Returns
    -------
    intervals : ndarray
        Array of (start, stop) time intervals.
    scores : ndarray
        Array of scores corresponding to intervals.
    """
    df = pandas.read_csv(file_path)
    intervals = np.c_[df['start'].values, df['stop'].values]
    scores = df['score'].values
    return intervals, scores


def _change_to_git_root():
    """
    Change working directory to git repository root.
    
    Uses git rev-parse --show-toplevel to find the repository root directory
    and changes the current working directory to that location.
    
    Raises
    ------
    SystemExit
        If git is not available or current directory is not in a git repository.
    """
    try:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                         stderr=subprocess.STDOUT).decode('utf-8').strip()
        os.chdir(git_root)
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository or git not available")
        exit(1)
    except FileNotFoundError:
        print("Error: git command not found")
        exit(1)


if __name__ == "__main__":
    main()
