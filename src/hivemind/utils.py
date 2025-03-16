#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from typing import Tuple
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage


def get_bitcoin_address(private_key: CBitcoinSecret) -> str:
    """Get the Bitcoin address corresponding to a private key.
    
    Args:
        private_key: Bitcoin private key
        
    Returns:
        str: Bitcoin address in base58 format
    """
    return str(P2PKHBitcoinAddress.from_pubkey(private_key.pub))


def generate_bitcoin_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a random Bitcoin private key and its corresponding address.
    
    Returns:
        Tuple[CBitcoinSecret, str]: (private_key, address) pair where address is in base58 format
    """
    # Generate a random private key
    entropy = random.getrandbits(256).to_bytes(32, byteorder='big')
    private_key = CBitcoinSecret.from_secret_bytes(entropy)

    # Get the corresponding public address
    address = get_bitcoin_address(private_key)

    return private_key, address


def sign_message(message: str, private_key: CBitcoinSecret) -> str:
    """Sign a message with a Bitcoin private key.
    
    Args:
        message: The message to sign
        private_key: Bitcoin private key
        
    Returns:
        str: The signature in base64 format
    """
    return SignMessage(key=private_key, message=BitcoinMessage(message)).decode()
