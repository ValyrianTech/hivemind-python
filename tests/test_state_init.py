#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from hivemind import HivemindState, HivemindIssue
from tests.test_state_common import state, basic_issue, color_choice_issue, bool_issue, test_keypair


@pytest.mark.init
class TestHivemindStateInit:
    """Tests for initialization and basic state management."""

    def test_init(self, state: HivemindState) -> None:
        """Test initialization of HivemindState."""
        assert state.hivemind_id is None
        assert state._issue is None
        assert state.option_cids == []
        assert state.opinion_cids == [{}]
        assert state.signatures == {}
        assert state.participants == {}
        assert state.selected == []
        assert state.final is False

    def test_set_hivemind_issue(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test setting hivemind issue."""
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        assert state.hivemind_id is not None
        assert isinstance(state._issue, HivemindIssue)
        assert len(state.opinion_cids) == len(state._issue.questions)

    def test_hivemind_issue_property(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test the hivemind_issue method."""
        # Initially should be None
        assert state.hivemind_issue() is None

        # After setting, should return the issue
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        assert state.hivemind_issue() == state._issue
        assert isinstance(state.hivemind_issue(), HivemindIssue)

    def test_load_with_existing_issue(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test loading a state with an existing issue that has questions."""
        # Create and save a state with an issue that has multiple questions
        basic_issue.add_question("Second Question")  # Now has 2 questions
        issue_hash = basic_issue.save()

        # Create and save initial state
        initial_state = HivemindState()
        initial_state.set_hivemind_issue(issue_hash)
        state_hash = initial_state.save()

        # Load the state in a new instance
        loaded_state = HivemindState()
        loaded_state.load(state_hash)

        # Verify opinions are initialized correctly for all questions
        assert len(loaded_state.opinion_cids) == len(basic_issue.questions)
        assert all(isinstance(opinions, dict) for opinions in loaded_state.opinion_cids)
        assert all(len(opinions) == 0 for opinions in loaded_state.opinion_cids)
