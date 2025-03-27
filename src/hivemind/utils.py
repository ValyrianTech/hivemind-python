#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from typing import Tuple
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage


def get_bitcoin_address(private_key: CBitcoinSecret) -> str:
    """Get the Bitcoin address corresponding to a private key.
    
    :param private_key: Bitcoin private key
    :type private_key: CBitcoinSecret
    :return: Bitcoin address in base58 format
    :rtype: str
    """
    return str(P2PKHBitcoinAddress.from_pubkey(private_key.pub))


def generate_bitcoin_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a random Bitcoin private key and its corresponding address.
    
    :return: (private_key, address) pair where address is in base58 format
    :rtype: Tuple[CBitcoinSecret, str]
    """
    # Generate a random private key
    entropy = random.getrandbits(256).to_bytes(32, byteorder='big')
    private_key = CBitcoinSecret.from_secret_bytes(entropy)

    # Get the corresponding public address
    address = get_bitcoin_address(private_key)

    return private_key, address


def sign_message(message: str, private_key: CBitcoinSecret) -> str:
    """Sign a message with a Bitcoin private key.
    
    :param message: The message to sign
    :type message: str
    :param private_key: Bitcoin private key
    :type private_key: CBitcoinSecret
    :return: The signature in base64 format
    :rtype: str
    """
    return SignMessage(key=private_key, message=BitcoinMessage(message)).decode()
