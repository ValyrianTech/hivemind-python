#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)

@pytest.mark.options
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
        for option_hash in state.options:
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
        for option_hash in state.options:
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
        option.set_hivemind_issue(issue_hash)
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
        assert option_hash in state.options

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
        for i, option_hash in enumerate(state.options, 1):
            option = HivemindOption(cid=option_hash)
            assert f'Option {i}:' in info
            assert option.info() in info
