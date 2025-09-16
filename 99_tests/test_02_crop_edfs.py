import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil
import sys
import os

# Add the project root to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the module under test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "crop_edfs", 
    os.path.join(os.path.dirname(__file__), '..', '02_preprocessing',
                 '02_crop_edfs.py')
)
crop_edfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crop_edfs)

# Import functions from the module
setup_environment = crop_edfs.setup_environment
setup_directories = crop_edfs.setup_directories
discover_edf_files = crop_edfs.discover_edf_files
process_all_files = crop_edfs.process_all_files
crop_edf_to_24_hours = crop_edfs.crop_edf_to_24_hours


class TestCropEDFs:
    """Test suite for EDF cropping functions."""
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_setup_directories(self, temp_directory):
        """Test that setup_directories creates correct paths and directories."""
        with patch.object(crop_edfs, 'Path') as mock_path:
            # Mock Path objects
            mock_input_dir = MagicMock()
            mock_output_dir = MagicMock()
            
            # Configure Path to return our mocks
            mock_path.side_effect = [mock_input_dir, mock_output_dir]
            
            input_dir, output_dir = setup_directories()
            
            # Verify correct paths were created
            assert mock_path.call_args_list == [
                call("01_data_files/02_edf_raw"),
                call("01_data_files/03_edf_cropped")
            ]
            
            # Verify output directory creation was called
            mock_output_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify return values
            assert input_dir == mock_input_dir
            assert output_dir == mock_output_dir

    def test_discover_edf_files_with_files(self, temp_directory):
        """Test discovering EDF files when files exist."""
        # Create test EDF files
        test_files = ["test1.edf", "test2.edf", "test3.edf"]
        for filename in test_files:
            (temp_directory / filename).touch()
        
        # Also create non-EDF files that should be ignored
        (temp_directory / "not_edf.txt").touch()
        (temp_directory / "another.dat").touch()
        
        file_list = discover_edf_files(temp_directory)
        
        # Should find exactly 3 EDF files
        assert len(file_list) == 3
        
        # Check that all found files are EDF files
        found_names = {f.name for f in file_list}
        assert found_names == set(test_files)

    def test_discover_edf_files_empty_directory(self, temp_directory):
        """Test discovering EDF files in empty directory."""
        file_list = discover_edf_files(temp_directory)
        assert len(file_list) == 0
        assert file_list == []

    @patch.object(crop_edfs, 'crop_edf_to_24_hours')
    def test_process_all_files(self, mock_crop_function, temp_directory):
        """Test processing all files calls crop function for each file."""
        # Create test input and output directories
        input_dir = temp_directory / "input"
        output_dir = temp_directory / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create test EDF files
        test_files = [
            input_dir / "test1.edf",
            input_dir / "test2.edf",
            input_dir / "test3.edf"
        ]
        for file_path in test_files:
            file_path.touch()
        
        process_all_files(test_files, input_dir, output_dir)
        
        # Verify crop function was called for each file
        assert mock_crop_function.call_count == 3
        
        # Check the calls were made with correct parameters
        expected_calls = [
            call(test_files[0], output_dir / "test1.edf", 1, 3),
            call(test_files[1], output_dir / "test2.edf", 2, 3),
            call(test_files[2], output_dir / "test3.edf", 3, 3)
        ]
        mock_crop_function.assert_has_calls(expected_calls)

    @patch.object(crop_edfs.pyedflib.highlevel, 'write_edf')
    @patch.object(crop_edfs.pyedflib.highlevel, 'read_edf')
    def test_crop_edf_to_24_hours_normal_case(self, mock_read_edf, mock_write_edf, temp_directory):
        """Test cropping EDF file with normal 48-hour data to 24 hours."""
        # Mock EDF data - simulate 48 hours of data at 1 Hz
        sample_rate = 1
        hours_48_samples = 48 * 60 * 60  # 48 hours worth of samples
        
        # Create mock signals (3 channels)
        mock_signals = [
            np.random.randn(hours_48_samples),  # Channel 1
            np.random.randn(hours_48_samples),  # Channel 2
            np.random.randn(hours_48_samples)   # Channel 3
        ]
        
        mock_signal_headers = [
            {"sample_rate": sample_rate},
            {"sample_rate": sample_rate},
            {"sample_rate": sample_rate}
        ]
        
        mock_header = {"record_duration": 48 * 60 * 60}
        
        mock_read_edf.return_value = (mock_signals, mock_signal_headers, mock_header)
        
        # Test file paths
        input_path = temp_directory / "input.edf"
        output_path = temp_directory / "output.edf"
        
        crop_edf_to_24_hours(input_path, output_path, 1, 1)
        
        # Verify read_edf was called
        mock_read_edf.assert_called_once_with(str(input_path))
        
        # Verify write_edf was called
        mock_write_edf.assert_called_once()
        
        # Get the arguments passed to write_edf
        write_args = mock_write_edf.call_args[0]
        write_kwargs = mock_write_edf.call_args[1] if mock_write_edf.call_args[1] else {}
        
        # Check output path
        assert write_args[0] == str(output_path)
        
        # Check cropped signals (should be 24 hours worth)
        cropped_signals = write_args[1]
        expected_samples = 24 * 60 * 60  # 24 hours at 1 Hz
        
        assert len(cropped_signals) == 3  # 3 channels
        for signal in cropped_signals:
            assert len(signal) == expected_samples
        
        # Check signal headers unchanged
        assert write_args[2] == mock_signal_headers
        
        # Check header duration updated
        updated_header = write_args[3]
        assert updated_header["record_duration"] == 24 * 60 * 60

    @patch.object(crop_edfs.pyedflib.highlevel, 'write_edf')
    @patch.object(crop_edfs.pyedflib.highlevel, 'read_edf')
    def test_crop_edf_to_24_hours_short_data(self, mock_read_edf, mock_write_edf, temp_directory):
        """Test cropping EDF file with less than 24 hours of data."""
        # Mock EDF data - simulate 12 hours of data at 1 Hz
        sample_rate = 1
        hours_12_samples = 12 * 60 * 60  # 12 hours worth of samples
        
        # Create mock signals (2 channels)
        mock_signals = [
            np.random.randn(hours_12_samples),  # Channel 1
            np.random.randn(hours_12_samples)   # Channel 2
        ]
        
        mock_signal_headers = [
            {"sample_rate": sample_rate},
            {"sample_rate": sample_rate}
        ]
        
        mock_header = {"record_duration": 12 * 60 * 60}
        
        mock_read_edf.return_value = (mock_signals, mock_signal_headers, mock_header)
        
        # Test file paths
        input_path = temp_directory / "short_input.edf"
        output_path = temp_directory / "short_output.edf"
        
        crop_edf_to_24_hours(input_path, output_path, 1, 1)
        
        # Get the arguments passed to write_edf
        write_args = mock_write_edf.call_args[0]
        
        # Check cropped signals (should be all available data, 12 hours)
        cropped_signals = write_args[1]
        
        assert len(cropped_signals) == 2  # 2 channels
        for signal in cropped_signals:
            assert len(signal) == hours_12_samples  # All available data

    @patch.object(crop_edfs.subprocess, 'check_output')
    @patch.object(crop_edfs.os, 'chdir')
    def test_change_to_git_root_success(self, mock_chdir, mock_check_output):
        """Test successful change to git root directory."""
        mock_git_root = "/path/to/git/root"
        mock_check_output.return_value = f"{mock_git_root}\n".encode('utf-8')
        
        crop_edfs._change_to_git_root()
        
        # Verify git command was called
        mock_check_output.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"], 
            stderr=crop_edfs.subprocess.DEVNULL
        )
        
        # Verify directory change
        mock_chdir.assert_called_once_with(mock_git_root)

    @patch.object(crop_edfs.subprocess, 'check_output')
    @patch.object(crop_edfs.os, 'chdir')
    def test_change_to_git_root_not_git_repo(self, mock_chdir, mock_check_output):
        """Test handling when not in a git repository."""
        mock_check_output.side_effect = crop_edfs.subprocess.CalledProcessError(1, 'git')
        
        # Should not raise exception
        crop_edfs._change_to_git_root()
        
        # Should not change directory
        mock_chdir.assert_not_called()

    @patch.object(crop_edfs, 'setup_environment')
    @patch.object(crop_edfs, 'setup_directories')
    @patch.object(crop_edfs, 'discover_edf_files')
    @patch.object(crop_edfs, 'process_all_files')
    def test_main_function_flow(self, mock_process_all, mock_discover, mock_setup_dirs, mock_setup_env):
        """Test that main function calls all steps in correct order."""
        # Mock return values
        mock_input_dir = MagicMock()
        mock_output_dir = MagicMock()
        mock_file_list = [MagicMock(), MagicMock()]
        
        mock_setup_dirs.return_value = (mock_input_dir, mock_output_dir)
        mock_discover.return_value = mock_file_list
        
        crop_edfs.main()
        
        # Verify all functions called in correct order
        mock_setup_env.assert_called_once()
        mock_setup_dirs.assert_called_once()
        mock_discover.assert_called_once_with(mock_input_dir)
        mock_process_all.assert_called_once_with(mock_file_list, mock_input_dir, mock_output_dir)


