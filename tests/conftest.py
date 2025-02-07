"""Shared pytest fixtures."""
from typing import Generator
import pytest
from ipfs_dict_chain.IPFS import connect
from src.hivemind.issue import HivemindIssue
from src.hivemind.option import HivemindOption
from src.hivemind.opinion import HivemindOpinion


def pytest_configure():
    """Configure IPFS connection for tests."""
    try:
        connect(host='127.0.0.1', port=5001)
    except Exception as e:
        pytest.skip(f"IPFS node not available: {e}")


@pytest.fixture
def issue() -> HivemindIssue:
    """Create a basic HivemindIssue instance."""
    return HivemindIssue()


@pytest.fixture
def option(issue: HivemindIssue) -> HivemindOption:
    """Create a basic HivemindOption instance linked to an issue."""
    option = HivemindOption()
    option._hivemind_issue = issue
    option._answer_type = issue.answer_type
    return option


@pytest.fixture
def opinion() -> HivemindOpinion:
    """Create a basic HivemindOpinion instance."""
    return HivemindOpinion()
