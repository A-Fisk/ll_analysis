import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import sys
import os

# Add the project root to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fft_create", 
    os.path.join(os.path.dirname(__file__), '..', '02_preprocessing',
                 '03_fft_create.py')
)
fft_autoscore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fft_autoscore)

# Import functions from the module
setup_parameters = fft_autoscore.setup_parameters
setup_directories = fft_autoscore.setup_directories
discover_edf_files = fft_autoscore.discover_edf_files
read_edf_signals = fft_autoscore.read_edf_signals
process_all_channels = fft_autoscore.process_all_channels
process_single_channel = fft_autoscore.process_single_channel
perform_fft_analysis = fft_autoscore.perform_fft_analysis
save_results_to_csv = fft_autoscore.save_results_to_csv


class TestFFTProcessing:
    """Test suite for FFT processing functions."""
    
    @pytest.fixture
    def sample_parameters(self):
        """Fixture providing sample FFT parameters."""
        return {
            'sampling_rate': 256,
            'window_length': 4,
            'freq_bin_size': 0.25,
            'freq_limit': 20,
            'window_samples': 1024,
            'channel_name_mapping': {0: "fro", 1: "occ", 2: "foc"}
        }
    
    @pytest.fixture
    def temp_directory(self):
        """Fixture providing a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_setup_parameters(self):
        """Test that setup_parameters returns correct parameter dictionary."""
        params = setup_parameters()
        
        # Test required parameters exist
        assert 'sampling_rate' in params
        assert 'window_length' in params
        assert 'freq_bin_size' in params
        assert 'freq_limit' in params
        assert 'channel_name_mapping' in params
        assert 'window_samples' in params
        
        # Test parameter values
        assert params['sampling_rate'] == 256
        assert params['window_length'] == 4
        assert params['freq_bin_size'] == 0.25
        assert params['freq_limit'] == 20
        assert params['window_samples'] == 1024  # 4 * 256
        
        # Test channel mapping
        assert params['channel_name_mapping'][0] == "fro"
        assert params['channel_name_mapping'][1] == "occ"
        assert params['channel_name_mapping'][2] == "foc"
    
    @patch('fft_autoscore.Path')
    def test_setup_directories(self, mock_path):
        """Test directory setup and creation."""
        mock_input_dir = MagicMock()
        mock_output_dir = MagicMock()
        mock_path.side_effect = [mock_input_dir, mock_output_dir]
        
        input_dir, output_dir = setup_directories()
        
        # Verify paths were created correctly
        mock_path.assert_any_call("01_data_files/02_edf_cropped")
        mock_path.assert_any_call("01_data_files/06_fft_files")
        
        # Verify output directory creation was called
        mock_output_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        assert input_dir == mock_input_dir
        assert output_dir == mock_output_dir
    
    def test_discover_edf_files_with_files(self, temp_directory):
        """Test EDF file discovery with existing files."""
        # Create test EDF files
        edf_files = ["test1.edf", "test2.edf", "test3.edf"]
        for filename in edf_files:
            (temp_directory / filename).touch()
        
        # Create non-EDF files (should be ignored)
        (temp_directory / "test.txt").touch()
        (temp_directory / "test.csv").touch()
        
        result = discover_edf_files(temp_directory)
        
        assert len(result) == 3
        assert all(file.suffix == ".edf" for file in result)
        assert all(file.name in edf_files for file in result)
    
    def test_discover_edf_files_empty_directory(self, temp_directory):
        """Test EDF file discovery with empty directory."""
        result = discover_edf_files(temp_directory)
        assert len(result) == 0
        assert isinstance(result, list)
    
    @patch('fft_autoscore.pyedflib.EdfReader')
    def test_read_edf_signals_three_channels(self, mock_edf_reader, sample_parameters):
        """Test reading EDF signals with three channels."""
        # Mock EDF reader
        mock_reader = MagicMock()
        mock_reader.signals_in_file = 3
        mock_reader.readSignal.side_effect = [
            np.random.randn(1000),  # Channel 0
            np.random.randn(1000),  # Channel 1
            np.random.randn(1000)   # Channel 2
        ]
        mock_edf_reader.return_value.__enter__.return_value = mock_reader
        
        result = read_edf_signals(Path("test.edf"), sample_parameters)
        
        assert len(result) == 3
        assert all(len(signal_data) == 2 for signal_data in result)
        assert all(isinstance(signal_data[0], int) for signal_data in result)
        assert all(isinstance(signal_data[1], np.ndarray) for signal_data in result)
        
        # Verify channel indices
        channel_indices = [signal_data[0] for signal_data in result]
        assert channel_indices == [0, 1, 2]
    
    @patch('fft_autoscore.pyedflib.EdfReader')
    def test_read_edf_signals_more_than_three_channels(self, mock_edf_reader, sample_parameters):
        """Test reading EDF signals with more than three channels (should limit to 3)."""
        # Mock EDF reader with 5 channels
        mock_reader = MagicMock()
        mock_reader.signals_in_file = 5
        mock_reader.readSignal.side_effect = [
            np.random.randn(1000),  # Channel 0
            np.random.randn(1000),  # Channel 1
            np.random.randn(1000)   # Channel 2
        ]
        mock_edf_reader.return_value.__enter__.return_value = mock_reader
        
        result = read_edf_signals(Path("test.edf"), sample_parameters)
        
        # Should only process first 3 channels
        assert len(result) == 3
        assert mock_reader.readSignal.call_count == 3
    
    def test_process_single_channel(self, sample_parameters):
        """Test processing a single channel's signal data."""
        # Create test signal (4 complete windows)
        signal = np.random.randn(4096)  # 4 * 1024 samples
        channel_index = 0
        
        result = process_single_channel(signal, channel_index, sample_parameters)
        
        # Should have 4 windows * 81 frequency bins = 324 records
        num_bins = int(sample_parameters['freq_limit'] / sample_parameters['freq_bin_size']) + 1
        expected_records = 4 * num_bins
        assert len(result) == expected_records
        
        # Check data structure
        assert all('Channel' in record for record in result)
        assert all('Frequency (Hz)' in record for record in result)
        assert all('Magnitude' in record for record in result)
        assert all('Window' in record for record in result)
        
        # Check channel mapping
        assert all(record['Channel'] == 'fro' for record in result)
        
        # Check window numbers
        window_numbers = set(record['Window'] for record in result)
        assert window_numbers == {1, 2, 3, 4}
    
    def test_process_single_channel_unknown_channel(self, sample_parameters):
        """Test processing with unknown channel index."""
        signal = np.random.randn(1024)  # 1 window
        channel_index = 5  # Unknown channel
        
        result = process_single_channel(signal, channel_index, sample_parameters)
        
        # Should use default channel name
        assert all(record['Channel'] == 'Channel 5' for record in result)
    
    def test_perform_fft_analysis_sine_wave(self, sample_parameters):
        """Test FFT analysis with a known sine wave signal."""
        # Create a 10 Hz sine wave
        t = np.linspace(0, 4, 1024, endpoint=False)
        signal = np.sin(2 * np.pi * 10 * t)
        
        result = perform_fft_analysis(signal, sample_parameters)
        
        # Check result shape
        expected_bins = int(sample_parameters['freq_limit'] / sample_parameters['freq_bin_size']) + 1
        assert len(result) == expected_bins
        
        # Check that peak is around 10 Hz bin (10/0.25 = 40th bin)
        peak_bin = np.argmax(result)
        expected_bin = int(10 / sample_parameters['freq_bin_size'])
        assert abs(peak_bin - expected_bin) <= 1
        
        # Check that the peak is significantly higher than DC component
        assert result[peak_bin] > result[0] * 2
    
    def test_perform_fft_analysis_dc_signal(self, sample_parameters):
        """Test FFT analysis with DC (constant) signal."""
        # Create a constant signal
        signal = np.ones(1024) * 5.0
        
        result = perform_fft_analysis(signal, sample_parameters)
        
        # DC component (bin 0) should be highest
        peak_bin = np.argmax(result)
        assert peak_bin == 0
        
        # DC magnitude should be much higher than other frequencies
        assert result[0] > result[1:].max() * 10
    
    def test_process_all_channels(self, sample_parameters):
        """Test processing multiple channels."""
        # Create test signals for 3 channels
        signals_data = [
            (0, np.random.randn(2048)),  # 2 windows each
            (1, np.random.randn(2048)),
            (2, np.random.randn(2048))
        ]
        
        result = process_all_channels(signals_data, sample_parameters)
        
        # Should have results from all 3 channels
        channels = set(record['Channel'] for record in result)
        assert channels == {'fro', 'occ', 'foc'}
        
        # Each channel should have 2 windows worth of data
        num_bins = int(sample_parameters['freq_limit'] / sample_parameters['freq_bin_size']) + 1
        expected_total_records = 3 * 2 * num_bins  # 3 channels * 2 windows * bins
        assert len(result) == expected_total_records
    
    def test_save_results_to_csv(self, temp_directory):
        """Test saving results to CSV file."""
        # Create sample results
        all_results = [
            {'Channel': 'fro', 'Frequency (Hz)': 0.0, 'Magnitude': 10.0, 'Window': 1},
            {'Channel': 'fro', 'Frequency (Hz)': 0.25, 'Magnitude': 5.0, 'Window': 1},
            {'Channel': 'occ', 'Frequency (Hz)': 0.0, 'Magnitude': 8.0, 'Window': 1},
            {'Channel': 'occ', 'Frequency (Hz)': 0.25, 'Magnitude': 3.0, 'Window': 1}
        ]
        
        edf_file_path = Path("test_file.edf")
        
        save_results_to_csv(all_results, edf_file_path, temp_directory)
        
        # Check file was created
        output_file = temp_directory / "test_file.csv"
        assert output_file.exists()
        
        # Verify CSV content
        df = pd.read_csv(output_file, index_col=[0, 1])
        assert df.shape[0] == 2  # 2 channels
        assert 0.0 in df.columns
        assert 0.25 in df.columns
        
        # Check values
        assert df.loc[('fro', 1), 0.0] == 10.0
        assert df.loc[('occ', 1), 0.25] == 3.0


