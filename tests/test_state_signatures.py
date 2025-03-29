#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.signatures
class TestHivemindStateSignatures:
    """Tests for signature management."""

    def test_add_signature(self, state: HivemindState) -> None:
        """Test adding signatures with timestamp validation."""
        address = generate_bitcoin_keypair()[1]
        message = 'test_message'

        # Add first signature
        timestamp1 = int(time.time())
        state.add_signature(address, timestamp1, message, 'sig1')
        assert address in state.signatures
        assert message in state.signatures[address]
        assert 'sig1' in state.signatures[address][message]

        # Try adding older signature
        timestamp2 = timestamp1 - 1
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, timestamp2, message, 'sig2')

        # Add newer signature
        timestamp3 = timestamp1 + 1
        state.add_signature(address, timestamp3, message, 'sig3')
        assert 'sig3' in state.signatures[address][message]

    def test_add_duplicate_signature(self, state: HivemindState) -> None:
        """Test adding the same signature twice doesn't create duplicate entries."""
        address = generate_bitcoin_keypair()[1]
        message = 'test_message'
        timestamp = int(time.time())
        signature = 'test_signature'
        
        # Add signature first time
        state.add_signature(address, timestamp, message, signature)
        assert address in state.signatures
        assert message in state.signatures[address]
        assert signature in state.signatures[address][message]
        assert state.signatures[address][message][signature] == timestamp
        
        # Get current size of signatures dict for comparison
        initial_signatures_count = sum(len(msgs) for msgs in state.signatures.values())
        
        # Add exact same signature again - should return early without changes
        state.add_signature(address, timestamp, message, signature)
        
        # Verify no new entries were added
        final_signatures_count = sum(len(msgs) for msgs in state.signatures.values())
        assert final_signatures_count == initial_signatures_count
        assert state.signatures[address][message][signature] == timestamp

    def test_no_null_signatures(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test that adding options without signatures doesn't create null entries.
        
        This verifies the fix for a bug where adding options without signatures
        would create entries with null keys in the signatures dictionary.
        """
        # Set up issue
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        timestamp = int(time.time())

        # Create and add first option without signature
        option1 = HivemindOption()
        option1.set_issue(issue_hash)
        option1.set("test option 1")
        option1_hash = option1.save()

        # Add option without address or signature
        state.add_option(timestamp, option1_hash)

        # Verify no null entries were created
        assert None not in state.signatures
        assert len(state.signatures) == 0

        # Create and add second option with just address but no signature
        option2 = HivemindOption()
        option2.set_issue(issue_hash)
        option2.set("test option 2")
        option2_hash = option2.save()
        state.add_option(timestamp, option2_hash, address="test_address")

        # Verify still no null entries
        assert None not in state.signatures
        assert len(state.signatures) == 0
