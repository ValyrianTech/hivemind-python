#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, test_keypair,
    sign_message, generate_bitcoin_keypair
)


@pytest.mark.author
class TestHivemindStateAuthor:
    """Tests for the author field and authorized consensus selection."""

    def test_set_author(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test setting the author of a hivemind state."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = address
        
        # Save and reload to ensure the author is persisted
        state_hash = state.save()
        new_state = HivemindState(cid=state_hash)
        
        # Verify the author was saved
        assert new_state.author == address
    
    def test_select_consensus_with_author(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus requires a valid signature from the author."""
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
            option.set_hivemind_issue(issue_hash)
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
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Verify state is not final before selecting consensus
        assert not state.final
        
        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, private_key)
        
        # Select consensus with valid author signature
        selection = state.select_consensus(timestamp=timestamp, address=address, signature=signature)
        
        # Verify state is now final
        assert state.final
        assert len(selection) > 0
    
    def test_select_consensus_without_author(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus works without an author if none is set."""
        private_key, address = test_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Ensure no author is set
        state.author = None
        
        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
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
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Verify state is not final before selecting consensus
        assert not state.final
        
        # Select consensus without author parameters (should work since no author is set)
        selection = state.select_consensus()
        
        # Verify state is now final
        assert state.final
        assert len(selection) > 0
    
    def test_select_consensus_invalid_signature(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test that select_consensus fails with an invalid signature."""
        # Generate two different keypairs
        author_keypair = generate_bitcoin_keypair()
        author_private_key, author_address = author_keypair
        
        user_keypair = generate_bitcoin_keypair()
        user_private_key, user_address = user_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = author_address
        
        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, user_private_key)
            state.add_option(timestamp, option_hash, user_address, signature)
        
        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[user_address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, user_private_key)
        state.add_opinion(timestamp, opinion_hash, signature, user_address)
        
        # Generate timestamp and signature with the wrong private key
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, user_private_key)  # Using user's key, not author's
        
        # Attempt to select consensus with invalid signature
        with pytest.raises(Exception, match='Invalid signature'):
            state.select_consensus(timestamp=timestamp, address=author_address, signature=signature)
        
        # Verify state is still not final
        assert not state.final
    
    def test_select_consensus_wrong_address(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test that select_consensus fails when called by a non-author address."""
        # Generate two different keypairs
        author_keypair = generate_bitcoin_keypair()
        author_private_key, author_address = author_keypair
        
        user_keypair = generate_bitcoin_keypair()
        user_private_key, user_address = user_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Set the author
        state.author = author_address
        
        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, user_private_key)
            state.add_option(timestamp, option_hash, user_address, signature)
        
        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[user_address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, user_private_key)
        state.add_opinion(timestamp, opinion_hash, signature, user_address)
        
        # Generate timestamp and signature with the user's key
        timestamp = int(time.time())
        message = f"{timestamp}select_consensus"
        signature = sign_message(message, user_private_key)
        
        # Attempt to select consensus with wrong address
        with pytest.raises(Exception, match='Not authorized'):
            state.select_consensus(timestamp=timestamp, address=user_address, signature=signature)
        
        # Verify state is still not final
        assert not state.final