class TestIntegration:
    """Integration tests for the complete EDF cropping pipeline."""
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @patch.object(crop_edfs.pyedflib.highlevel, 'read_edf')
    @patch.object(crop_edfs.pyedflib.highlevel, 'write_edf')
    def test_full_pipeline_integration(self, mock_write_edf, mock_read_edf, temp_directory):
        """Test the complete pipeline from file discovery to cropping."""
        # Set up test directory structure
        input_dir = temp_directory / "input"
        output_dir = temp_directory / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create test EDF files
        test_files = ["recording1.edf", "recording2.edf"]
        for filename in test_files:
            (input_dir / filename).touch()
        
        # Mock EDF data for each file
        sample_rate = 250  # 250 Hz
        hours_30_samples = 30 * 60 * 60 * sample_rate  # 30 hours of data
        
        mock_signals = [
            np.random.randn(hours_30_samples),  # Channel 1
            np.random.randn(hours_30_samples),  # Channel 2
        ]
        
        mock_signal_headers = [
            {"sample_rate": sample_rate},
            {"sample_rate": sample_rate}
        ]
        
        mock_header = {"record_duration": 30 * 60 * 60}
        
        mock_read_edf.return_value = (mock_signals, mock_signal_headers, mock_header)
        
        # Run the pipeline
        file_list = discover_edf_files(input_dir)
        process_all_files(file_list, input_dir, output_dir)
        
        # Verify files were discovered
        assert len(file_list) == 2
        
        # Verify read_edf called for each file
        assert mock_read_edf.call_count == 2
        
        # Verify write_edf called for each file
        assert mock_write_edf.call_count == 2
        
        # Check that cropped data has correct length (24 hours)
        expected_samples_24h = 24 * 60 * 60 * sample_rate
        
        for call_args in mock_write_edf.call_args_list:
            cropped_signals = call_args[0][1]
            for signal in cropped_signals:
                assert len(signal) == expected_samples_24h

    def test_edge_case_empty_input_directory(self, temp_directory):
        """Test handling of empty input directory."""
        empty_dir = temp_directory / "empty"
        empty_dir.mkdir()
        
        file_list = discover_edf_files(empty_dir)
        assert len(file_list) == 0
        
        # Processing empty file list should not crash
        output_dir = temp_directory / "output"
        output_dir.mkdir()
        
        # Should complete without error
        process_all_files(file_list, empty_dir, output_dir)

    @patch.object(crop_edfs.pyedflib.highlevel, 'read_edf')
    @patch.object(crop_edfs.pyedflib.highlevel, 'write_edf')
    def test_edge_case_high_sample_rate(self, mock_write_edf, mock_read_edf, temp_directory):
        """Test cropping with high sample rate data."""
        # High sample rate: 1000 Hz
        sample_rate = 1000
        hours_25_samples = 25 * 60 * 60 * sample_rate  # 25 hours of data
        
        mock_signals = [np.random.randn(hours_25_samples)]
        mock_signal_headers = [{"sample_rate": sample_rate}]
        mock_header = {"record_duration": 25 * 60 * 60}
        
        mock_read_edf.return_value = (mock_signals, mock_signal_headers, mock_header)
        
        input_path = temp_directory / "high_rate.edf"
        output_path = temp_directory / "high_rate_cropped.edf"
        
        crop_edf_to_24_hours(input_path, output_path, 1, 1)
        
        # Verify correct number of samples for 24 hours at 1000 Hz
        write_args = mock_write_edf.call_args[0]
        cropped_signals = write_args[1]
        
        expected_samples = 24 * 60 * 60 * sample_rate
        assert len(cropped_signals[0]) == expected_samples


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
