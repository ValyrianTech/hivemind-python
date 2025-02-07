from typing import Dict, Any
import pytest
from hivemind import HivemindOption, HivemindIssue


@pytest.fixture(scope="module")
def string_question_hash() -> str:
    """Create and save a HivemindIssue with string constraints for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Hivemind'
    hivemind_issue.add_question(question='What is the Answer to the Ultimate Question of Life, the Universe, and Everything?')
    hivemind_issue.description = 'What is the meaning of life?'
    hivemind_issue.tags = ['life', 'universe', 'everything']
    hivemind_issue.answer_type = 'String'
    hivemind_issue.set_constraints({'min_length': 2, 'max_length': 10, 'regex': '^[a-zA-Z0-9]+'})
    return hivemind_issue.save()


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

    def test_initialization(self):
        option = HivemindOption()
        assert isinstance(option, HivemindOption)

    def test_initializing_with_option_hash(self, string_question_hash):
        option = HivemindOption()
        option.set_hivemind_issue(hivemind_issue_hash=string_question_hash)
        option.set('42')

        option_hash = option.save()

        option2 = HivemindOption(cid=option_hash)
        assert option2.hivemind_id == option.hivemind_id
        assert option2.value == option.value
        assert option2._answer_type == option._answer_type

    def test_setting_value_that_conflicts_with_constraints(self):
        """Test that setting a value that conflicts with constraints raises an exception."""
        # Create an option with constraints directly
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'String'
        issue.set_constraints({'min_length': 2, 'max_length': 10, 'regex': '^[a-zA-Z0-9]+'})
        
        # Set the issue directly instead of loading from IPFS
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        
        with pytest.raises(Exception):
            option.set('a')  # constraint min_length: 2

    def test_setting_value_that_conflicts_with_answer_type(self, string_question_hash):
        option = HivemindOption()
        option.set_hivemind_issue(hivemind_issue_hash=string_question_hash)
        with pytest.raises(Exception):
            option.set(42)  # must be string instead of number

    @pytest.mark.parametrize("value, expected", [
        ('42', True),
        ('a', False),
        ('12345678901', False),
        ('!éç', False),

    ])
    def test_is_valid_string_option(self, value, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'String'
        issue.set_constraints({'min_length': 2, 'max_length': 10, 'regex': '^[a-zA-Z0-9]+'})
        
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        assert option.is_valid_string_option() is expected

    @pytest.mark.parametrize("value, expected", [
        (42.42, True),
        ('a', False),
        (42, False),
        (51, False),
        (1, False),
        (42, False),
        (42.123, False),
        (42.10, True),  # This is valid because it has 2 decimal places
        (42.1, True),   # This is also valid because 42.1 == 42.10
    ])
    def test_is_valid_float_option(self, value, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'Float'
        issue.set_constraints({'min_value': 2, 'max_value': 50, 'decimals': 2})
        
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        assert option.is_valid_float_option() is expected

    @pytest.mark.parametrize("value, expected", [
        (42, True),
        ('a', False),
        (42.0, False),
        (51, False),
        (1, False),
        ('42', False),
        (42.123, False),
        (42.1, False),

    ])
    def test_is_valid_integer_option(self, value, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'Integer'
        issue.set_constraints({'min_value': 2, 'max_value': 50})
        
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        assert option.is_valid_integer_option() is expected

    @pytest.mark.parametrize("value, expected", [
        (True, True),
        (False, True),
        ('True', False),
        ('true', False),
        ('False', False),
        ('false', False),
        (0, False),
        (1.12, False),

    ])
    def test_is_valid_bool_option(self, value, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'Bool'
        issue.set_constraints({})
        
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        assert option.is_valid_bool_option() is expected

    @pytest.mark.parametrize("value, expected", [
        ({'a_string': 'foo', 'a_float': 42.0}, True),
        ({'a_string': 'foo'}, False),
        ({'a_float': 42}, False),
        ({'foo': 'foo', 'a_float': 42}, False),
        ({'a_string': 'foo', 'a_float': 42, 'foo': 'bar'}, False),
        ({'a_string': 42, 'a_float': 42}, False),
        ({'a_string': 'foo', 'a_float': 'bar'}, False),
    ])
    def test_is_valid_complex_option(self, value, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'Complex'
        issue.set_constraints({'specs': {'a_string': 'String', 'a_float': 'Float'}})
        
        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        assert option.is_valid_complex_option() is expected
