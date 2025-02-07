#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Examples of advanced Hivemind Protocol features including constraints,
restrictions, and auto-ranking.
"""

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState

def demonstrate_constraints():
    """Example of setting up custom constraints on a voting issue."""
    issue = HivemindIssue()
    issue.name = "Temperature Setting"
    issue.add_question("What should be the optimal temperature?")
    issue.answer_type = "Integer"
    
    # Set constraints for valid temperature values
    issue.set_constraints({
        'min_value': 0,
        'max_value': 100,
        'specs': {'type': 'Integer'}
    })
    
    return issue

def demonstrate_restrictions():
    """Example of setting up voting restrictions."""
    issue = HivemindIssue()
    issue.name = "Governance Proposal"
    issue.add_question("Should we implement the new governance model?")
    
    # Set restrictions on who can vote
    issue.set_restrictions({
        'min_participants': 5,
        'allowed_addresses': ['addr1', 'addr2'],
        'min_weight': 10
    })
    
    return issue

def demonstrate_auto_ranking(voter_address: str, signature: str, timestamp: int):
    """
    Example of using auto-ranking with numerical values.
    
    Args:
        voter_address: The address of the voter
        signature: The signature for verification
        timestamp: Current timestamp for the vote
    """
    # Create issue
    issue = HivemindIssue()
    issue.name = "Temperature Preference"
    issue.add_question("What is your preferred temperature?")
    issue.answer_type = "Integer"
    
    # Create state
    state = HivemindState()
    state.set_hivemind_issue(issue.cid)
    
    # Create options with numerical values
    option1 = HivemindOption()
    option1.set_hivemind_issue(issue.cid)
    option1.set(75)  # 75 degrees
    state.add_option(timestamp, option1.cid, voter_address, signature)
    
    option2 = HivemindOption()
    option2.set_hivemind_issue(issue.cid)
    option2.set(25)  # 25 degrees
    state.add_option(timestamp, option2.cid, voter_address, signature)
    
    # Create opinion using auto-ranking
    opinion = HivemindOpinion()
    # Will rank options by proximity to 75 degrees
    opinion.ranking.set_auto_high(option1.cid)
    state.add_opinion(timestamp, opinion.cid, signature, voter_address)
    
    return state.calculate_results()

if __name__ == "__main__":
    # Example usage (replace with actual values)
    VOTER_ADDRESS = "your_address_here"
    SIGNATURE = "your_signature_here"
    TIMESTAMP = 1234567890
    
    # Demonstrate constraints
    constrained_issue = demonstrate_constraints()
    print(f"Constrained Issue CID: {constrained_issue.cid}")
    
    # Demonstrate restrictions
    restricted_issue = demonstrate_restrictions()
    print(f"Restricted Issue CID: {restricted_issue.cid}")
    
    # Demonstrate auto-ranking
    results = demonstrate_auto_ranking(VOTER_ADDRESS, SIGNATURE, TIMESTAMP)
    print(f"Auto-ranking Results: {results}")
