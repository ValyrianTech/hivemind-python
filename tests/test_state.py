from typing import Dict, Any
import pytest
import time
from unittest.mock import patch, Mock
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from ipfs_dict_chain.IPFS import connect, IPFSError

# Mock addresses for testing (valid Bitcoin addresses)
MOCK_ADDRESS_1 = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'  # Genesis block address
MOCK_ADDRESS_2 = '12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX'  # Another early Bitcoin address

# Mock signatures (these would normally be base64-encoded signatures)
MOCK_SIGNATURE_VALID = 'valid_signature'
MOCK_SIGNATURE_INVALID = 'fake_sig'

@pytest.fixture(autouse=True)
def mock_verify():
    """Mock the verify_message function for all tests"""
    def mock_verify_message(*args, **kwargs):
        """Mock implementation of verify_message for testing"""
        if 'signature' in kwargs:
            return kwargs['signature'] != MOCK_SIGNATURE_INVALID
        return True
        
    with patch('hivemind.state.verify_message', side_effect=mock_verify_message):
        yield

# Mock verify_message function
def mock_verify_message(message: str, address: str, signature: str) -> bool:
    """Mock implementation of verify_message for testing"""
    return signature != MOCK_SIGNATURE_INVALID  # Any signature except 'fake_sig' is valid


@pytest.fixture(scope="module")
def string_issue_hash() -> str:
    """Create and save a HivemindIssue with string constraints for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Hivemind'
    hivemind_issue.add_question(question='What is your favorite color?')
    hivemind_issue.description = 'Choose your favorite color'
    hivemind_issue.tags = ['color', 'preference']
    hivemind_issue.answer_type = 'String'
    hivemind_issue.constraints = {}  # Initialize constraints
    hivemind_issue.set_constraints({'choices': [
        {'value': 'red', 'text': 'Red'},
        {'value': 'blue', 'text': 'Blue'},
        {'value': 'green', 'text': 'Green'}
    ]})
    return hivemind_issue.save()


@pytest.fixture(scope="module")
def bool_issue_hash() -> str:
    """Create and save a HivemindIssue with boolean constraints for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Bool Hivemind'
    hivemind_issue.add_question(question='Do you agree?')
    hivemind_issue.description = 'Yes/No question'
    hivemind_issue.answer_type = 'Bool'
    hivemind_issue.constraints = {}  # Initialize constraints
    hivemind_issue.set_constraints({
        'true_value': 'Yes',
        'false_value': 'No'
    })
    return hivemind_issue.save()


@pytest.fixture(scope="module")
def restricted_issue_hash() -> str:
    """Create and save a HivemindIssue with address restrictions for testing."""
    hivemind_issue = HivemindIssue()
    hivemind_issue.name = 'Test Restricted Hivemind'
    hivemind_issue.add_question(question='What is your opinion?')
    hivemind_issue.description = 'Restricted voting'
    hivemind_issue.answer_type = 'String'
    hivemind_issue.restrictions = {}  # Initialize restrictions
    hivemind_issue.set_restrictions({
        'addresses': [MOCK_ADDRESS_1, MOCK_ADDRESS_2],
        'options_per_address': 2
    })
    return hivemind_issue.save()


@pytest.fixture
def state() -> HivemindState:
    return HivemindState()


@pytest.fixture(scope="module", autouse=True)
def setup_ipfs():
    """Setup IPFS connection for all tests"""
    try:
        connect(host='127.0.0.1', port=5001)
    except IPFSError as e:
        pytest.skip(f"IPFS connection failed: {str(e)}")


