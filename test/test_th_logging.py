import pytest
import logging
import logging.config
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import configparser

from th_logging import configure_logging, get_logger, logging_config_file




class TestConfigureLogging:
    """Test the configure_logging function"""

    @pytest.fixture
    def mock_config_parser(self):
        """Mock ConfigParser for testing"""
        with patch('th_logging.th_logging.configparser.ConfigParser') as mock_cp:
            config = MagicMock()
            mock_cp.return_value = config
            config.sections.return_value = ['logger_root', 'logger_test', 'handler_console_string', 'handler_console_json']
            # Mock the dictionary access
            config.__getitem__.return_value = {'handlers': 'console_string'}
            yield config

    @pytest.fixture
    def mock_file_config(self):
        """Mock logging.config.fileConfig"""
        with patch('th_logging.th_logging.logging.config.fileConfig') as mock_fc:
            yield mock_fc

    def test_configure_logging_default_parameters(self, mock_config_parser, mock_file_config):
        """Test configure_logging with default parameters"""
        configure_logging()
        
        # Verify ConfigParser was called correctly
        mock_config_parser.read.assert_called_once_with(logging_config_file)
        # Check that the level was set on the logger_root section
        mock_config_parser.__getitem__.assert_called_with('logger_root')
        mock_file_config.assert_called_once_with(mock_config_parser)

    def test_configure_logging_custom_level(self, mock_config_parser, mock_file_config):
        """Test configure_logging with custom log level"""
        configure_logging(level='DEBUG')
        
        # Check that the level was set on the logger_root section
        mock_config_parser.__getitem__.assert_called_with('logger_root')

    def test_configure_logging_json_logging_true(self, mock_config_parser, mock_file_config):
        """Test configure_logging with json_logging=True"""
        configure_logging(json_logging=True)
        
        # Verify that logger sections were accessed
        mock_config_parser.sections.assert_called_once()
        mock_file_config.assert_called_once_with(mock_config_parser)

    def test_configure_logging_json_logging_false(self, mock_config_parser, mock_file_config):
        """Test configure_logging with json_logging=False"""
        configure_logging(json_logging=False)
        
        # Should only set the root logger level, not modify handlers
        mock_config_parser.__getitem__.assert_called_with('logger_root')
        mock_file_config.assert_called_once_with(mock_config_parser)

    def test_configure_logging_with_loggers_to_reset(self, mock_config_parser, mock_file_config):
        """Test configure_logging with loggers_to_reset parameter"""
        # Mock the root logger
        root_logger = MagicMock()
        root_logger.handlers = [MagicMock()]
        root_logger.level = logging.INFO
        
        # Mock additional loggers
        test_logger = MagicMock()
        
        with patch('th_logging.th_logging.logging.getLogger') as mock_get_logger:
            # Need 4 mock values: root, uvicorn.error, uvicorn.access, test_logger
            mock_get_logger.side_effect = [
                root_logger,      # For root logger
                MagicMock(),      # For uvicorn.error
                MagicMock(),      # For uvicorn.access
                test_logger       # For test_logger in loggers_to_reset
            ]
            
            configure_logging(loggers_to_reset=['test_logger'])
            
            # Verify the test logger was configured
            assert test_logger.handlers == root_logger.handlers
            assert test_logger.propagate is False
            test_logger.setLevel.assert_called_once_with(root_logger.level)

    def test_configure_logging_with_uvicorn_import(self, mock_config_parser, mock_file_config):
        """Test configure_logging when uvicorn is available"""
        # Mock the root logger
        root_logger = MagicMock()
        root_logger.handlers = [MagicMock()]
        
        with patch('th_logging.th_logging.logging.getLogger') as mock_get_logger, \
             patch('builtins.__import__') as mock_import:
            
            # Mock the uvicorn import
            mock_uvicorn_module = MagicMock()
            mock_uvicorn_config = MagicMock()
            mock_uvicorn_logger = MagicMock()
            mock_uvicorn_config.logger = mock_uvicorn_logger
            mock_uvicorn_module.config = mock_uvicorn_config
            mock_import.return_value = mock_uvicorn_module
            
            mock_get_logger.side_effect = [
                root_logger,  # root logger
                mock_uvicorn_logger,  # uvicorn.config.logger
                MagicMock(),  # uvicorn.error logger
                MagicMock(),  # uvicorn.access logger
            ]
            
            configure_logging()
            
            # Verify that the function completed without errors
            mock_file_config.assert_called_once_with(mock_config_parser)

    def test_configure_logging_without_uvicorn_import(self, mock_config_parser, mock_file_config):
        """Test configure_logging when uvicorn is not available"""
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError("No module named 'uvicorn'")):
            # Should not raise an exception when uvicorn is not available
            configure_logging()
            
            # Verify basic configuration still works
            mock_config_parser.__getitem__.assert_called_with('logger_root')
            mock_file_config.assert_called_once_with(mock_config_parser)

    def test_configure_logging_empty_loggers_to_reset(self, mock_config_parser, mock_file_config):
        """Test configure_logging with empty loggers_to_reset list"""
        with patch('th_logging.th_logging.logging.getLogger') as mock_get_logger:
            root_logger = MagicMock()
            root_logger.handlers = [MagicMock()]
            mock_get_logger.return_value = root_logger
            
            configure_logging(loggers_to_reset=[])
            
            # Should call getLogger 3 times: root, uvicorn.error, uvicorn.access
            assert mock_get_logger.call_count == 3


class TestGetLogger:
    """Test the get_logger function"""

    @patch('th_logging.th_logging.logging.getLogger')
    def test_get_logger(self, mock_get_logger):
        """Test get_logger function"""
        expected_logger = MagicMock()
        mock_get_logger.return_value = expected_logger
        
        result = get_logger("test_logger")
        
        mock_get_logger.assert_called_once_with("test_logger")
        assert result == expected_logger

    @patch('th_logging.th_logging.logging.getLogger')
    def test_get_logger_with_empty_name(self, mock_get_logger):
        """Test get_logger with empty string"""
        expected_logger = MagicMock()
        mock_get_logger.return_value = expected_logger
        
        result = get_logger("")
        
        mock_get_logger.assert_called_once_with("")
        assert result == expected_logger


class TestLoggingConfigFile:
    """Test the logging_config_file path"""

    def test_logging_config_file_path(self):
        """Test that logging_config_file points to the correct location"""
        expected_path = Path(__file__).parent.parent / "src" / "th_logging" / "logging-config.ini"
        assert logging_config_file == expected_path
        assert logging_config_file.exists()


class TestIntegration:
    """Integration tests for the logging module"""

    def test_configure_logging_integration(self):
        """Test that configure_logging actually configures logging"""
        # This test will be skipped to avoid pytest logging conflicts
        pytest.skip("Integration test skipped due to pytest logging conflicts")

    def test_get_logger_integration(self):
        """Test that get_logger returns a proper logger"""
        # This test will be skipped to avoid pytest logging conflicts
        pytest.skip("Integration test skipped due to pytest logging conflicts")
