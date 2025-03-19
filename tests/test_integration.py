#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import time
from typing import Dict, List, Tuple, Optional, Union
import base64
from datetime import datetime

import pytest
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, SignMessage

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState
from hivemind.utils import generate_bitcoin_keypair, sign_message


def log_step(step_num: int, description: str) -> None:
    """Print a formatted step header with timestamp.
    
    Args:
        step_num: Step number in the workflow
        description: Description of the step
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] Step {step_num}: {description}')
    print('=' * 60)


def log_substep(description: str) -> None:
    """Print a formatted substep header.
    
    Args:
        description: Description of the substep
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] {description}')
    print('-' * 40)


def test_full_hivemind_workflow() -> None:
    """Test the complete Hivemind voting workflow.
    
    Test Scenarios:
        1. Issue Creation:
           - Create issue with multiple questions
           - Verify question addition
           - Verify property setting
           
        2. Access Control:
           - Set voter restrictions
           - Verify address validation
           
        3. Option Management:
           - Add multiple options
           - Verify option persistence
           
        4. Opinion Collection:
           - Submit multiple opinions
           - Verify signature validation
           
        5. Results Calculation:
           - Calculate rankings
           - Verify contribution scores
    
    Raises:
        AssertionError: If any verification step fails
    """
    start_time: float = time.time()
    print('\nStarting Hivemind Integration Test')
    print('=' * 60)
    print(f'Test started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Create the issue
    log_step(1, 'Creating and Configuring Hivemind Issue')

    name: str = 'test hivemind'
    question1: str = 'Which number is bigger?'
    question2: str = 'Which number is smaller?'
    description: str = 'Rank the numbers'
    option_type: str = 'Integer'

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
    assert len(hivemind_issue.questions) == 2

    hivemind_issue.description = description
    hivemind_issue.save()
    print('Added description')
    assert hivemind_issue.description == description

    hivemind_issue.answer_type = option_type
    hivemind_issue.save()
    print('Set answer type')
    assert hivemind_issue.answer_type == option_type

    tags: List[str] = ['mytag', 'anothertag']
    hivemind_issue.tags = tags
    hivemind_issue.save()
    print(f'Added tags: {tags}')
    assert hivemind_issue.tags == tags

    log_step(2, 'Setting up Access Restrictions')

    # Set restrictions using random Bitcoin addresses
    voter_keys: List[Tuple[CBitcoinSecret, str]] = [generate_bitcoin_keypair() for _ in range(2)]
    options_per_address: int = 11  # Increased to match the number of options
    restrictions: Dict[str, Union[List[str], int]] = {
        'addresses': [addr for _, addr in voter_keys],
        'options_per_address': options_per_address
    }
    print('Generated voter keys and setting restrictions:')
    print(f'- Allowed addresses: {restrictions["addresses"]}')
    print(f'- Options per address: {restrictions["options_per_address"]}')

    hivemind_issue.set_restrictions(restrictions=restrictions)
    hivemind_issue_hash: str = hivemind_issue.save()
    print(f'\nHivemind issue saved')
    print(f'  IPFS Hash: {hivemind_issue_hash}')
    assert hivemind_issue_hash is not None and len(hivemind_issue_hash) > 0

    log_step(3, 'Initializing Hivemind State')

    # Create and set up the state
    hivemind_state = HivemindState()
    hivemind_state.set_hivemind_issue(issue_hash=hivemind_issue_hash)
    statehash: str = hivemind_state.save()

    print('Initial state created:')
    print(f'- Hash: {statehash}')
    print(f'- State: {hivemind_state}')
    print(f'- Current options: {hivemind_state.option_cids}')
    assert hivemind_state.option_cids == []
    assert statehash is not None and len(statehash) > 0

    log_step(4, 'Adding Voting Options')

    # Add options
    option_hashes: Dict[int, str] = {}
    option_values: Dict[int, str] = {i: v for i, v in enumerate(['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'])}

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

        timestamp: int = int(time.time())
        message: str = '%s%s' % (timestamp, option.cid())
        signature: str = sign_message(message, proposer_key)
        print(f'Signed by: {proposer_address}')

        hivemind_state.add_option(
            option_hash=option.cid(),
            address=proposer_address,
            signature=signature,
            timestamp=timestamp
        )
        print('Option added to state')

    print('\nOptions summary:')
    print(f'- Total options added: {len(hivemind_state.option_cids)}')
    print(f'- Current state options: {hivemind_state.option_cids}')
    assert len(hivemind_state.option_cids) == len(option_values)
    assert all(opt_hash in hivemind_state.option_cids for opt_hash in option_hashes.values())

    # Verify options_per_address restriction
    print('\nVerifying options_per_address restriction:')
    proposer_options = hivemind_state.options_by_participant(proposer_address)
    print(f'- Options added by {proposer_address}: {len(proposer_options)}')
    assert len(proposer_options) == options_per_address, f"Expected {options_per_address} options for {proposer_address}, got {len(proposer_options)}"

    # Try to add one more option (should fail)
    extra_option = HivemindOption()
    extra_option.set_hivemind_issue(hivemind_issue_hash)
    extra_option._answer_type = option_type  # Set the answer type to match others
    extra_option.set(11)  # Use next integer in sequence
    extra_option.text = "Eleven"  # Add descriptive text
    extra_option_hash = extra_option.save()

    timestamp = int(time.time())
    message = '%s%s' % (timestamp, extra_option.cid())
    signature = sign_message(message, proposer_key)

    print('\nTesting options_per_address limit:')
    try:
        hivemind_state.add_option(timestamp, extra_option_hash, proposer_address, signature)
        assert False, "Should have rejected option due to options_per_address limit"
    except Exception as e:
        print(f'Successfully rejected extra option: {str(e)}')
        assert 'already added too many options' in str(e)

    hivemind_state_hash: str = hivemind_state.save()
    print(f'\nUpdated state saved')
    print(f'  - New state hash: {hivemind_state_hash}')
    print(f'  - Hivemind issue id: {hivemind_state.hivemind_id}')

    log_step(5, 'Collecting and Processing Opinions')

    # Add opinions for each question
    for question_index in range(len(hivemind_issue.questions)):
        log_substep(f'Processing opinions for Question {question_index + 1}')
        print(f'Question: {hivemind_issue.questions[question_index]}')

        # Test that unauthorized address is rejected
        unauthorized_key, unauthorized_address = generate_bitcoin_keypair()
        unauthorized_opinion = HivemindOpinion()
        unauthorized_opinion.hivemind_id = hivemind_state.hivemind_id
        unauthorized_opinion.set_question_index(question_index)
        ranked_choice = hivemind_state.option_cids.copy()
        random.shuffle(ranked_choice)
        unauthorized_opinion.ranking.set_fixed(ranked_choice)
        unauthorized_opinion.ranking = unauthorized_opinion.ranking.get()
        unauthorized_opinion_hash = unauthorized_opinion.save()

        timestamp = int(time.time())
        message = '%s%s' % (timestamp, unauthorized_opinion.cid())
        signature = sign_message(message, unauthorized_key)

        print('\nTesting unauthorized opinion rejection:')
        print(f'- Unauthorized address: {unauthorized_address}')
        try:
            hivemind_state.add_opinion(
                timestamp=timestamp,
                opinion_hash=unauthorized_opinion.cid(),
                signature=signature,
                address=unauthorized_address
            )
            assert False, "Should have rejected unauthorized address"
        except Exception as e:
            print(f'Successfully rejected unauthorized address: {str(e)}')
            assert 'not allowed to add opinions' in str(e)

        # Now add valid opinions from authorized addresses
        n_opinions = len(voter_keys)  # Use only the authorized addresses
        print(f'\nAdding {n_opinions} opinions from authorized addresses')

        for i in range(n_opinions):
            private_key, address = voter_keys[i]
            opinion = HivemindOpinion()
            opinion.hivemind_id = hivemind_state.hivemind_id
            opinion.set_question_index(question_index)
            ranked_choice = hivemind_state.option_cids.copy()
            random.shuffle(ranked_choice)
            opinion.ranking.set_fixed(ranked_choice)
            opinion.ranking = opinion.ranking.get()
            opinion_hash = opinion.save()

            print(f'\nProcessing opinion {i + 1}/{n_opinions}:')
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

        # Verify opinions were properly added
        assert len(hivemind_state.opinion_cids[question_index]) == n_opinions, f"Expected {n_opinions} opinions for question {question_index}, got {len(hivemind_state.opinion_cids[question_index])}"

        # Calculate and display results
        log_substep(f'Calculating results for Question {question_index + 1}')
        results: Dict[str, float] = hivemind_state.calculate_results(question_index=question_index)
        print('Results calculation complete')
        print(f'Raw results: {results}')

        print('\nAnalyzing contributions by participant:')
        contributions: Dict[str, float] = hivemind_state.contributions(results, question_index=question_index)
        for addr, score in contributions.items():
            print(f'- {addr}: {score}')

        # Verify all opinion givers have contribution scores
        assert all(addr in contributions for _, addr in voter_keys)

        print('\nFinal rankings:')
        sorted_options: List[HivemindOption] = hivemind_state.get_sorted_options(question_index=question_index)
        for i, option in enumerate(sorted_options, 1):
            print(f'{i}. Value: {option.value}, Text: {option.text}')

        # Verify rankings are complete
        assert len(sorted_options) == len(option_values)

    log_step(6, 'Finalizing Test')
    final_state_hash: str = hivemind_state.save()
    assert final_state_hash is not None and len(final_state_hash) > 0

    end_time: float = time.time()
    duration: float = end_time - start_time

    print('Test Summary:')
    print('-' * 40)
    print(f'- Test completed successfully')
    print(f'- Duration: {duration:.2f} seconds')
    print(f'- Final state hash: {final_state_hash}')
    print(f'- Questions processed: {len(hivemind_issue.questions)}')
    print(f'- Total options: {len(option_values)}')
    print(f'- Total opinions: {n_opinions * len(hivemind_issue.questions)}')
    print('=' * 60)
