#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, test_keypair,
    sign_message, generate_bitcoin_keypair
)


@pytest.mark.consensus
class TestHivemindStateSelectConsensus:
    """Tests for specific coverage of the select_consensus method."""

    def test_select_consensus_already_finalized(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that select_consensus raises an error when the hivemind is already finalized."""
        private_key, address = test_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        # Set the author on the issue
        color_choice_issue.author = address
        
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
        
        # Generate timestamp and signature for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{issue_hash}"
        signature = sign_message(message, private_key)
        
        # First call to select_consensus should succeed
        selection = state.select_consensus(timestamp=timestamp, address=address, signature=signature)
        
        # Verify state is now final
        assert state.final
        assert len(selection) > 0
        
        # Second call should raise ValueError because the hivemind is already finalized
        with pytest.raises(Exception, match="Can not add option: hivemind issue is finalized"):
            state.select_consensus(timestamp=timestamp, address=address, signature=signature)

    def test_select_consensus_wrong_author(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test that select_consensus raises an error when called by a non-author address."""
        # Generate two different keypairs
        author_keypair = generate_bitcoin_keypair()
        author_private_key, author_address = author_keypair
        
        user_keypair = generate_bitcoin_keypair()
        user_private_key, user_address = user_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        # Set the author on the issue
        color_choice_issue.author = author_address
        issue_hash = color_choice_issue.save()
        
        # Create a fresh state object to ensure it's properly initialized
        state = HivemindState()
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
            signature = sign_message(message, user_private_key)
            state.add_option(timestamp, option_hash, user_address, signature)
        
        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[user_address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, user_private_key)
        state.add_opinion(timestamp, opinion_hash, user_address, signature)
        
        # Try to select consensus with wrong address (user instead of author)
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{state.hivemind_id}"
        signature = sign_message(message, user_private_key)
        
        # Should raise ValueError because only the author can select consensus
        with pytest.raises(ValueError, match=f"Only the author \\({author_address}\\) can select consensus"):
            state.select_consensus(timestamp=timestamp, address=user_address, signature=signature)

    def test_select_consensus_invalid_signature(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test that select_consensus raises an error when an invalid signature is provided."""
        # Generate keypair for the author
        author_keypair = generate_bitcoin_keypair()
        author_private_key, author_address = author_keypair
        
        # Generate a different keypair for creating an invalid signature
        other_keypair = generate_bitcoin_keypair()
        other_private_key, other_address = other_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
        # Set the author on the issue
        color_choice_issue.author = author_address
        issue_hash = color_choice_issue.save()
        
        # Create a fresh state object to ensure it's properly initialized
        state = HivemindState()
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
            signature = sign_message(message, author_private_key)
            state.add_option(timestamp, option_hash, author_address, signature)
        
        # Add an opinion to ensure we have a consensus
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion_hash = opinion.save()
        
        # Initialize participants dictionary and add participant
        timestamp = int(time.time())
        state.participants[author_address] = {'name': 'Author User', 'timestamp': timestamp}
        
        # Add opinion with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, author_private_key)
        state.add_opinion(timestamp, opinion_hash, author_address, signature)
        
        # Generate timestamp and create a message for consensus selection
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{state.hivemind_id}"
        
        # Create an invalid signature using the other private key
        invalid_signature = sign_message(message, other_private_key)
        
        # Should raise ValueError because the signature is invalid
        with pytest.raises(ValueError, match="Invalid signature"):
            state.select_consensus(timestamp=timestamp, address=author_address, signature=invalid_signature)

    def test_update_participant_name_finalized(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test that update_participant_name raises an error when the hivemind is finalized."""
        private_key, address = test_keypair
        
        # Set on_selection to 'Finalize'
        color_choice_issue.on_selection = 'Finalize'
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
        
        # Finalize the hivemind
        state.final = True
        
        # Try to update participant name after finalization
        timestamp = int(time.time())
        new_name = "New User Name"
        message = f"{timestamp}{new_name}"
        signature = sign_message(message, private_key)
        
        # Should raise Exception because the hivemind is finalized
        with pytest.raises(Exception, match="Can not update participant name: hivemind state is finalized"):
            state.update_participant_name(timestamp, new_name, address, signature, message)
