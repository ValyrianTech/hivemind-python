"""Validation functions for Hivemind Bitcoin address formats.

This module provides functions for validating both legacy and Bech32 Bitcoin addresses.
It supports validation for both mainnet and testnet addresses.
"""
import re
from typing import Tuple, List

# Address validation patterns
MAINNET_ADDRESS_REGEX = "^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"
TESTNET_ADDRESS_REGEX = "^[nm2][a-km-zA-HJ-NP-Z1-9]{25,34}$"
LOWERCASE_TESTNET_BECH32_ADDRESS_REGEX = '^tb1[ac-hj-np-z02-9]{11,71}$'
UPPERCASE_TESTNET_BECH32_ADDRESS_REGEX = '^TB1[AC-HJ-NP-Z02-9]{11,71}$'
LOWERCASE_MAINNET_BECH32_ADDRESS_REGEX = '^bc1[ac-hj-np-z02-9]{11,71}$'
UPPERCASE_MAINNET_BECH32_ADDRESS_REGEX = '^BC1[AC-HJ-NP-Z02-9]{11,71}$'

# Bech32 character set
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def bech32_decode(bech: str) -> Tuple[str | None, List[int] | None]:
    """Validate a Bech32 string and determine its HRP and data components.

    :param bech: The Bech32 string to decode
    :type bech: str
    :return: A tuple containing the human-readable part (HRP) and data part as integers
    :rtype: Tuple[str | None, List[int] | None]
    
    The function performs various validations including:
    
    * Character set validation
    * Case consistency check
    * Length constraints
    * Checksum verification
    """
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return None, None
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return None, None
    if not all(x in CHARSET for x in bech[pos + 1:]):
        return None, None
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos + 1:]]
    if not bech32_verify_checksum(hrp, data):
        return None, None
    return hrp, data[:-6]


def bech32_verify_checksum(hrp: str, data: List[int]) -> bool:
    """Verify a checksum given HRP and converted data characters.

    :param hrp: The human-readable part of the address
    :type hrp: str
    :param data: The data part as a list of integers
    :type data: list[int]
    :return: True if the checksum is valid, False otherwise
    :rtype: bool
    """
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def bech32_polymod(values: List[int]) -> int:
    """Compute the Bech32 checksum.

    :param values: List of integers representing the data to checksum
    :type values: list[int]
    :return: The computed checksum value
    :rtype: int
    
    This is an internal function that implements the Bech32 checksum algorithm
    using the specified generator polynomial.
    """
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp: str) -> List[int]:
    """Expand the HRP into values for checksum computation.

    :param hrp: The human-readable part of the address
    :type hrp: str
    :return: The expanded values used in checksum computation
    :rtype: list[int]
    
    This function splits each character into high bits (>>5) and low bits (&31)
    with a zero byte separator between them.
    """
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def valid_address(address: str, testnet: bool = False) -> bool:
    """Validate a Bitcoin address (both legacy and Bech32 formats).

    :param address: The Bitcoin address to validate
    :type address: str
    :param testnet: Whether to validate as testnet address
    :type testnet: bool
    :return: True if the address is valid, False otherwise
    :rtype: bool
    
    This function checks both legacy and Bech32 address formats.
    For legacy addresses, it uses regex patterns.
    For Bech32 addresses, it delegates to valid_bech32_address().
    """
    if not isinstance(address, str):
        return False

    if testnet:
        return bool(re.match(TESTNET_ADDRESS_REGEX, address)) or valid_bech32_address(address, testnet=True)
    else:
        return bool(re.match(MAINNET_ADDRESS_REGEX, address)) or valid_bech32_address(address, testnet=False)


def valid_bech32_address(address: str, testnet: bool = False) -> bool:
    """Validate a Bech32 Bitcoin address.

    :param address: The Bech32 address to validate
    :type address: str
    :param testnet: Whether to validate as testnet address
    :type testnet: bool
    :return: True if the address is valid, False otherwise
    :rtype: bool
    
    This function performs both structural validation through regex patterns
    and Bech32 specific validation through bech32_decode().
    It supports both lowercase and uppercase address formats.
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
