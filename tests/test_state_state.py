#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from .test_state_common import (
    state, basic_issue, color_choice_issue, bool_issue, test_keypair,
    TestHelper, sign_message, generate_bitcoin_keypair
)


@pytest.mark.state
class TestHivemindStateManagement:
    """Tests for state management."""

    def test_info(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test the info() method output."""
        # Set up initial state
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add some predefined options
        basic_issue.answer_type = "String"
        basic_issue.set_constraints({
            "choices": [
                {"value": "option1", "text": "Option 1"},
                {"value": "option2", "text": "Option 2"}
            ]
        })

        # Add options
        private_key, address = test_keypair
        timestamp = int(time.time())

        helper = TestHelper()
        option1_hash = helper.create_and_sign_option(
            state, issue_hash, "option1", "Option 1",
            private_key, address, timestamp
        )
        option2_hash = helper.create_and_sign_option(
            state, issue_hash, "option2", "Option 2",
            private_key, address, timestamp + 1
        )

        # Add an opinion
        ranking = [option1_hash, option2_hash]
        helper.create_and_sign_opinion(
            state, issue_hash, ranking,
            private_key, address, timestamp + 2
        )

        # Get the info output
        info_output = state.info()

        # Verify all components are present
        assert "================================================================================" in info_output
        assert "Hivemind id: " in info_output
        assert "Hivemind main question: Test Question" in info_output
        assert "Hivemind description: Test Description" in info_output
        assert "Hivemind tags: test" in info_output
        assert "Answer type: String" in info_output
        assert "Option constraints:" in info_output

        # Verify options info is included
        assert "Options\n=======" in info_output
        assert "Option 1:" in info_output
        assert "Option 2:" in info_output

        # Verify opinions and results are included
        assert "Opinions\n========" in info_output
        assert "Results:\n========" in info_output

        # Verify the separator is present at the end of sections
        assert info_output.count("================================================================================") >= 2


@pytest.mark.state
class TestHivemindStateVerification:
    """Tests for state verification functions."""

    def test_state_verification(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test state verification functions."""
        # Set up initial state
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('Test Question?')
        issue.description = 'Test description'
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())

        # Test first signature
        message = "test_message"
        signature = sign_message(message, private_key)
        state.add_signature(address, timestamp, message, signature)
        assert address in state.signatures
        assert message in state.signatures[address]
        assert signature in state.signatures[address][message]

        # Test duplicate signature with same timestamp (should fail)
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, timestamp, message, signature)
        assert 'Invalid timestamp' in str(Exception)

        # Test older timestamp (should fail)
        older_timestamp = timestamp - 1
        older_signature = sign_message(message, private_key)
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, older_timestamp, message, older_signature)
        assert 'Invalid timestamp' in str(Exception)

        # Test newer timestamp (should succeed)
        newer_timestamp = timestamp + 1
        newer_signature = sign_message(message, private_key)
        state.add_signature(address, newer_timestamp, message, newer_signature)
        assert newer_signature in state.signatures[address][message]

        # Test state finalization
        state.final = True
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set("New Option")
        option_hash = option.save()

        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)

        # Should not be able to add options when state is final
        with pytest.raises(Exception):
            state.add_option(timestamp, option_hash, address, signature)


@pytest.mark.state
class TestHivemindStateOpinionTimestampValidation:
    """Tests for opinion timestamp validation."""

    def test_add_opinion_timestamp_validation(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test opinion timestamp validation when adding opinions."""
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('Test Question?')
        issue.description = 'Test description'
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp1 = int(time.time())

        # Add first opinion
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue_hash
        opinion1.question_index = 0
        opinion1.ranking.set_fixed([])
        opinion1_hash = opinion1.save()

        message1 = f"{timestamp1}{opinion1_hash}"
        signature1 = sign_message(message1, private_key)
        state.add_opinion(timestamp1, opinion1_hash, address, signature1)

        # Try to add opinion with older timestamp
        time.sleep(1)  # Ensure we have a different timestamp
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue_hash
        opinion2.question_index = 0
        opinion2.ranking.set_fixed([])
        opinion2_hash = opinion2.save()

        old_timestamp = timestamp1 - 10
        message2 = f"{old_timestamp}{opinion2_hash}"
        signature2 = sign_message(message2, private_key)

        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_opinion(old_timestamp, opinion2_hash, address, signature2)

        # Add opinion with newer timestamp should succeed
        new_timestamp = int(time.time())
        message3 = f"{new_timestamp}{opinion2_hash}"
        signature3 = sign_message(message3, private_key)
        state.add_opinion(new_timestamp, opinion2_hash, address, signature3)

        # Verify the opinion was updated
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion2_hash
        assert state.opinion_cids[0][address]['timestamp'] == new_timestamp


@pytest.mark.state
class TestHivemindStateVerification:
    """Tests for state verification."""

    def test_state_verification(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test state verification functions."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # 1. Test option verification
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        option.text = color_choice_issue.constraints['choices'][0]['text']
        option_hash = option.save()

        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)

        # Valid option should be added
        state.add_option(timestamp, option_hash, address, signature)
        assert option_hash in state.option_cids

        # 2. Test opinion verification
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])
        opinion_hash = opinion.save()

        # Add participant
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}

        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)

        # Valid opinion should be added
        state.add_opinion(timestamp, opinion_hash, address, signature)
        assert state.opinion_cids[0][address]['opinion_cid'] == opinion_hash

        # 3. Test participant verification
        name = "Test User"
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)

        # Valid participant update should work
        state.update_participant_name(timestamp, name, address, signature, message)
        assert state.participants[address]['name'] == name

        # 4. Test signature verification
        test_message = "test_message"
        message = f"{timestamp}{test_message}"
        signature = sign_message(message, private_key)

        # Valid signature should be added
        state.add_signature(address, timestamp, test_message, signature)
        assert test_message in state.signatures[address]
        assert signature in state.signatures[address][test_message]
