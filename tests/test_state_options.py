#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.option_cids
class TestHivemindStateOptions:
    """Tests for option management."""

    def test_add_predefined_options(self, state: HivemindState, bool_issue: HivemindIssue) -> None:
        """Test adding predefined options for both boolean and choice types."""
        issue_hash = bool_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Test boolean options
        options = state.add_predefined_options()
        assert len(options) == 2

        # Verify boolean options
        option_values = []
        option_texts = []
        for option_hash in state.option_cids:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)

        assert True in option_values
        assert False in option_values
        assert "Yes" in option_texts
        assert "No" in option_texts

        # Test with color choices
        state = HivemindState()  # Reset state
        color_issue = HivemindIssue()
        color_issue.name = "Test Choice Issue"
        color_issue.add_question("What's your favorite color?")
        color_issue.description = "Choose your favorite color"
        color_issue.answer_type = "String"
        color_issue.set_constraints({
            "choices": [
                {"value": "red", "text": "Red"},
                {"value": "blue", "text": "Blue"},
                {"value": "green", "text": "Green"}
            ]
        })
        issue_hash = color_issue.save()
        state.set_hivemind_issue(issue_hash)

        options = state.add_predefined_options()
        assert len(options) == 3

        # Verify color options
        option_values = []
        option_texts = []
        for option_hash in state.option_cids:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)

        assert "red" in option_values
        assert "blue" in option_values
        assert "green" in option_values
        assert "Red" in option_texts
        assert "Blue" in option_texts
        assert "Green" in option_texts

    def test_add_option_with_restrictions(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test adding options with address restrictions."""
        # Generate test keypairs
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()

        # Set restrictions
        basic_issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        timestamp = int(time.time())

        # Test with unauthorized address
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set('test option')
        option_hash = option.save()

        # Test adding option without address/signature when restrictions are enabled
        with pytest.raises(Exception, match='Can not add option: no address or signature given'):
            state.add_option(timestamp, option_hash)

        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key3)
        with pytest.raises(Exception, match='address restrictions'):
            state.add_option(timestamp, option_hash, address3, signature)

        # Test with authorized address but invalid signature
        with pytest.raises(Exception, match='Signature is not valid'):
            state.add_option(timestamp, option_hash, address1, 'invalid_sig')

        # Test with authorized address and valid signature
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key1)
        state.add_option(timestamp, option_hash, address1, signature)
        assert option_hash in state.option_cids

    def test_get_options(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test getting the list of hivemind options."""
        # Setup state with color choice issue
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        state.add_predefined_options()

        # Manually update the _options list since it's not automatically updated after add_predefined_options
        state._options = [HivemindOption(cid=option_cid) for option_cid in state.option_cids]

        # Get options using get_options method
        options = state.get_options()

        # Verify the options list
        assert len(options) == 3
        assert all(isinstance(option, HivemindOption) for option in options)

        # Verify option values match the color choices
        option_values = [option.value for option in options]
        assert "red" in option_values
        assert "blue" in option_values
        assert "green" in option_values

        # Verify option texts match the color choices
        option_texts = [option.text for option in options]
        assert "Red" in option_texts
        assert "Blue" in option_texts
        assert "Green" in option_texts

    def test_options_info(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test getting formatted information about all options."""
        # Setup state with color choice issue
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        state.add_predefined_options()

        # Get options info
        info = state.options_info()

        # Verify the format and content
        assert info.startswith("Options\n=======")

        # Verify each option is included
        for i, option_hash in enumerate(state.option_cids, 1):
            option = HivemindOption(cid=option_hash)
            assert f'Option {i}:' in info
            assert option.info() in info

    def test_prevent_duplicate_value_options(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test that options with the same value but different text cannot be added."""
        # Setup
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate test keypair
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Create and add first option
        option1 = HivemindOption()
        option1.set_issue(issue_hash)
        option1.set("test_value")
        option1.text = "First option text"
        option1_hash = option1.save()
        
        message = f"{timestamp}{option1_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option1_hash, address, signature)
        
        # Verify first option was added
        assert option1_hash in state.option_cids
        
        # Create second option with same value but different text
        timestamp = int(time.time())  # Update timestamp for new signature
        option2 = HivemindOption()
        option2.set_issue(issue_hash)
        option2.set("test_value")  # Same value
        option2.text = "Second option text"  # Different text
        option2_hash = option2.save()
        
        # Verify it's a different option (different CID)
        assert option1_hash != option2_hash
        
        # Try to add second option with same value
        message = f"{timestamp}{option2_hash}"
        signature = sign_message(message, private_key)
        
        # This should raise an exception
        with pytest.raises(Exception, match="Option with value 'test_value' already exists with different text"):
            state.add_option(timestamp, option2_hash, address, signature)
            
        # Verify second option was not added
        assert option2_hash not in state.option_cids
