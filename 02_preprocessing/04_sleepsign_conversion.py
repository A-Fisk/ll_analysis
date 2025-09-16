#!/usr/bin/env python

"""
Utilities to convert sleepsign output files.
"""

import os
import subprocess
import warnings
import numpy as np
from somnotate._utils import convert_state_vector_to_state_intervals

from data_io import (
    ArgumentParser,
    load_dataframe,
    check_dataframe,
    export_hypnogram,
)


def main():
    """
    Main function to convert sleepsign hypnogram files to standard format.
    
    Process:
    1. Setup environment (change to git root)
    2. Parse command line arguments
    3. Load and validate datasets from spreadsheet
    4. Filter datasets if --only parameter specified
    5. Process all conversions
    """
    setup_environment()
    
    args = parse_arguments()
    
    datasets = load_and_validate_datasets(args.spreadsheet_file_path)
    
    datasets = filter_datasets(datasets, args.only)
    
    process_all_conversions(datasets)


def setup_environment():
    """
    Setup the execution environment by changing to git repository root.
    """
    _change_to_git_root()


def parse_arguments():
    """
    Parse command line arguments for sleepsign conversion.
    
    Returns
    -------
    argparse.Namespace
        Parsed command line arguments containing spreadsheet_file_path and only parameters.
    """
    parser = ArgumentParser()
    parser.add_argument("spreadsheet_file_path", help="Use datasets specified in /path/to/spreadsheet.csv")
    parser.add_argument('--only',
                        nargs = '+',
                        type  = int,
                        help  = 'Indices corresponding to the rows to use (default: all). Indexing starts at zero.'
    )
    return parser.parse_args()


def load_and_validate_datasets(spreadsheet_file_path):
    """
    Load datasets from spreadsheet and validate required columns.
    
    Parameters
    ----------
    spreadsheet_file_path : str
        Path to the spreadsheet file containing dataset information.
        
    Returns
    -------
    pandas.DataFrame
        Validated dataframe containing dataset information.
    """
    datasets = load_dataframe(spreadsheet_file_path)
    
    check_dataframe(datasets,
                    columns = [
                        'file_path_sleepsign_state_annotation',
                        'file_path_manual_state_annotation',
                    ],
                    column_to_dtype = {
                        'file_path_sleepsign_state_annotation' : str,
                        'file_path_manual_state_annotation' : str,
                    }
    )
    
    return datasets


def filter_datasets(datasets, only_indices):
    """
    Filter datasets to only include specified row indices.
    
    Parameters
    ----------
    datasets : pandas.DataFrame
        Full dataset dataframe.
    only_indices : list of int or None
        List of row indices to include, or None to include all.
        
    Returns
    -------
    pandas.DataFrame
        Filtered dataset dataframe.
    """
    if only_indices:
        datasets = datasets.loc[np.in1d(range(len(datasets)), only_indices)]
    
    return datasets


def process_all_conversions(datasets):
    """
    Process all sleepsign to hypnogram conversions for the given datasets.
    
    Parameters
    ----------
    datasets : pandas.DataFrame
        Dataframe containing file paths for sleepsign and output files.
    """
    sleepsign_key = get_sleepsign_key_mapping()
    
    for ii, (idx, dataset) in enumerate(datasets.iterrows()):
        print("{} ({}/{})".format(dataset['file_path_sleepsign_state_annotation'], ii+1, len(datasets)))
        old_file_path = dataset['file_path_sleepsign_state_annotation']
        new_file_path = dataset['file_path_manual_state_annotation']
        convert_sleepsign_hypnogram(old_file_path, new_file_path, sleepsign_key)


def get_sleepsign_key_mapping():
    """
    Get the mapping dictionary for sleepsign state codes to readable names.
    
    Returns
    -------
    dict
        Dictionary mapping sleepsign codes to state names.
    """
    return dict([
        ('w'  , 'awake'),
        ('wa' , 'awake (artefact)'),
        ('ws' , 'awake (artefact)'),
        ('wb' , 'awake (artefact)'),
        ('w1' , 'awake (artefact)'),
        ('m'  , 'sleep movement'),
        ('nr' , 'non-REM'),
        ('na' , 'non-REM (artefact)'),
        ('nb' , 'non-REM (artefact)'),
        ('n1' , 'non-REM (artefact)'),
        ('r'  , 'REM'),
        ('ra' , 'REM (artefact)'),
        ('rb' , 'REM (artefact)'),
        ('r1' , 'REM (artefact)'),
        ('no' , 'undefined'),
    ])


