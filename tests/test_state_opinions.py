#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from ipfs_dict_chain.IPFS import connect, IPFSError
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage
import random
import pytest
from typing import Dict, Any, Tuple, List
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)

@pytest.mark.opinions
class TestHivemindStateOpinions:
    """Tests for opinion management."""
    
    def test_add_opinion(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test adding opinions."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add options first
        options = []
        for i in range(3):
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(f"Option {i+1}")
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)  # First address prefers red > blue > green
        opinion.ranking = opinion.ranking.get()  # Get serializable representation
        opinion_hash = opinion.save()  # Save will use the data we just set
        
        # Initialize participants dictionary and add participant
        state.participants = {}
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Test with invalid signature
        with pytest.raises(Exception, match='invalid'):
            state.add_opinion(timestamp, opinion_hash, 'invalid_sig', address)
        
        # Test with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Verify opinion was added
        assert state.opinions[0][address]['opinion_cid'] == opinion_hash  # First question's opinions
        assert address in state.participants
        
        # Test adding opinion when state is final
        state.final = True
        new_opinion = HivemindOpinion()
        new_opinion.hivemind_id = issue_hash
        new_opinion.question_index = 0
        new_opinion.ranking.set_fixed(options)
        new_opinion.ranking = new_opinion.ranking.get()
        new_opinion_hash = new_opinion.save()
        
        # Try to add opinion when state is final
        new_timestamp = timestamp + 1
        message = f"{new_timestamp}{new_opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(new_timestamp, new_opinion_hash, signature, address)
        
        # Verify the opinion was not added (state remained unchanged)
        assert state.opinions[0][address]['opinion_cid'] == opinion_hash  # Original opinion still there

        # Test adding opinion with higher question index
        higher_index_opinion = HivemindOpinion()
        higher_index_opinion.hivemind_id = issue_hash
        higher_index_opinion.question_index = 2  # Set a higher question index
        higher_index_opinion.ranking.set_fixed(options)
        higher_index_opinion.ranking = higher_index_opinion.ranking.get()
        higher_index_hash = higher_index_opinion.save()

        # Add the opinion with higher index
        new_timestamp = timestamp + 2
        message = f"{new_timestamp}{higher_index_hash}"
        signature = sign_message(message, private_key)
        
        # Reset final flag to allow adding new opinion
        state.final = False
        state.add_opinion(new_timestamp, higher_index_hash, signature, address)

        # Verify opinions list was extended and opinion was added
        assert len(state.opinions) == 3  # Should have lists for indices 0, 1, and 2
        assert isinstance(state.opinions[1], dict)  # Middle index should be empty dict
        assert state.opinions[2][address]['opinion_cid'] == higher_index_hash  # New opinion at index 2

        # Test adding invalid opinion (with non-existent option)
        invalid_opinion = HivemindOpinion()
        invalid_opinion.hivemind_id = issue_hash
        invalid_opinion.question_index = 0
        invalid_opinion.ranking.set_fixed(options + ['non_existent_option'])  # Add non-existent option
        invalid_opinion.ranking = invalid_opinion.ranking.get()
        invalid_opinion_hash = invalid_opinion.save()

        # Try to add invalid opinion
        new_timestamp = timestamp + 3
        message = f"{new_timestamp}{invalid_opinion_hash}"
        signature = sign_message(message, private_key)
        
        with pytest.raises(Exception, match='Opinion is invalid'):
            state.add_opinion(new_timestamp, invalid_opinion_hash, signature, address)

    def test_opinions_info(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test the opinions_info method."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add an option first
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set("Test Option")
        option_hash = option.save()
        
        # Sign and add option
        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        
        # Create and add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Add the opinion to the state
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Get the opinions info
        info = state.opinions_info()
        
        # Verify the output format
        assert "Opinions" in info
        assert "========" in info
        assert f"Timestamp: {timestamp}" in info
