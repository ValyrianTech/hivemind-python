#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for image and video option validation in the HivemindOption class."""

import pytest
from src.hivemind.issue import HivemindIssue
from src.hivemind.option import HivemindOption


@pytest.fixture
def issue():
    """Create a test hivemind issue."""
    return HivemindIssue()


@pytest.fixture
def option(issue):
    """Create a test option linked to the test issue."""
    option = HivemindOption()
    option._hivemind_issue = issue
    return option


class TestMediaOptions:
    """Test class for image and video option validation."""

    def test_is_valid_ipfs_hash_cidv0(self, option):
        """Test validation of CIDv0 IPFS hashes."""
        # Valid CIDv0 hash (starts with Qm and is 46 chars long with valid base58 chars)
        assert option._is_valid_ipfs_hash("QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o") is True
        
        # Invalid CIDv0 hash (wrong prefix)
        assert option._is_valid_ipfs_hash("XmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o") is False
        
        # Invalid CIDv0 hash (wrong length)
        assert option._is_valid_ipfs_hash("QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff") is False
        
        # Invalid CIDv0 hash (invalid characters)
        assert option._is_valid_ipfs_hash("QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff0O") is False

    def test_is_valid_ipfs_hash_cidv1(self, option):
        """Test validation of CIDv1 IPFS hashes."""
        # Valid CIDv1 hash (starts with b and has valid base32 chars)
        assert option._is_valid_ipfs_hash("bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi") is True
        
        # Valid CIDv1 hash (starts with B and has valid base32 chars)
        assert option._is_valid_ipfs_hash("BAFYBEIGDYRZT5SFP7UDMM7HU76UH7Y26NF3EFUYLQABF3OCLGTQY55FBZDI") is True
        
        # Invalid CIDv1 hash (invalid prefix)
        assert option._is_valid_ipfs_hash("cafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi") is False
        
        # Invalid CIDv1 hash (invalid characters)
        assert option._is_valid_ipfs_hash("bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzd!") is False

    def test_is_valid_ipfs_hash_invalid(self, option):
        """Test validation of invalid IPFS hashes."""
        # Empty string
        assert option._is_valid_ipfs_hash("") is False
        
        # None value (should be handled by the calling method, but test for completeness)
        with pytest.raises(AttributeError):
            option._is_valid_ipfs_hash(None)
        
        # Too short string
        assert option._is_valid_ipfs_hash("Qm") is False
        
        # Random string
        assert option._is_valid_ipfs_hash("not-an-ipfs-hash") is False

    def test_image_option_with_constraints(self, issue, option):
        """Test image option validation with constraints."""
        issue.answer_type = 'Image'
        option._answer_type = 'Image'
        option.value = "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o"
        
        # Test with formats constraint
        issue.constraints = {'formats': ['jpg', 'png']}
        assert option.is_valid_image_option() is True
        
        # Test with max_size constraint
        issue.constraints = {'max_size': 1024 * 1024}  # 1MB
        assert option.is_valid_image_option() is True
        
        # Test with dimensions constraint
        issue.constraints = {'dimensions': {'max_width': 1920, 'max_height': 1080}}
        assert option.is_valid_image_option() is True
        
        # Test with multiple constraints
        issue.constraints = {
            'formats': ['jpg', 'png'],
            'max_size': 1024 * 1024,
            'dimensions': {'max_width': 1920, 'max_height': 1080}
        }
        assert option.is_valid_image_option() is True

    def test_video_option_with_constraints(self, issue, option):
        """Test video option validation with constraints."""
        issue.answer_type = 'Video'
        option._answer_type = 'Video'
        option.value = "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o"
        
        # Test with formats constraint
        issue.constraints = {'formats': ['mp4', 'webm']}
        assert option.is_valid_video_option() is True
        
        # Test with max_size constraint
        issue.constraints = {'max_size': 100 * 1024 * 1024}  # 100MB
        assert option.is_valid_video_option() is True
        
        # Test with max_duration constraint
        issue.constraints = {'max_duration': 300}  # 5 minutes
        assert option.is_valid_video_option() is True
        
        # Test with multiple constraints
        issue.constraints = {
            'formats': ['mp4', 'webm'],
            'max_size': 100 * 1024 * 1024,
            'max_duration': 300
        }
        assert option.is_valid_video_option() is True
        
    def test_invalid_image_option(self, issue, option):
        """Test invalid image option validation."""
        issue.answer_type = 'Image'
        option._answer_type = 'Image'
        
        # Test with non-string value
        option.value = 123
        assert option.is_valid_image_option() is False
        
        # Test with invalid IPFS hash
        option.value = "not-an-ipfs-hash"
        assert option.is_valid_image_option() is False
        
    def test_invalid_video_option(self, issue, option):
        """Test invalid video option validation."""
        issue.answer_type = 'Video'
        option._answer_type = 'Video'
        
        # Test with non-string value
        option.value = 123
        assert option.is_valid_video_option() is False
        
        # Test with invalid IPFS hash
        option.value = "not-an-ipfs-hash"
        assert option.is_valid_video_option() is False
