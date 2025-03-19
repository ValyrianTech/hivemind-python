import pytest
from hivemind import HivemindOption, HivemindIssue


@pytest.fixture
def issue() -> HivemindIssue:
    """Create a test issue with complex answer type."""
    issue = HivemindIssue()
    issue.name = 'Test Issue'
    issue.description = 'Test Description'
    issue.tags = ['test']
    issue.questions = ['Test Question?']
    issue.answer_type = 'Complex'
    # Initialize empty constraints
    issue.constraints = {}
    return issue


@pytest.fixture
def option(issue: HivemindIssue) -> HivemindOption:
    """Create a test option with complex answer type."""
    option = HivemindOption()
    option._hivemind_issue = issue
    option._answer_type = issue.answer_type
    return option


@pytest.mark.unit
class TestComplexHivemindOption:
    def test_valid_complex_option_missing_spec_key(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of complex option when a required spec key is missing.
        This test specifically targets line 234 in option.py where a spec key from
        the constraints is missing in the value dictionary."""

        # First verify that a dictionary without specs is valid
        option.value = {'any_key': 'any_value'}
        assert option.valid()

        # Now add constraints with specs
        issue.constraints = {
            'specs': {
                'required_key': 'string'  # Single required key for clarity
            }
        }

        # Test with dictionary missing the required key - should hit line 234
        option.value = {'wrong_key': 'some_value'}
        assert not option.valid()

        # Test with correct key for comparison
        option.value = {'required_key': 'some_value'}
        assert option.valid()

    def test_valid_complex_option_no_specs_in_constraints(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of complex option when constraints exist but 'specs' key is missing."""
        # Set constraints without 'specs' key
        issue.constraints = {'some_other_key': 'some_value'}

        # Any dictionary value should be valid since there are no specs
        option.value = {'any_key': 'any_value'}
        assert option.valid()

    def test_invalid_complex_option_not_dict(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of complex option when value is not a dictionary."""
        # Test with string value
        option.value = "not a dictionary"
        assert not option.valid()

        # Test with list value
        option.value = ["also", "not", "a", "dictionary"]
        assert not option.valid()

        # Test with integer value
        option.value = 42
        assert not option.valid()

    def test_complex_option_with_bool_field(self, issue: HivemindIssue, option: HivemindOption) -> None:
        """Test validation of complex option with a Bool field type."""
        # Set constraints with a Bool field
        issue.constraints = {
            'specs': {
                'bool_field': 'Bool'
            }
        }

        # Test with correct Bool value
        option.value = {'bool_field': True}
        assert option.valid()

        # Test with incorrect value type (string instead of bool)
        option.value = {'bool_field': 'True'}
        assert not option.valid()

        # Test with incorrect value type (integer instead of bool)
        option.value = {'bool_field': 1}
        assert not option.valid()