class TestIntegration:
    """Integration tests for the complete FFT processing pipeline."""
    
    @pytest.fixture
    def temp_directory(self):
        """Fixture providing a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_parameters(self):
        """Fixture providing sample FFT parameters."""
        return {
            'sampling_rate': 256,
            'window_length': 4,
            'freq_bin_size': 0.25,
            'freq_limit': 20,
            'window_samples': 1024,
            'channel_name_mapping': {0: "fro", 1: "occ", 2: "foc"}
        }
    
    @patch('fft_autoscore.read_edf_signals')
    def test_full_pipeline_integration(self, mock_read_signals, temp_directory, sample_parameters):
        """Test the complete pipeline with mocked EDF data."""
        # Create mock EDF files
        edf_files = [temp_directory / "test1.edf", temp_directory / "test2.edf"]
        for edf_file in edf_files:
            edf_file.touch()
        
        # Mock the EDF reading to return synthetic data
        mock_read_signals.return_value = [
            (0, np.random.randn(2048)),  # 2 windows of data
            (1, np.random.randn(2048))
        ]
        
        # Test discover_edf_files
        files = discover_edf_files(temp_directory)
        assert len(files) == 2
        
        # Test processing pipeline for each file
        for edf_file in files:
            signals_data = read_edf_signals(edf_file, sample_parameters)
            all_results = process_all_channels(signals_data, sample_parameters)
            save_results_to_csv(all_results, edf_file, temp_directory)
            
            # Verify output exists and has correct structure
            output_file = temp_directory / f"{edf_file.stem}.csv"
            assert output_file.exists()
            
            # Verify CSV structure
            df = pd.read_csv(output_file, index_col=[0, 1])
            assert df.shape[0] == 4  # 2 channels * 2 windows
            assert df.shape[1] == 81  # 0 to 20 Hz in 0.25 Hz bins
    
    def test_edge_case_short_signal(self, sample_parameters):
        """Test processing with signal shorter than one window."""
        # Signal with only 512 samples (less than 1024 window size)
        short_signal = np.random.randn(512)
        
        result = process_single_channel(short_signal, 0, sample_parameters)
        
        # Should return empty list since no complete windows
        assert len(result) == 0
    
    def test_edge_case_exact_window_size(self, sample_parameters):
        """Test processing with signal exactly one window size."""
        # Signal with exactly 1024 samples
        exact_signal = np.random.randn(1024)
        
        result = process_single_channel(exact_signal, 0, sample_parameters)
        
        # Should have exactly one window worth of data
        num_bins = int(sample_parameters['freq_limit'] / sample_parameters['freq_bin_size']) + 1
        assert len(result) == num_bins
        assert all(record['Window'] == 1 for record in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
