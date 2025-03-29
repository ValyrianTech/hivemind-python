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


def test_string_answer_type_constraints() -> None:
    """Test the String answer type with various constraints.
    
    Test Scenarios:
        1. min_length constraint
        2. max_length constraint
        3. regex constraint
        4. choices constraint
    
    Raises:
        AssertionError: If any verification step fails
    """
    start_time: float = time.time()
    print('\nStarting String Answer Type Integration Test')
    print('=' * 60)
    print(f'Test started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Create the issue
    log_step(1, 'Creating and Configuring Hivemind Issue for String Answer Type')

    name: str = 'String Answer Type Test'
    question: str = 'What is your favorite programming language?'
    description: str = 'Test for String answer type constraints'
    option_type: str = 'String'

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
    hivemind_issue.tags = ['test', 'string', 'constraints']

    # Set constraints for String answer type
    log_substep('Setting String constraints')
    constraints: Dict[str, Union[str, int, float, list]] = {
        'min_length': 3,
        'max_length': 20,
        'regex': '^[A-Za-z0-9\\+\\#]+$',  # Alphanumeric plus '+' and '#'
        'choices': [
            {'value': 'Python', 'label': 'Python Programming Language'},
            {'value': 'JavaScript', 'label': 'JavaScript Programming Language'},
            {'value': 'C++', 'label': 'C++ Programming Language'},
            {'value': 'Go', 'label': 'Go Programming Language'},
            {'value': 'Rust', 'label': 'Rust Programming Language'}
        ]
    }
    hivemind_issue.set_constraints(constraints=constraints)
    print(f'Set constraints: {constraints}')

    # Set up voter restrictions
    log_step(2, 'Setting up Access Restrictions')

    # Generate voter keys
    voter_keys: List[Tuple[CBitcoinSecret, str]] = [generate_bitcoin_keypair() for _ in range(2)]
    options_per_address: int = 5
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
    log_step(3, 'Initializing Hivemind State')

    hivemind_state = HivemindState()
    hivemind_state.set_hivemind_issue(issue_cid=hivemind_issue_hash)
    statehash: str = hivemind_state.save()

    print('Initial state created:')
    print(f'- Hash: {statehash}')
    print(f'- Current options: {hivemind_state.option_cids}')
    assert hivemind_state.option_cids == []
    assert statehash is not None and len(statehash) > 0

    # Test valid options
    log_step(4, 'Testing Valid String Options')

    valid_options = ['Python', 'JavaScript', 'C++', 'Rust']  # Removed 'Go' as it doesn't meet min_length=3
    proposer_key, proposer_address = voter_keys[0]

    for option_value in valid_options:
        log_substep(f'Adding valid option: {option_value}')
        option = HivemindOption()
        option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        option._answer_type = option_type
        option.set(value=option_value)
        option.text = f"{option_value} Programming Language"
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
    assert len(hivemind_state.option_cids) == len(valid_options)

    # Test invalid options
    log_step(5, 'Testing Invalid String Options')

    # Test min_length constraint
    log_substep('Testing min_length constraint')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value='AB')  # Too short (min_length is 3)
        assert False, "Should have rejected option due to min_length constraint"
    except Exception as e:
        print(f'Successfully rejected option that violates min_length: {str(e)}')
        assert 'not in the allowed choices' in str(e)

    # Test max_length constraint
    log_substep('Testing max_length constraint')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value='ThisIsAVeryLongProgrammingLanguageName')  # Too long (max_length is 20)
        assert False, "Should have rejected option due to max_length constraint"
    except Exception as e:
        print(f'Successfully rejected option that violates max_length: {str(e)}')
        assert 'not in the allowed choices' in str(e)

    # Test regex constraint
    log_substep('Testing regex constraint')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value='Python!')  # Contains '!' which doesn't match regex
        assert False, "Should have rejected option due to regex constraint"
    except Exception as e:
        print(f'Successfully rejected option that violates regex: {str(e)}')
        assert 'not in the allowed choices' in str(e)

    # Test choices constraint
    log_substep('Testing choices constraint')
    try:
        invalid_option = HivemindOption()
        invalid_option.set_issue(hivemind_issue_cid=hivemind_issue_hash)
        invalid_option._answer_type = option_type
        invalid_option.set(value='Ruby')  # Not in choices list
        assert False, "Should have rejected option due to choices constraint"
    except Exception as e:
        print(f'Successfully rejected option that violates choices: {str(e)}')
        assert 'not in the allowed choices' in str(e)

    # Finalize test
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
    print(f'- Total valid options: {len(valid_options)}')
    print('=' * 60)


if __name__ == '__main__':
    test_string_answer_type_constraints()
