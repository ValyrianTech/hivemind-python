# hivemind-python
A python package implementing the Hivemind Protocol, a Condorcet-style Ranked Choice Voting System that stores all data on IPFS

## Installation

You can install the package using pip:

```bash
pip install hivemind-python
```

Or install from source:

```bash
git clone https://github.com/ValyrianTech/hivemind-python.git
cd hivemind-python
pip install -e .
```

## Requirements

- Python 3.10 or higher
- ipfs-dict-chain >= 1.0.9

## Basic Usage

```python
from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState

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
```

## Features

- Condorcet-style ranked choice voting
- IPFS-based data storage
- Support for multiple question types
- Cryptographic verification of votes
- Flexible voting restrictions and weights
- Support for auto-ranking and fixed ranking

## License

This project is licensed under the MIT License - see the LICENSE file for details.
