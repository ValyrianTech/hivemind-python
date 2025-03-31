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
        option.set_issue(issue_hash)
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
        option.save()
        info = option.info()
        assert "Value: test" in info
        assert "Text: Test description" in info

    def test_initialization(self):
        option = HivemindOption()
        assert isinstance(option, HivemindOption)

    def test_initializing_with_option_hash(self, string_question_hash):
        option = HivemindOption()
        option.set_issue(hivemind_issue_cid=string_question_hash)
        option.set('42')

        option_hash = option.save()

        option2 = HivemindOption()
        option2.load(option_hash)
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
        option.set_issue(hivemind_issue_cid=string_question_hash)
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
        (42.123, False),
        (42.10, True),  # This is valid because it has 2 decimal places
        (42.1, True),  # This is also valid because 42.1 == 42.10
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

    @pytest.mark.parametrize("value, text, constraints, expected", [
        (True, None, {}, True),
        (False, None, {}, True),
        ('True', None, {}, False),
        ('true', None, {}, False),
        ('False', None, {}, False),
        ('false', None, {}, False),
        (0, None, {}, False),
        (1.12, None, {}, False),
        # Test cases for text validation with constraints
        (True, 'Agree', {'true_value': 'Agree', 'false_value': 'Disagree'}, True),
        (True, 'Wrong Text', {'true_value': 'Agree', 'false_value': 'Disagree'}, False),
        (False, 'Disagree', {'true_value': 'Agree', 'false_value': 'Disagree'}, True),
        (False, 'Wrong Text', {'true_value': 'Agree', 'false_value': 'Disagree'}, False),
    ])
    def test_is_valid_bool_option(self, value, text, constraints, expected):
        option = HivemindOption()
        issue = HivemindIssue()
        issue.name = 'Test'
        issue.add_question('What?')
        issue.answer_type = 'Bool'
        issue.set_constraints(constraints)

        option._hivemind_issue = issue
        option._answer_type = issue.answer_type
        option.value = value
        if text is not None:
            option.text = text
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

    def test_cid_method(self, option: HivemindOption) -> None:
        """Test the cid() method"""
        assert option.cid() is None

        # Set a value and save to get a CID
        option.value = "test"
        option.save()
        assert option.cid() is not None
        assert isinstance(option.cid(), str)

    def test_load_method(self, option: HivemindOption) -> None:
        """Test the load() method"""
        # Save an option first
        option.value = "test"
        saved_cid = option.save()

        # Create a new option and load the saved one
        new_option = HivemindOption()
        new_option.load(saved_cid)
        assert new_option.value == "test"
        # Note: CID might have /ipfs/ prefix when loaded
        assert saved_cid in new_option.cid()

    def test_set_hivemind_issue_errors(self) -> None:
        """Test error cases in set_hivemind_issue()"""
        option = HivemindOption()

        # Test with invalid CID
        with pytest.raises(Exception):
            option.set_issue("invalid_cid")

    def test_set_method_errors(self, option: HivemindOption) -> None:
        """Test error cases in set() method"""
        option._answer_type = 'Integer'

        # Test setting invalid type
        with pytest.raises(Exception):
            option.set("not an integer")

    def test_valid_method_edge_cases(self, option: HivemindOption) -> None:
        """Test edge cases in valid() method"""
        # Test without hivemind issue
        option = HivemindOption()
        with pytest.raises(Exception) as exc_info:
            option.valid()
        assert "No hivemind question set" in str(exc_info.value)

        # Test with mismatched answer type
        option._hivemind_issue = HivemindIssue()
        option._hivemind_issue.answer_type = 'Integer'
        option._answer_type = 'String'
        assert option.valid() is False

        # Test with invalid choice
        option._answer_type = 'String'
        option._hivemind_issue.answer_type = 'String'
        option._hivemind_issue.constraints = {'choices': [{'value': 'A'}, {'value': 'B'}]}
        option.value = 'C'
        with pytest.raises(Exception) as exc_info:
            option.valid()
        assert "not in the allowed choices" in str(exc_info.value)

    def test_valid_float_option_decimals(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test float validation with decimal constraints"""
        issue.answer_type = 'Float'
        option._answer_type = 'Float'
        option._hivemind_issue.constraints = {'decimals': 2}

        # Valid cases
        option.value = 42.12
        assert option.valid() is True

        option.value = 42.1
        assert option.valid() is True

        # Invalid cases
        option.value = 42.123
        assert option.valid() is False

    def test_valid_hivemind_option(self, issue: HivemindIssue, option: HivemindOption, string_question_hash) -> None:
        """Test hivemind option validation"""
        # First create a valid hivemind issue
        test_issue = HivemindIssue()
        test_issue.name = "Test Issue"
        test_issue.add_question("Test Question?")
        test_issue.answer_type = "String"
        hivemind_cid = test_issue.save()

        # Now test the hivemind option
        issue.answer_type = 'Hivemind'
        option._answer_type = 'Hivemind'
        option._hivemind_issue = issue

        # Test with valid CID
        option.value = hivemind_cid
        assert option.valid() is True

        # Test with invalid CID
        option.value = "QmInvalidCIDThatDoesNotExist"
        assert option.valid() is False

        # Test with wrong type
        option.value = 123
        assert option.valid() is False

    def test_valid_complex_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test complex option validation"""
        issue.answer_type = 'Complex'
        option._answer_type = 'Complex'

        # Set up complex constraints
        option._hivemind_issue.constraints = {
            'specs': {
                'name': 'String',
                'age': 'Integer',
                'score': 'Float'
            }
        }

        # Test valid complex value
        option.value = {
            'name': 'John',
            'age': 30,
            'score': 85.5
        }
        assert option.valid() is True

        # Test missing field
        option.value = {
            'name': 'John',
            'age': 30
        }
        assert option.valid() is False

        # Test wrong type
        option.value = {
            'name': 'John',
            'age': '30',  # Should be integer
            'score': 85.5
        }
        assert option.valid() is False

    def test_valid_address_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test address option validation"""
        issue.answer_type = 'Address'
        option._answer_type = 'Address'

        # Test with valid address format
        option.value = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
        assert option.valid() is True

        # Test with invalid address
        option.value = "not_an_address"
        assert option.valid() is False

        # Test with wrong type
        option.value = 123
        assert option.valid() is False

    def test_info_method_comprehensive(self, option: HivemindOption) -> None:
        """Test info() method with different value types"""
        # Test with string
        option.value = "test"
        option.text = "description"
        info = option.info()
        assert "Value: test" in info
        assert "Text: description" in info

        # Test with number
        option.value = 42
        info = option.info()
        assert "Value: 42" in info

        # Test with boolean
        option.value = True
        info = option.info()
        assert "Value: True" in info

        # Test with complex
        option.value = {"name": "test", "value": 42}
        info = option.info()
        assert "Value: {'name': 'test', 'value': 42}" in info

    def test_set_method_edge_cases_2(self, option: HivemindOption) -> None:
        """Test additional edge cases in set()"""
        # Test with None value for String type
        option._answer_type = "String"
        with pytest.raises(Exception):
            option.set(None)

        # Test with None value for Integer type
        option._answer_type = "Integer"
        with pytest.raises(Exception):
            option.set(None)

        # Test with complex object - should raise Exception for invalid type
        class TestObject:
            pass

        with pytest.raises(Exception):
            option.set(TestObject())

    def test_info_method_edge_cases(self, option: HivemindOption) -> None:
        """Test edge cases in info()"""
        # Test with no value set
        info = option.info()
        assert "Value: None" in info

    def test_valid_file_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of file option"""
        issue.answer_type = 'File'
        option._answer_type = 'File'

        # Valid IPFS hash for a file
        option.value = "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o"
        assert option.valid() is True

        # Invalid type (not a string)
        option.value = 42
        assert option.valid() is False

        # Invalid IPFS hash format
        option.value = "not-an-ipfs-hash"
        assert option.valid() is False

    def test_valid_address_option(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test address option validation"""
        issue.answer_type = 'Address'
        option._answer_type = 'Address'

        # Test with valid address format
        option.value = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
        assert option.valid() is True

        # Test with invalid address
        option.value = "not_an_address"
        assert option.valid() is False

        # Test with wrong type
        option.value = 123
        assert option.valid() is False

    def test_info_method_comprehensive(self, option: HivemindOption) -> None:
        """Test info() method with different value types"""
        # Test with string
        option.value = "test"
        option.text = "description"
        option.save()
        info = option.info()
        assert "Value: test" in info
        assert "Text: description" in info

        # Test with number
        option.value = 42
        info = option.info()
        assert "Value: 42" in info

        # Test with boolean
        option.value = True
        info = option.info()
        assert "Value: True" in info

        # Test with complex
        option.value = {"name": "test", "value": 42}
        info = option.info()
        assert "Value: {'name': 'test', 'value': 42}" in info

    def test_set_method_edge_cases_2(self, option: HivemindOption) -> None:
        """Test additional edge cases in set()"""
        # Test with None value for String type
        option._answer_type = "String"
        with pytest.raises(Exception):
            option.set(None)

        # Test with None value for Integer type
        option._answer_type = "Integer"
        with pytest.raises(Exception):
            option.set(None)

        # Test with complex object - should raise Exception for invalid type
        class TestObject:
            pass

        with pytest.raises(Exception):
            option.set(TestObject())

    def test_info_method_edge_cases(self, option: HivemindOption) -> None:
        """Test edge cases in info()"""
        # First save the option to get a valid CID
        option.value = None
        option.save()
        info = option.info()
        assert "Value: None" in info

    def test_valid_hivemind_option(self, issue: HivemindIssue, option: HivemindOption, string_question_hash) -> None:
        """Test hivemind option validation"""
        # First create a valid hivemind issue
        test_issue = HivemindIssue()
        test_issue.name = "Test Issue"
        test_issue.add_question("Test Question?")
        test_issue.answer_type = "String"
        hivemind_cid = test_issue.save()

        # Now test the hivemind option
        issue.answer_type = 'Hivemind'
        option._answer_type = 'Hivemind'
        option._hivemind_issue = issue

        # Test with valid CID
        option.value = hivemind_cid
        assert option.valid() is True

        # Test with invalid CID
        option.value = "QmInvalidCIDThatDoesNotExist"
        assert option.valid() is False

        # Test with wrong type
        option.value = 123
        assert option.valid() is False

    def test_get_answer_type(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test the get_answer_type method."""
        # Test default answer type
        assert option.get_answer_type() == 'String'
        
        # Test with different answer types
        for answer_type in ['Integer', 'Float', 'Bool', 'Complex', 'Hivemind', 'File', 'Address']:
            option._answer_type = answer_type
            assert option.get_answer_type() == answer_type
            
        # Test when answer type is set via issue
        new_option = HivemindOption()
        issue.answer_type = 'Integer'
        new_option._hivemind_issue = issue
        new_option._answer_type = issue.answer_type
        assert new_option.get_answer_type() == 'Integer'
