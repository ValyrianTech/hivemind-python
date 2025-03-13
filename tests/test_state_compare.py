#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, integer_issue, test_keypair,
    TestHelper, sign_message
)
import logging

@pytest.mark.consensus
class TestHivemindStateCompare:
    """Tests for the compare method in HivemindState."""
    
    def test_compare_with_auto_ranking(self, state: HivemindState, integer_issue: HivemindIssue, test_keypair) -> None:
        """Test the compare method with auto_high ranking type to cover line 687."""
        private_key, address = test_keypair
        issue_hash = integer_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Create three options with integer values
        helper = TestHelper()
        first_hash = helper.create_and_sign_option(
            state, issue_hash, 10, "First Option", private_key, address, int(time.time())
        )
        second_hash = helper.create_and_sign_option(
            state, issue_hash, 20, "Second Option", private_key, address, int(time.time())
        )
        third_hash = helper.create_and_sign_option(
            state, issue_hash, 30, "Third Option", private_key, address, int(time.time())
        )
        
        # Create an opinion with auto_high ranking
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        
        # Set up an auto_high ranking with the second option as preferred
        opinion.ranking.set_auto_high(second_hash)
        # Convert ranking to dictionary before saving
        opinion.ranking = opinion.ranking.to_dict()
        opinion_hash = opinion.save()
        
        # Compare options using this opinion
        # This should use the auto_high branch (line 687)
        result = state.compare(first_hash, third_hash, opinion_hash)
        
        # The third option should be preferred as it's closer to the second option value
        assert result == third_hash
    
    def test_compare_error_handling(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair, monkeypatch) -> None:
        """Test error handling in the compare method to cover lines 703-705."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Create two options
        helper = TestHelper()
        first_hash = helper.create_and_sign_option(
            state, issue_hash, "first", "First Option", private_key, address, int(time.time())
        )
        second_hash = helper.create_and_sign_option(
            state, issue_hash, "second", "Second Option", private_key, address, int(time.time())
        )
        
        # Create a valid opinion with a ranking
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([first_hash, second_hash])
        # Convert ranking to dictionary before saving
        opinion.ranking = opinion.ranking.to_dict()
        opinion_hash = opinion.save()
        
        # Monkeypatch the HivemindOpinion constructor to raise an exception
        # This will trigger the error handling in lines 703-705
        def mock_init(*args, **kwargs):
            raise Exception("Test exception")
        
        # Save the original __init__ method
        original_init = HivemindOpinion.__init__
        
        # Apply the monkeypatch
        monkeypatch.setattr(HivemindOpinion, "__init__", mock_init)
        
        # Test the compare method with the monkeypatch
        result = state.compare(first_hash, second_hash, opinion_hash)
        assert result is None
        
        # Restore the original __init__ method
        monkeypatch.setattr(HivemindOpinion, "__init__", original_init)
