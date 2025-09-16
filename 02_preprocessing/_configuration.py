#!/usr/bin/env python

"""
User defined variables and functions that are used across all scripts.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import sosfilt, iirfilter
from functools import partial
from somnotate._plotting import plot_signals, plot_states
from somnotate._utils import pad_along_axis, remove_padding_along_axis

def main():
    """
    Main function to setup configuration and apply matplotlib settings.
    
    Returns
    -------
    dict
        Configuration dictionary containing all settings and functions.
    """
    # Setup signal configuration
    signal_config = setup_signal_configuration()
    
    # Setup state configuration  
    state_config = setup_state_configuration()
    
    # Setup plotting functions
    plotting_config = setup_plotting_configuration(signal_config, state_config)
    
    # Apply matplotlib settings
    apply_matplotlib_settings()
    
    # Return complete configuration
    return {**signal_config, **state_config, **plotting_config}

def setup_signal_configuration():
    """
    Setup signal processing configuration parameters.
    
    Returns
    -------
    dict
        Dictionary containing signal configuration parameters.
    """
    return {
        'state_annotation_signals': [
            'frontal_eeg_signal_label',
            'occipital_eeg_signal_label', 
            'emg_signal_label',
        ],
        'state_annotation_signal_labels': [
            'frontal EEG',
            'occipital EEG',
            'EMG'
        ],
        'state_annotation_signal_frequency_bands': [
            (0.5, 30.),  # Frontal EEG
            (0.5, 30.),  # Occipital EEG
            (10., 45.),  # EMG
        ],
        'time_resolution': 1,
    }

def setup_state_configuration():
    """
    Setup state mapping and display configuration.
    
    Returns
    -------
    dict
        Dictionary containing state configuration parameters.
    """
    state_to_int = {
        'awake': 1,
        'awake (artefact)': -1,
        'sleep movement': 1,
        'non-REM': 2,
        'non-REM (artefact)': -2,
        'REM': 3,
        'REM (artefact)': -3,
        'undefined': 0,
    }
    
    int_to_state = {ii: state for state, ii in state_to_int.items() if state != 'sleep movement'}
    
    keymap = {
        'w': 'awake', 'W': 'awake (artefact)',
        'n': 'non-REM', 'N': 'non-REM (artefact)',
        'r': 'REM', 'R': 'REM (artefact)',
        'x': 'undefined', 'X': 'undefined (artefact)',
        'm': 'sleep movement', 'M': 'sleep movement (artefact)',
    }
    
    state_to_color = {
        'awake': 'crimson', 'awake (artefact)': 'coral',
        'sleep movement': 'violet', 'non-REM': 'blue',
        'non-REM (artefact)': 'cornflowerblue', 'REM': 'gold',
        'REM (artefact)': 'yellow', 'undefined': 'gray',
        'undefined (artefact)': 'lightgray',
    }
    
    state_display_order = [
        'awake', 'awake (artefact)', 'non-REM', 'non-REM (artefact)',
        'REM', 'REM (artefact)', 'sleep movement', 'sleep movement (artefact)',
        'undefined', 'undefined (artefact)',
    ]
    
    return {
        'state_to_int': state_to_int,
        'int_to_state': int_to_state,
        'keymap': keymap,
        'state_to_color': state_to_color,
        'state_display_order': state_display_order,
        'default_view_length': 60.,
        'default_selection_length': 4.,
    }

def setup_plotting_configuration(signal_config, state_config):
    """
    Setup plotting functions with partial application of parameters.
    
    Parameters
    ----------
    signal_config : dict
        Signal configuration parameters.
    state_config : dict
        State configuration parameters.
        
    Returns
    -------
    dict
        Dictionary containing configured plotting functions.
    """
    plot_raw_signals_configured = partial(
        plot_raw_signals,
        frequency_bands=signal_config['state_annotation_signal_frequency_bands'],
        signal_labels=signal_config['state_annotation_signal_labels']
    )
    
    plot_states_configured = partial(
        plot_states,
        unique_states=state_config['state_display_order'],
        state_to_color=state_config['state_to_color'],
        mode='lines'
    )
    
    return {
        'plot_raw_signals': plot_raw_signals_configured,
        'plot_states': plot_states_configured,
    }

def apply_matplotlib_settings():
    """Apply matplotlib configuration settings."""
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['ytick.labelsize'] = 'medium'
    plt.rcParams['xtick.labelsize'] = 'medium'
    plt.rcParams['axes.labelsize'] = 'medium'

def plot_raw_signals(raw_signals, frequency_bands, sampling_frequency, *args, **kwargs):
    """
    Thin wrapper around `plot_signals` that applies a Chebychev bandpass filter.

    Parameters
    ----------
    raw_signals : ndarray, shape (total_samples, total_signals)
        The signals to plot.
    frequency_bands : list of tuple
        The frequency bands to use in the bandpass filter for each signal.
    sampling_frequency : float
        The sampling frequency of the signals.
    *args, **kwargs
        Passed through to plot_signals.

    Returns
    -------
    ax : matplotlib.axes._subplots.AxesSubplot
        The axis plotted onto.
    """
    filtered = np.zeros_like(raw_signals)
    for ii, signal in enumerate(raw_signals.T):
        lowcut, highcut = frequency_bands[ii]
        filtered[:, ii] = chebychev_bandpass_filter(
            signal, lowcut=lowcut, highcut=highcut, fs=sampling_frequency
        )

    return plot_signals(filtered, sampling_frequency=sampling_frequency, *args, **kwargs)

def chebychev_bandpass_filter(data, lowcut, highcut, fs, rs=60, order=5, axis=-1):
    """
    Apply band pass filter with specified low and high cutoffs to data.

    Parameters
    ----------
    data : ndarray
        Input signal data.
    lowcut : float
        Low frequency cutoff.
    highcut : float
        High frequency cutoff.
    fs : float
        Sampling frequency.
    rs : float, optional
        Minimum attenuation in stop band (default: 60).
    order : int, optional
        Filter order (default: 5).
    axis : int, optional
        Axis along which to apply filter (default: -1).

    Returns
    -------
    ndarray
        Filtered signal data.
    """
    chebychev = _chebychev_bandpass(lowcut, highcut, rs=rs, fs=fs, order=order)
    
    pad_length = int(float(fs) / lowcut)
    padded = pad_along_axis(data, before=pad_length, after=pad_length, 
                           axis=axis, mode='reflect')
    
    filtered = sosfilt(chebychev, padded, axis=axis)
    
    return remove_padding_along_axis(filtered, before=pad_length, 
                                   after=pad_length, axis=axis)

def _chebychev_bandpass(lowcut, highcut, fs, rs, order=5):
    """Create Chebyshev bandpass filter."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return iirfilter(order, [low, high], rs=rs, btype='band',
                    analog=False, ftype='cheby2', output='sos')

if __name__ == "__main__":
    config = main()