@pytest.mark.unit
class TestHivemindState:
    def test_init(self, state: HivemindState) -> None:
        """Test initialization of HivemindState"""
        assert state.hivemind_id is None
        assert state._hivemind_issue is None
        assert state.options == []
        assert state.opinions == [{}]
        assert state.signatures == {}
        assert state.participants == {}
        assert state.selected == []
        assert state.final is False

    def test_set_hivemind_issue(self, state: HivemindState, string_issue_hash: str) -> None:
        """Test setting hivemind issue"""
        state.set_hivemind_issue(string_issue_hash)
        assert state.hivemind_id == string_issue_hash
        assert isinstance(state._hivemind_issue, HivemindIssue)
        assert len(state.opinions) == len(state._hivemind_issue.questions)

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_add_predefined_bool_options(self, state: HivemindState, bool_issue_hash: str) -> None:
        """Test adding predefined boolean options"""
        state.set_hivemind_issue(bool_issue_hash)
        options = state.add_predefined_options()
        
        assert len(state.options) == 2
        assert len(options) == 2
        
        # Verify option values
        option_values = [HivemindOption(cid=opt_hash).value for opt_hash in state.options]
        assert True in option_values
        assert False in option_values

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_add_predefined_choice_options(self, state: HivemindState, string_issue_hash: str) -> None:
        """Test adding predefined choice options"""
        state.set_hivemind_issue(string_issue_hash)
        options = state.add_predefined_options()
        
        assert len(state.options) == 3
        assert len(options) == 3
        
        # Verify option values
        option_values = [HivemindOption(cid=opt_hash).value for opt_hash in state.options]
        assert 'red' in option_values
        assert 'blue' in option_values
        assert 'green' in option_values

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_add_option_with_restrictions(self, state: HivemindState, restricted_issue_hash: str) -> None:
        """Test adding options with address restrictions"""
        state.set_hivemind_issue(restricted_issue_hash)
        
        # Create a valid option
        option = HivemindOption()
        option.set_hivemind_issue(restricted_issue_hash)
        option.set('test option')
        option_hash = option.save()
        
        # Test with unauthorized address
        timestamp = int(time.time())
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, '0x789', 'valid_sig')
        assert 'address restrictions' in str(exc_info.value)
        
        # Test with authorized address but invalid signature
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, MOCK_ADDRESS_1, 'fake_sig')
        assert 'Signature is not valid' in str(exc_info.value)

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_add_opinion(self, state: HivemindState, string_issue_hash: str) -> None:
        """Test adding opinions"""
        state.set_hivemind_issue(string_issue_hash)
        state.add_predefined_options()
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.ranking.set_fixed(state.options[:2])  # Rank first two options
        opinion_hash = opinion.save()
        
        # Test adding opinion with invalid signature
        timestamp = int(time.time())
        with pytest.raises(Exception) as exc_info:
            state.add_opinion(timestamp, opinion_hash, 'fake_sig', MOCK_ADDRESS_1)
        assert 'Signature is invalid' in str(exc_info.value)

    def test_get_weight(self, state: HivemindState) -> None:
        """Test getting opinion weights"""
        # Create a test issue with weights
        issue = HivemindIssue()
        issue.name = 'Test Weight'
        issue.add_question('Test?')
        issue.restrictions = {
            MOCK_ADDRESS_1: {'weight': 2.5}
        }
        state._hivemind_issue = issue
        
        # Test default weight
        assert state.get_weight(MOCK_ADDRESS_2) == 1.0
        
        # Test custom weight
        assert state.get_weight(MOCK_ADDRESS_1) == 2.5

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_calculate_results(self, state: HivemindState, string_issue_hash: str) -> None:
        """Test calculating voting results"""
        state.set_hivemind_issue(string_issue_hash)
        options = state.add_predefined_options()
        
        results = state.calculate_results()
        assert len(results) == len(options)
        for option_hash in options:
            assert 'win' in results[option_hash]
            assert 'loss' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]

    @pytest.mark.skip(reason="Requires message verification implementation")
    @pytest.mark.parametrize("selection_mode", [None, 'Finalize', 'Exclude', 'Reset'])
    def test_select_consensus_modes(self, state: HivemindState, selection_mode: str) -> None:
        """Test different consensus selection modes"""
        # Create issue with selection mode
        issue = HivemindIssue()
        issue.name = 'Test Selection'
        issue.add_question('Test?')
        issue.answer_type = 'String'
        issue.on_selection = selection_mode
        issue_hash = issue.save()
        
        # Setup state
        state.set_hivemind_issue(issue_hash)
        
        # Add an option
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test')
        option_hash = option.save()
        state.options.append(option_hash)
        
        # Select consensus
        state.select_consensus()
        
        if selection_mode == 'Finalize':
            assert state.final is True
        elif selection_mode == 'Reset':
            assert state.opinions == [{}]
        elif selection_mode == 'Exclude':
            assert len(state.selected) == 1
        else:  # None
            assert not state.final
            assert state.opinions == [{}]

    def test_add_signature(self, state: HivemindState) -> None:
        """Test adding signatures with timestamp validation"""
        address = MOCK_ADDRESS_1
        message = 'test_message'
        
        # Add first signature
        timestamp1 = int(time.time())
        state.add_signature(address, timestamp1, message, 'sig1')
        assert address in state.signatures
        assert message in state.signatures[address]
        assert 'sig1' in state.signatures[address][message]
        
        # Try adding older signature
        timestamp2 = timestamp1 - 1
        with pytest.raises(Exception) as exc_info:
            state.add_signature(address, timestamp2, message, 'sig2')
        assert 'Invalid timestamp' in str(exc_info.value)
        
        # Add newer signature
        timestamp3 = timestamp1 + 1
        state.add_signature(address, timestamp3, message, 'sig3')
        assert 'sig3' in state.signatures[address][message]

    @pytest.mark.skip(reason="Requires message verification implementation")
    def test_update_participant_name(self, state: HivemindState) -> None:
        """Test updating participant names"""
        address = MOCK_ADDRESS_1
        name = 'Alice'
        timestamp = int(time.time())
        
        # Test with invalid signature
        with pytest.raises(Exception) as exc_info:
            state.update_participant_name(timestamp, name, address, 'fake_sig')
        assert 'Invalid signature' in str(exc_info.value)
        
        # Verify participant not added
        assert address not in state.participants

    def test_options_per_address_limit(self, state: HivemindState, restricted_issue_hash: str) -> None:
        """Test enforcement of options_per_address restriction.
        
        This test verifies that:
        1. An address can add up to the maximum allowed options
        2. Adding more than the allowed number fails
        3. Different addresses have independent limits
        4. The limit persists across multiple operations
        """
        state.set_hivemind_issue(restricted_issue_hash)  # Issue has options_per_address = 2
        timestamp = int(time.time())

        # Create base option template
        def create_option(content: str) -> str:
            option = HivemindOption()
            option.set_hivemind_issue(restricted_issue_hash)
            option.set(content)
            return option.save()

        # Test address 1 can add up to limit
        option1_hash = create_option("option1 from addr1")
        option2_hash = create_option("option2 from addr1")
        
        # Both options should succeed
        state.add_option(timestamp, option1_hash, MOCK_ADDRESS_1, 'valid_sig')
        state.add_option(timestamp, option2_hash, MOCK_ADDRESS_1, 'valid_sig')

        # Third option should fail for address 1
        option3_hash = create_option("option3 from addr1")
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option3_hash, MOCK_ADDRESS_1, 'valid_sig')
        assert 'already added too many options' in str(exc_info.value)

        # Address 2 should still be able to add options
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")
        
        # Both options should succeed for address 2
        state.add_option(timestamp, option4_hash, MOCK_ADDRESS_2, 'valid_sig')
        state.add_option(timestamp, option5_hash, MOCK_ADDRESS_2, 'valid_sig')

        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option6_hash, MOCK_ADDRESS_2, 'valid_sig')
        assert 'already added too many options' in str(exc_info.value)
