#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic example of creating and managing a simple voting issue.
"""

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState

def run_basic_vote(voter_address: str, signature: str, timestamp: int):
    """
    Run a basic voting example for choosing a favorite color.
    
    Args:
        voter_address: The address of the voter
        signature: The signature for verification
        timestamp: Current timestamp for the vote
    """
    # Create a new voting issue
    issue = HivemindIssue()
    issue.name = "Best Color"
    issue.add_question("What is the best color?")
    issue.answer_type = "String"

    # Create the hivemind state
    state = HivemindState()
    state.set_hivemind_issue(issue.cid)

    # Add options
    blue = HivemindOption()
    blue.set_hivemind_issue(issue.cid)
    blue.set("Blue")
    state.add_option(timestamp, blue.cid, voter_address, signature)

    red = HivemindOption()
    red.set_hivemind_issue(issue.cid)
    red.set("Red")
    state.add_option(timestamp, red.cid, voter_address, signature)

    # Add an opinion
    opinion = HivemindOpinion()
    opinion.ranking.set_fixed([blue.cid, red.cid])  # Prefers blue over red
    state.add_opinion(timestamp, opinion.cid, signature, voter_address)

    # Get results
    results = state.calculate_results()
    winner = state.consensus()
    
    return results, winner

if __name__ == "__main__":
    # Example usage (replace with actual values)
    VOTER_ADDRESS = "your_address_here"
    SIGNATURE = "your_signature_here"
    TIMESTAMP = 1234567890
    
    results, winner = run_basic_vote(VOTER_ADDRESS, SIGNATURE, TIMESTAMP)
    print(f"Voting Results: {results}")
    print(f"Winner: {winner}")
