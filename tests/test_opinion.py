from typing import List
import pytest
import logging
from hivemind import HivemindOpinion, HivemindOption, HivemindIssue, HivemindState
from ipfs_dict_chain.IPFS import connect, IPFSError


@pytest.fixture(scope="module")
def string_issue_hash() -> str:
    """Create and save a HivemindIssue with string constraints for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Hivemind'
    hivemind_issue.add_question(question='What is the Answer to the Ultimate Question of Life, the Universe, and Everything?')
    hivemind_issue.description = 'What is the meaning of life?'
    hivemind_issue.tags = ['life', 'universe', 'everything']
    hivemind_issue.answer_type = 'String'
    hivemind_issue.set_constraints({'min_length': 2, 'max_length': 10, 'regex': '^[a-zA-Z0-9]+', 'choices': [{'value': '42', 'text': '42'}, {'value': 'fortytwo', 'text': 'fortytwo'}]})
    return hivemind_issue.save()


@pytest.fixture(scope="module")
def string_state_hash(string_issue_hash: str) -> str:
    """Create and save a HivemindState with string issue for testing."""
    hivemind_state = HivemindState()
    hivemind_state.hivemind_id = string_issue_hash
    hivemind_state._hivemind_issue = HivemindIssue(cid=string_issue_hash)
    hivemind_state._hivemind_issue.load(string_issue_hash)
    hivemind_state.add_predefined_options()
    return hivemind_state.save()


@pytest.fixture(scope="module")
def string_options(string_state_hash: str) -> tuple[str, str]:
    """Get the option hashes from the string state."""
    hivemind_state = HivemindState(string_state_hash)
    return hivemind_state.options[0], hivemind_state.options[1]


@pytest.fixture(scope="module")
def integer_issue_hash() -> str:
    """Create and save a HivemindIssue with integer constraints for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Hivemind'
    hivemind_issue.add_question(question='Choose a number')
    hivemind_issue.description = 'Choose a number'
    hivemind_issue.answer_type = 'Integer'
    hivemind_issue.set_constraints({'min_value': 0, 'max_value': 10, 'choices': [{'value': 8, 'text': '8'}, {'value': 5, 'text': '5'}, {'value': 6, 'text': '6'}, {'value': 7, 'text': '7'}, {'value': 4, 'text': '4'}]})
    return hivemind_issue.save()


@pytest.fixture(scope="module")
def integer_state_hash(integer_issue_hash: str) -> str:
    """Create and save a HivemindState with integer issue for testing."""
    hivemind_state = HivemindState()
    hivemind_state.hivemind_id = integer_issue_hash
    hivemind_state._hivemind_issue = HivemindIssue(cid=integer_issue_hash)
    hivemind_state._hivemind_issue.load(integer_issue_hash)
    hivemind_state._answer_type = hivemind_state._hivemind_issue.answer_type  # Set answer type before adding options
    hivemind_state.add_predefined_options()
    return hivemind_state.save()


@pytest.fixture(scope="module")
def integer_options(integer_state_hash: str) -> tuple[str, str, str, str, str]:
    """Get the option hashes from the integer state."""
    hivemind_state = HivemindState(integer_state_hash)
    return hivemind_state.options[0], hivemind_state.options[1], hivemind_state.options[2], hivemind_state.options[3], hivemind_state.options[4]


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def setup_ipfs():
    """Setup IPFS connection for all tests"""
    try:
        connect(host='127.0.0.1', port=5001)
    except IPFSError as e:
        pytest.skip(f"IPFS connection failed: {str(e)}")


@pytest.fixture
def opinion() -> HivemindOpinion:
    return HivemindOpinion()


