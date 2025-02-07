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


def bech32_decode(bech: str) -> Tuple[Optional[str], Optional[list]]:
    """Simplified bech32 decoder for testing.
    
    Args:
        bech: The bech32 string to decode
        
    Returns:
        Tuple containing the human readable part and data, or (None, None) if invalid
    """
    # For testing purposes, we'll just validate the format
    # In production, you'd want to use a proper bech32 decoder
    if re.match(r'^(bc|BC|tb|TB)1[ac-hj-np-z02-9]{11,71}$', bech):
        hrp = bech[:2].lower()
        data = list(bech[3:])  # Convert remaining chars to list
        return hrp, data
    return None, None


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