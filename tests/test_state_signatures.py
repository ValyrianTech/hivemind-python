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
    pass  # Add signature management tests here

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
