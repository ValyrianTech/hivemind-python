#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, integer_issue, test_keypair,
    TestHelper, sign_message
)
from ipfs_dict_chain.IPFS import IPFSError
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

        # Save and reload state to initialize option cache
        state_hash = state.save()
        state = HivemindState(cid=state_hash)

        # Create an opinion with auto_high ranking
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0

        # Set up an auto_high ranking with the second option as preferred
        opinion.ranking.set_auto_high(second_hash)
        # Convert ranking to dictionary before saving
        opinion.ranking = opinion.ranking.to_dict()
        opinion_hash = opinion.save()

        # Add the opinion to the state
        timestamp = int(time.time())
        signature = sign_message(f"{timestamp}{opinion_hash}", private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Compare options using this opinion
        # This should use the auto_high branch (line 687)
        result = state.compare(first_hash, third_hash, opinion_hash)

        # The third option should be preferred as it's closer to the second option value
        assert result == third_hash

    def test_get_option(self, state: HivemindState, integer_issue: HivemindIssue, test_keypair) -> None:
        """Test the get_option method for both cached and uncached options."""
        private_key, address = test_keypair
        issue_hash = integer_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Create an option
        helper = TestHelper()
        option_hash = helper.create_and_sign_option(
            state, issue_hash, 42, "Test Option", private_key, address, int(time.time())
        )

        # Test getting uncached option
        uncached_option = state.get_option(cid=option_hash)
        assert uncached_option.value == 42
        assert uncached_option.text == "Test Option"

        # Save and reload state to initialize cache
        state_hash = state.save()
        state = HivemindState(cid=state_hash)

        # Test getting cached option
        cached_option = state.get_option(cid=option_hash)
        assert cached_option.value == 42
        assert cached_option.text == "Test Option"

        # Test getting non-existent option
        with pytest.raises(IPFSError) as exc_info:
            state.get_option(cid="QmNonExistent")
        assert "Failed to retrieve json data from IPFS hash" in str(exc_info.value)
