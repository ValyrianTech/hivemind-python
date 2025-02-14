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

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
    def test_add_option_with_restrictions(self, state: HivemindState) -> None:
        """Test adding options with address restrictions"""
        issue = HivemindIssue()
        issue.name = 'Test Restricted Hivemind'
        issue.add_question('What is your opinion?')
        issue.description = 'Restricted voting'
        issue.answer_type = 'String'
        issue.restrictions = {}  # Initialize restrictions
        issue.set_restrictions({
            'addresses': [MOCK_ADDRESS_1, MOCK_ADDRESS_2],
            'options_per_address': 2
        })
        state.set_hivemind_issue(issue.save())
        
        # Create a valid option
        option = HivemindOption()
        option.set_hivemind_issue(issue.save())
        option.set('test option')
        option_hash = option.save()
        
        # Test with unauthorized address
        timestamp = int(time.time())
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, '0x789', 'valid_sig')
        assert 'address restrictions' in str(exc_info.value)
        
        # Test with authorized address but invalid signature
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option_hash, MOCK_ADDRESS_1, 'fake_sig')
        assert 'Signature is not valid' in str(exc_info.value)

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
    def test_add_opinion(self, state: HivemindState) -> None:
        """Test adding opinions"""
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
        state.add_predefined_options()
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.ranking.set_fixed(state.options[:2])  # Rank first two options
        opinion_hash = opinion.save()
        
        # Test adding opinion with invalid signature
        timestamp = int(time.time())
        with pytest.raises(Exception) as exc_info:
            state.add_opinion(timestamp, opinion_hash, 'fake_sig', MOCK_ADDRESS_1)
        assert 'Signature is invalid' in str(exc_info.value)

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
    def test_calculate_results(self, state: HivemindState) -> None:
        """Test calculating voting results"""
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
        options = state.add_predefined_options()
        
        results = state.calculate_results()
        assert len(results) == len(options)
        for option_hash in options:
            assert 'win' in results[option_hash]
            assert 'loss' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
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
        
        # Add an option
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test')
        option_hash = option.save()
        state.options.append(option_hash)
        
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
        address = MOCK_ADDRESS_1
        name = 'Alice'
        timestamp = int(time.time())
        
        # Test with invalid signature
        with pytest.raises(Exception) as exc_info:
            state.update_participant_name(timestamp, name, address, 'fake_sig')
        assert 'Invalid signature' in str(exc_info.value)
        
        # Verify participant not added
        assert address not in state.participants

    @pytest.mark.skip(reason="Needs real Bitcoin signatures")
    def test_options_per_address_limit(self, state: HivemindState) -> None:
        """Test enforcement of options_per_address restriction.
        
        This test verifies that:
        1. An address can add up to the maximum allowed options
        2. Adding more than the allowed number fails
        3. Different addresses have independent limits
        4. The limit persists across multiple operations
        """
        issue = HivemindIssue()
        issue.name = 'Test Restricted Hivemind'
        issue.add_question('What is your opinion?')
        issue.description = 'Restricted voting'
        issue.answer_type = 'String'
        issue.restrictions = {}  # Initialize restrictions
        issue.set_restrictions({
            'addresses': [MOCK_ADDRESS_1, MOCK_ADDRESS_2],
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
        state.add_option(timestamp, option1_hash, MOCK_ADDRESS_1, 'valid_sig')
        state.add_option(timestamp, option2_hash, MOCK_ADDRESS_1, 'valid_sig')

        # Third option should fail for address 1
        option3_hash = create_option("option3 from addr1")
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option3_hash, MOCK_ADDRESS_1, 'valid_sig')
        assert 'already added too many options' in str(exc_info.value)

        # Address 2 should still be able to add options
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")
        
        # Both options should succeed for address 2
        state.add_option(timestamp, option4_hash, MOCK_ADDRESS_2, 'valid_sig')
        state.add_option(timestamp, option5_hash, MOCK_ADDRESS_2, 'valid_sig')

        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        with pytest.raises(Exception) as exc_info:
            state.add_option(timestamp, option6_hash, MOCK_ADDRESS_2, 'valid_sig')
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
