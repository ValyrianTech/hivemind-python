#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from typing import Dict, List, Union, Tuple
from datetime import datetime

import pytest
from bitcoin.wallet import CBitcoinSecret

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


def test_hivemind_answer_type_constraints() -> None:
    """Test the Hivemind answer type with various constraints.
    
    Test Scenarios:
        1. Valid Hivemind references (IPFS hashes)
        2. Invalid Hivemind references
    
    Raises:
        AssertionError: If any verification step fails
    """
    start_time: float = time.time()
    print('\nStarting Hivemind Answer Type Integration Test')
    print('=' * 60)
    print(f'Test started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # First, create some valid Hivemind issues to reference
    log_step(1, 'Creating Reference Hivemind Issues')

    reference_hiveminds = []
    for i in range(3):
        log_substep(f'Creating reference Hivemind {i + 1}')
        ref_issue = HivemindIssue()
        ref_issue.name = f'Reference Hivemind {i + 1}'
        ref_issue.add_question(f'Reference Question {i + 1}')
        ref_issue.description = f'Reference Description {i + 1}'
        ref_issue.answer_type = 'String'
        ref_issue.tags = [f'ref{i + 1}', 'test']
        ref_hash = ref_issue.save()
        reference_hiveminds.append(ref_hash)
        print(f'Created reference Hivemind with hash: {ref_hash}')

    # Create the main issue
    log_step(2, 'Creating and Configuring Hivemind Issue for Hivemind Answer Type')

    name: str = 'Hivemind Answer Type Test'
    question: str = 'Which Hivemind do you prefer?'
    description: str = 'Test for Hivemind answer type constraints'
    option_type: str = 'Hivemind'

    log_substep('Setting initial issue properties')
    print(f'Name: {name}')
    print(f'Question: {question}')
    print(f'Description: {description}')
    print(f'Option type: {option_type}')

    hivemind_issue = HivemindIssue()
    assert isinstance(hivemind_issue, HivemindIssue)
    print('\nHivemind issue instance created successfully')

    # Set up the issue
    hivemind_issue.name = name
    hivemind_issue.add_question(question=question)
    hivemind_issue.description = description
    hivemind_issue.answer_type = option_type
    hivemind_issue.tags = ['test', 'hivemind', 'constraints']

    # Set up voter restrictions
    log_step(3, 'Setting up Access Restrictions')

    # Generate voter keys
    voter_keys: List[Tuple[CBitcoinSecret, str]] = [generate_bitcoin_keypair() for _ in range(2)]
    options_per_address: int = 3
    restrictions: Dict[str, Union[List[str], int]] = {
        'addresses': [addr for _, addr in voter_keys],
        'options_per_address': options_per_address
    }
    print('Generated voter keys and setting restrictions:')
    print(f'- Allowed addresses: {restrictions["addresses"]}')
    print(f'- Options per address: {restrictions["options_per_address"]}')

    # hivemind_issue.set_restrictions(restrictions=restrictions)  # Leave this for easier manual testing
    hivemind_issue_hash: str = hivemind_issue.save()
    print(f'\nHivemind issue saved')
    print(f'  IPFS Hash: {hivemind_issue_hash}')
    assert hivemind_issue_hash is not None and len(hivemind_issue_hash) > 0

    # Initialize the state
    log_step(4, 'Initializing Hivemind State')

    hivemind_state = HivemindState()
    hivemind_state.set_hivemind_issue(issue_hash=hivemind_issue_hash)
    statehash: str = hivemind_state.save()

    print('Initial state created:')
    print(f'- Hash: {statehash}')
    print(f'- Current options: {hivemind_state.option_cids}')
    assert hivemind_state.option_cids == []
    assert statehash is not None and len(statehash) > 0

    # Test valid options
    log_step(5, 'Testing Valid Hivemind Options')

    option_texts = ['First Reference', 'Second Reference', 'Third Reference']
    proposer_key, proposer_address = voter_keys[0]

    for i, option_value in enumerate(reference_hiveminds):
        log_substep(f'Adding valid Hivemind option: {option_value}')
        option = HivemindOption()
        option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        option._answer_type = option_type
        option.set(value=option_value)
        option.text = option_texts[i]
        option_hash = option.save()
        print(f'Option saved with IPFS hash: {option.cid()}')

        timestamp: int = int(time.time())
        message: str = '%s%s' % (timestamp, option.cid())
        signature: str = sign_message(message, proposer_key)

        hivemind_state.add_option(
            option_hash=option.cid(),
            address=proposer_address,
            signature=signature,
            timestamp=timestamp
        )
        print('Option added to state')

    print('\nOptions summary:')
    print(f'- Total options added: {len(hivemind_state.option_cids)}')
    assert len(hivemind_state.option_cids) == len(reference_hiveminds)

    # Test invalid options
    log_step(6, 'Testing Invalid Hivemind Options')

    # Test invalid IPFS hash
    log_substep('Testing invalid IPFS hash')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value="QmInvalidIPFSHash")
        assert False, "Should have rejected option due to invalid IPFS hash"
    except Exception as e:
        print(f'Successfully rejected option with invalid IPFS hash: {str(e)}')
        assert 'Invalid value' in str(e) or 'not a valid hivemind' in str(e).lower()

    # Test non-existent Hivemind
    log_substep('Testing non-existent Hivemind')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        # Create a valid-looking but non-existent IPFS hash
        invalid_option.set(value="QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG")
        assert False, "Should have rejected option due to non-existent Hivemind"
    except Exception as e:
        print(f'Successfully rejected option with non-existent Hivemind: {str(e)}')
        assert 'Invalid value' in str(e) or 'not a valid hivemind' in str(e).lower()

    # Test empty IPFS hash
    log_substep('Testing empty IPFS hash')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value="")
        assert False, "Should have rejected option due to empty IPFS hash"
    except Exception as e:
        print(f'Successfully rejected option with empty IPFS hash: {str(e)}')
        assert 'Invalid value' in str(e) or 'not a valid hivemind' in str(e).lower()

    # Finalize test
    log_step(7, 'Finalizing Test')
    final_state_hash: str = hivemind_state.save()
    assert final_state_hash is not None and len(final_state_hash) > 0

    end_time: float = time.time()
    duration: float = end_time - start_time

    print('Test Summary:')
    print('-' * 40)
    print(f'- Test completed successfully')
    print(f'- Duration: {duration:.2f} seconds')
    print(f'- Final state hash: {final_state_hash}')
    print(f'- Total valid options: {len(reference_hiveminds)}')
    print('=' * 60)


if __name__ == '__main__':
    test_hivemind_answer_type_constraints()
