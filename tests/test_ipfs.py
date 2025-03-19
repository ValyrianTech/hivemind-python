import pytest
from ipfs_dict_chain.IPFSDict import IPFSDict
from ipfs_dict_chain.IPFS import connect, IPFSError


@pytest.mark.integration
def test_ipfs_dict_chain():
    """Test basic IPFS dictionary functionality"""
    try:
        # First try to connect to IPFS
        connect(host='127.0.0.1', port=5001)

        # Create a test dictionary
        test_dict = IPFSDict()
        test_dict["test_key"] = "test_value"

        # Store data
        cid = test_dict.save()
        assert cid is not None

        # Create new dictionary and load data
        loaded_dict = IPFSDict()
        loaded_dict.load(cid)

        # Verify data
        assert loaded_dict["test_key"] == "test_value"
    except IPFSError as e:
        pytest.skip(f"IPFS connection failed: {str(e)}")
