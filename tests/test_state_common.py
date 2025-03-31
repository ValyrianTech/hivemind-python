#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import pytest
from typing import Tuple, List
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from hivemind.utils import generate_bitcoin_keypair, sign_message


# Common Fixtures
@pytest.fixture
def state() -> HivemindState:
    """Create a fresh HivemindState instance for each test."""
    return HivemindState()


@pytest.fixture
def basic_issue() -> HivemindIssue:
    """Create a basic issue for testing."""
    issue = HivemindIssue()
    issue.name = "Test Issue"
    issue.add_question("Test Question")
    issue.description = "Test Description"
    issue.tags = ["test"]
    issue.answer_type = "String"
    issue.constraints = {}
    issue.restrictions = {}
    return issue


@pytest.fixture
def color_choice_issue(basic_issue) -> HivemindIssue:
    """Create an issue with color choices."""
    basic_issue.set_constraints({
        "choices": [
            {"value": "red", "text": "Red"},
            {"value": "blue", "text": "Blue"},
            {"value": "green", "text": "Green"}
        ]
    })
    return basic_issue


@pytest.fixture
def bool_issue(basic_issue) -> HivemindIssue:
    """Create a boolean issue."""
    basic_issue.answer_type = "Bool"
    basic_issue.set_constraints({
        "true_value": "Yes",
        "false_value": "No"
    })
    return basic_issue


@pytest.fixture
def integer_issue(basic_issue) -> HivemindIssue:
    """Create an integer issue for testing."""
    basic_issue.answer_type = "Integer"
    basic_issue.set_constraints({
        "min_value": 0,
        "max_value": 100
    })
    return basic_issue


@pytest.fixture
def test_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a consistent test keypair."""
    return generate_bitcoin_keypair()


class TestHelper:
    """Helper class containing common test operations."""

    @staticmethod
    def create_and_sign_option(state: HivemindState, issue_hash: str, value: str, text: str,
                               private_key: CBitcoinSecret, address: str, timestamp: int) -> str:
        """Helper to create and sign an option.
        
        Args:
            state: HivemindState instance
            issue_hash: Hash of the issue
            value: Option value
            text: Option display text
            private_key: Signer's private key
            address: Signer's address
            timestamp: Current timestamp
            
        Returns:
            str: Hash of the created option
        """
        option = HivemindOption()
        option.set_issue(issue_hash)
        option.set(value=value)
        option.text = text
        option_hash = option.save()

        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        return option_hash

    @staticmethod
    def create_and_sign_opinion(state: HivemindState, issue_hash: str, ranking: List[str],
                                private_key: CBitcoinSecret, address: str, timestamp: int) -> str:
        """Helper to create and sign an opinion.
        
        Args:
            state: HivemindState instance
            issue_hash: Hash of the issue
            ranking: List of option hashes in preferred order
            private_key: Signer's private key
            address: Signer's address
            timestamp: Current timestamp
            
        Returns:
            str: Hash of the created opinion
        """
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(ranking)  # First address prefers red > blue > green
        opinion_hash = opinion.save()  # Save will use the data we just set

        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, address, signature)
        return opinion_hash
