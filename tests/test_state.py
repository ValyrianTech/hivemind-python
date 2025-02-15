#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from hivemind import HivemindState, HivemindIssue, HivemindOption, HivemindOpinion
from ipfs_dict_chain.IPFS import connect, IPFSError
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage
import random
import pytest
from typing import Dict, Any, Tuple, List

def generate_bitcoin_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a random Bitcoin private key and its corresponding address.
    
    Returns:
        Tuple[CBitcoinSecret, str]: (private_key, address) pair where address is in base58 format
    """
    entropy = random.getrandbits(256).to_bytes(32, byteorder='big')
    private_key = CBitcoinSecret.from_secret_bytes(entropy)
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

# Common Fixtures
@pytest.fixture
def state() -> HivemindState:
    """Create a fresh HivemindState instance for each test."""
    return HivemindState()

@pytest.fixture
def basic_issue() -> HivemindIssue:
    """Create a basic issue for testing."""
    issue = HivemindIssue()
    issue.name = "Test Issue"
    issue.add_question("Test Question")
    issue.description = "Test Description"
    issue.tags = ["test"]
    issue.answer_type = "String"
    issue.constraints = {}
    issue.restrictions = {}
    return issue

@pytest.fixture
def color_choice_issue(basic_issue) -> HivemindIssue:
    """Create an issue with color choices."""
    basic_issue.set_constraints({
        "choices": [
            {"value": "red", "text": "Red"},
            {"value": "blue", "text": "Blue"},
            {"value": "green", "text": "Green"}
        ]
    })
    return basic_issue

@pytest.fixture
def bool_issue(basic_issue) -> HivemindIssue:
    """Create a boolean issue."""
    basic_issue.answer_type = "Bool"
    basic_issue.set_constraints({
        "true_value": "Yes",
        "false_value": "No"
    })
    return basic_issue

@pytest.fixture
def test_keypair() -> Tuple[CBitcoinSecret, str]:
    """Generate a consistent test keypair."""
    return generate_bitcoin_keypair()

class TestHelper:
    """Helper class containing common test operations."""
    
    @staticmethod
    def create_and_sign_option(state: HivemindState, issue_hash: str, value: str, text: str, 
                             private_key: CBitcoinSecret, address: str, timestamp: int) -> str:
        """Helper to create and sign an option.
        
        Args:
            state: HivemindState instance
            issue_hash: Hash of the issue
            value: Option value
            text: Option display text
            private_key: Signer's private key
            address: Signer's address
            timestamp: Current timestamp
            
        Returns:
            str: Hash of the created option
        """
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set(value=value)
        option.text = text
        option_hash = option.save()
        
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        return option_hash

    @staticmethod
    def create_and_sign_opinion(state: HivemindState, issue_hash: str, ranking: List[str],
                              private_key: CBitcoinSecret, address: str, timestamp: int) -> str:
        """Helper to create and sign an opinion.
        
        Args:
            state: HivemindState instance
            issue_hash: Hash of the issue
            ranking: List of option hashes in preferred order
            private_key: Signer's private key
            address: Signer's address
            timestamp: Current timestamp
            
        Returns:
            str: Hash of the created opinion
        """
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(ranking)  # First address prefers red > blue > green
        opinion.ranking = opinion.ranking.get()  # Get serializable representation
        opinion_hash = opinion.save()  # Save will use the data we just set
        
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        return opinion_hash

@pytest.mark.init
class TestHivemindStateInit:
    """Tests for initialization and basic state management."""
    
    def test_init(self, state: HivemindState) -> None:
        """Test initialization of HivemindState."""
        assert state.hivemind_id is None
        assert state._hivemind_issue is None
        assert state.options == []
        assert state.opinions == [{}]
        assert state.signatures == {}
        assert state.participants == {}
        assert state.selected == []
        assert state.final is False

    def test_set_hivemind_issue(self, state: HivemindState, color_choice_issue: HivemindIssue) -> None:
        """Test setting hivemind issue."""
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        assert state.hivemind_id is not None
        assert isinstance(state._hivemind_issue, HivemindIssue)
        assert len(state.opinions) == len(state._hivemind_issue.questions)

@pytest.mark.options
class TestHivemindStateOptions:
    """Tests for option management."""
    
    def test_add_predefined_options(self, state: HivemindState, bool_issue: HivemindIssue) -> None:
        """Test adding predefined options for both boolean and choice types."""
        issue_hash = bool_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Test boolean options
        options = state.add_predefined_options()
        assert len(options) == 2
        
        # Verify boolean options
        option_values = []
        option_texts = []
        for option_hash in state.options:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)
        
        assert True in option_values
        assert False in option_values
        assert "Yes" in option_texts
        assert "No" in option_texts
        
        # Test with color choices
        state = HivemindState()  # Reset state
        color_issue = HivemindIssue()
        color_issue.name = "Test Choice Issue"
        color_issue.add_question("What's your favorite color?")
        color_issue.description = "Choose your favorite color"
        color_issue.answer_type = "String"
        color_issue.set_constraints({
            "choices": [
                {"value": "red", "text": "Red"},
                {"value": "blue", "text": "Blue"},
                {"value": "green", "text": "Green"}
            ]
        })
        issue_hash = color_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        options = state.add_predefined_options()
        assert len(options) == 3
        
        # Verify color options
        option_values = []
        option_texts = []
        for option_hash in state.options:
            option = HivemindOption(cid=option_hash)
            option_values.append(option.value)
            option_texts.append(option.text)
        
        assert "red" in option_values
        assert "blue" in option_values
        assert "green" in option_values
        assert "Red" in option_texts
        assert "Blue" in option_texts
        assert "Green" in option_texts

    def test_add_option_with_restrictions(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test adding options with address restrictions."""
        # Generate test keypairs
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        private_key3, address3 = generate_bitcoin_keypair()
        
        # Set restrictions
        basic_issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        timestamp = int(time.time())
        
        # Test with unauthorized address
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set('test option')
        option_hash = option.save()
        
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key3)
        with pytest.raises(Exception, match='address restrictions'):
            state.add_option(timestamp, option_hash, address3, signature)
        
        # Test with authorized address but invalid signature
        with pytest.raises(Exception, match='Signature is not valid'):
            state.add_option(timestamp, option_hash, address1, 'invalid_sig')
        
        # Test with authorized address and valid signature
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key1)
        state.add_option(timestamp, option_hash, address1, signature)
        assert option_hash in state.options

