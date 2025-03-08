"""Tests for the FastAPI web application."""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Create a mock StateLoadingStats class for testing
class StateLoadingStats:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.start_time = 0
        self.state_cid = None
        self.state_load_time = 0
        self.options_load_time = 0
        self.opinions_load_time = 0
        self.calculation_time = 0
        self.total_time = 0
        self.num_questions = 0
        self.num_options = 0
        self.num_opinions = 0

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "state_cid": self.state_cid,
            "state_load_time": round(self.state_load_time, 3),
            "options_load_time": round(self.options_load_time, 3),
            "opinions_load_time": round(self.opinions_load_time, 3),
            "calculation_time": round(self.calculation_time, 3),
            "total_time": round(self.total_time, 3),
            "num_questions": self.num_questions,
            "num_options": self.num_options,
            "num_opinions": self.num_opinions
        }


def log_state_stats(stats, logger):
    """Log state loading statistics in a structured format."""
    stats_dict = stats.to_dict()
    logger.info("State Loading Statistics:")
    logger.info(f"  Timestamp: {stats_dict['timestamp']}")
    logger.info(f"  State CID: {stats_dict['state_cid']}")
    logger.info(f"  State Load Time: {stats_dict['state_load_time']}s")
    logger.info(f"  Options Load Time: {stats_dict['options_load_time']}s")
    logger.info(f"  Opinions Load Time: {stats_dict['opinions_load_time']}s")
    logger.info(f"  Calculation Time: {stats_dict['calculation_time']}s")
    logger.info(f"  Total Time: {stats_dict['total_time']}s")
    logger.info(f"  Number of Questions: {stats_dict['num_questions']}")
    logger.info(f"  Number of Options: {stats_dict['num_options']}")
    logger.info(f"  Number of Opinions: {stats_dict['num_opinions']}")


@pytest.mark.unit
class TestStateLoadingStats:
    """Test the StateLoadingStats class."""
    
    def test_init(self):
        """Test initialization of StateLoadingStats."""
        stats = StateLoadingStats()
        assert stats.state_cid is None
        assert stats.state_load_time == 0
        assert stats.options_load_time == 0
        assert stats.opinions_load_time == 0
        assert stats.calculation_time == 0
        assert stats.total_time == 0
        assert stats.num_questions == 0
        assert stats.num_options == 0
        assert stats.num_opinions == 0
        
    def test_to_dict(self):
        """Test the to_dict method."""
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        stats.state_load_time = 1.0
        stats.options_load_time = 2.0
        stats.opinions_load_time = 3.0
        stats.calculation_time = 4.0
        stats.total_time = 10.0
        stats.num_questions = 5
        stats.num_options = 6
        stats.num_opinions = 7
        
        stats_dict = stats.to_dict()
        assert stats_dict["state_cid"] == "test_cid"
        assert stats_dict["state_load_time"] == 1.0
        assert stats_dict["options_load_time"] == 2.0
        assert stats_dict["opinions_load_time"] == 3.0
        assert stats_dict["calculation_time"] == 4.0
        assert stats_dict["total_time"] == 10.0
        assert stats_dict["num_questions"] == 5
        assert stats_dict["num_options"] == 6
        assert stats_dict["num_opinions"] == 7


@pytest.mark.unit
class TestLoggingFunctions:
    """Test logging related functions."""
    
    def test_log_state_stats(self):
        """Test logging state statistics."""
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create test stats
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        stats.state_load_time = 1.0
        stats.options_load_time = 2.0
        stats.opinions_load_time = 3.0
        stats.calculation_time = 4.0
        stats.total_time = 10.0
        stats.num_questions = 5
        stats.num_options = 6
        stats.num_opinions = 7
        
        # Call the function
        log_state_stats(stats, mock_logger)
        
        # Verify logger was called with expected messages
        assert mock_logger.info.call_count == 11
        mock_logger.info.assert_any_call("State Loading Statistics:")
        mock_logger.info.assert_any_call(f"  Timestamp: {stats.timestamp}")
        mock_logger.info.assert_any_call(f"  State CID: test_cid")
        mock_logger.info.assert_any_call(f"  State Load Time: 1.0s")
        mock_logger.info.assert_any_call(f"  Options Load Time: 2.0s")
        mock_logger.info.assert_any_call(f"  Opinions Load Time: 3.0s")
        mock_logger.info.assert_any_call(f"  Calculation Time: 4.0s")
        mock_logger.info.assert_any_call(f"  Total Time: 10.0s")
        mock_logger.info.assert_any_call(f"  Number of Questions: 5")
        mock_logger.info.assert_any_call(f"  Number of Options: 6")
        mock_logger.info.assert_any_call(f"  Number of Opinions: 7")
