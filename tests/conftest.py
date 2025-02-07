"""Shared pytest fixtures."""
from typing import Generator
import pytest
from src.hivemind.issue import HivemindIssue
from src.hivemind.option import HivemindOption
from src.hivemind.opinion import HivemindOpinion


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
