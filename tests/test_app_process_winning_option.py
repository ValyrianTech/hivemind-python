"""Tests for the process_winning_option function in app.py."""
import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import required modules from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.option import HivemindOption


@pytest.mark.unit
class TestProcessWinningOption:
    """Test the process_winning_option function."""

    def test_process_winning_option_with_valid_option(self):
        """Test processing a valid winning option with a score."""
        # Create a mock option with text and value
        mock_option = MagicMock(spec=HivemindOption)
        mock_option.text = "Test Option"
        mock_option.value = 42
        mock_option.cid.return_value = "test_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results
        question_results = {"test_cid": {"score": 0.75}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "Test Option"
        assert result["value"] == 42
        assert result["score"] == 75.0  # 0.75 * 100, rounded to 2 decimal places

    def test_process_winning_option_with_ipfs_prefix(self):
        """Test processing an option with an IPFS prefix in the CID."""
        # Create a mock option
        mock_option = MagicMock(spec=HivemindOption)
        mock_option.text = "IPFS Option"
        mock_option.value = 100
        mock_option.cid.return_value = "/ipfs/test_ipfs_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results
        question_results = {"test_ipfs_cid": {"score": 0.5}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "IPFS Option"
        assert result["value"] == 100
        assert result["score"] == 50.0  # 0.5 * 100, rounded to 2 decimal places

    def test_process_winning_option_with_none_score(self):
        """Test processing an option with a None score."""
        # Create a mock option
        mock_option = MagicMock(spec=HivemindOption)
        mock_option.text = "None Score Option"
        mock_option.value = 200
        mock_option.cid.return_value = "none_score_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results with None score
        question_results = {"none_score_cid": {"score": None}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "None Score Option"
        assert result["value"] == 200
        assert result["score"] == 0.0  # None score should be converted to 0

    def test_process_winning_option_with_missing_score(self):
        """Test processing an option with a missing score."""
        # Create a mock option
        mock_option = MagicMock(spec=HivemindOption)
        mock_option.text = "Missing Score Option"
        mock_option.value = 300
        mock_option.cid.return_value = "missing_score_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create empty question results
        question_results = {}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "Missing Score Option"
        assert result["value"] == 300
        assert result["score"] == 0.0  # Missing score should default to 0

    def test_process_winning_option_with_no_text_attribute(self):
        """Test processing an option without a text attribute but with a value."""
        # Create a mock option without text attribute
        mock_option = MagicMock(spec=HivemindOption)
        # Remove text attribute
        del mock_option.text
        mock_option.value = 400
        mock_option.cid.return_value = "no_text_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results
        question_results = {"no_text_cid": {"score": 0.25}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "400"  # Should use str(value)
        assert result["value"] == 400
        assert result["score"] == 25.0  # 0.25 * 100, rounded to 2 decimal places

    def test_process_winning_option_with_no_value_attribute(self):
        """Test processing an option without a value attribute."""
        # Create a mock option without value attribute
        mock_option = MagicMock(spec=HivemindOption)
        mock_option.text = "No Value Option"
        # Remove value attribute
        del mock_option.value
        mock_option.cid.return_value = "no_value_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results
        question_results = {"no_value_cid": {"score": 0.8}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "No Value Option"
        assert result["value"] is None
        assert result["score"] == 80.0  # 0.8 * 100, rounded to 2 decimal places

    def test_process_winning_option_with_no_text_or_value_attribute(self):
        """Test processing an option without text or value attributes."""
        # Create a mock option without text or value attributes
        mock_option = MagicMock(spec=HivemindOption)
        # Remove text and value attributes
        del mock_option.text
        del mock_option.value
        mock_option.cid.return_value = "no_attributes_cid"

        # Create mock sorted options list
        sorted_options = [mock_option]

        # Create mock question results
        question_results = {"no_attributes_cid": {"score": 0.9}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is as expected
        assert result is not None
        assert result["text"] == "Unnamed Option"  # Should use default text
        assert result["value"] is None
        assert result["score"] == 90.0  # 0.9 * 100, rounded to 2 decimal places

    def test_process_winning_option_with_empty_sorted_options(self):
        """Test processing with empty sorted options."""
        # Create empty sorted options list
        sorted_options = []

        # Create mock question results
        question_results = {"some_cid": {"score": 0.5}}

        # Call the function
        result = app.process_winning_option(sorted_options, question_results)

        # Assert the result is None
        assert result is None


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_process_winning_option.py"])
