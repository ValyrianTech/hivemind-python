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


@pytest.mark.opinion_cids
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
            option.set_issue(issue_hash)
            option.set(f"Option {i + 1}")
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
        opinion_hash = opinion.save()  # Save will use the data we just set

        # Initialize participants dictionary and add participant
        state.participants = {}
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}

        # Test with invalid signature
        with pytest.raises(Exception, match='invalid'):
            state.add_opinion(timestamp, opinion_hash, address, 'invalid_sig')

        # Test with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Verify opinion was added
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_hash  # First question's opinions
        assert address in state.participants

        # Test adding opinion when state is final
        state.final = True
        new_opinion = HivemindOpinion()
        new_opinion.hivemind_id = issue_hash
        new_opinion.question_index = 0
        new_opinion.ranking.set_fixed(options)
        new_opinion_hash = new_opinion.save()

        # Try to add opinion when state is final
        new_timestamp = timestamp + 1
        message = f"{new_timestamp}{new_opinion_hash}"
        signature = sign_message(message, private_key)
        
        # Expect an exception when trying to add opinion to a finalized state
        with pytest.raises(Exception, match='Can not add opinion: hivemind state is finalized'):
            state.add_opinion(new_timestamp, new_opinion_hash, address, signature)

        # Verify the opinion was not added (state remained unchanged)
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_hash  # Original opinion still there

        # Reset final flag to allow adding new opinions
        state.final = False

        # Test adding opinion with higher question index
        higher_index_opinion = HivemindOpinion()
        higher_index_opinion.hivemind_id = issue_hash
        higher_index_opinion.question_index = 2  # Set a higher question index
        higher_index_opinion.ranking.set_fixed(options)
        higher_index_hash = higher_index_opinion.save()

        # Add the opinion with higher index
        new_timestamp = timestamp + 2
        message = f"{new_timestamp}{higher_index_hash}"
        signature = sign_message(message, private_key)

        state.add_opinion(new_timestamp, higher_index_hash, address, signature)

        # Verify opinions list was extended and opinion was added
        assert len(state.opinion_cids) == 3  # Should have lists for indices 0, 1, and 2
        assert isinstance(state.opinion_cids[1], dict)  # Middle index should be empty dict
        assert state.opinion_cids[2][address]['opinion_cid'] == higher_index_hash  # New opinion at index 2

        # Test adding invalid opinion (with non-existent option)
        invalid_opinion = HivemindOpinion()
        invalid_opinion.hivemind_id = issue_hash
        invalid_opinion.question_index = 0
        invalid_opinion.ranking.set_fixed(options + ['non_existent_option'])  # Add non-existent option
        invalid_opinion_hash = invalid_opinion.save()

        # Try to add invalid opinion
        new_timestamp = timestamp + 3
        message = f"{new_timestamp}{invalid_opinion_hash}"
        signature = sign_message(message, private_key)

        with pytest.raises(Exception, match='Opinion is invalid: contains options that do not exist in the hivemind state'):
            state.add_opinion(new_timestamp, invalid_opinion_hash, address, signature)

    def test_opinions_info(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test the opinions_info method."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add an option first
        option = HivemindOption()
        option.set_issue(issue_hash)
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
        opinion_hash = opinion.save()

        # Add the opinion to the state
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Get the opinions info
        info = state.opinions_info()

        # Verify the output format
        assert "Opinions" in info
        assert "========" in info
        assert f"Timestamp: {timestamp}" in info

    def test_load_state_opinions_none(self, basic_issue: HivemindIssue) -> None:
        """Test loading state with opinions attribute set to None."""
        # First test loading state with questions
        issue_hash = basic_issue.save()

        # Create a new state and set the issue
        state = HivemindState()
        state.set_hivemind_issue(issue_hash)

        # Set opinions to None
        state.opinion_cids = None
        state_hash = state.save()

        # Load state in a new instance
        loaded_state = HivemindState()
        loaded_state.load(state_hash)

        # Verify opinions list was initialized correctly
        assert len(loaded_state.opinion_cids) == len(basic_issue.questions)
        assert all(isinstance(opinions, dict) for opinions in loaded_state.opinion_cids)

    def test_add_opinion_with_dict_ranking(self, state: HivemindState, test_keypair) -> None:
        """Test adding opinions with dictionary-based rankings.
        
        This test specifically targets the code in state.py lines 266-276 that handles
        converting dictionary-based rankings to Ranking objects.
        """
        private_key, address = test_keypair

        # Create a numeric issue for testing auto rankings
        numeric_issue = HivemindIssue()
        numeric_issue.name = "Numeric Test Issue"
        numeric_issue.add_question("Numeric Test Question")
        numeric_issue.description = "Test Description"
        numeric_issue.tags = ["test"]
        numeric_issue.answer_type = "Integer"  # Set answer type to Integer
        numeric_issue.constraints = {}
        numeric_issue.restrictions = {}
        issue_hash = numeric_issue.save()

        state.set_hivemind_issue(issue_hash)

        # Add numeric options
        options = []
        for i in range(3):
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(i + 1)  # Numeric values: 1, 2, 3
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Initialize participants dictionary and add participant
        state.participants = {}
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}

        # Create a mock HivemindOpinion that will directly test the dictionary-based ranking conversion
        # This is a more direct approach to ensure we hit lines 266-276 in state.py

        # Test with auto_high dictionary ranking
        from ipfs_dict_chain.IPFSDict import IPFSDict

        # Create an opinion with a dictionary ranking that will be loaded from IPFS
        opinion_dict = IPFSDict()
        opinion_dict['hivemind_id'] = issue_hash
        opinion_dict['question_index'] = 0
        # This is the key part - setting the ranking as a dictionary directly
        opinion_dict['ranking'] = {'auto_high': options[0]}
        opinion_auto_high_hash = opinion_dict.save()

        # Add the opinion with auto_high ranking
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_auto_high_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_auto_high_hash, address, signature)

        # Verify opinion was added
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_auto_high_hash

        # Test with auto_low dictionary ranking
        opinion_dict = IPFSDict()
        opinion_dict['hivemind_id'] = issue_hash
        opinion_dict['question_index'] = 0
        # Setting the ranking as a dictionary directly
        opinion_dict['ranking'] = {'auto_low': options[1]}
        opinion_auto_low_hash = opinion_dict.save()

        # Add the opinion with auto_low ranking
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_auto_low_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_auto_low_hash, address, signature)

        # Verify opinion was added
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_auto_low_hash

        # Test with fixed dictionary ranking
        opinion_dict = IPFSDict()
        opinion_dict['hivemind_id'] = issue_hash
        opinion_dict['question_index'] = 0
        # Setting the ranking as a dictionary directly
        opinion_dict['ranking'] = {'fixed': options}
        opinion_fixed_hash = opinion_dict.save()

        # Add the opinion with fixed ranking
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_fixed_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_fixed_hash, address, signature)

        # Verify opinion was added
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_fixed_hash

    def test_get_opinion(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test getting an opinion from the state."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Create and add an option first
        option = HivemindOption()
        option.set_issue(issue_hash)
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
        opinion_hash = opinion.save()

        # Add the opinion to the state
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Create a new state instance and load the saved state
        state_hash = state.save()
        new_state = HivemindState(cid=state_hash)

        # Test getting the opinion that's already in state
        retrieved_opinion = new_state.get_opinion(opinion_hash)
        assert retrieved_opinion is not None
        assert retrieved_opinion.cid().replace('/ipfs/', '') == opinion_hash.replace('/ipfs/', '')

        # Test getting an opinion with /ipfs/ prefix
        prefixed_hash = f"/ipfs/{opinion_hash}"
        retrieved_opinion = new_state.get_opinion(prefixed_hash)
        assert retrieved_opinion is not None
        assert retrieved_opinion.cid().replace('/ipfs/', '') == opinion_hash.replace('/ipfs/', '')

        # Test getting a new opinion not in state
        new_opinion = HivemindOpinion()
        new_opinion.hivemind_id = issue_hash
        new_opinion.question_index = 0
        new_opinion.ranking.set_fixed([option_hash])
        new_opinion_hash = new_opinion.save()

        retrieved_new_opinion = new_state.get_opinion(new_opinion_hash)
        assert retrieved_new_opinion is not None
        assert retrieved_new_opinion.cid().replace('/ipfs/', '') == new_opinion_hash.replace('/ipfs/', '')
