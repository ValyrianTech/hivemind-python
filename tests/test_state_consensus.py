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


@pytest.mark.consensus
class TestHivemindStateConsensus:
    """Tests for consensus calculation."""

    def test_calculate_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test calculating results."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add opinions
        base_timestamp = int(time.time())
        for i in range(3):
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = 0
            opinion.ranking.set_fixed(options)  # First address prefers red > blue > green
            opinion_hash = opinion.save()

            # Initialize participants dictionary and add participant
            current_timestamp = base_timestamp + i  # Ensure unique, increasing timestamps
            state.participants[address] = {'name': f'Test User {i + 1}', 'timestamp': current_timestamp}

            # Test with valid signature
            message = f"{current_timestamp}{opinion_hash}"
            signature = sign_message(message, private_key)
            state.add_opinion(current_timestamp, opinion_hash, address, signature)

        # Calculate results
        results = state.calculate_results()

        # Verify results structure
        for option_hash in options:
            assert option_hash in results
            assert 'win' in results[option_hash]
            assert 'loss' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]

        # Verify red wins (2 first-place votes vs 1 for blue)
        red_option = HivemindOption(cid=options[0])
        assert red_option.value == 'red'
        assert results[options[0]]['score'] > results[options[1]]['score']

    def test_get_score(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test getting score for a specific option."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion that ranks red > blue > green
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Add the opinion to the state
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Get score for each option and verify they are valid
        for option_hash in options:
            score = state.get_score(option_hash)
            assert isinstance(score, float)
            assert 0 <= score <= 1  # Scores should be normalized between 0 and 1

        # Verify first option (red) has highest score
        red_score = state.get_score(options[0])
        blue_score = state.get_score(options[1])
        green_score = state.get_score(options[2])
        assert red_score > blue_score
        assert blue_score > green_score

        # Test with question_index parameter
        red_score_q0 = state.get_score(options[0], question_index=0)
        assert red_score_q0 == red_score  # Should be same as default question_index=0


@pytest.mark.consensus
class TestHivemindStateRankedConsensus:
    """Tests for ranked consensus calculation."""

    def test_ranked_consensus(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test ranked consensus calculation."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add opinions with different rankings
        rankings = [
            options,  # red > blue > green
            [options[1], options[0], options[2]],  # blue > red > green
            [options[0], options[2], options[1]]  # red > green > blue
        ]

        # Generate different key pairs for each opinion
        keypairs = [test_keypair] + [generate_bitcoin_keypair() for _ in range(2)]

        for i, (ranking, (voter_key, voter_address)) in enumerate(zip(rankings, keypairs)):
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = 0
            opinion.ranking.set_fixed(ranking)
            opinion_hash = opinion.save()

            # Initialize participants dictionary and add participant
            timestamp = int(time.time())
            state.participants[voter_address] = {'name': f'Test User {i + 1}', 'timestamp': timestamp}

            # Add opinion with valid signature
            message = f"{timestamp}{opinion_hash}"
            signature = sign_message(message, voter_key)
            state.add_opinion(timestamp, opinion_hash, voter_address, signature)

        # Calculate ranked consensus
        sorted_options = state.get_sorted_options()

        # Verify ranked consensus
        assert len(sorted_options) == 3
        # Red should win (2 first-place votes)
        assert sorted_options[0].value == 'red'
        # Blue should be second (1 first-place vote)
        assert sorted_options[1].value == 'blue'
        # Green should be last (0 first-place votes)
        assert sorted_options[2].value == 'green'

    def test_compare_edge_cases(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test edge cases in option comparison where options are not in the ranking."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Create three options
        helper = TestHelper()
        first_hash = helper.create_and_sign_option(
            state, issue_hash, "first", "First Option", private_key, address, int(time.time())
        )
        second_hash = helper.create_and_sign_option(
            state, issue_hash, "second", "Second Option", private_key, address, int(time.time())
        )
        unranked_hash = helper.create_and_sign_option(
            state, issue_hash, "unranked", "Unranked Option", private_key, address, int(time.time())
        )

        # Create an opinion ranking only first and second
        timestamp = int(time.time())
        ranking = [first_hash, second_hash]  # Explicitly not including unranked
        opinion_hash = helper.create_and_sign_opinion(
            state, issue_hash, ranking, private_key, address, timestamp
        )

        # Test comparing ranked vs unranked option
        assert state.compare(first_hash, unranked_hash, opinion_hash) == first_hash  # ranked wins
        assert state.compare(unranked_hash, second_hash, opinion_hash) == second_hash  # ranked wins

        # Test comparing two unranked options
        another_unranked = helper.create_and_sign_option(
            state, issue_hash, "another", "Another Unranked", private_key, address, int(time.time())
        )
        assert state.compare(unranked_hash, another_unranked, opinion_hash) is None  # neither wins


@pytest.mark.consensus
class TestHivemindStateConsensusEdgeCases:
    """Tests for edge cases in consensus calculation."""

    def test_consensus_no_opinions(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test consensus methods when there are no opinions."""
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        state.add_predefined_options()

        # Test consensus with no opinions
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) == 0

        # Test ranked_consensus with no opinions
        sorted_options = state.get_sorted_options()
        ranked_values = [option.value for option in sorted_options]
        assert len(ranked_values) == 0

        # Test contributions with no opinions
        results = state.calculate_results()
        contributions = state.contributions(results)
        assert len(contributions) == 0

    def test_consensus_no_options(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test consensus when there are no options at all."""
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Get sorted options to verify it's empty
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) == 0

        # Test consensus with no options
        consensus = state.consensus()
        assert consensus is None  # This should hit line 467


@pytest.mark.consensus
class TestHivemindStateConsensusMethods:
    """Tests for consensus methods."""

    def test_consensus_methods(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus and ranked_consensus methods."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        options = state.add_predefined_options()
        option_hashes = list(options.keys())

        # Generate key pairs for multiple participants
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()

        timestamp = int(time.time())

        # First participant prefers red > blue > green
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue_hash
        opinion1.question_index = 0
        opinion1.ranking.set_fixed(option_hashes)  # First address prefers red > blue > green
        opinion1_hash = opinion1.save()

        message1 = f"{timestamp}{opinion1_hash}"
        signature1 = sign_message(message1, private_key1)
        state.add_opinion(timestamp, opinion1_hash, address1, signature1)

        # Second participant prefers blue > red > green
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue_hash
        opinion2.question_index = 0
        opinion2.ranking.set_fixed([option_hashes[1], option_hashes[0], option_hashes[2]])  # blue > red > green
        opinion2_hash = opinion2.save()

        message2 = f"{timestamp}{opinion2_hash}"
        signature2 = sign_message(message2, private_key2)
        state.add_opinion(timestamp, opinion2_hash, address2, signature2)

        # Third participant prefers red > green > blue
        opinion3 = HivemindOpinion()
        opinion3.hivemind_id = issue_hash
        opinion3.question_index = 0
        opinion3.ranking.set_fixed([option_hashes[0], option_hashes[2], option_hashes[1]])  # red > green > blue
        opinion3_hash = opinion3.save()

        message3 = f"{timestamp}{opinion3_hash}"
        signature3 = sign_message(message3, private_key3)
        state.add_opinion(timestamp, opinion3_hash, address3, signature3)

        # Test consensus method
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) > 0
        consensus_value = sorted_options[0].value
        assert consensus_value == "red"  # Red should win as it's preferred by 2 out of 3 participants

        # Test ranked_consensus method using get_sorted_options
        sorted_options = state.get_sorted_options()
        ranked_values = [option.value for option in sorted_options]
        assert len(ranked_values) == 3
        # Order should be: red (2 votes) > blue (1 vote) > green (0 votes)
        assert ranked_values[0] == "red"
        assert ranked_values[1] == "blue"
        assert ranked_values[2] == "green"

        # Test contributions method
        results = state.calculate_results()
        contributions = state.contributions(results)

        # All participants should have contributed since they all voted
        assert len(contributions) == 3
        assert address1 in contributions
        assert address2 in contributions
        assert address3 in contributions

        # Contributions should be positive for all participants
        assert all(value > 0 for value in contributions.values())


@pytest.mark.consensus
class TestHivemindStateConsensusEdgeCases:
    """Tests for edge cases in consensus calculation."""

    def test_consensus_edge_cases(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test edge cases in consensus calculation."""
        issue = HivemindIssue()
        issue.name = 'Test Consensus'
        issue.add_question('Test Question?')
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Test with no options
        results = state.calculate_results()
        assert len(results) == 0

        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())

        # Add options
        options = []
        for i in range(3):
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(f"Option {i + 1}")
            option_hash = option.save()
            options.append(option_hash)

            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Test with options but no opinions
        results = state.calculate_results()
        for option_id in results:
            assert results[option_id]['win'] == 0
            assert results[option_id]['loss'] == 0
            assert results[option_id]['unknown'] == 0
            assert results[option_id]['score'] == 0

        # Add a single opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)


@pytest.mark.consensus
class TestHivemindStateExcludeSelectionMode:
    """Tests for the 'Exclude' selection mode."""

    def test_exclude_selection_mode(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test the 'Exclude' selection mode."""
        private_key, address = test_keypair
        timestamp = int(time.time())

        # Set up issue with 'Exclude' mode
        color_choice_issue.on_selection = 'Exclude'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # No need to initialize selected list anymore as it's a flat list now

        # Create options
        options = []
        for value, text in [("red", "Red"), ("blue", "Blue")]:
            option_hash = TestHelper.create_and_sign_option(state, issue_hash, value, text, private_key, address, timestamp)
            options.append(option_hash)

        # Create and add an opinion ranking red > blue
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # First selection should be red
        selection = state.select_consensus()
        assert selection[0].replace('/ipfs/', '') == options[0]  # Red is selected
        
        # Verify the selection was added to state.selected
        assert len(state.selected) == 1  # One option selected
        assert state.selected[0] == options[0].replace('/ipfs/', '')  # Red is in selected list

    def test_results_info_excluded_options(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test results_info method when some options are excluded."""
        private_key, address = test_keypair

        # Set up issue with 'Exclude' selection mode
        color_choice_issue.on_selection = 'Exclude'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        option_values = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)
            option_values.append(choice['value'])

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Mark first option as selected to exclude it
        state.selected = [options[0]]

        # Create results dict that includes the excluded option
        results = {
            options[0]: {'score': 0.8, 'win': 2, 'loss': 0, 'unknown': 0},  # Excluded option
            options[1]: {'score': 0.6, 'win': 1, 'loss': 1, 'unknown': 0},  # Available option
        }

        # Get results info
        info = state.results_info(results)

        # Verify the first option value is not in the results info
        assert option_values[0] not in info
        # Verify the second option value is in the results info
        assert option_values[1] in info


@pytest.mark.consensus
class TestHivemindStateWeightedConsensus:
    """Tests for weighted consensus calculation."""

    def test_get_weight(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test the get_weight method with different weight restrictions."""
        # Set up issue without weight restrictions initially
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Modify restrictions to include weights using the '@' symbol
        test_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa@2.5"
        other_address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        invalid_weight_address = "1MzQwSR3s7RqxJPuQzF7Y4iybjhHNV4bZq@invalid"
        state._issue.restrictions = {
            'addresses': [test_address, other_address, invalid_weight_address]
        }

        # Test weight for address with weight
        assert state.get_weight("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") == 2.5

        # Test weight for address without weight (should return default 1.0)
        assert state.get_weight(other_address) == 1.0

        # Test weight for address with invalid weight format (should return default 1.0)
        assert state.get_weight("1MzQwSR3s7RqxJPuQzF7Y4iybjhHNV4bZq") == 1.0


@pytest.mark.consensus
class TestHivemindStateFinalizeSelectionMode:
    """Tests for the 'Finalize' selection mode."""

    def test_select_consensus_finalize(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus sets final=True when on_selection='Finalize'."""
        private_key, address = test_keypair

        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}

        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Verify state is not final before selecting consensus
        assert not state.final

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Select consensus with valid author signature
        state.select_consensus(timestamp=timestamp, address=address, signature=signature)

        # Verify state is now final
        assert state.final

        # Verify we can't add new options or opinions
        new_option = HivemindOption()
        new_option.set_issue(issue_hash)
        new_option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red' from constraints
        new_option_hash = new_option.save()

        timestamp = int(time.time())
        message = f"{timestamp}{new_option_hash}"
        signature = sign_message(message, private_key)

        with pytest.raises(Exception):
            state.add_option(timestamp, new_option_hash, address, signature)

    def test_select_consensus_finalize_with_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus sets final=True when on_selection='Finalize'."""
        private_key, address = test_keypair

        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}

        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Verify state is not final before selecting consensus
        assert not state.final

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Select consensus with valid author signature
        state.select_consensus(timestamp=timestamp, address=address, signature=signature)

        # Verify state is now final
        assert state.final

        # Verify we can't add new options or opinions
        new_option = HivemindOption()
        new_option.set_issue(issue_hash)
        new_option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red' from constraints
        new_option_hash = new_option.save()

        timestamp = int(time.time())
        message = f"{timestamp}{new_option_hash}"
        signature = sign_message(message, private_key)

        with pytest.raises(Exception):
            state.add_option(timestamp, new_option_hash, address, signature)


@pytest.mark.consensus
class TestHivemindStateResetSelectionMode:
    """Tests for the 'Reset' selection mode."""

    def test_select_consensus_reset(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus resets all opinions when on_selection='Reset'."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Add participant and opinion
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Verify opinion was added
        assert len(state.opinion_cids) > 0
        assert state.opinion_cids != [{}]

        # Set on_selection to Reset
        color_choice_issue.on_selection = 'Reset'
        state._issue = color_choice_issue

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Call select_consensus with valid author signature
        state.select_consensus(timestamp=timestamp, address=address, signature=signature)

        # Verify opinions were reset
        assert state.opinion_cids == [{}]

    def test_select_consensus_reset_with_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus resets all opinions when on_selection='Reset'."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Add participant and opinion
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Verify opinion was added
        assert len(state.opinion_cids) > 0
        assert state.opinion_cids != [{}]

        # Set on_selection to Reset
        color_choice_issue.on_selection = 'Reset'
        state._issue = color_choice_issue

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Call select_consensus with valid author signature
        state.select_consensus(timestamp=timestamp, address=address, signature=signature)

        # Verify opinions were reset
        assert state.opinion_cids == [{}]


@pytest.mark.consensus
class TestHivemindStateUnknownSelectionMode:
    """Tests for when on_selection is None."""

    def test_select_consensus_unknown_mode(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus raises NotImplementedError for unknown selection mode."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Add participant and opinion
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Set an invalid selection mode
        color_choice_issue.on_selection = 'InvalidMode'
        state._issue = color_choice_issue

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Verify NotImplementedError is raised
        with pytest.raises(NotImplementedError, match='Unknown selection mode: InvalidMode'):
            state.select_consensus(timestamp=timestamp, address=address, signature=signature)

    def test_select_consensus_unknown_mode_with_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus raises NotImplementedError for unknown selection mode."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()

        # Add participant and opinion
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Set an invalid selection mode
        color_choice_issue.on_selection = 'InvalidMode'
        state._issue = color_choice_issue

        # Calculate results
        state.calculate_results()

        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)

        # Verify NotImplementedError is raised
        with pytest.raises(NotImplementedError, match='Unknown selection mode: InvalidMode'):
            state.select_consensus(timestamp=timestamp, address=address, signature=signature)


@pytest.mark.consensus
class TestHivemindStateNullSelectionMode:
    """Tests for when on_selection is None."""

    def test_select_consensus_null_selection(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus works correctly when on_selection is None."""
        private_key, address = test_keypair

        # Set on_selection to None
        color_choice_issue.on_selection = None
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Ensure no author is set
        state.author = None

        # Add an option
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set("red")
        option.text = "Red"
        option_hash = option.save()

        # Sign and add option
        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])
        opinion_hash = opinion.save()

        # Sign and add opinion
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Select consensus
        selection = state.select_consensus()

        # Verify the selection was made but no side effects occurred
        assert selection[0].replace('/ipfs/', '') == option_hash  # The correct option was selected
        assert not state.final  # Should not be finalized
        assert len(state.opinion_cids) == 1  # Opinions should not be reset

    def test_select_consensus_null_selection_with_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus works correctly when on_selection is None."""
        private_key, address = test_keypair

        # Set on_selection to None
        color_choice_issue.on_selection = None
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Ensure no author is set
        state.author = None

        # Add an option
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set("red")
        option.text = "Red"
        option_hash = option.save()

        # Sign and add option
        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)

        # Add an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])
        opinion_hash = opinion.save()

        # Sign and add opinion
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Select consensus
        selection = state.select_consensus()

        # Verify the selection was made but no side effects occurred
        assert selection[0].replace('/ipfs/', '') == option_hash  # The correct option was selected
        assert not state.final  # Should not be finalized
        assert len(state.opinion_cids) == 1  # Opinions should not be reset


@pytest.mark.consensus
class TestHivemindStateContributions:
    """Tests for contributions calculation."""

    def test_contributions_missing_options(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test contributions calculation when opinion doesn't rank all options."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Create opinion that only ranks first two options
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options[:2])  # Only rank first two options
        opinion.ranking = opinion.ranking.to_dict()  # Convert ranking to dictionary before saving
        opinion_hash = opinion.save()

        # Add opinion
        timestamp = int(time.time())
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Calculate results and contributions
        results = state.calculate_results()
        contributions = state.contributions(results)

        # Verify contributions were calculated
        assert address in contributions
        assert isinstance(contributions[address], float)


@pytest.mark.consensus
class TestHivemindStateConsensusTie:
    """Tests for consensus calculation when there is a tie."""

    def test_consensus_tie(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus when there is a tie between the top two options."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Create two opinions that rank red first and one that ranks blue first
        # This will create a tie between red and blue
        rankings = [
            [options[0], options[1], options[2]],  # red > blue > green
            [options[1], options[0], options[2]],  # blue > red > green
        ]

        # Generate different key pairs for each opinion
        keypairs = [test_keypair] + [generate_bitcoin_keypair()]

        # Add the opinions
        for i, (ranking, (voter_key, voter_address)) in enumerate(zip(rankings, keypairs)):
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = 0
            opinion.ranking.set_fixed(ranking)
            opinion_hash = opinion.save()

            # Initialize participants dictionary and add participant
            timestamp = int(time.time())
            state.participants[voter_address] = {'name': f'Test User {i + 1}', 'timestamp': timestamp}

            # Add opinion with valid signature
            message = f"{timestamp}{opinion_hash}"
            signature = sign_message(message, voter_key)
            state.add_opinion(timestamp, opinion_hash, voter_address, signature)

        # Get consensus - should be None since there's a tie
        consensus = state.consensus()
        assert consensus is None

        # Verify that the scores are actually tied
        results = state.calculate_results()
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) >= 2
        assert results[sorted_options[0].cid().replace('/ipfs/', '')]['score'] == results[sorted_options[1].cid().replace('/ipfs/', '')]['score']


@pytest.mark.consensus
class TestHivemindStateSingleOptionConsensus:
    """Tests for consensus calculation when there is exactly one option with votes."""

    def test_consensus_single_option(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus when there is exactly one option with votes."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Create and add a single option
        helper = TestHelper()
        option_hash = helper.create_and_sign_option(
            state, issue_hash, "only_option", "Only Option", private_key, address, int(time.time())
        )

        # Create an opinion ranking the single option
        timestamp = int(time.time())
        ranking = [option_hash]
        helper.create_and_sign_opinion(
            state, issue_hash, ranking, private_key, address, timestamp
        )

        # Test consensus with single option
        consensus = state.consensus()
        assert consensus == "only_option"  # This should hit line 469


@pytest.mark.consensus
class TestHivemindStateConsensusAllBranches:
    """Tests for all branches of the consensus method."""

    def test_consensus_all_branches(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test all branches of the consensus method."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Test empty state (should hit line 467)
        assert state.consensus() is None
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) == 0

        # Create and add a single option
        helper = TestHelper()
        option_hash = helper.create_and_sign_option(
            state, issue_hash, "test_option", "Test Option", private_key, address, int(time.time())
        )

        # Add opinion to make the option have votes
        timestamp = int(time.time())
        ranking = [option_hash]
        helper.create_and_sign_opinion(
            state, issue_hash, ranking, private_key, address, timestamp
        )

        # Test single option case (should hit line 469)
        assert state.consensus() == "test_option"
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) == 1


@pytest.mark.consensus
class TestHivemindStateIncomparableOptions:
    """Tests for consensus calculation when options are incomparable."""

    def test_consensus_incomparable_options(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus calculation when options are incomparable (neither preferred over the other)."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)

            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Create an opinion that only ranks one option
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        # Only include the first option in the ranking
        opinion.ranking.set_fixed([options[0]])
        opinion_hash = opinion.save()

        # Add the opinion
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Calculate results
        results = state.calculate_results()

        # Verify that options not in the ranking have 'unknown' scores
        # When comparing options[1] and options[2], neither should be preferred
        assert results[options[1]]['unknown'] > 0
        assert results[options[2]]['unknown'] > 0

        # The first option should have some wins but no unknowns
        assert results[options[0]]['win'] > 0
        assert results[options[0]]['unknown'] == 0


@pytest.mark.consensus
class TestHivemindStateConsensusWithClearWinner:
    """Tests for consensus calculation when there is a clear winner."""

    def test_consensus_with_clear_winner(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus when there is a clear winner (no tie)."""
        private_key, address = test_keypair
        
        # Set up the issue
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add two options
        option1 = HivemindOption()
        option1.set_issue(issue_hash)
        option1.set("Option 1")
        option1_hash = option1.save()
        
        option2 = HivemindOption()
        option2.set_issue(issue_hash)
        option2.set("Option 2")
        option2_hash = option2.save()
        
        # Add options to state
        timestamp = int(time.time())
        state.add_option(timestamp, option1_hash)
        state.add_option(timestamp, option2_hash)
        
        # Create an opinion that clearly prefers option1 over option2
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option1_hash, option2_hash])
        opinion_hash = opinion.save()
        
        # Add the opinion
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)
        
        # Test consensus method - this will hit line 482
        consensus_value = state.consensus()
        assert consensus_value == "Option 1"
        
        # Test ranked_consensus method - this will hit line 494
        ranked_values = state.ranked_consensus()
        assert ranked_values == ["Option 1", "Option 2"]


@pytest.mark.consensus
class TestHivemindStateMultiQuestionConsensus:
    """Tests for consensus calculation with multiple questions."""

    def test_select_consensus_multi_question(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus properly initializes self.selected for multiple questions."""
        private_key, address = test_keypair
        
        # Modify the issue to have multiple questions
        basic_issue.add_question("Second Test Question")
        basic_issue.add_question("Third Test Question")
        assert len(basic_issue.questions) == 3  # Verify we have 3 questions
        
        # Set the issue author to our test address and set selection mode to 'Exclude'
        basic_issue.author = address
        basic_issue.on_selection = 'Exclude'  # Set this before saving the issue
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add options for each question
        options = []
        for q_idx in range(len(basic_issue.questions)):
            for i in range(3):  # Add 3 options per question
                option = HivemindOption()
                option.set_issue(issue_hash)
                option.set(f"option{q_idx}_{i}")
                option.text = f"Option {q_idx}_{i}"
                option.question_index = q_idx
                option_hash = option.save()
                options.append(option_hash)
                
                # Sign and add option
                timestamp = int(time.time()) + i  # Ensure unique timestamps
                message = f"{timestamp}{option_hash}"
                signature = sign_message(message, private_key)
                state.add_option(timestamp, option_hash, address, signature)
        
        # Add opinions for each question
        for q_idx in range(len(basic_issue.questions)):
            # Get options for this question
            q_options = [opt for i, opt in enumerate(options) if i // 3 == q_idx]
            
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = q_idx
            opinion.ranking.set_fixed(q_options)
            opinion_hash = opinion.save()
            
            # Add the opinion
            timestamp = int(time.time()) + q_idx  # Ensure unique timestamps
            state.participants[address] = {'name': f'Test User {q_idx}', 'timestamp': timestamp}
            message = f"{timestamp}{opinion_hash}"
            signature = sign_message(message, private_key)
            state.add_opinion(timestamp, opinion_hash, address, signature)
        
        # Clear selected list
        state.selected = []
        
        # Call select_consensus which should add the winner of the first question to self.selected
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{issue_hash}"
        signature = sign_message(message, private_key)
        selection = state.select_consensus(timestamp, address, signature)
        
        # Verify self.selected contains only the winner of the first question
        assert len(state.selected) == 1
        assert state.selected[0] == selection[0]
