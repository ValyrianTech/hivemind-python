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
    # Using an address with inconsistent mixed case that should fail validation
    address = "tb1qRp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
    hrp, data = bech32_decode(address)
    assert hrp is None
    assert data is None


def test_bech32_decode_valid():
    """Test bech32_decode with valid input."""
    # This tests lines 44 and 48 for successful decoding path
    # Using a valid lowercase Bech32 address
    address = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
    hrp, data = bech32_decode(address)
    assert hrp == "tb"
    assert data is not None
    assert len(data) > 0


def test_bech32_decode_non_printable():
    """Test bech32_decode with non-printable characters."""
    # Test with a string containing a non-printable character (ASCII 31)
    address = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7\x1f"
    hrp, data = bech32_decode(address)
    assert hrp is None
    assert data is None


def test_bech32_decode_invalid_lengths():
    """Test bech32_decode with invalid length inputs."""
    # Test with string too short (no '1' separator)
    assert bech32_decode("tooshort") == (None, None)

    # Test with string where position of '1' is too early
    assert bech32_decode("1toolate") == (None, None)

    # Test with string that's too long (>90 chars)
    long_address = "bc1" + "q" * 88  # 91 characters total
    assert bech32_decode(long_address) == (None, None)

    # Test with string where data part is too short after '1'
    assert bech32_decode("bc1short") == (None, None)


def test_bech32_decode_invalid_charset():
    """Test bech32_decode with invalid characters after separator."""
    # Test with invalid characters after the separator
    assert bech32_decode("bc1!nvalid") == (None, None)
    assert bech32_decode("bc1inv@lid") == (None, None)

    # Test with valid HRP but invalid data characters
    assert bech32_decode("bc1123456") == (None, None)


def test_bech32_decode_invalid_checksum():
    """Test bech32_decode with invalid checksum."""
    # Take a valid address and modify the last character to make checksum invalid
    valid_addr = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
    invalid_addr = valid_addr[:-1] + ('p' if valid_addr[-1] != 'p' else 'q')
    assert bech32_decode(invalid_addr) == (None, None)


def test_valid_address_mainnet():
    """Test valid_address with mainnet addresses."""
    # This tests line 118 for mainnet addresses
    # Legacy mainnet address
    assert valid_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", testnet=False)
    # Bech32 mainnet address - must be lowercase
    assert valid_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", testnet=False)
    # Another valid mainnet address
    assert valid_address("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", testnet=False)


def test_valid_address_testnet():
    """Test valid_address with testnet addresses."""
    # Legacy testnet address
    assert valid_address("mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn", testnet=True)
    # Bech32 testnet address
    assert valid_address("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx", testnet=True)
    # Another valid testnet address
    assert valid_address("2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc", testnet=True)


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
