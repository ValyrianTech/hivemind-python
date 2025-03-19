#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.participants
class TestHivemindStateParticipants:
    """Tests for participant management."""

    def test_update_participant_name(self, state: HivemindState, test_keypair) -> None:
        """Test updating participant names."""
        private_key, address = test_keypair
        name = 'Alice'
        timestamp = int(time.time())

        # Create message and sign it
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)

        # Test with invalid signature
        with pytest.raises(Exception, match='Invalid signature'):
            state.update_participant_name(timestamp, name, address, 'fake_sig', message)

        # Test with valid signature
        state.update_participant_name(timestamp, name, address, signature, message)

        # Verify participant was added with correct name
        assert address in state.participants
        assert state.participants[address].get('name') == name

        # Test with name exceeding maximum length
        long_name = 'A' * 51  # 51 characters, exceeding the 50 character limit
        long_message = f"{timestamp}{long_name}"
        long_signature = sign_message(long_message, private_key)

        with pytest.raises(Exception, match='Name exceeds maximum length of 50 characters'):
            state.update_participant_name(timestamp, long_name, address, long_signature, long_message)


@pytest.mark.participants
class TestHivemindStateParticipantManagement:
    """Tests for participant management."""

    def test_participant_management(self, state: HivemindState, test_keypair) -> None:
        """Test participant management functions."""
        private_key, address = test_keypair
        timestamp = int(time.time())

        # Test 1: Basic participant management
        # Add participant with name
        name = "Test User"
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)
        state.update_participant_name(timestamp, name, address, signature, message)

        assert address in state.participants
        assert state.participants[address]['name'] == name
        assert name in state.signatures[address]
        assert signature in state.signatures[address][name]
        assert state.signatures[address][name][signature] == timestamp

        # Test 2: Update participant name
        new_name = "Updated User"
        new_timestamp = timestamp + 1
        new_message = f"{new_timestamp}{new_name}"
        new_signature = sign_message(new_message, private_key)
        state.update_participant_name(new_timestamp, new_name, address, signature=new_signature, message=new_message)

        assert state.participants[address]['name'] == new_name
        assert new_name in state.signatures[address]
        assert new_signature in state.signatures[address][new_name]
        assert state.signatures[address][new_name][new_signature] == new_timestamp

        # Test 3: Reject old timestamp for same name
        old_timestamp = timestamp - 1
        old_message = f"{old_timestamp}{name}"  # Try to update the same name with older timestamp
        old_signature = sign_message(old_message, private_key)
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.update_participant_name(old_timestamp, name, address, signature=old_signature, message=old_message)
        assert state.participants[address]['name'] == new_name  # Name should not change

        # Test 4: Allow old timestamp for different name
        different_name = "Different Name"
        old_message = f"{old_timestamp}{different_name}"
        old_signature = sign_message(old_message, private_key)
        # This should work since it's a different name message
        state.update_participant_name(old_timestamp, different_name, address, signature=old_signature, message=old_message)
        assert state.participants[address]['name'] == different_name

        # Test 5: Invalid signature
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception, match='Invalid signature'):
            state.update_participant_name(timestamp, name, address, signature=invalid_signature, message=message)
