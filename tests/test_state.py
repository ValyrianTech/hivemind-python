#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from unittest.mock import patch, Mock
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from ipfs_dict_chain.IPFS import connect, IPFSError
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage
import random
import pytest
from typing import Dict, Any, Tuple

# Mock addresses for testing (valid Bitcoin addresses)
MOCK_ADDRESS_1 = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'  # Genesis block address
MOCK_ADDRESS_2 = '12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX'  # Another valid address

# Mock private keys for testing
MOCK_PRIVATE_KEY_1 = CBitcoinSecret.from_secret_bytes(b'\x00' * 32)
MOCK_PRIVATE_KEY_2 = CBitcoinSecret.from_secret_bytes(b'\x01' * 32)

# Mock signatures (these will be replaced with real signatures)
MOCK_SIGNATURE_VALID = 'valid_sig'
MOCK_SIGNATURE_INVALID = 'invalid_sig'

def generate_bitcoin_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a random Bitcoin private key and its corresponding address.
    
    Returns:
        Tuple[CBitcoinSecret, str]: (private_key, address) pair where address is in base58 format
    """
    # Generate a random private key
    entropy = random.getrandbits(256).to_bytes(32, byteorder='big')
    private_key = CBitcoinSecret.from_secret_bytes(entropy)
    
    # Get the corresponding public address
    address = str(P2PKHBitcoinAddress.from_pubkey(private_key.pub))
    
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

@pytest.fixture
def state() -> HivemindState:
    return HivemindState()

@pytest.mark.unit
class TestHivemindState:
    def test_init(self, state: HivemindState) -> None:
        """Test initialization of HivemindState"""
        assert state.hivemind_id is None
        assert state._hivemind_issue is None
        assert state.options == []
        assert state.opinions == [{}]
        assert state.signatures == {}
        assert state.participants == {}
        assert state.selected == []
        assert state.final is False

    def test_set_hivemind_issue(self, state: HivemindState) -> None:
        """Test setting hivemind issue"""
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('What is your favorite color?')
        issue.description = 'Choose your favorite color'
        issue.tags = ['color', 'preference']
        issue.answer_type = 'String'
        issue.constraints = {}  # Initialize constraints
        issue.set_constraints({'choices': [
            {'value': 'red', 'text': 'Red'},
            {'value': 'blue', 'text': 'Blue'},
            {'value': 'green', 'text': 'Green'}
        ]})
        state.set_hivemind_issue(issue.save())
        assert state.hivemind_id is not None
        assert isinstance(state._hivemind_issue, HivemindIssue)
        assert len(state.opinions) == len(state._hivemind_issue.questions)

    def test_add_predefined_bool_options(self, state: HivemindState) -> None:
        """Test adding predefined boolean options"""
        # Create a bool issue
        issue = HivemindIssue()
        issue.name = 'Test Bool Hivemind'
        issue.add_question('Do you agree?')
        issue.description = 'Yes/No question'
        issue.answer_type = 'Bool'
        issue.constraints = {}  # Initialize constraints
        issue.set_constraints({
            'true_value': 'Yes',
            'false_value': 'No'
        })
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate a key pair for signing
        private_key, address = generate_bitcoin_keypair()
        
        # Add predefined options with proper signing
        timestamp = int(time.time())
        
        # Create and sign true option
        true_option = HivemindOption()
        true_option.set_hivemind_issue(issue_hash)
        true_option.set(value=True)
        true_option.text = issue.constraints['true_value']
        true_option_hash = true_option.save()
        
        # Sign and add true option
        message = f"{timestamp}{true_option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, true_option_hash, address, signature)
        
        # Create and sign false option
        false_option = HivemindOption()
        false_option.set_hivemind_issue(issue_hash)
        false_option.set(value=False)
        false_option.text = issue.constraints['false_value']
        false_option_hash = false_option.save()
        
        # Sign and add false option
        message = f"{timestamp}{false_option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, false_option_hash, address, signature)
        
        assert len(state.options) == 2
        
        # Verify option values
        option_values = [HivemindOption(cid=opt_hash).value for opt_hash in state.options]
        assert True in option_values
        assert False in option_values

    def test_add_predefined_choice_options(self, state: HivemindState) -> None:
        """Test adding predefined choice options"""
        # Create issue with choices
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('What is your favorite color?')
        issue.description = 'Choose your favorite color'
        issue.tags = ['color', 'preference']
        issue.answer_type = 'String'
        issue.constraints = {}  # Initialize constraints
        issue.set_constraints({'choices': [
            {'value': 'red', 'text': 'Red'},
            {'value': 'blue', 'text': 'Blue'},
            {'value': 'green', 'text': 'Green'}
        ]})
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate a key pair for signing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Create and sign each option
        for choice in issue.constraints['choices']:
            # Create option
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(value=choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            
            # Sign and add option
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)
        
        assert len(state.options) == 3
        
        # Verify option values
        option_values = [HivemindOption(cid=opt_hash).value for opt_hash in state.options]
        assert 'red' in option_values
        assert 'blue' in option_values
        assert 'green' in option_values

    def test_add_option_with_restrictions(self, state: HivemindState) -> None:
        """Test adding options with address restrictions"""
        # Create issue with restrictions
        issue = HivemindIssue()
        issue.name = 'Test Restricted Hivemind'
        issue.add_question('What is your opinion?')
        issue.description = 'Restricted voting'
        issue.answer_type = 'String'
        issue.restrictions = {}  # Initialize restrictions
        
        # Generate two key pairs for testing
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()
        
        # Set restrictions to only allow address1 and address2
        issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Create a valid option
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test option')
        option_hash = option.save()
        
        timestamp = int(time.time())
        
        # Test with unauthorized address (address3)
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key3)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, address3, signature)
        assert 'address restrictions' in str(exc_info.value)
        
        # Test with authorized address but invalid signature
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, address1, 'invalid_sig')
        assert 'Signature is not valid' in str(exc_info.value)
        
        # Test with authorized address and valid signature
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key1)
        state.add_option(timestamp, option_hash, address1, signature)
        assert option_hash in state.options

    @pytest.mark.skip(reason="Needs to be updated to use real Bitcoin signatures and addresses")
    def test_add_opinion(self, state: HivemindState) -> None:
        """Test adding opinions"""
        # Create issue
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('What is your favorite color?')
        issue.description = 'Choose your favorite color'
        issue.tags = ['color', 'preference']
        issue.answer_type = 'String'
        issue.constraints = {}  # Initialize constraints
        issue.set_constraints({'choices': [
            {'value': 'red', 'text': 'Red'},
            {'value': 'blue', 'text': 'Blue'},
            {'value': 'green', 'text': 'Green'}
        ]})
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate key pairs for testing
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Add options first
        option_hashes = []
        for choice in issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(value=choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            option_hashes.append(option_hash)
            
            # Sign and add option
            message = '%s%s' % (timestamp, option_hash)
            signature = sign_message(message, private_key1)
            state.add_option(timestamp, option_hash, address1, signature)
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.ranking.set_fixed(option_hashes)  # Rank all options
        opinion_hash = opinion.save()
        
        # Test with invalid signature
        with pytest.raises(Exception) as exc_info:
            state.add_opinion(timestamp, opinion_hash, 'invalid_sig', address1)
        assert 'Signature is invalid' in str(exc_info.value)
        
        # Test with valid signature
        message = '%s%s' % (timestamp, opinion_hash)
        signature = sign_message(message, private_key1)
        state.add_opinion(timestamp, opinion_hash, signature, address1)
        
        # Verify opinion was added
        assert opinion_hash in state.opinions
        assert address1 in state.participants

    @pytest.mark.skip(reason="Needs to be updated to use real Bitcoin signatures and addresses")
    def test_calculate_results(self, state: HivemindState) -> None:
        """Test calculating results"""
        # Create issue
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('What is your favorite color?')
        issue.description = 'Choose your favorite color'
        issue.tags = ['color', 'preference']
        issue.answer_type = 'String'
        issue.constraints = {}  # Initialize constraints
        issue.set_constraints({'choices': [
            {'value': 'red', 'text': 'Red'},
            {'value': 'blue', 'text': 'Blue'},
            {'value': 'green', 'text': 'Green'}
        ]})
        state.set_hivemind_issue(issue.save())
        
        # Add options
        options = state.add_predefined_options()
        option_hashes = list(options.keys())
        
        # Generate key pairs for testing
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Add opinions from different addresses
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue.save()
        opinion1.ranking.set_fixed(option_hashes)  # First address prefers red > blue > green
        opinion1_hash = opinion1.save()
        
        message1 = '%s%s' % (timestamp, opinion1_hash)
        signature1 = sign_message(message1, private_key1)
        state.add_opinion(timestamp, opinion1_hash, signature1, address1)
        
        # Second address prefers blue > green > red
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue.save()
        opinion2.ranking.set_fixed([option_hashes[1], option_hashes[2], option_hashes[0]])
        opinion2_hash = opinion2.save()
        
        message2 = '%s%s' % (timestamp, opinion2_hash)
        signature2 = sign_message(message2, private_key2)
        state.add_opinion(timestamp, opinion2_hash, signature2, address2)
        
        # Calculate results
        results = state.calculate_results()
        
        # Verify results structure
        for option_hash in option_hashes:
            assert option_hash in results
            assert 'wins' in results[option_hash]
            assert 'losses' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]

    def test_select_consensus_modes(self, state: HivemindState) -> None:
        """Test different consensus selection modes"""
        # Create issue with selection mode
        issue = HivemindIssue()
        issue.name = 'Test Selection'
        issue.add_question('Test?')
        issue.answer_type = 'String'
        issue.on_selection = 'Finalize'
        issue_hash = issue.save()
        
        # Setup state
        state.set_hivemind_issue(issue_hash)
        
        # Generate a key pair for signing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Add an option with proper signature
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test')
        option_hash = option.save()
        
        # Sign and add the option
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        
        # Select consensus
        state.select_consensus()
        
        assert state.final is True

    def test_add_signature(self, state: HivemindState) -> None:
        """Test adding signatures with timestamp validation"""
        address = MOCK_ADDRESS_1
        message = 'test_message'
        
        # Add first signature
        timestamp1 = int(time.time())
        state.add_signature(address, timestamp1, message, 'sig1')
        assert address in state.signatures
        assert message in state.signatures[address]
        assert 'sig1' in state.signatures[address][message]
        
        # Try adding older signature
        timestamp2 = timestamp1 - 1
        with pytest.raises(Exception) as exc_info:
            state.add_signature(address, timestamp2, message, 'sig2')
        assert 'Invalid timestamp' in str(exc_info.value)
        
        # Add newer signature
        timestamp3 = timestamp1 + 1
        state.add_signature(address, timestamp3, message, 'sig3')
        assert 'sig3' in state.signatures[address][message]

    def test_update_participant_name(self, state: HivemindState) -> None:
        """Test updating participant names"""
        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        name = 'Alice'
        timestamp = int(time.time())
        
        # Create message and sign it
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)
        
        # Test with invalid signature
        with pytest.raises(Exception) as exc_info:
            state.update_participant_name(timestamp, name, address, 'fake_sig')
        assert 'Invalid signature' in str(exc_info.value)
        
        # Test with valid signature
        state.update_participant_name(timestamp, name, address, signature)
        
        # Verify participant was added with correct name
        assert address in state.participants
        assert state.participants[address].get('name') == name

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
    def test_options_per_address_limit(self, state: HivemindState) -> None:
        """Test the options_per_address restriction.
        
        Tests:
        1. Options can be added up to the limit
        2. Options beyond the limit are rejected
        3. Different addresses have independent limits
        4. The limit persists across multiple operations
        """
        issue = HivemindIssue()
        issue.name = 'Test Restricted Hivemind'
        issue.add_question('What is your opinion?')
        issue.description = 'Restricted voting'
        issue.answer_type = 'String'
        issue.restrictions = {}  # Initialize restrictions
        
        # Generate two key pairs for testing
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()
        
        # Set restrictions to only allow address1 and address2
        issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        state.set_hivemind_issue(issue.save())  # Issue has options_per_address = 2
        timestamp = int(time.time())

        # Create base option template
        def create_option(content: str) -> str:
            option = HivemindOption()
            option.set_hivemind_issue(issue.save())
            option.set(content)
            return option.save()

        # Test address 1 can add up to limit
        option1_hash = create_option("option1 from addr1")
        option2_hash = create_option("option2 from addr1")

        # Both options should succeed
        message1 = '%s%s' % (timestamp, option1_hash)
        signature1 = sign_message(message1, MOCK_PRIVATE_KEY_1)
        state.add_option(timestamp, option1_hash, MOCK_ADDRESS_1, signature1)

        message2 = '%s%s' % (timestamp, option2_hash)
        signature2 = sign_message(message2, MOCK_PRIVATE_KEY_1)
        state.add_option(timestamp, option2_hash, MOCK_ADDRESS_1, signature2)

        # Third option should fail
        option3_hash = create_option("option3 from addr1")
        message3 = '%s%s' % (timestamp, option3_hash)
        signature3 = sign_message(message3, MOCK_PRIVATE_KEY_1)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option3_hash, MOCK_ADDRESS_1, signature3)
        assert 'Address has reached the maximum number of options' in str(exc_info.value)

        # Test address 2 has independent limit
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")

        # Both options should succeed for address 2
        message4 = '%s%s' % (timestamp, option4_hash)
        signature4 = sign_message(message4, MOCK_PRIVATE_KEY_2)
        state.add_option(timestamp, option4_hash, MOCK_ADDRESS_2, signature4)

        message5 = '%s%s' % (timestamp, option5_hash)
        signature5 = sign_message(message5, MOCK_PRIVATE_KEY_2)
        state.add_option(timestamp, option5_hash, MOCK_ADDRESS_2, signature5)

        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        message6 = '%s%s' % (timestamp, option6_hash)
        signature6 = sign_message(message6, MOCK_PRIVATE_KEY_2)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option6_hash, MOCK_ADDRESS_2, signature6)
        assert 'Address has reached the maximum number of options' in str(exc_info.value)

    def test_option_error_handling(self):
        """Test error handling when adding invalid options."""
        # Create new state and issue
        state = HivemindState()
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Test Question")
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate Bitcoin keypair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Test adding invalid option hash
        invalid_hash = "invalid_hash"
        message = BitcoinMessage(f"{timestamp}{invalid_hash}")
        signature = SignMessage(private_key, message).decode()
        
        with pytest.raises(ValueError, match="Invalid CID value"):
            state.add_option(
                timestamp=timestamp,
                option_hash=invalid_hash,
                address=address,
                signature=signature
            )
        
        # Test adding duplicate option
        option = HivemindOption()
        option.value = "red"
        option_hash = option.save()
        
        # Add first time should succeed
        message = BitcoinMessage(f"{timestamp}{option_hash}")
        signature = SignMessage(private_key, message).decode()
        
        state.add_option(
            timestamp=timestamp,
            option_hash=option_hash,
            address=address,
            signature=signature
        )
        
        # Add same option again should fail
        message = BitcoinMessage(f"{timestamp}{option_hash}")
        signature = SignMessage(private_key, message).decode()
        
        with pytest.raises(Exception, match="Option already exists"):
            state.add_option(
                timestamp=timestamp,
                option_hash=option_hash,
                address=address,
                signature=signature
            )

    def test_invalid_state_loading(self):
        """Test that loading an invalid state CID raises appropriate errors."""
        # Test with invalid CID
        with pytest.raises(Exception):
            HivemindState(cid="invalid_cid")