def convert_sleepsign_hypnogram(old_file_path, new_file_path, sleepsign_key, epoch_duration=4):
    """
    Convert a sleepsign hypnogram file to standard hypnogram format.
    
    Parameters
    ----------
    old_file_path : str
        Path to the input sleepsign file.
    new_file_path : str
        Path for the output hypnogram file.
    sleepsign_key : dict
        Mapping dictionary for sleepsign state codes.
    epoch_duration : int, optional
        Duration of each epoch in seconds (default: 4).
    """
    states, intervals = load_sleepsign_hypnogram(old_file_path,
                                                 epoch_duration=epoch_duration,
                                                 mapping=sleepsign_key)
    export_hypnogram(new_file_path, states, intervals)


def load_sleepsign_hypnogram(file_path, epoch_duration=1, mapping=None, max_duration=86400, *args, **kwargs):
    """
    Load hypnogram given in sleepsign format.
    
    Parameters
    ----------
    file_path : str
        Path to the sleepsign hypnogram file.
    epoch_duration : int, optional
        Duration of each epoch in seconds (default: 1).
    mapping : dict, optional
        Dictionary to map sleepsign codes to readable names.
    max_duration : int, optional
        Maximum duration in seconds to include (default: 86400 for 24 hours).
    *args, **kwargs
        Additional arguments passed to np.genfromtxt.
        
    Returns
    -------
    tuple
        Tuple containing (states, intervals) lists.
    """
    lines = read_sleepsign_file(file_path)
    
    data = parse_sleepsign_data(lines, *args, **kwargs)
    
    epochs = extract_and_format_epochs(data)
    
    epochs = apply_state_mapping(epochs, mapping)
    
    epochs = crop_to_duration(epochs, epoch_duration, max_duration)
    
    states, intervals = convert_state_vector_to_state_intervals(epochs, epoch_duration)
    
    return states, intervals


def read_sleepsign_file(file_path):
    """
    Read sleepsign hypnogram file, handling multiple annotation sets.
    
    Sleepsign appends state annotations to an existing file instead of overwriting them.
    As a result, sleepsign hypnograms often contain one or more annotations.
    This function reads the file and returns the lines corresponding to the header
    and the last set of annotations.
    
    Parameters
    ----------
    file_path : str
        Path to the sleepsign hypnogram file.
        
    Returns
    -------
    list
        List of file lines containing header and last annotation set.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    empty_lines = [ii for ii, line in enumerate(lines) if line in ('\r\n', '\n')]

    if len(empty_lines) <= 2:  # only a linebreak at the end of the header and at the end of the file
        return lines
    else:
        warnings.warn("{} seems to contain multiple sets of annotations. Reading only the last set.".format(file_path))
        new_lines = lines[:empty_lines[0]] + lines[empty_lines[-2]:]
        return new_lines


def parse_sleepsign_data(lines, *args, **kwargs):
    """
    Parse sleepsign data from file lines into structured array.
    
    Parameters
    ----------
    lines : list
        List of file lines to parse.
    *args, **kwargs
        Additional arguments passed to np.genfromtxt.
        
    Returns
    -------
    numpy.ndarray
        Structured array containing EpochNo, Stage, and DateTime columns.
    """
    dtype = [('EpochNo', int),
             ('Stage', '|S2'),
             ('DateTime', '|S19')]

    data = np.genfromtxt(lines, usecols=(0, 1, 2), dtype=dtype, skip_header=19,
                        delimiter=',', *args, **kwargs)
    
    return data


def extract_and_format_epochs(data):
    """
    Extract and format epoch stages from parsed sleepsign data.
    
    Parameters
    ----------
    data : numpy.ndarray
        Structured array containing sleepsign data.
        
    Returns
    -------
    list
        List of epoch stage strings in lowercase format.
    """
    epochs = [state.astype(str).lower() for state in data['Stage']]
    return epochs


def apply_state_mapping(epochs, mapping):
    """
    Apply state mapping to convert sleepsign codes to readable names.
    
    Parameters
    ----------
    epochs : list
        List of epoch stage codes.
    mapping : dict or None
        Dictionary to map codes to readable names.
        
    Returns
    -------
    list
        List of mapped epoch stage names.
    """
    if mapping:
        epochs = [mapping[state] for state in epochs]
    
    return epochs


def crop_to_duration(epochs, epoch_duration, max_duration):
    """
    Crop epochs list to specified maximum duration.
    
    Parameters
    ----------
    epochs : list
        List of epoch stages.
    epoch_duration : int
        Duration of each epoch in seconds.
    max_duration : int or None
        Maximum duration in seconds to include.
        
    Returns
    -------
    list
        Cropped list of epochs.
    """
    if max_duration:
        max_epochs = int(max_duration // epoch_duration)
        epochs = epochs[:max_epochs]  # Crop to the specified duration
    
    return epochs


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


if __name__ == '__main__':
    main()
