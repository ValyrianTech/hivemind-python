#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from typing import Tuple
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage, VerifyMessage
import logging

LOG = logging.getLogger(__name__)


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


def verify_message(message: str, address: str, signature: str) -> bool:
    """
    Verify a signed message using Bitcoin's message verification.

    :param message: The message that was signed
    :type message: str
    :param address: The Bitcoin address that signed the message
    :type address: str
    :param signature: The base64-encoded signature
    :type signature: str
    :return: Whether the signature is valid
    :rtype: bool
    """
    try:
        return VerifyMessage(address, BitcoinMessage(message), signature)
    except Exception as ex:
        LOG.error('Error verifying message: %s' % ex)
        return False
