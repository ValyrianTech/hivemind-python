#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.restrictions
class TestHivemindStateRestrictions:
    """Tests for state restrictions."""

    def test_options_per_address_limit(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test the options_per_address restriction.
        
        Tests:
        1. Options can be added up to the limit
        2. Options beyond the limit are rejected
        3. Different addresses have independent limits
        4. The limit persists across multiple operations
        """
        # Generate test keypairs
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()

        # Set restrictions
        basic_issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        timestamp = int(time.time())

        # Helper to create option
        def create_option(content: str) -> str:
            option = HivemindOption()
            option.set_issue(issue_hash)
            option.set(content)
            return option.save()

        # Test address 1 can add up to limit
        option1_hash = create_option("option1 from addr1")
        option2_hash = create_option("option2 from addr1")

        # Both options should succeed
        message1 = f"{timestamp}{option1_hash}"
        signature1 = sign_message(message1, private_key1)
        state.add_option(timestamp, option1_hash, address1, signature1)

        message2 = f"{timestamp}{option2_hash}"
        signature2 = sign_message(message2, private_key1)
        state.add_option(timestamp, option2_hash, address1, signature2)

        # Third option should fail
        option3_hash = create_option("option3 from addr1")
        message3 = f"{timestamp}{option3_hash}"
        signature3 = sign_message(message3, private_key1)
        with pytest.raises(Exception, match='already added too many options'):
            state.add_option(timestamp, option3_hash, address1, signature3)

        # Test address 2 has independent limit
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")

        # Both options should succeed for address 2
        message4 = f"{timestamp}{option4_hash}"
        signature4 = sign_message(message4, private_key2)
        state.add_option(timestamp, option4_hash, address2, signature4)

        message5 = f"{timestamp}{option5_hash}"
        signature5 = sign_message(message5, private_key2)
        state.add_option(timestamp, option5_hash, address2, signature5)

        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        message6 = f"{timestamp}{option6_hash}"
        signature6 = sign_message(message6, private_key2)
        with pytest.raises(Exception, match='already added too many options'):
            state.add_option(timestamp, option6_hash, address2, signature6)

    def test_get_weight_none_restrictions(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test that get_weight handles None restrictions correctly.
        
        This verifies the fix for a bug where get_weight would fail when trying to
        access restrictions that were None.
        """
        # Set up issue with no restrictions
        basic_issue.restrictions = None
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Should return default weight of 1.0 without error
        weight = state.get_weight("test_address")
        assert weight == 1.0

        # Set empty restrictions
        basic_issue.restrictions = {}
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Should still return default weight
        weight = state.get_weight("test_address")
        assert weight == 1.0

        # Set restrictions but without weights
        basic_issue.restrictions = {"addresses": ["test_address"]}
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Should still return default weight
        weight = state.get_weight("test_address")
        assert weight == 1.0
