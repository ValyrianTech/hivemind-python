from typing import Dict, Any
import pytest
from hivemind import HivemindOption, HivemindIssue


@pytest.fixture
def issue() -> HivemindIssue:
    issue = HivemindIssue()
    issue.name = 'Test Issue'
    issue.description = 'Test Description'
    issue.tags = ['test']
    issue.questions = ['Test Question?']
    issue.answer_type = 'String'
    return issue


@pytest.fixture
def option(issue: HivemindIssue) -> HivemindOption:
    option = HivemindOption()
    option._hivemind_issue = issue
    option._answer_type = issue.answer_type
    return option


@pytest.mark.unit
class TestHivemindOption:
    def test_init(self) -> None:
        """Test initialization of HivemindOption"""
        option = HivemindOption()
        assert option.value is None
        assert option.text == ''
        assert option._hivemind_issue is None
        assert option._answer_type == 'String'

    def test_set_hivemind_issue(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test setting hivemind issue"""
        # Create a new issue and get its CID
        test_issue = HivemindIssue()
        test_issue.name = 'Test Issue'
        test_issue.description = 'Test Description'
        test_issue.tags = ['test']
        test_issue.questions = ['Test Question?']
        test_issue.answer_type = 'String'
        test_issue.save()
        issue_hash = test_issue._cid  # Use _cid directly since it's already a string

        # Test setting the issue
        option.set_hivemind_issue(issue_hash)
        assert option.hivemind_id == issue_hash
        assert isinstance(option._hivemind_issue, HivemindIssue)
        assert option._answer_type == 'String'

    def test_set_value(self, option: HivemindOption) -> None:
        """Test setting value"""
        value: str = "test value"
        option.set(value)
        assert option.value == value

    def test_valid_string_option(self, option: HivemindOption) -> None:
        """Test validation of string option"""
        option.value = "test"
        assert option.valid() is True

        # Test with constraints
        option._hivemind_issue.constraints = {
            'min_length': 3,
            'max_length': 10,
            'regex': r'^[a-z]+$'
        }

        option.value = "test"
        assert option.valid() is True

        option.value = "ab"  # Too short
        assert option.valid() is False

        option.value = "abcdefghijk"  # Too long
        assert option.valid() is False

        option.value = "Test123"  # Invalid regex
        assert option.valid() is False

    def test_valid_integer_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of integer option"""
        issue.answer_type = 'Integer'
        option._answer_type = 'Integer'

        option.value = 42
        assert option.valid() is True

        option.value = "42"  # String instead of int
        assert option.valid() is False

        # Test with constraints
        option._hivemind_issue.constraints = {
            'min_value': 0,
            'max_value': 100
        }

        option.value = 42
        assert option.valid() is True

        option.value = -1  # Too small
        assert option.valid() is False

        option.value = 101  # Too large
        assert option.valid() is False

    def test_valid_float_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of float option"""
        issue.answer_type = 'Float'
        option._answer_type = 'Float'

        option.value = 42.5
        assert option.valid() is True

        option.value = "42.5"  # String instead of float
        assert option.valid() is False

        # Test with constraints
        option._hivemind_issue.constraints = {
            'min_value': 0.0,
            'max_value': 100.0
        }

        option.value = 42.5
        assert option.valid() is True

        option.value = -0.1  # Too small
        assert option.valid() is False

        option.value = 100.1  # Too large
        assert option.valid() is False

    def test_valid_bool_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of boolean option"""
        issue.answer_type = 'Bool'
        option._answer_type = 'Bool'

        option.value = True
        assert option.valid() is True

        option.value = "true"  # String instead of bool
        assert option.valid() is False

    def test_info(self, option: HivemindOption) -> None:
        """Test info string generation"""
        option.value = "test"
        option.text = "Test description"
        info = option.info()
        assert "Value: test" in info
        assert "Text: Test description" in info
