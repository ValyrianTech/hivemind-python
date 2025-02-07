#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example of using Hivemind Protocol for governance decisions,
specifically for protocol upgrades.
"""

from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState

def create_upgrade_proposal(proposal_name: str, description: str):
    """
    Create a new protocol upgrade proposal.
    
    Args:
        proposal_name: Name of the upgrade proposal
        description: Detailed description of the upgrade
    """
    issue = HivemindIssue()
    issue.name = proposal_name
    issue.description = description
    issue.add_question("Should we implement this protocol upgrade?")
    issue.answer_type = "String"
    
    # Set minimum requirements for upgrade decision
    issue.set_restrictions({
        'min_participants': 100,  # Require at least 100 voters
        'min_weight': 1000,      # Minimum stake requirement
    })
    
    return issue

def submit_upgrade_options(state: HivemindState, 
                         voter_address: str, 
                         signature: str, 
                         timestamp: int):
    """
    Submit options for the upgrade proposal.
    
    Args:
        state: The HivemindState instance
        voter_address: Address of the voter
        signature: Signature for verification
        timestamp: Current timestamp
    """
    # Option for accepting the upgrade
    accept = HivemindOption()
    accept.set_hivemind_issue(state.hivemind_id)
    accept.set("Accept Upgrade")
    state.add_option(timestamp, accept.cid, voter_address, signature)
    
    # Option for rejecting the upgrade
    reject = HivemindOption()
    reject.set_hivemind_issue(state.hivemind_id)
    reject.set("Reject Upgrade")
    state.add_option(timestamp, reject.cid, voter_address, signature)
    
    # Option for delaying the upgrade
    delay = HivemindOption()
    delay.set_hivemind_issue(state.hivemind_id)
    delay.set("Delay for Further Review")
    state.add_option(timestamp, delay.cid, voter_address, signature)
    
    return accept, reject, delay

def submit_vote(state: HivemindState,
               ranked_options: list,
               voter_address: str,
               signature: str,
               timestamp: int):
    """
    Submit a ranked vote for the upgrade proposal.
    
    Args:
        state: The HivemindState instance
        ranked_options: List of options in order of preference
        voter_address: Address of the voter
        signature: Signature for verification
        timestamp: Current timestamp
    """
    opinion = HivemindOpinion()
    opinion.ranking.set_fixed([opt.cid for opt in ranked_options])
    state.add_opinion(timestamp, opinion.cid, signature, voter_address)

def main():
    # Example usage (replace with actual values)
    VOTER_ADDRESS = "your_address_here"
    SIGNATURE = "your_signature_here"
    TIMESTAMP = 1234567890
    
    # Create upgrade proposal
    proposal = create_upgrade_proposal(
        "EIP-1559 Implementation",
        "Implement EIP-1559 to improve gas fee mechanism"
    )
    
    # Initialize state
    state = HivemindState()
    state.set_hivemind_issue(proposal.cid)
    
    # Submit options
    accept, reject, delay = submit_upgrade_options(
        state, VOTER_ADDRESS, SIGNATURE, TIMESTAMP
    )
    
    # Submit a vote (example: prefer accept, then delay, then reject)
    submit_vote(
        state,
        [accept, delay, reject],
        VOTER_ADDRESS,
        SIGNATURE,
        TIMESTAMP
    )
    
    # Calculate results
    results = state.calculate_results()
    winner = state.consensus()
    
    print(f"Voting Results: {results}")
    print(f"Final Decision: {winner}")

if __name__ == "__main__":
    main()
