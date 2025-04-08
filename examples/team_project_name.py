#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Team Project Name Selection Example

This example demonstrates using the Hivemind Protocol to select a project name
through a decentralized decision-making process. It uses string answer type
with constraints for project name suggestions.

The example shows:
1. Creating an issue with string answer type and constraints
2. Adding options (project name suggestions)
3. Collecting opinions from participants
4. Calculating and displaying results
"""

import time
from typing import Dict, List
from datetime import datetime

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState
from hivemind.utils import generate_bitcoin_keypair, sign_message


def log_step(step_num: int, description: str) -> None:
    """Print a formatted step header with timestamp.
    
    :param step_num: Step number in the workflow
    :type step_num: int
    :param description: Description of the step
    :type description: str
    :return: None
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] Step {step_num}: {description}')
    print('=' * 60)


def log_substep(description: str) -> None:
    """Print a formatted substep header.
    
    :param description: Description of the substep
    :type description: str
    :return: None
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'\n[{timestamp}] {description}')
    print('-' * 40)


def main() -> None:
    """Run the Team Project Name selection example."""
    start_time = time.time()
    print('\nStarting Team Project Name Selection Example')
    print('=' * 60)
    print(f'Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Step 1: Create the issue
    log_step(1, 'Creating Project Name Selection Issue')

    issue = HivemindIssue()
    issue.name = "Team Project Name Selection"
    issue.description = "We need to select a name for our new decentralized application project"
    issue.tags = ["project", "naming", "branding", "decision"]
    issue.answer_type = "String"
    
    # Add questions
    issue.add_question("What should we name our new decentralized application project?")
    issue.add_question("Which name best represents our project's core values?")
    
    # Set constraints for string answers
    issue.set_constraints({
        "min_length": 3,
        "max_length": 30,
        "regex": "^[a-zA-Z0-9_-]+$"  # Only alphanumeric, underscore, and hyphen
    })
    
    # Save the issue to IPFS
    issue_cid = issue.save()
    
    print(f"Issue created with CID: {issue_cid}")
    print(f"Name: {issue.name}")
    print(f"Description: {issue.description}")
    print(f"Tags: {issue.tags}")
    print(f"Answer Type: {issue.answer_type}")
    print(f"Constraints: {issue.constraints}")
    print(f"Questions:")
    for i, q in enumerate(issue.questions):
        print(f"  {i+1}. {q}")

    # Step 2: Create the state
    log_step(2, 'Initializing Hivemind State')
    
    state = HivemindState()
    state.set_hivemind_issue(issue_cid=issue_cid)
    state_cid = state.save()
    
    print(f"Initial state created with CID: {state_cid}")

    # Step 3: Generate participant keys
    log_step(3, 'Generating Participant Keys')
    
    # Generate keys for 5 team members
    participants = [
        ("Alice", generate_bitcoin_keypair()),
        ("Bob", generate_bitcoin_keypair()),
        ("Charlie", generate_bitcoin_keypair()),
        ("Diana", generate_bitcoin_keypair()),
        ("Ethan", generate_bitcoin_keypair())
    ]
    
    for name, (key, address) in participants:
        print(f"Generated key for {name}: {address}")

    # Step 4: Add project name options
    log_step(4, 'Adding Project Name Options')
    
    # Project name suggestions
    name_options = [
        {"value": "BlockVote", "text": "BlockVote: A voting system on the blockchain"},
        {"value": "DecentralChain", "text": "DecentralChain: Emphasizes the decentralized nature"},
        {"value": "CryptoConsensus", "text": "CryptoConsensus: Focuses on cryptographic consensus"},
        {"value": "VoteBlocks", "text": "VoteBlocks: Simple and direct name"},
        {"value": "ChainDecision", "text": "ChainDecision: Highlights decision-making on chain"},
        {"value": "ConsenSys", "text": "ConsenSys: Emphasizes consensus building"},
        {"value": "VoteChain", "text": "VoteChain: Combines voting and blockchain"}
    ]
    
    option_cids = {}
    
    # Use Alice as the option proposer
    proposer_name = "Alice"
    proposer_key, proposer_address = participants[0][1]
    
    print(f"Using {proposer_name} ({proposer_address}) as the proposer")
    
    for option_data in name_options:
        option = HivemindOption()
        option.set_issue(hivemind_issue_cid=issue_cid)
        option.set(option_data["value"])
        option.text = option_data["text"]
        option_cid = option.save()
        option_cids[option_data["value"]] = option_cid
        
        # Sign and add the option
        timestamp = int(time.time())
        message = f"{timestamp}{option_cid}"
        signature = sign_message(message, proposer_key)
        
        state.add_option(
            timestamp=timestamp,
            option_hash=option_cid,
            address=proposer_address,
            signature=signature
        )
        
        print(f"Added option: {option_data['value']} - {option_data['text']}")
        print(f"  CID: {option_cid}")
    
    # Save the updated state
    state_cid = state.save()
    print(f"Updated state CID: {state_cid}")
    print(f"Total options: {len(state.option_cids)}")

    # Step 5: Collect opinions
    log_step(5, 'Collecting Participant Opinions')
    
    # Define each participant's preferences for each question
    preferences = {
        # Question 0: What should we name our new decentralized application project?
        0: {
            "Alice": ["VoteChain", "BlockVote", "DecentralChain", "CryptoConsensus", "ChainDecision", "ConsenSys", "VoteBlocks"],
            "Bob": ["BlockVote", "VoteChain", "ConsenSys", "CryptoConsensus", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Charlie": ["CryptoConsensus", "ConsenSys", "VoteChain", "BlockVote", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Diana": ["ChainDecision", "VoteChain", "BlockVote", "ConsenSys", "CryptoConsensus", "DecentralChain", "VoteBlocks"],
            "Ethan": ["ConsenSys", "BlockVote", "VoteChain", "ChainDecision", "CryptoConsensus", "DecentralChain", "VoteBlocks"]
        },
        # Question 1: Which name best represents our project's core values?
        1: {
            "Alice": ["VoteChain", "CryptoConsensus", "BlockVote", "ConsenSys", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Bob": ["CryptoConsensus", "BlockVote", "ConsenSys", "VoteChain", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Charlie": ["ConsenSys", "CryptoConsensus", "VoteChain", "BlockVote", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Diana": ["BlockVote", "VoteChain", "ConsenSys", "CryptoConsensus", "ChainDecision", "DecentralChain", "VoteBlocks"],
            "Ethan": ["DecentralChain", "ConsenSys", "BlockVote", "VoteChain", "CryptoConsensus", "ChainDecision", "VoteBlocks"]
        }
    }
    
    # Process opinions for each question
    for question_index in range(len(issue.questions)):
        log_substep(f"Processing opinions for Question {question_index + 1}")
        print(f"Question: {issue.questions[question_index]}")
        
        for i, (name, (key, address)) in enumerate(participants):
            # Get this participant's ranking for this question
            ranking = preferences[question_index][name]
            
            # Convert project names to option CIDs
            ranking_cids = [option_cids[name] for name in ranking]
            
            # Create and save the opinion
            opinion = HivemindOpinion()
            opinion.hivemind_id = issue_cid
            opinion.set_question_index(question_index)
            opinion.ranking.set_fixed(ranking_cids)
            opinion_cid = opinion.save()
            
            # Sign and add the opinion
            timestamp = int(time.time())
            message = f"{timestamp}{opinion_cid}"
            signature = sign_message(message, key)
            
            state.add_opinion(
                timestamp=timestamp,
                opinion_hash=opinion_cid,
                address=address,
                signature=signature
            )
            
            print(f"Added opinion from {name} ({address})")
            print(f"  Ranking: {', '.join(ranking)}")
            print(f"  Opinion CID: {opinion_cid}")
    
    # Save the updated state
    state_cid = state.save()
    print(f"Updated state with all opinions, CID: {state_cid}")

    # Step 6: Calculate and display results
    log_step(6, 'Calculating Results')
    
    # Get cached results for all questions
    all_results = state.results()
    
    for question_index in range(len(issue.questions)):
        log_substep(f"Results for Question {question_index + 1}")
        print(f"Question: {issue.questions[question_index]}")
        
        # Get options sorted by score
        sorted_options = state.get_sorted_options(question_index=question_index)
        
        print("\nRanked Results:")
        for i, option in enumerate(sorted_options, 1):
            score = state.get_score(option.cid(), question_index)
            print(f"{i}. {option.value} - {option.text}")
            print(f"   Score: {score}")
        
        # Get the consensus (winning option)
        consensus = state.consensus(question_index=question_index)
        print(f"\nConsensus winner: {consensus}")
        
        # Calculate participant contributions
        contributions = state.contributions(all_results[question_index], question_index)
        
        print("\nParticipant Contributions:")
        for i, (name, (_, address)) in enumerate(participants):
            contribution = contributions.get(address, 0)
            print(f"{name} ({address}): {contribution}")
    
    # End of example
    end_time = time.time()
    duration = end_time - start_time
    
    print("\nExample Summary:")
    print("-" * 40)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Final state CID: {state_cid}")
    print(f"Questions processed: {len(issue.questions)}")
    print(f"Total options: {len(name_options)}")
    print(f"Total participants: {len(participants)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
