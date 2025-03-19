"""Tests for the extract_ranking_from_opinion_object function in app.py."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import required modules from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.ranking import Ranking


@pytest.mark.unit
class TestExtractRankingFromOpinion:
    """Test the extract_ranking_from_opinion_object function."""

    @patch("app.logger")
    def test_extract_ranking_fixed(self, mock_logger):
        """Test extracting a fixed ranking."""
        # Create a mock ranking object with fixed ranking
        mock_ranking = MagicMock()
        mock_ranking.__dict__ = {
            "type": "fixed",
            "fixed": ["option1", "option2", "option3"]
        }

        # Call the function
        ranking, ranking_type = app.extract_ranking_from_opinion_object(mock_ranking)

        # Verify results
        assert ranking_type == "fixed"
        assert ranking == ["option1", "option2", "option3"]

    @patch("app.logger")
    def test_extract_ranking_auto_high(self, mock_logger):
        """Test extracting an auto_high ranking."""
        # Create a mock ranking object with auto_high ranking
        mock_ranking = MagicMock()
        mock_ranking.__dict__ = {
            "type": "auto_high",
            "auto": "option1"
        }

        # Call the function
        ranking, ranking_type = app.extract_ranking_from_opinion_object(mock_ranking)

        # Verify results
        assert ranking_type == "auto_high"
        assert ranking == ["option1"]

    @patch("app.logger")
    def test_extract_ranking_auto_low(self, mock_logger):
        """Test extracting an auto_low ranking."""
        # Create a mock ranking object with auto_low ranking
        mock_ranking = MagicMock()
        mock_ranking.__dict__ = {
            "type": "auto_low",
            "auto": "option1"
        }

        # Call the function
        ranking, ranking_type = app.extract_ranking_from_opinion_object(mock_ranking)

        # Verify results
        assert ranking_type == "auto_low"
        assert ranking == ["option1"]

    @patch("app.logger")
    def test_extract_ranking_no_dict(self, mock_logger):
        """Test extracting a ranking from an object without __dict__."""
        # Create a mock ranking object without __dict__
        mock_ranking = "not_a_ranking_object"

        # Call the function
        ranking, ranking_type = app.extract_ranking_from_opinion_object(mock_ranking)

        # Verify results
        assert ranking is None
        assert ranking_type is None
        # Verify no logging of ranking attributes
        mock_logger.debug.assert_not_called()

    @patch("app.logger")
    def test_extract_ranking_missing_type(self, mock_logger):
        """Test extracting a ranking from an object with __dict__ but no type."""
        # Create a mock ranking object with __dict__ but no type
        mock_ranking = MagicMock()
        mock_ranking.__dict__ = {
            "some_other_attribute": "value"
        }

        # Call the function
        ranking, ranking_type = app.extract_ranking_from_opinion_object(mock_ranking)

        # Verify results
        assert ranking is None
        assert ranking_type is None


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_extract_ranking.py"])