@pytest.mark.opinions
class TestHivemindStateOpinions:
    """Tests for opinion management."""
    
    def test_add_opinion(self, state: HivemindState, basic_issue: HivemindIssue, test_keypair) -> None:
        """Test adding opinions."""
        private_key, address = test_keypair
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add options first
        options = []
        for i in range(3):
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(f"Option {i+1}")
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)
        
        # Create an opinion
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed(options)  # First address prefers red > blue > green
        opinion.ranking = opinion.ranking.get()  # Get serializable representation
        opinion_hash = opinion.save()  # Save will use the data we just set
        
        # Initialize participants dictionary and add participant
        state.participants = {}
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        
        # Test with invalid signature
        with pytest.raises(Exception, match='invalid'):
            state.add_opinion(timestamp, opinion_hash, 'invalid_sig', address)
        
        # Test with valid signature
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Verify opinion was added
        assert state.opinions[0][address]['opinion_cid'] == opinion_hash  # First question's opinions
        assert address in state.participants

@pytest.mark.consensus
class TestHivemindStateConsensus:
    """Tests for consensus calculation."""
    
    def test_calculate_results(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test calculating results."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)
        
        # Add opinions
        for i in range(3):
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = 0
            # Create different rankings for each participant
            if i == 0:
                ranking = options  # red > blue > green
            elif i == 1:
                ranking = [options[1], options[0], options[2]]  # blue > red > green
            else:
                ranking = [options[0], options[2], options[1]]  # red > green > blue
                
            opinion.ranking.set_fixed(ranking)
            opinion.ranking = opinion.ranking.get()
            opinion_hash = opinion.save()
            
            # Initialize participants dictionary and add participant
            state.participants[address] = {'name': f'Test User {i+1}', 'timestamp': timestamp}
            
            # Test with valid signature
            message = f"{timestamp}{opinion_hash}"
            signature = sign_message(message, private_key)
            state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Calculate results
        results = state.calculate_results()
        
        # Verify results structure
        for option_hash in options:
            assert option_hash in results
            assert 'win' in results[option_hash]
            assert 'loss' in results[option_hash]
            assert 'unknown' in results[option_hash]
            assert 'score' in results[option_hash]
            
        # Verify red wins (2 first-place votes vs 1 for blue)
        red_option = HivemindOption(cid=options[0])
        assert red_option.value == 'red'
        assert results[options[0]]['score'] > results[options[1]]['score']

@pytest.mark.consensus
class TestHivemindStateRankedConsensus:
    """Tests for ranked consensus calculation."""
    
    def test_ranked_consensus(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test ranked consensus calculation."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add options from constraints
        options = []
        for choice in color_choice_issue.constraints['choices']:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(choice['value'])
            option.text = choice['text']
            option_hash = option.save()
            options.append(option_hash)
            
            # Sign and add option
            timestamp = int(time.time())
            message = f"{timestamp}{option_hash}"
            signature = sign_message(message, private_key)
            state.add_option(timestamp, option_hash, address, signature)
        
        # Add opinions with different rankings
        rankings = [
            options,  # red > blue > green
            [options[1], options[0], options[2]],  # blue > red > green
            [options[0], options[2], options[1]]  # red > green > blue
        ]
        
        # Generate different key pairs for each opinion
        keypairs = [test_keypair] + [generate_bitcoin_keypair() for _ in range(2)]
        
        for i, (ranking, (voter_key, voter_address)) in enumerate(zip(rankings, keypairs)):
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_hash
            opinion.question_index = 0
            opinion.ranking.set_fixed(ranking)
            opinion.ranking = opinion.ranking.get()
            opinion_hash = opinion.save()
            
            # Initialize participants dictionary and add participant
            timestamp = int(time.time())
            state.participants[voter_address] = {'name': f'Test User {i+1}', 'timestamp': timestamp}
            
            # Add opinion with valid signature
            message = f"{timestamp}{opinion_hash}"
            signature = sign_message(message, voter_key)
            state.add_opinion(timestamp, opinion_hash, signature, voter_address)
        
        # Calculate ranked consensus
        sorted_options = state.get_sorted_options()
        
        # Verify ranked consensus
        assert len(sorted_options) == 3
        # Red should win (2 first-place votes)
        assert sorted_options[0].value == 'red'
        # Blue should be second (1 first-place vote)
        assert sorted_options[1].value == 'blue'
        # Green should be last (0 first-place votes)
        assert sorted_options[2].value == 'green'

@pytest.mark.participants
class TestHivemindStateParticipants:
    """Tests for participant management."""
    
    def test_update_participant_name(self, state: HivemindState, test_keypair) -> None:
        """Test updating participant names."""
        private_key, address = test_keypair
        name = 'Alice'
        timestamp = int(time.time())
        
        # Create message and sign it
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)
        
        # Test with invalid signature
        with pytest.raises(Exception, match='Invalid signature'):
            state.update_participant_name(timestamp, name, address, 'fake_sig')
        
        # Test with valid signature
        state.update_participant_name(timestamp, name, address, signature)
        
        # Verify participant was added with correct name
        assert address in state.participants
        assert state.participants[address].get('name') == name

@pytest.mark.participants
class TestHivemindStateParticipantManagement:
    """Tests for participant management."""
    
    def test_participant_management(self, state: HivemindState, test_keypair) -> None:
        """Test participant management functions."""
        private_key, address = test_keypair
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
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.update_participant_name(old_timestamp, name, address, signature=old_signature)
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
        with pytest.raises(Exception, match='Invalid signature'):
            state.update_participant_name(timestamp, name, address, signature=invalid_signature)

@pytest.mark.consensus
class TestHivemindStateConsensusEdgeCases:
    """Tests for edge cases in consensus calculation."""
    
    def test_consensus_no_opinions(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test consensus methods when there are no opinions."""
        issue_hash = basic_issue.save()
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

@pytest.mark.consensus
class TestHivemindStateConsensusMethods:
    """Tests for consensus methods."""
    
    def test_consensus_methods(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test consensus and ranked_consensus methods."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
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

@pytest.mark.consensus
class TestHivemindStateConsensusEdgeCases:
    """Tests for edge cases in consensus calculation."""
    
    def test_consensus_edge_cases(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test edge cases in consensus calculation."""
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

@pytest.mark.state
class TestHivemindStateVerification:
    """Tests for state verification functions."""
    
    def test_state_verification(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test state verification functions."""
        # Set up initial state
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
        timestamp = int(time.time())

        # Test first signature
        message = "test_message"
        signature = sign_message(message, private_key)
        state.add_signature(address, timestamp, message, signature)
        assert address in state.signatures
        assert message in state.signatures[address]
        assert signature in state.signatures[address][message]

        # Test duplicate signature with same timestamp (should fail)
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, timestamp, message, signature)
        assert 'Invalid timestamp' in str(Exception)

        # Test older timestamp (should fail)
        older_timestamp = timestamp - 1
        older_signature = sign_message(message, private_key)
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, older_timestamp, message, older_signature)
        assert 'Invalid timestamp' in str(Exception)

        # Test newer timestamp (should succeed)
        newer_timestamp = timestamp + 1
        newer_signature = sign_message(message, private_key)
        state.add_signature(address, newer_timestamp, message, newer_signature)
        assert newer_signature in state.signatures[address][message]

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

@pytest.mark.state
class TestHivemindStateOpinionTimestampValidation:
    """Tests for opinion timestamp validation."""
    
    def test_add_opinion_timestamp_validation(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test opinion timestamp validation when adding opinions."""
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

@pytest.mark.errors
class TestHivemindStateErrors:
    """Tests for error handling in HivemindState."""
    
    def test_invalid_state_loading(self, state: HivemindState) -> None:
        """Test loading invalid state data."""
        with pytest.raises(Exception):
            state.load('invalid_cid')
    
    def test_verify_message_error_handling(self, state: HivemindState, test_keypair) -> None:
        """Test error handling in verify_message."""
        private_key, address = test_keypair
        
        # Test with invalid signature
        message = "test_message"
        timestamp = int(time.time())
        invalid_signature = "invalid_signature"
        
        with pytest.raises(Exception):
            state.verify_message(address, timestamp, message, invalid_signature)
    
    def test_add_option_error_handling(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test error handling in add_option."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Test with invalid option CID
        timestamp = int(time.time())
        invalid_option_hash = "invalid_option_hash"
        message = f"{timestamp}{invalid_option_hash}"
        signature = sign_message(message, private_key)
        
        with pytest.raises(Exception):
            state.add_option(timestamp, invalid_option_hash, address, signature)
        
        # Test with invalid option value
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        with pytest.raises(Exception):
            option.set("invalid_color")  # Not in color_choice_issue constraints
        
        # Test with invalid signature
        valid_option = HivemindOption()
        valid_option.set_hivemind_issue(issue_hash)
        valid_option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        valid_option_hash = valid_option.save()
        
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_option(timestamp, valid_option_hash, address, invalid_signature)
    
    def test_add_opinion_error_handling(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test error handling in add_opinion."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # Add a valid option first
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        option.text = color_choice_issue.constraints['choices'][0]['text']
        option_hash = option.save()
        
        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        state.add_option(timestamp, option_hash, address, signature)
        
        # Test with invalid opinion CID
        invalid_opinion_hash = "invalid_opinion_hash"
        message = f"{timestamp}{invalid_opinion_hash}"
        signature = sign_message(message, private_key)
        
        with pytest.raises(Exception):
            state.add_opinion(timestamp, invalid_opinion_hash, signature, address)
        
        # Create an opinion with empty ranking (this should be valid)
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([])  # Empty ranking is allowed
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        
        # Empty rankings should be allowed
        state.add_opinion(timestamp, opinion_hash, signature, address)
        
        # Test with invalid signature
        valid_opinion = HivemindOpinion()
        valid_opinion.hivemind_id = issue_hash
        valid_opinion.question_index = 0
        valid_opinion.ranking.set_fixed([option_hash])
        valid_opinion.ranking = valid_opinion.ranking.get()
        valid_opinion_hash = valid_opinion.save()
        
        invalid_signature = "invalid_signature"
        with pytest.raises(Exception):
            state.add_opinion(timestamp, valid_opinion_hash, invalid_signature, address)

@pytest.mark.restrictions
class TestHivemindStateRestrictions:
    """Tests for state restrictions."""
    
    def test_options_per_address_limit(self, state: HivemindState, basic_issue: HivemindIssue) -> None:
        """Test the options_per_address restriction.
        
        Tests:
        1. Options can be added up to the limit
        2. Options beyond the limit are rejected
        3. Different addresses have independent limits
        4. The limit persists across multiple operations
        """
        # Generate test keypairs
        private_key1, address1 = generate_bitcoin_keypair()
        private_key2, address2 = generate_bitcoin_keypair()
        
        # Set restrictions
        basic_issue.set_restrictions({
            'addresses': [address1, address2],
            'options_per_address': 2
        })
        issue_hash = basic_issue.save()
        state.set_hivemind_issue(issue_hash)
        timestamp = int(time.time())
        
        # Helper to create option
        def create_option(content: str) -> str:
            option = HivemindOption()
            option.set_hivemind_issue(issue_hash)
            option.set(content)
            return option.save()
        
        # Test address 1 can add up to limit
        option1_hash = create_option("option1 from addr1")
        option2_hash = create_option("option2 from addr1")
        
        # Both options should succeed
        message1 = f"{timestamp}{option1_hash}"
        signature1 = sign_message(message1, private_key1)
        state.add_option(timestamp, option1_hash, address1, signature1)
        
        message2 = f"{timestamp}{option2_hash}"
        signature2 = sign_message(message2, private_key1)
        state.add_option(timestamp, option2_hash, address1, signature2)
        
        # Third option should fail
        option3_hash = create_option("option3 from addr1")
        message3 = f"{timestamp}{option3_hash}"
        signature3 = sign_message(message3, private_key1)
        with pytest.raises(Exception, match='already added too many options'):
            state.add_option(timestamp, option3_hash, address1, signature3)
        
        # Test address 2 has independent limit
        option4_hash = create_option("option1 from addr2")
        option5_hash = create_option("option2 from addr2")
        
        # Both options should succeed for address 2
        message4 = f"{timestamp}{option4_hash}"
        signature4 = sign_message(message4, private_key2)
        state.add_option(timestamp, option4_hash, address2, signature4)
        
        message5 = f"{timestamp}{option5_hash}"
        signature5 = sign_message(message5, private_key2)
        state.add_option(timestamp, option5_hash, address2, signature5)
        
        # Third option should fail for address 2
        option6_hash = create_option("option3 from addr2")
        message6 = f"{timestamp}{option6_hash}"
        signature6 = sign_message(message6, private_key2)
        with pytest.raises(Exception, match='already added too many options'):
            state.add_option(timestamp, option6_hash, address2, signature6)

@pytest.mark.signatures
class TestHivemindStateSignatures:
    """Tests for signature management."""
    
    def test_add_signature(self, state: HivemindState) -> None:
        """Test adding signatures with timestamp validation."""
        address = generate_bitcoin_keypair()[1]
        message = 'test_message'
        
        # Add first signature
        timestamp1 = int(time.time())
        state.add_signature(address, timestamp1, message, 'sig1')
        assert address in state.signatures
        assert message in state.signatures[address]
        assert 'sig1' in state.signatures[address][message]
        
        # Try adding older signature
        timestamp2 = timestamp1 - 1
        with pytest.raises(Exception, match='Invalid timestamp'):
            state.add_signature(address, timestamp2, message, 'sig2')
        
        # Add newer signature
        timestamp3 = timestamp1 + 1
        state.add_signature(address, timestamp3, message, 'sig3')
        assert 'sig3' in state.signatures[address][message]

@pytest.mark.state
class TestHivemindStateVerification:
    """Tests for state verification."""
    
    def test_state_verification(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test state verification functions."""
        private_key, address = test_keypair
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)
        
        # 1. Test option verification
        option = HivemindOption()
        option.set_hivemind_issue(issue_hash)
        option.set(color_choice_issue.constraints['choices'][0]['value'])  # Use 'red'
        option.text = color_choice_issue.constraints['choices'][0]['text']
        option_hash = option.save()
        
        timestamp = int(time.time())
        message = f"{timestamp}{option_hash}"
        signature = sign_message(message, private_key)
        
        # Valid option should be added
        state.add_option(timestamp, option_hash, address, signature)
        assert option_hash in state.options
        
        # 2. Test opinion verification
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking.set_fixed([option_hash])
        opinion.ranking = opinion.ranking.get()
        opinion_hash = opinion.save()
        
        # Add participant
        state.participants[address] = {'name': 'Test User', 'timestamp': timestamp}
        
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        
        # Valid opinion should be added
        state.add_opinion(timestamp, opinion_hash, signature, address)
        assert state.opinions[0][address]['opinion_cid'] == opinion_hash
        
        # 3. Test participant verification
        name = "Test User"
        message = f"{timestamp}{name}"
        signature = sign_message(message, private_key)
        
        # Valid participant update should work
        state.update_participant_name(timestamp, name, address, signature)
        assert state.participants[address]['name'] == name
        
        # 4. Test signature verification
        test_message = "test_message"
        message = f"{timestamp}{test_message}"
        signature = sign_message(message, private_key)
        
        # Valid signature should be added
        state.add_signature(address, timestamp, test_message, signature)
        assert test_message in state.signatures[address]
        assert signature in state.signatures[address][test_message]

@pytest.mark.consensus
class TestHivemindStateExcludeSelectionMode:
    """Tests for the 'Exclude' selection mode."""
    
    def test_exclude_selection_mode(self, state: HivemindState, color_choice_issue: HivemindIssue, test_keypair) -> None:
        """Test the 'Exclude' selection mode."""
        private_key, address = test_keypair
        timestamp = int(time.time())

        # Set up issue with 'Exclude' mode
        color_choice_issue.on_selection = 'Exclude'
        issue_hash = color_choice_issue.save()
        state.set_hivemind_issue(issue_hash)

        # Create options
        options = []
        for value, text in [("red", "Red"), ("blue", "Blue")]:
            option_hash = TestHelper.create_and_sign_option(state, issue_hash, value, text, private_key, address, timestamp)
            state.add_option(timestamp, option_hash, address)
            options.append(option_hash)

        # Create and add an opinion ranking red > blue
        opinion = HivemindOpinion()
        opinion.hivemind_id = issue_hash
        opinion.question_index = 0
        opinion.ranking = options
        opinion_hash = opinion.save()
        message = f"{timestamp}{opinion_hash}"
        signature = sign_message(message, private_key)
        state.add_opinion(timestamp, opinion_hash, signature, address)

        # First selection should be red
        selection = state.select_consensus()
        assert selection[0].replace('/ipfs/', '') == options[0]  # Red is selected