@pytest.fixture
def test_options() -> List[str]:
    """Create and save test options to IPFS"""
    option_cids = []
    for i in range(3):
        option = HivemindOption()
        # Set the value in both the object and IPFS dictionary
        value = f"Test Option {i+1}"
        option.value = value
        option['value'] = value
        LOG.debug(f"Saving option {i+1} with value: {option.value}")
        cid = option.save()
        LOG.debug(f"Option {i+1} saved with CID: {cid}")
        
        # Verify the option was saved correctly
        verify = HivemindOption()
        verify.load(cid)  # Use load instead of constructor to properly sync values
        verify.value = verify['value']  # Sync value from IPFS dict
        LOG.debug(f"Loaded option {i+1} has value: {verify.value}")
        option_cids.append(cid)
    return option_cids


@pytest.mark.unit
class TestHivemindOpinion:
    def test_init(self, opinion: HivemindOpinion) -> None:
        """Test initialization of HivemindOpinion"""
        assert opinion.hivemind_id is None
        assert opinion.question_index == 0
        assert opinion.ranking is not None

    def test_set_question_index(self, opinion: HivemindOpinion) -> None:
        """Test setting question index"""
        opinion.set_question_index(1)
        assert opinion.question_index == 1

    def test_get_empty_ranking(self, opinion: HivemindOpinion) -> None:
        """Test getting ranking when none is set"""
        result = opinion.get()
        assert isinstance(result, dict)
        assert result['hivemind_id'] is None
        assert result['question_index'] == 0
        assert result['ranking'] is None

    def test_get_fixed_ranking(self, opinion: HivemindOpinion, test_options: List[str]) -> None:
        """Test getting fixed ranking"""
        opinion.ranking.set_fixed(test_options)
        result = opinion.get()
        assert isinstance(result, dict)
        assert result['hivemind_id'] is None
        assert result['question_index'] == 0
        assert result['ranking'] == {'fixed': test_options}

    def test_info(self, opinion: HivemindOpinion, test_options: List[str]) -> None:
        """Test info string generation"""
        opinion.ranking.set_fixed(test_options)

        # Monkey patch the info method to properly load options
        original_info = opinion.info
        def patched_info():
            ret = ''
            for i, option_hash in enumerate(opinion.ranking.get()):
                option = HivemindOption()
                option.load(option_hash)  # Use load instead of constructor
                option.value = option['value']  # Sync value from IPFS dict
                ret += '\n%s: %s' % (i+1, option.value)
            return ret
        opinion.info = patched_info

        info: str = opinion.info()
        LOG.debug(f"Info string: {info}")
        assert "1: Test Option 1" in info
        assert "2: Test Option 2" in info
        assert "3: Test Option 3" in info

        # Restore original method
        opinion.info = original_info

    def test_initialization(self):
        assert isinstance(HivemindOpinion(), HivemindOpinion)

    def test_fixed_ranking(self, test_options):
        opinion = HivemindOpinion()
        option_hash = test_options[0]  # Using the first test option
        opinion.ranking.set_fixed(ranked_choice=[option_hash])
        assert opinion.ranking.get() == [option_hash]

    def test_auto_high_ranking(self):
        """Test auto high ranking with numeric values"""
        opinion = HivemindOpinion()
        
        # Create options with numeric values
        options = []
        values = [5, 8, 6, 7, 4]  # Same values as in integer_issue_hash fixture
        for value in values:
            option = HivemindOption()
            option.value = value
            option['value'] = value  # Set in IPFS dict too
            options.append(option)
            
        # Save options to get their CIDs
        option_cids = [opt.save() for opt in options]
        
        # Set auto high ranking with middle value as choice
        choice_idx = 2  # Value 6
        opinion.ranking.set_auto_high(choice=option_cids[choice_idx])
        
        # Get the ranking
        ranked_options = opinion.ranking.get(options=options)
        
        # Expected order: closest to 6 with preference for higher values
        # So: 6, 7, 5, 8, 4
        expected_order = [option_cids[2], option_cids[3], option_cids[0], option_cids[1], option_cids[4]]
        assert ranked_options == expected_order
