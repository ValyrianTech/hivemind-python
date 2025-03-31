#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.errors
class TestHivemindStateErrors:
    """Tests for error handling in HivemindState."""

    def test_invalid_state_loading(self, state: HivemindState) -> None:
        """Test loading invalid state data."""
        with pytest.raises(Exception):
            state.load('invalid_cid')

    def test_verify_message_error_handling(self, state: HivemindState, test_keypair) -> None:
        """Test error handling in verify_message."""
        private_key, address = test_keypair

        # Test with invalid signature
        message = "test_message"
        timestamp = int(time.time())
        invalid_signature = "invalid_signature"

        with pytest.raises(Exception):
            state.verify_message(address, timestamp, message, invalid_signature)

    def test_add_option_error_handling(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test error handling in add_option."""
        private_key, address = test_keypair

        # Test adding option without setting hivemind issue
        timestamp = int(time.time())
        option_hash = "some_option_hash"
        # Should return silently without error when no hivemind issue is set
        state.add_option(timestamp, option_hash, address, "some_signature")

        # Now set up the issue for remaining tests
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Test with invalid option CID
        timestamp = int(time.time())
        invalid_option_hash = "invalid_option_hash"
        message = f"{timestamp}{invalid_option_hash}"
        signature = sign_message(message, private_key)

        with pytest.raises(Exception):
            state.add_option(timestamp, invalid_option_hash, address, signature)

        # Test with invalid option value
        option = HivemindOption()
        option.set_issue(issue_hash)
        with pytest.raises(Exception):
            option.set("invalid_color")  # Not in color_choice_issue constraints

        # Test with invalid signature
        valid_option = HivemindOption()
        valid_option.set_issue(issue_hash)
        valid_option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        valid_option.text = color_choice_issue.constraints['choices'][0]['text']
        valid_option_hash = valid_option.save()

        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_option(timestamp, valid_option_hash, address, invalid_signature)

        # Test adding duplicate option
        # First add a valid option
        valid_signature = sign_message(f"{timestamp}{valid_option_hash}", private_key)
        state.add_option(timestamp, valid_option_hash, address, valid_signature)

        # Try to add the same option again
        with pytest.raises(Exception, match="Option already exists"):
            state.add_option(timestamp, valid_option_hash, address, valid_signature)

        # Test adding option to finalized issue
        state.final = True
        with pytest.raises(Exception, match='Can not add option: hivemind state is finalized'):
            state.add_option(timestamp, valid_option_hash, address, signature)

    def test_add_opinion_error_handling(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test error handling in add_opinion."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add a valid option first
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        option.text = color_choice_issue.constraints['choices'][0]['text']
        option_hash = option.save()

        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)

        # Test with invalid opinion CID
        invalid_opinion_hash = "invalid_opinion_hash"
        message = f"{timestamp}{invalid_opinion_hash}"
        signature = sign_message(message, private_key)

        with pytest.raises(Exception):
            state.add_opinion(timestamp, invalid_opinion_hash, address, signature)

        # Create an opinion with empty ranking (this should be valid)
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([])  # Empty ranking is allowed
        opinion_hash = opinion.save()

        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)

        # Empty rankings should be allowed
        state.add_opinion(timestamp, opinion_hash, address, signature)

        # Test with invalid signature
        valid_opinion = HivemindOpinion()
        valid_opinion.hivemind_id = issue_hash
        valid_opinion.question_index = 0
        valid_opinion.ranking.set_fixed([option_hash])
        valid_opinion.ranking = valid_opinion.ranking.get()
        valid_opinion_hash = valid_opinion.save()

        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_opinion(timestamp, valid_opinion_hash, address, invalid_signature)

    def test_ranking_options_error_handling(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair, monkeypatch) -> None:
        """Test error handling when getting ranking options in add_opinion."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add options first
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set("Test Option")
        option_hash = option.save()

        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)

        # Create a valid opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])  # Set a valid ranking
        opinion.ranking = opinion.ranking.to_dict()  # Use to_dict() to make it JSON serializable
        opinion_hash = opinion.save()

        # Sign the opinion
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)

        # Create a patched version of the ranking.get method that raises an exception
        def mock_get(*args, **kwargs):
            raise ValueError("Mock error in ranking.get()")

        # Create a patched version of the Ranking class
        from hivemind.ranking import Ranking
        original_get = Ranking.get

        # Patch the Ranking.get method to raise an exception
        monkeypatch.setattr(Ranking, 'get', mock_get)

        # Test that the error in ranking.get() is properly handled
        with pytest.raises(Exception, match="Error validating opinion: Mock error in ranking.get()"):
            state.add_opinion(timestamp, opinion_hash, address, signature)

        # Restore the original method
        monkeypatch.setattr(Ranking, 'get', original_get)
