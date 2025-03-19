#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, VerifyMessage
from hivemind.utils import generate_bitcoin_keypair, sign_message


def test_generate_bitcoin_keypair():
    """Test that generate_bitcoin_keypair creates valid Bitcoin key pairs."""
    private_key, address = generate_bitcoin_keypair()

    # Test that private key is valid Bitcoin secret
    assert isinstance(private_key, CBitcoinSecret)

    # Test that address is valid Bitcoin address string
    assert isinstance(address, str)
    assert len(address) > 25  # Bitcoin addresses are at least 26 chars
    assert address.startswith('1')  # P2PKH addresses start with 1

    # Verify address matches private key
    derived_address = str(P2PKHBitcoinAddress.from_pubkey(private_key.pub))
    assert address == derived_address


def test_generate_bitcoin_keypair_uniqueness():
    """Test that generate_bitcoin_keypair creates unique keys each time."""
    # Generate multiple keypairs and ensure they're unique
    num_pairs = 5
    keypairs = [generate_bitcoin_keypair() for _ in range(num_pairs)]

    # Check all private keys are unique
    private_keys = [pair[0] for pair in keypairs]
    assert len(set(private_keys)) == num_pairs

    # Check all addresses are unique
    addresses = [pair[1] for pair in keypairs]
    assert len(set(addresses)) == num_pairs


def test_sign_message():
    """Test that sign_message creates valid Bitcoin signatures."""
    # Generate a test key pair
    private_key, address = generate_bitcoin_keypair()

    # Sign a test message
    message = "Test message"
    signature = sign_message(message, private_key)

    # Verify signature is valid base64 string
    assert isinstance(signature, str)

    # Verify signature is valid for message and address
    assert VerifyMessage(
        P2PKHBitcoinAddress.from_pubkey(private_key.pub),
        BitcoinMessage(message),
        signature.encode()
    )


def test_sign_message_empty():
    """Test signing an empty message."""
    private_key, _ = generate_bitcoin_keypair()
    signature = sign_message("", private_key)
    assert isinstance(signature, str)
    assert len(signature) > 0


def test_sign_message_special_chars():
    """Test signing messages with special characters."""
    private_key, _ = generate_bitcoin_keypair()
    special_messages = [
        "Hello\nWorld",  # newline
        "Tab\there",  # tab
        "Unicode 😊",  # emoji
        "!@#$%^&*()",  # special chars
        "   ",  # whitespace
    ]

    for message in special_messages:
        signature = sign_message(message, private_key)
        assert isinstance(signature, str)
        assert len(signature) > 0
        # Verify signature
        assert VerifyMessage(
            P2PKHBitcoinAddress.from_pubkey(private_key.pub),
            BitcoinMessage(message),
            signature.encode()
        )


def test_sign_message_invalid_key():
    """Test that sign_message raises appropriate error for invalid key."""
    with pytest.raises(AttributeError, match="'str' object has no attribute 'sign_compact'"):
        sign_message("test", "not_a_valid_key")


def test_sign_message_invalid_message():
    """Test that sign_message raises appropriate error for invalid message type."""
    private_key, _ = generate_bitcoin_keypair()
    with pytest.raises(AttributeError, match="'int' object has no attribute 'encode'"):
        sign_message(123, private_key)  # Non-string message
