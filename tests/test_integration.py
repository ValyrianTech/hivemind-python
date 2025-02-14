#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import time
from typing import Dict, List, Tuple
import base64
from datetime import datetime

import pytest
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState

def log_step(step_num: int, description: str) -> None:
    """Print a formatted step header with timestamp.
    
    Args:
        step_num: Step number in the workflow
        description: Description of the step
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] Step {step_num}: {description}')
    print('='*60)

def log_substep(description: str) -> None:
    """Print a formatted substep header.
    
    Args:
        description: Description of the substep
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] {description}')
    print('-'*40)

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

def test_full_hivemind_workflow():
    """
    Integration test that tests the full workflow of:
    1. Creating a hivemind issue with multiple questions
    2. Adding options to the issue
    3. Setting restrictions
    4. Adding multiple opinions from different addresses
    5. Calculating and verifying results
    """
    start_time = time.time()
    print('\nStarting Hivemind Integration Test')
    print('='*60)
    print(f'Test started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Create the issue
    log_step(1, 'Creating and Configuring Hivemind Issue')
    
    name = 'test hivemind'
    question1 = 'Which number is bigger?'
    question2 = 'Which number is smaller?'
    description = 'Rank the numbers'
    option_type = 'Integer'

    log_substep('Setting initial issue properties')
    print(f'Name: {name}')
    print(f'Question 1: {question1}')
    print(f'Question 2: {question2}')
    print(f'Description: {description}')
    print(f'Option type: {option_type}')

    hivemind_issue = HivemindIssue()
    assert isinstance(hivemind_issue, HivemindIssue)
    print('\nHivemind issue instance created successfully')

    # Set up the issue
    log_substep('Configuring issue properties')
    hivemind_issue.name = name
    hivemind_issue.add_question(question=question1)
    hivemind_issue.save()
    print('Added question 1')
    assert hivemind_issue.questions[0] == question1

    hivemind_issue.add_question(question=question2)
    hivemind_issue.save()
    print('Added question 2')
    assert hivemind_issue.questions[1] == question2

    hivemind_issue.description = description
    hivemind_issue.save()
    print('Added description')
    assert hivemind_issue.description == description

    hivemind_issue.answer_type = option_type
    hivemind_issue.save()
    print('Set answer type')
    assert hivemind_issue.answer_type == option_type

    tags = ['mytag', 'anothertag']
    hivemind_issue.tags = tags
    hivemind_issue.save()
    print(f'Added tags: {tags}')
    assert hivemind_issue.tags == tags

    log_step(2, 'Setting up Access Restrictions')
    
    # Set restrictions using random Bitcoin addresses
    voter_keys = [generate_bitcoin_keypair() for _ in range(2)]
    restrictions = {
        'addresses': [addr for _, addr in voter_keys],
        'options_per_address': 10
    }
    print('Generated voter keys and setting restrictions:')
    print(f'- Allowed addresses: {restrictions["addresses"]}')
    print(f'- Options per address: {restrictions["options_per_address"]}')
    
    hivemind_issue.set_restrictions(restrictions=restrictions)
    hivemind_issue_hash = hivemind_issue.save()
    print(f'\nHivemind issue saved')
    print(f'  IPFS Hash: {hivemind_issue_hash}')

    log_step(3, 'Initializing Hivemind State')
    
    # Create and set up the state
    hivemind_state = HivemindState()
    hivemind_state.set_hivemind_issue(issue_hash=hivemind_issue_hash)
    statehash = hivemind_state.save()

    print('Initial state created:')
    print(f'- Hash: {statehash}')
    print(f'- State: {hivemind_state}')
    print(f'- Current options: {hivemind_state.options}')
    assert hivemind_state.options == []

    log_step(4, 'Adding Voting Options')
    
    # Add options
    option_hashes: Dict[int, str] = {}
    option_values = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten']
    option_values = {i: option_values[i] for i in range(len(option_values))}

    # Use the first voter key for adding options
    proposer_key, proposer_address = voter_keys[0]
    print(f'Using proposer address: {proposer_address}')
    print(f'Total options to add: {len(option_values)}\n')

    for option_value, option_text in option_values.items():
        log_substep(f'Adding option {option_value}: {option_text}')
        option = HivemindOption()
        option.set_hivemind_issue(hivemind_issue_hash=hivemind_issue_hash)
        option._answer_type = option_type
        option.set(value=option_value)
        option.text = option_text
        option_hash = option.save()
        option_hashes[option_value] = option_hash
        print(f'Option saved with IPFS hash: {option.cid()}')

        timestamp = int(time.time())
        message = '%s%s' % (timestamp, option.cid())
        signature = sign_message(message, proposer_key)
        print(f'Signed by: {proposer_address}')

        hivemind_state.add_option(
            option_hash=option.cid(),
            address=proposer_address,
            signature=signature,
            timestamp=timestamp
        )
        print('Option added to state')

    print('\nOptions summary:')
    print(f'- Total options added: {len(hivemind_state.options)}')
    print(f'- Current state options: {hivemind_state.options}')
    assert len(hivemind_state.options) == len(option_values)

    hivemind_state_hash = hivemind_state.save()
    print(f'\nUpdated state saved')
    print(f'  - New state hash: {hivemind_state_hash}')
    print(f'  - Hivemind issue id: {hivemind_state.hivemind_id}')

    log_step(5, 'Collecting and Processing Opinions')
    
    # Add opinions for each question
    for question_index in range(len(hivemind_issue.questions)):
        log_substep(f'Processing opinions for Question {question_index + 1}')
        print(f'Question: {hivemind_issue.questions[question_index]}')

        n_opinions = 20
        # Generate a set of opinion givers with their keys
        opinion_keys = [generate_bitcoin_keypair() for _ in range(n_opinions)]
        print(f'Generated {n_opinions} unique opinion giver keys')

        for i in range(n_opinions):
            private_key, address = opinion_keys[i]
            opinion = HivemindOpinion()
            opinion.hivemind_id = hivemind_state.hivemind_id
            opinion.set_question_index(question_index)
            ranked_choice = hivemind_state.options.copy()
            random.shuffle(ranked_choice)
            opinion.ranking.set_fixed(ranked_choice)
            opinion.ranking = opinion.ranking.get()
            opinion_hash = opinion.save()
            
            print(f'\nProcessing opinion {i+1}/{n_opinions}:')
            print(f'- Address: {address}')
            print(f'- Ranking: {ranked_choice}')
            print(f'- Opinion hash: {opinion.cid()}')

            timestamp = int(time.time())
            message = '%s%s' % (timestamp, opinion.cid())
            signature = sign_message(message, private_key)

            print('Adding opinion to state...')
            hivemind_state.add_opinion(
                timestamp=timestamp,
                opinion_hash=opinion.cid(),
                signature=signature,
                address=address
            )
            print('Opinion successfully added')

        print(f'\nCompleted processing all opinions for Question {question_index + 1}')
        
        # Calculate and display results
        log_substep(f'Calculating results for Question {question_index + 1}')
        results = hivemind_state.calculate_results(question_index=question_index)
        print('Results calculation complete')
        print(f'Raw results: {results}')
        
        print('\nAnalyzing contributions by participant:')
        contributions = hivemind_state.contributions(results, question_index=question_index)
        for addr, score in contributions.items():
            print(f'- {addr}: {score}')
        
        print('\nFinal rankings:')
        sorted_options = hivemind_state.get_sorted_options(question_index=question_index)
        for i, option in enumerate(sorted_options, 1):
            print(f'{i}. Value: {option.value}, Text: {option.text}')

    log_step(6, 'Finalizing Test')
    final_state_hash = hivemind_state.save()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print('Test Summary:')
    print('-' * 40)
    print(f'- Test completed successfully')
    print(f'- Duration: {duration:.2f} seconds')
    print(f'- Final state hash: {final_state_hash}')
    print(f'- Questions processed: {len(hivemind_issue.questions)}')
    print(f'- Total options: {len(option_values)}')
    print(f'- Total opinions: {n_opinions * len(hivemind_issue.questions)}')
    print('='*60)
