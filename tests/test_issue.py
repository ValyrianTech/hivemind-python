from typing import Dict, Any
import pytest
from src.hivemind.issue import HivemindIssue


@pytest.fixture
def issue() -> HivemindIssue:
    return HivemindIssue()


@pytest.mark.unit
class TestHivemindIssue:
    def test_init(self, issue: HivemindIssue) -> None:
        """Test initialization of HivemindIssue"""
        assert issue.questions == []
        assert issue.name is None
        assert issue.description == ''
        assert issue.tags == []
        assert issue.answer_type == 'String'
        assert issue.constraints is None
        assert issue.restrictions is None
        assert issue.on_selection is None

    def test_add_question(self, issue: HivemindIssue) -> None:
        """Test adding questions"""
        question: str = "What is your favorite color?"
        issue.add_question(question)
        assert len(issue.questions) == 1
        assert issue.questions[0] == question

        # Test duplicate question
        issue.add_question(question)
        assert len(issue.questions) == 1

        # Test non-string question
        issue.add_question(123)  # type: ignore
        assert len(issue.questions) == 1

    def test_set_constraints_valid(self, issue: HivemindIssue) -> None:
        """Test setting valid constraints"""
        constraints: Dict[str, Any] = {
            'min_length': 5,
            'max_length': 10,
            'regex': r'^[a-z]+$',
            'choices': ['red', 'blue', 'green']
        }
        issue.set_constraints(constraints)
        assert issue.constraints == constraints

    def test_set_constraints_invalid_type(self, issue: HivemindIssue) -> None:
        """Test setting constraints with invalid type"""
        with pytest.raises(Exception) as exc_info:
            issue.set_constraints([])  # type: ignore
        assert 'constraints must be a dict' in str(exc_info.value)

    def test_set_constraints_invalid_key(self, issue: HivemindIssue) -> None:
        """Test setting constraints with invalid key"""
        with pytest.raises(Exception) as exc_info:
            issue.set_constraints({'invalid_key': 'value'})
        assert 'constraints contain an invalid key' in str(exc_info.value)

    def test_set_restrictions_valid(self, issue: HivemindIssue) -> None:
        """Test setting valid restrictions"""
        restrictions: Dict[str, int] = {
            'options_per_address': 3
        }
        issue.set_restrictions(restrictions)
        assert issue.restrictions == restrictions

    def test_set_restrictions_invalid_type(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid type"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions([])  # type: ignore
        assert 'Restrictions is not a dict' in str(exc_info.value)

    def test_set_restrictions_invalid_key(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid key"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions({'invalid_key': 'value'})
        assert 'Invalid key in restrictions' in str(exc_info.value)

    def test_set_restrictions_invalid_options_per_address(self, issue: HivemindIssue) -> None:
        """Test setting restrictions with invalid options_per_address"""
        with pytest.raises(Exception) as exc_info:
            issue.set_restrictions({'options_per_address': 0})
        assert 'options_per_address in restrictions must be a positive integer' in str(exc_info.value)
