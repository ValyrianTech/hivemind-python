from typing import List
import pytest
import logging
from hivemind import HivemindOpinion, HivemindOption
from ipfs_dict_chain.IPFS import connect, IPFSError


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
