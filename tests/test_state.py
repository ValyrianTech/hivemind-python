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
        issue.restrictions = {}  # Initialize restrictions
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
        issue.restrictions = {}  # Initialize restrictions
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
        issue.restrictions = {}  # Initialize restrictions
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
        issue.restrictions = {}  # Initialize restrictions
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
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key1)
            state.add_option(timestamp, option_hash, address1, signature)
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(option_hashes)  # First address prefers red > blue > green
        opinion.ranking = opinion.ranking.get()  # Get serializable representation
        opinion_hash = opinion.save()  # Save will use the data we just set
        
        # Initialize participants dictionary and add participant
        state.participants = {}
        state.participants[address1] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Test with invalid signature
        with pytest.raises(Exception) as exc_info:
            state.add_opinion(timestamp, opinion_hash, 'invalid_sig', address1)
        assert 'invalid' in str(exc_info.value).lower()
        
        # Test with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key1)
        state.add_opinion(timestamp, opinion_hash, signature, address1)
        
        # Verify opinion was added
        assert state.opinions[0][address1]['opinion_cid'] == opinion_hash  # First question's opinions
        assert address1 in state.participants

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
        issue.restrictions = {}  # Initialize restrictions
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
        
        # Initialize participants
        state.participants = {}
        state.participants[address1] = {'name': 'User 1', 'timestamp': timestamp}
        state.participants[address2] = {'name': 'User 2', 'timestamp': timestamp}
        
        # Add options manually
        option_hashes = []
        for choice in issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(value=choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            option_hashes.append(option_hash)
            
            # Sign and add option
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key1)
            state.add_option(timestamp, option_hash, address1, signature)
        
        # Add opinions from different addresses
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue_hash
        opinion1.question_index = 0
        opinion1.ranking.set_fixed(option_hashes)  # First address prefers red > blue > green
        opinion1.ranking = opinion1.ranking.get()  # Get serializable representation
        opinion1_hash = opinion1.save()  # Save will use the data we just set
        
        message1 = '%s%s' % (timestamp, opinion1_hash)
        signature1 = sign_message(message1, private_key1)
        state.add_opinion(timestamp, opinion1_hash, signature1, address1)
        
        # Second address prefers blue > green > red
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue_hash
        opinion2.question_index = 0
        opinion2.ranking.set_fixed([option_hashes[1], option_hashes[2], option_hashes[0]])
        opinion2.ranking = opinion2.ranking.get()  # Get serializable representation
        opinion2_hash = opinion2.save()
        
        message2 = '%s%s' % (timestamp, opinion2_hash)
        signature2 = sign_message(message2, private_key2)
        state.add_opinion(timestamp, opinion2_hash, signature2, address2)
        
        # Calculate results
        results = state.calculate_results()
        
        # Verify results structure
        for option_hash in option_hashes:
            assert option_hash in results
            assert 'win' in results[option_hash]
            assert 'loss' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]

    def test_calculate_results_invalid_question_index(self, state: HivemindState) -> None:
        """Test calculating results with invalid question index"""
        # Create issue with multiple questions
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('Question 1?')
        issue.add_question('Question 2?')
        issue.description = 'Test description'
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())
        
        # Add an option
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test option')
        option_hash = option.save()
        
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        
        # Try to calculate results with invalid question index
        with pytest.raises(IndexError, match='list index out of range'):
            state.calculate_results(question_index=999)
        
        # Valid question indices should work
        results0 = state.calculate_results(question_index=0)
        results1 = state.calculate_results(question_index=1)
        assert isinstance(results0, dict)
        assert isinstance(results1, dict)

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
        signature1 = sign_message(message1, private_key1)
        state.add_option(timestamp, option1_hash, address1, signature1)

        message2 = '%s%s' % (timestamp, option2_hash)
        signature2 = sign_message(message2, private_key1)
        state.add_option(timestamp, option2_hash, address1, signature2)

        # Third option should fail
        option3_hash = create_option("option3 from addr1")
        message3 = '%s%s' % (timestamp, option3_hash)
        signature3 = sign_message(message3, private_key1)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option3_hash, address1, signature3)
        assert 'already added too many options' in str(exc_info.value)

        # Test address 2 has independent limit
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")

        # Both options should succeed for address 2
        message4 = '%s%s' % (timestamp, option4_hash)
        signature4 = sign_message(message4, private_key2)
        state.add_option(timestamp, option4_hash, address2, signature4)

        message5 = '%s%s' % (timestamp, option5_hash)
        signature5 = sign_message(message5, private_key2)
        state.add_option(timestamp, option5_hash, address2, signature5)

        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        message6 = '%s%s' % (timestamp, option6_hash)
        signature6 = sign_message(message6, private_key2)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option6_hash, address2, signature6)
        assert 'already added too many options' in str(exc_info.value)

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

    def test_verify_message_error_handling(self) -> None:
        """Test error handling in verify_message function"""
        from hivemind.state import verify_message
        
        # Generate a real key pair
        private_key, address = generate_bitcoin_keypair()
        
        # Test with invalid signature format
        assert not verify_message("test message", address, "invalid_sig")
        
        # Test with invalid address
        assert not verify_message("test message", "invalid_address", sign_message("test message", private_key))
        
        # Test with None/invalid values
        assert not verify_message(None, address, sign_message("test message", private_key))
        assert not verify_message("test message", None, sign_message("test message", private_key))
        assert not verify_message("test message", address, None)

    def test_add_option_error_handling(self, state: HivemindState) -> None:
        """Test error handling in add_option"""
        # Generate key pairs
        private_key, address = generate_bitcoin_keypair()
        
        # Setup basic issue with restrictions
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Test Question?")
        issue.restrictions = {
            "addresses": [address],  # List of allowed addresses
            "options_per_address": 1  # Max options per address
        }
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Test adding option when state is final
        state.final = True
        timestamp = int(time.time())
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option_hash = option.save()
        
        # Sign the option
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        
        # Try to add when final (should raise exception)
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, address, signature)
        assert 'finalized' in str(exc_info.value)
        assert option_hash not in state.options
        
        # Reset final state and test adding option with invalid signature
        state.final = False
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_option(timestamp, option_hash, address, invalid_signature)

    def test_add_opinion_error_handling(self, state: HivemindState) -> None:
        """Test error handling in add_opinion"""
        # Generate key pairs
        private_key, address = generate_bitcoin_keypair()
        
        # Setup basic issue
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Test Question?")
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add some options first
        option1 = HivemindOption()
        option1.set_hivemind_issue(issue_hash)
        option1.set(value="option1")
        option1_hash = option1.save()
        
        option2 = HivemindOption()
        option2.set_hivemind_issue(issue_hash)
        option2.set(value="option2")
        option2_hash = option2.save()
        
        # Create and save opinion
        timestamp = int(time.time())
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option1_hash, option2_hash])  # Use set_fixed instead of add
        opinion.ranking = opinion.ranking.get()  # Get serializable representation
        opinion_hash = opinion.save()  # Save will use the data we just set
        
        # Test adding opinion when state is final
        state.final = True
        signature = sign_message(f"{timestamp}{opinion_hash}", private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        assert address not in state.opinions[0]

        # Reset final state and test adding opinion with invalid signature
        state.final = False
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_opinion(timestamp, opinion_hash, invalid_signature, address)

    def test_calculate_results_error_handling(self, state: HivemindState) -> None:
        """Test error handling in calculate_results"""
        # Setup basic issue
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Test Question?")
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Test with invalid question index
        with pytest.raises(IndexError):
            state.calculate_results(question_index=999)
        
        # Test with no options
        results = state.calculate_results()
        assert results == {}

    def test_load_error_handling(self, state: HivemindState) -> None:
        """Test error handling in load method"""
        # Create a basic issue first
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Test Question?")
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Save current state
        state_hash = state.save()
        
        # Create new state and load
        new_state = HivemindState()
        new_state.opinions = None
        new_state.load(state_hash)
        
        # Verify opinions are properly initialized
        assert isinstance(new_state.opinions, list)
        assert len(new_state.opinions) == 1
        assert new_state.opinions[0] == {}

    def test_add_predefined_options_boolean(self, state: HivemindState) -> None:
        """Test adding predefined boolean options"""
        # Setup basic issue with boolean type
        issue = HivemindIssue()
        issue.name = "Test Boolean Issue"
        issue.add_question("Yes or No?")
        issue.description = "A simple yes/no question"
        issue.tags = ["test", "boolean"]
        issue.answer_type = "Bool"
        issue.constraints = {}  # Initialize constraints
        issue.restrictions = {}  # Initialize restrictions
        issue.set_constraints({
            "true_value": "Yes",
            "false_value": "No"
        })
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        options = state.add_predefined_options()

        # Should have exactly 2 options (true and false)
        assert len(options) == 2
        assert len(state.options) == 2

        # Check the options were created correctly
        option_values = []
        option_texts = []
        for option_hash in state.options:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)

        # Should have True and False values
        assert True in option_values
        assert False in option_values
        # Should have correct display texts
        assert "Yes" in option_texts
        assert "No" in option_texts

    def test_add_predefined_options_choices(self, state: HivemindState) -> None:
        """Test adding predefined choice options"""
        # Setup basic issue with choices
        issue = HivemindIssue()
        issue.name = "Test Choice Issue"
        issue.add_question("What's your favorite color?")
        issue.description = "Choose your favorite color"
        issue.tags = ["test", "color"]
        issue.answer_type = "String"
        issue.constraints = {}  # Initialize constraints
        issue.restrictions = {}  # Initialize restrictions
        issue.set_constraints({
            "choices": [
                {"value": "red", "text": "Red"},
                {"value": "blue", "text": "Blue"},
                {"value": "green", "text": "Green"}
            ]
        })
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        options = state.add_predefined_options()

        # Should have exactly 3 options
        assert len(options) == 3
        assert len(state.options) == 3

        # Check the options were created correctly
        option_values = []
        option_texts = []
        for option_hash in state.options:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)

        # Should have all color values
        assert "red" in option_values
        assert "blue" in option_values
        assert "green" in option_values
        # Should have correct display texts
        assert "Red" in option_texts
        assert "Blue" in option_texts
        assert "Green" in option_texts

    def test_add_predefined_options_no_constraints(self, state: HivemindState) -> None:
        """Test adding predefined options with no constraints"""
        # Setup basic issue without constraints
        issue = HivemindIssue()
        issue.name = "Test Issue"
        issue.add_question("Question without constraints?")
        issue.description = "A question with no predefined options"
        issue.tags = ["test", "open"]
        issue.answer_type = "String"  # Use String instead of Text
        issue.constraints = {}  # Initialize constraints
        issue.restrictions = {}  # Initialize restrictions
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        options = state.add_predefined_options()

        # Should have no options since there are no constraints
        assert len(options) == 0
        assert len(state.options) == 0

    def test_consensus_methods(self, state: HivemindState) -> None:
        """Test consensus and ranked_consensus methods"""
        # Setup basic issue with choices
        issue = HivemindIssue()
        issue.name = "Test Consensus"
        issue.add_question("What's your favorite color?")
        issue.description = "Choose your favorite color"
        issue.tags = ["test", "color"]
        issue.answer_type = "String"
        issue.constraints = {}  # Initialize constraints
        issue.restrictions = {}  # Initialize restrictions
        issue.set_constraints({
            "choices": [
                {"value": "red", "text": "Red"},
                {"value": "blue", "text": "Blue"},
                {"value": "green", "text": "Green"}
            ]
        })
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        options = state.add_predefined_options()
        option_hashes = list(options.keys())

        # Generate key pairs for multiple participants
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()

        timestamp = int(time.time())

        # First participant prefers red > blue > green
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue_hash
        opinion1.question_index = 0
        opinion1.ranking.set_fixed(option_hashes)  # First address prefers red > blue > green
        opinion1.ranking = opinion1.ranking.get()
        opinion1_hash = opinion1.save()
        
        message1 = f"{timestamp}{opinion1_hash}"
        signature1 = sign_message(message1, private_key1)
        state.add_opinion(timestamp, opinion1_hash, signature1, address1)

        # Second participant prefers blue > red > green
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue_hash
        opinion2.question_index = 0
        opinion2.ranking.set_fixed([option_hashes[1], option_hashes[0], option_hashes[2]])  # blue > red > green
        opinion2.ranking = opinion2.ranking.get()
        opinion2_hash = opinion2.save()
        
        message2 = f"{timestamp}{opinion2_hash}"
        signature2 = sign_message(message2, private_key2)
        state.add_opinion(timestamp, opinion2_hash, signature2, address2)

        # Third participant prefers red > green > blue
        opinion3 = HivemindOpinion()
        opinion3.hivemind_id = issue_hash
        opinion3.question_index = 0
        opinion3.ranking.set_fixed([option_hashes[0], option_hashes[2], option_hashes[1]])  # red > green > blue
        opinion3.ranking = opinion3.ranking.get()
        opinion3_hash = opinion3.save()
        
        message3 = f"{timestamp}{opinion3_hash}"
        signature3 = sign_message(message3, private_key3)
        state.add_opinion(timestamp, opinion3_hash, signature3, address3)

        # Test consensus method
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) > 0
        consensus_value = sorted_options[0].value
        assert consensus_value == "red"  # Red should win as it's preferred by 2 out of 3 participants

        # Test ranked_consensus method using get_sorted_options
        sorted_options = state.get_sorted_options()
        ranked_values = [option.value for option in sorted_options]
        assert len(ranked_values) == 3
        # Order should be: red (2 votes) > blue (1 vote) > green (0 votes)
        assert ranked_values[0] == "red"
        assert ranked_values[1] == "blue"
        assert ranked_values[2] == "green"

        # Test contributions method
        results = state.calculate_results()
        contributions = state.contributions(results)
        
        # All participants should have contributed since they all voted
        assert len(contributions) == 3
        assert address1 in contributions
        assert address2 in contributions
        assert address3 in contributions
        
        # Contributions should be positive for all participants
        assert all(value > 0 for value in contributions.values())

    def test_consensus_no_opinions(self, state: HivemindState) -> None:
        """Test consensus methods when there are no opinions"""
        # Setup basic issue
        issue = HivemindIssue()
        issue.name = "Test No Opinions"
        issue.add_question("Question?")
        issue.description = "A test question"
        issue.tags = ["test"]
        issue.answer_type = "String"
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Add predefined options
        state.add_predefined_options()

        # Test consensus with no opinions
        sorted_options = state.get_sorted_options()
        assert len(sorted_options) == 0

        # Test ranked_consensus with no opinions
        sorted_options = state.get_sorted_options()
        ranked_values = [option.value for option in sorted_options]
        assert len(ranked_values) == 0

        # Test contributions with no opinions
        results = state.calculate_results()
        contributions = state.contributions(results)
        assert len(contributions) == 0

    def test_state_initialization_error_handling(self, state: HivemindState) -> None:
        """Test error handling during state initialization"""
        # Test loading non-existent CID
        with pytest.raises(Exception):
            HivemindState(cid="QmInvalidCID")

        # Test loading invalid state data
        with patch('hivemind.state.HivemindState.load') as mock_load:
            mock_load.side_effect = Exception("Invalid state data")
            with pytest.raises(Exception):
                state.load("QmValidButIncorrectData")

    def test_participant_management(self, state: HivemindState) -> None:
        """Test participant management functions"""
        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())

        # Test 1: Basic participant management
        # Add participant with name
        name = "Test User"
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)
        state.update_participant_name(timestamp, name, address, signature)
        
        assert address in state.participants
        assert state.participants[address]['name'] == name
        assert name in state.signatures[address]
        assert signature in state.signatures[address][name]
        assert state.signatures[address][name][signature] == timestamp

        # Test 2: Update participant name
        new_name = "Updated User"
        new_timestamp = timestamp + 1
        new_message = f"{new_timestamp}{new_name}"
        new_signature = sign_message(new_message, private_key)
        state.update_participant_name(new_timestamp, new_name, address, signature=new_signature)
        
        assert state.participants[address]['name'] == new_name
        assert new_name in state.signatures[address]
        assert new_signature in state.signatures[address][new_name]
        assert state.signatures[address][new_name][new_signature] == new_timestamp

        # Test 3: Reject old timestamp for same name
        old_timestamp = timestamp - 1
        old_message = f"{old_timestamp}{name}"  # Try to update the same name with older timestamp
        old_signature = sign_message(old_message, private_key)
        with pytest.raises(Exception) as exc_info:
            state.update_participant_name(old_timestamp, name, address, signature=old_signature)
        assert "Invalid timestamp" in str(exc_info.value)
        assert state.participants[address]['name'] == new_name  # Name should not change

        # Test 4: Allow old timestamp for different name
        different_name = "Different Name"
        old_message = f"{old_timestamp}{different_name}"
        old_signature = sign_message(old_message, private_key)
        # This should work since it's a different name message
        state.update_participant_name(old_timestamp, different_name, address, signature=old_signature)
        assert state.participants[address]['name'] == different_name

        # Test 5: Invalid signature
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception) as exc_info:
            state.update_participant_name(timestamp, name, address, signature=invalid_signature)
        assert "Invalid signature" in str(exc_info.value)

    def test_consensus_edge_cases(self, state: HivemindState) -> None:
        """Test edge cases in consensus calculation"""
        issue = HivemindIssue()
        issue.name = 'Test Consensus'
        issue.add_question('Test Question?')
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Test with no options
        results = state.calculate_results()
        assert len(results) == 0

        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())

        # Add options
        options = []
        for i in range(3):
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(f"Option {i+1}")
            option_hash = option.save()
            options.append(option_hash)
            
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)

        # Test with options but no opinions
        results = state.calculate_results()
        for option_id in results:
            assert results[option_id]['win'] == 0
            assert results[option_id]['loss'] == 0
            assert results[option_id]['unknown'] == 0
            assert results[option_id]['score'] == 0

        # Add a single opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()

        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)

        # Test consensus modes
        consensus = state.get_consensus(consensus_type='Single')
        assert consensus is not None

        ranked = state.get_consensus(consensus_type='Ranked')
        assert isinstance(ranked, list)
        assert len(ranked) > 0

        with pytest.raises(NotImplementedError):
            state.get_consensus(consensus_type='Invalid')

    def test_state_verification(self, state: HivemindState) -> None:
        """Test state verification functions"""
        issue = HivemindIssue()
        issue.name = 'Test Verification'
        issue.add_question('Test Question?')
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)

        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp = int(time.time())

        # Test first signature (should succeed)
        message = "test_message"
        signature = "sig1"  # Actual signature verification is done elsewhere
        state.add_signature(address, timestamp, message, signature)
        assert address in state.signatures
        assert message in state.signatures[address]
        assert signature in state.signatures[address][message]

        # Test duplicate signature with same timestamp (should fail)
        with pytest.raises(Exception) as exc_info:
            state.add_signature(address, timestamp, message, signature)
        assert 'Invalid timestamp' in str(exc_info.value)

        # Test older timestamp (should fail)
        older_timestamp = timestamp - 1
        with pytest.raises(Exception) as exc_info:
            state.add_signature(address, older_timestamp, message, "sig2")
        assert 'Invalid timestamp' in str(exc_info.value)

        # Test newer timestamp (should succeed)
        newer_timestamp = timestamp + 1
        state.add_signature(address, newer_timestamp, message, "sig3")
        assert "sig3" in state.signatures[address][message]

        # Test state finalization
        state.final = True
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set("New Option")
        option_hash = option.save()
        
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        
        # Should not be able to add options when state is final
        with pytest.raises(Exception):
            state.add_option(timestamp, option_hash, address, signature)

    def test_add_opinion_timestamp_validation(self, state: HivemindState) -> None:
        """Test opinion timestamp validation when adding opinions"""
        # Create issue
        issue = HivemindIssue()
        issue.name = 'Test Hivemind'
        issue.add_question('Test Question?')
        issue.description = 'Test description'
        issue.answer_type = 'String'
        issue.constraints = {}
        issue.restrictions = {}
        issue_hash = issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Generate key pair for testing
        private_key, address = generate_bitcoin_keypair()
        timestamp1 = int(time.time())
        
        # Add first opinion
        opinion1 = HivemindOpinion()
        opinion1.hivemind_id = issue_hash
        opinion1.question_index = 0
        opinion1.ranking = []
        opinion1_hash = opinion1.save()
        
        message1 = f"{timestamp1}{opinion1_hash}"
        signature1 = sign_message(message1, private_key)
        state.add_opinion(timestamp1, opinion1_hash, signature1, address)
        
        # Try to add opinion with older timestamp
        time.sleep(1)  # Ensure we have a different timestamp
        opinion2 = HivemindOpinion()
        opinion2.hivemind_id = issue_hash
        opinion2.question_index = 0
        opinion2.ranking = []
        opinion2_hash = opinion2.save()
        
        old_timestamp = timestamp1 - 10
        message2 = f"{old_timestamp}{opinion2_hash}"
        signature2 = sign_message(message2, private_key)
        
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_opinion(old_timestamp, opinion2_hash, signature2, address)
        
        # Add opinion with newer timestamp should succeed
        new_timestamp = int(time.time())
        message3 = f"{new_timestamp}{opinion2_hash}"
        signature3 = sign_message(message3, private_key)
        state.add_opinion(new_timestamp, opinion2_hash, signature3, address)
        
        # Verify the opinion was updated
        assert state.opinions[0][address]['opinion_cid'] == opinion2_hash
        assert state.opinions[0][address]['timestamp'] == new_timestamp
