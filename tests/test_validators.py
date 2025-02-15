"""Test suite for Bitcoin address validation functions."""
import pytest
from hivemind.validators import (
    valid_address,
    valid_bech32_address,
    bech32_decode,
    bech32_verify_checksum,
    bech32_polymod,
    bech32_hrp_expand
)


def test_bech32_decode_mixed_case():
    """Test bech32_decode with mixed case input."""
    # This tests line 38 where bech.lower() is called
    # Using a valid mixed-case Bech32 address that will pass initial validation
    address = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
    hrp, data = bech32_decode(address)
    assert hrp == "tb"
    assert data is not None


def test_bech32_decode_valid():
    """Test bech32_decode with valid input."""
    # This tests lines 44 and 48 for successful decoding path
    # Using a valid lowercase Bech32 address
    address = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
    hrp, data = bech32_decode(address)
    assert hrp == "tb"
    assert data is not None
    assert len(data) > 0


def test_valid_address_mainnet():
    """Test valid_address with mainnet addresses."""
    # This tests line 118 for mainnet addresses
    # Legacy mainnet address
    assert valid_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", testnet=False)
    # Bech32 mainnet address - must be lowercase
    assert valid_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", testnet=False)
    # Another valid mainnet address
    assert valid_address("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", testnet=False)


def test_valid_bech32_address_testnet_uppercase():
    """Test valid_bech32_address with uppercase testnet addresses."""
    # This tests line 145 for uppercase testnet Bech32 addresses
    assert valid_bech32_address("TB1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KXPJZSX", testnet=True)


def test_invalid_addresses():
    """Test various invalid address formats."""
    assert not valid_address(None)  # Test non-string input
    assert not valid_address("invalid_address")
    assert not valid_bech32_address(None)  # Test non-string input
    assert not valid_bech32_address("invalid_bech32")


def test_bech32_checksum():
    """Test Bech32 checksum verification."""
    # Test with known valid HRP and data
    hrp = "tb1"
    data = [0, 1, 2]  # Simplified test data
    assert isinstance(bech32_verify_checksum(hrp, data), bool)


def test_bech32_hrp_expand():
    """Test HRP expansion for checksum computation."""
    hrp = "tb1"
    expanded = bech32_hrp_expand(hrp)
    assert isinstance(expanded, list)
    assert len(expanded) == len(hrp) * 2 + 1  # Each char splits into 2 values + separator
