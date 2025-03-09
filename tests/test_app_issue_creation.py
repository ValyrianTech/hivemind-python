"""Tests for issue creation functionality in the FastAPI web application."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import HivemindState from src.hivemind.state
sys.path.append(os.path.join(project_root, "src"))
from hivemind.state import HivemindState

@pytest.mark.unit
class TestIssueCreationFunctionality:
    """Test create_issue functionality, specifically Boolean constraint handling."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindIssue")
    def test_create_issue_bool_constraints(self, mock_hivemind_issue):
        """Test Boolean constraint handling in create_issue function (lines 538-546).
        
        This test specifically verifies that when a Boolean issue type is created with
        custom true/false labels in the 'choices' array, the constraints are properly
        modified to use the expected format with 'true_value' and 'false_value' keys.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type and custom true/false labels
        issue_data = {
            "name": "Boolean Test Issue",
            "description": "Test Description for Boolean Issue",
            "questions": ["Do you agree?"],
            "tags": ["test", "boolean"],
            "answer_type": "Bool",
            "constraints": {
                "choices": ["Yes", "No"]  # Custom true/false labels
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_issue_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the modified constraints
        # This specifically tests lines 538-546 where the Boolean constraints are modified
        expected_modified_constraints = {
            "true_value": "Yes",
            "false_value": "No"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_modified_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_bool_constraints_default_labels(self, mock_hivemind_issue):
        """Test Boolean constraint handling with default labels in create_issue function.
        
        This test verifies that when a Boolean issue type is created without custom labels
        or with an empty 'choices' array, the default 'True' and 'False' labels are used.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type but empty choices array
        issue_data = {
            "name": "Default Boolean Test Issue",
            "description": "Test Description for Default Boolean Issue",
            "questions": ["Do you agree?"],
            "tags": ["test", "boolean", "default"],
            "answer_type": "Bool",
            "constraints": {
                "choices": []  # Empty choices array should use default labels
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_issue_cid"
        
        # Verify the default labels were used
        expected_default_constraints = {
            "true_value": "True",
            "false_value": "False"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_default_constraints)

    @patch("app.HivemindIssue")
    def test_create_issue_bool_no_constraints(self, mock_hivemind_issue):
        """Test Boolean issue creation without constraints (lines 594-596).
        
        This test verifies that when a Boolean issue type is created without any constraints,
        default 'True' and 'False' labels are automatically applied.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_bool_no_constraints_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type but NO constraints
        issue_data = {
            "name": "Bool Issue Without Constraints",
            "description": "Test Description for Bool Issue Without Constraints",
            "questions": ["Do you agree with the proposal?"],
            "tags": ["test", "boolean", "no-constraints"],
            "answer_type": "Bool",
            "constraints": None,  # No constraints provided
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_bool_no_constraints_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the default Bool constraints
        # This specifically tests lines 594-596 where default Bool constraints are applied
        expected_default_constraints = {
            "true_value": "True",
            "false_value": "False"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_default_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_image_constraints(self, mock_hivemind_issue):
        """Test Image constraint handling in create_issue function (lines 550-572).
        
        This test verifies that when an Image issue type is created with various constraints
        (formats, max_size, and dimensions), these constraints are properly validated and
        set on the HivemindIssue instance.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_image_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Image answer_type and various constraints
        issue_data = {
            "name": "Image Test Issue",
            "description": "Test Description for Image Issue",
            "questions": ["Upload an image that represents your idea"],
            "tags": ["test", "image"],
            "answer_type": "Image",
            "constraints": {
                "formats": ["jpg", "png", "gif"],
                "max_size": 5242880,  # 5MB in bytes
                "dimensions": {
                    "max_width": 1920,
                    "max_height": 1080
                }
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_image_issue_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the expected image constraints
        # This specifically tests lines 550-572 where the Image constraints are processed
        expected_image_constraints = {
            "formats": ["jpg", "png", "gif"],
            "max_size": 5242880,
            "dimensions": {
                "max_width": 1920,
                "max_height": 1080
            }
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_image_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_partial_image_constraints(self, mock_hivemind_issue):
        """Test Image constraint handling with partial constraints in create_issue function.
        
        This test verifies that when an Image issue type is created with only some of the
        possible constraints, only the valid constraints are included in the final constraints
        object passed to set_constraints.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_partial_image_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Image answer_type and only some constraints
        issue_data = {
            "name": "Partial Image Test Issue",
            "description": "Test Description for Partial Image Constraints",
            "questions": ["Upload a profile picture"],
            "tags": ["test", "image", "partial"],
            "answer_type": "Image",
            "constraints": {
                "formats": ["jpg", "png"],
                # No max_size provided
                "dimensions": {
                    "max_width": 800,
                    # No max_height provided
                }
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify the expected partial constraints were used
        expected_partial_constraints = {
            "formats": ["jpg", "png"],
            "dimensions": {
                "max_width": 800
            }
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_partial_constraints)

    @patch("app.HivemindIssue")
    def test_create_issue_video_constraints(self, mock_hivemind_issue):
        """Test Video constraint handling in create_issue function (lines 576-591).
        
        This test verifies that when a Video issue type is created with various constraints
        (formats, max_size, and max_duration), these constraints are properly validated and
        set on the HivemindIssue instance.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_video_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Video answer_type and various constraints
        issue_data = {
            "name": "Video Test Issue",
            "description": "Test Description for Video Issue",
            "questions": ["Upload a video that demonstrates your idea"],
            "tags": ["test", "video"],
            "answer_type": "Video",
            "constraints": {
                "formats": ["mp4", "mov", "avi"],
                "max_size": 104857600,  # 100MB in bytes
                "max_duration": 300  # 5 minutes in seconds
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_video_issue_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the expected video constraints
        # This specifically tests lines 576-591 where the Video constraints are processed
        expected_video_constraints = {
            "formats": ["mp4", "mov", "avi"],
            "max_size": 104857600,
            "max_duration": 300
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_video_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_partial_video_constraints(self, mock_hivemind_issue):
        """Test Video constraint handling with partial constraints in create_issue function.
        
        This test verifies that when a Video issue type is created with only some of the
        possible constraints, only the valid constraints are included in the final constraints
        object passed to set_constraints.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_partial_video_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Video answer_type and only some constraints
        issue_data = {
            "name": "Partial Video Test Issue",
            "description": "Test Description for Partial Video Constraints",
            "questions": ["Upload a short video clip"],
            "tags": ["test", "video", "partial"],
            "answer_type": "Video",
            "constraints": {
                "formats": ["mp4"],
                # No max_size provided
                "max_duration": 60  # 1 minute in seconds
            },
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify the expected partial constraints were used
        expected_partial_constraints = {
            "formats": ["mp4"],
            "max_duration": 60
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_partial_constraints)


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_issue_creation.py"])
