"""Validation functions for Hivemind."""
import re
from typing import Optional, Tuple, Any


# Address validation patterns
MAINNET_ADDRESS_REGEX = "^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"
TESTNET_ADDRESS_REGEX = "^[nm2][a-km-zA-HJ-NP-Z1-9]{25,34}$"
LOWERCASE_TESTNET_BECH32_ADDRESS_REGEX = '^tb1[ac-hj-np-z02-9]{11,71}$'
UPPERCASE_TESTNET_BECH32_ADDRESS_REGEX = '^TB1[AC-HJ-NP-Z02-9]{11,71}$'
LOWERCASE_MAINNET_BECH32_ADDRESS_REGEX = '^bc1[ac-hj-np-z02-9]{11,71}$'
UPPERCASE_MAINNET_BECH32_ADDRESS_REGEX = '^BC1[AC-HJ-NP-Z02-9]{11,71}$'


def bech32_decode(bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in CHARSET for x in bech[pos+1:]):
        return (None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos+1:]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])

def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1

def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk

def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def valid_address(address: str, testnet: bool = False) -> bool:
    """Validate a legacy Bitcoin address.
    
    Args:
        address: The address to validate
        testnet: Whether to validate as testnet address
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(address, str):
        return False

    if testnet:
        return bool(re.match(TESTNET_ADDRESS_REGEX, address)) or valid_bech32_address(address, testnet=True)
    else:
        return bool(re.match(MAINNET_ADDRESS_REGEX, address)) or valid_bech32_address(address, testnet=False)


def valid_bech32_address(address: str, testnet: bool = False) -> bool:
    """Validate a Bech32 Bitcoin address.
    
    Args:
        address: The address to validate
        testnet: Whether to validate as testnet address
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(address, str):
        return False

    hrp, data = bech32_decode(address)
    if (hrp, data) == (None, None):
        return False

    if testnet:
        return bool(re.match(LOWERCASE_TESTNET_BECH32_ADDRESS_REGEX, address)) or \
               bool(re.match(UPPERCASE_TESTNET_BECH32_ADDRESS_REGEX, address))
    else:
        return bool(re.match(LOWERCASE_MAINNET_BECH32_ADDRESS_REGEX, address)) or \
               bool(re.match(UPPERCASE_MAINNET_BECH32_ADDRESS_REGEX, address))