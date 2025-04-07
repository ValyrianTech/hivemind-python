# Hivemind Protocol

A decentralized decision-making protocol implementing Condorcet-style Ranked Choice Voting with IPFS-based data storage and Bitcoin-signed message verification.

[![Tests](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml)
[![Documentation](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/ValyrianTech/hivemind-python)](https://codecov.io/gh/ValyrianTech/hivemind-python)
[![License](https://img.shields.io/github/license/ValyrianTech/hivemind-python)](https://github.com/ValyrianTech/hivemind-python/blob/main/LICENSE)

> **Note:** Looking for the web application implementation? Check out the [Web App README](https://github.com/ValyrianTech/hivemind-python/blob/main/hivemind/README.md) for details on the included web interface and mobile signing app.

## What is the Hivemind Protocol?

The Hivemind Protocol is a revolutionary approach to decentralized decision-making that combines:
- Condorcet-style ranked choice voting
- Immutable IPFS-based data storage
- Cryptographic verification using Bitcoin signed messages
- Flexible voting mechanisms and constraints
- Advanced consensus calculation

### Key Features

1. **Decentralized & Transparent**
   - All voting data stored on IPFS
   - Complete audit trail of decisions
   - No central authority or server
   - Cryptographically verifiable results

2. **Advanced Voting Mechanisms**
   - Condorcet-style ranked choice voting
   - Multiple ranking strategies (fixed, auto-high, auto-low)
   - Support for various answer types (Boolean, String, Integer, Float)
   - Weighted voting with contribution calculation
   - Custom voting restrictions and rules
   - Predefined options for common types

3. **Secure & Verifiable**
   - Bitcoin-style message signing for vote verification
   - Immutable voting history
   - Cryptographic proof of participation
   - Tamper-evident design
   - Comprehensive validation checks

4. **Flexible Consensus**
   - Single-winner and ranked consensus types
   - Advanced tie-breaking mechanisms
   - State management with reset and exclude options
   - Dynamic result recalculation

## System Architecture

The protocol's architecture is documented through comprehensive diagrams in the `diagrams/` directory:

1. **Class Diagram** (`class_diagram.md`): Core components and their relationships
2. **Component Diagram** (`component_diagram.md`): System-level architecture and interactions
3. **State Diagram** (`state_diagram.md`): State transitions and validation flows
4. **Voting Sequence** (`voting_sequence.md`): Detailed voting process flow
5. **Data Flow Diagram** (`data_flow_diagram.md`): How data moves through the system
6. **Cache Invalidation Diagram** (`cache_invalidation_diagram.md`): Result caching mechanism
7. **Selection Mode Diagram** (`selection_mode_diagram.md`): Different selection behaviors
8. **Verification Process Diagram** (`verification_process_diagram.md`): Message signing and verification
9. **Ranking Algorithm Diagram** (`ranking_algorithm_diagram.md`): Ranking strategies visualization

## Installation

```bash
pip install hivemind-python
```
## How It Works

### 1. Issue Creation
An issue represents a decision to be made. It can contain:
- Multiple questions with indices
- Answer type constraints (Boolean/String/Integer/Float)
- Participation rules
- Custom validation rules
- Predefined options for common types

### 2. Option Submission
Options can be predefined or submitted dynamically:
- Automatic options for Boolean types (Yes/No)
- Predefined choices for common scenarios
- Dynamic option submission with validation
- Complex type validation support
- Signature and timestamp verification

### 3. Opinion Formation
Participants express preferences through three ranking methods:

1. **Fixed Ranking**
   ```python
   opinion = HivemindOpinion()
   opinion.ranking.set_fixed([option1.cid, option2.cid])  # Explicit order
   ```

2. **Auto-High Ranking**
   ```python
   opinion.ranking.set_auto_high(preferred_option.cid)  # Higher values preferred
   ```

3. **Auto-Low Ranking**
   ```python
   opinion.ranking.set_auto_low(preferred_option.cid)  # Lower values preferred
   ```

### 4. State Management
The protocol maintains state through:
- IPFS connectivity management
- Option and opinion tracking
- Comprehensive validation
- Contribution calculation
- Multiple state transitions
- Result caching for performance optimization
- Author verification for finalization

## Dependencies

### IPFSDictChain

This package relies on [IPFSDictChain](https://github.com/ValyrianTech/ipfs_dict_chain), a library that provides a dictionary-like data structure with IPFS-based storage and blockchain-like chaining capabilities. IPFSDictChain enables the Hivemind Protocol to store and retrieve data in a decentralized manner while maintaining data integrity and immutability.

## HivemindIssue Class

The `HivemindIssue` class is the foundation of the Hivemind Protocol, representing a voting issue to be decided by participants.

### Class Structure

```python
from hivemind import HivemindIssue

# Create a new issue
issue = HivemindIssue()
issue.name = "Team Laptop Selection"
issue.description = "We need to select a new standard laptop model for the development team"
issue.tags = ["equipment", "technology", "procurement"]
issue.answer_type = "String"
```

### Key Properties

- **questions**: List of questions for ranking the same set of options by different criteria
  ```python
  # All questions will use the same set of options (laptop models)
  # but participants can rank them differently for each question
  issue.add_question("Which laptop model is best overall?")
  issue.add_question("Which laptop model is most reliable based on past experience?")
  issue.add_question("Which laptop model has the best support options?")
  ```

- **answer_type**: Defines the expected answer format
  ```python
  # Supported types: String, Integer, Float, Bool, Hivemind, File, Complex, Address
  issue.answer_type = "String"  # For laptop model names
  ```

- **constraints**: Validation rules for answers
  ```python
  # For numeric answers
  issue.set_constraints({
      "min_value": 0,
      "max_value": 100
  })
  
  # For boolean answers
  issue.set_constraints({
      "true_value": "Approve",
      "false_value": "Reject"
  })
  
  # For string answers
  issue.set_constraints({
      "min_length": 5,
      "max_length": 500,
      "regex": "^[a-zA-Z0-9 ]+$"
  })
  
  # For predefined choices
  issue.set_constraints({
      "choices": ["Option A", "Option B", "Option C"]
  })
  ```

- **restrictions**: Controls who can participate
  ```python
  issue.set_restrictions({
      # Only these addresses can vote
      "addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "..."],
      
      # Limit options per address
      "options_per_address": 3
  })
  ```

  **Weighted Voting**: You can assign different weights to addresses using the `@weight` syntax:
  ```python
  issue.set_restrictions({
      # Addresses with weights (format: "address@weight")
      "addresses": [
          "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa@2.5",  # This address has 2.5x voting power
          "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",      # Default weight of 1.0
          "1MzQwSR3s7RqxJPuQzF7Y4iybjhHNV4bZq@0.5"   # This address has 0.5x voting power
      ],
      "options_per_address": 3
  })
  ```
  Weights affect the influence of each participant's opinion in the final consensus calculation. Higher weights give more influence to certain participants, which can be useful for stakeholder voting or expertise-weighted decisions.

- **on_selection**: Action when consensus is reached
  ```python
  # Valid values: None, Finalize, Exclude, Reset
  issue.on_selection = "Finalize"  # Locks the issue after consensus
  ```

### Validation System

The `HivemindIssue` class enforces strict validation rules:

- **Name**: Non-empty string ≤ 50 characters
- **Description**: String ≤ 5000 characters
- **Tags**: Unique strings without spaces, each ≤ 20 characters
- **Questions**: Non-empty, unique strings, each ≤ 255 characters
- **Answer Type**: Must be one of the allowed types
- **Constraints**: Must match the answer type
- **Restrictions**: Must follow the defined format

### IPFS Integration

All issue data is stored on IPFS:

```python
# Save to IPFS
issue_cid = issue.save()  # Returns the IPFS CID

# Load from IPFS
loaded_issue = HivemindIssue(cid=issue_cid)
```

### Participant Identification

```python
# Generate an identification CID for a participant
identification_cid = issue.get_identification_cid("Participant Name")
```

## HivemindOption Class

The `HivemindOption` class represents a voting option in the Hivemind protocol, allowing participants to create and validate options for different answer types.

### Class Structure

```python
from hivemind import HivemindOption, HivemindIssue

# Create a new option
option = HivemindOption()

# Associate with an issue
option.set_issue(issue_cid)

# Set the option value (type depends on issue.answer_type)
option.set("Dell XPS 13")  # For String answer type
option.text = "Latest model with 32GB RAM"  # Optional descriptive text
```

### Key Properties

- **value**: The actual value of the option (type varies based on answer_type)
  ```python
  # Different value types based on answer_type
  option.set("Dell XPS 13")  # String
  option.set(True)           # Bool
  option.set(1500)           # Integer
  option.set(4.5)            # Float
  option.set({"cpu": "i7", "ram": 32, "ssd": 1})  # Complex
  ```

- **text**: Additional descriptive text for the option
  ```python
  option.text = "Detailed description of this option"
  ```

- **hivemind_id**: The IPFS hash of the associated hivemind issue
  ```python
  option.hivemind_id = issue.cid()
  ```

### Type-Specific Validation

The class validates options based on the issue's answer_type and constraints:

1. **String Validation**
   ```python
   # Validates against min_length, max_length, and regex constraints
   issue.set_constraints({"min_length": 5, "max_length": 100})
   option.set("Valid string value")  # Will be validated
   ```

2. **Boolean Validation**
   ```python
   # Validates boolean values and ensures text matches constraints
   issue.set_constraints({"true_value": "Yes", "false_value": "No"})
   option.set(True)
   option.text = "Yes"  # Must match the true_value constraint
   ```

3. **Numeric Validation**
   ```python
   # Validates against min_value and max_value constraints
   issue.set_constraints({"min_value": 0, "max_value": 100})
   option.set(75)  # Will be validated
   
   # Float validation also checks decimals
   issue.set_constraints({"decimals": 2})
   option.set(75.25)  # Valid: has 2 decimal places
   ```

4. **Complex Validation**
   ```python
   # Validates complex objects against specs
   issue.set_constraints({
       "specs": {
           "cpu": "String",
           "ram": "Integer",
           "ssd": "Integer"
       }
   })
   option.set({
       "cpu": "i7",
       "ram": 32,
       "ssd": 1
   })  # Will validate all fields against their types
   ```

5. **File Validation**
   ```python
   # Validates IPFS hashes for file options
   option.set("QmZ9nfyBfBJMZVqQPiTtEGcBXHAKZ4qMtQ5vwNJNrxQZBb")
   ```

6. **Address Validation**
   ```python
   # Validates Bitcoin addresses
   option.set("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
   ```

### IPFS Integration

Options are stored on IPFS for immutability and decentralization:

```python
# Save to IPFS
option_cid = option.save()  # Returns the IPFS CID

# Load from IPFS
loaded_option = HivemindOption(cid=option_cid)
```

### Utility Methods

```python
# Get information about the option
info_str = option.info()

# Get the answer type
answer_type = option.get_answer_type()

# Get the CID
cid = option.cid()
```

## HivemindOpinion and Ranking Classes

The `HivemindOpinion` and `Ranking` classes work together to represent a voter's preferences in the Hivemind protocol, providing flexible ways to express opinions on options.

### HivemindOpinion Class

```python
from hivemind import HivemindOpinion

# Create a new opinion
opinion = HivemindOpinion()
opinion.hivemind_id = issue_cid
opinion.question_index = 0  # First question in the issue
```

#### Key Properties

- **hivemind_id**: The IPFS hash of the associated hivemind issue
  ```python
  opinion.hivemind_id = issue.cid()
  ```

- **question_index**: The index of the question this opinion is for
  ```python
  # For multi-question issues, specify which question this opinion addresses
  opinion.set_question_index(2)  # Third question (zero-indexed)
  ```

- **ranking**: The ranking of options for this opinion
  ```python
  # The ranking object handles the preference ordering
  # (See Ranking class below for details)
  opinion.ranking.set_fixed(["option1_cid", "option2_cid", "option3_cid"])
  ```

#### IPFS Integration

```python
# Save to IPFS
opinion_cid = opinion.save()  # Returns the IPFS CID

# Load from IPFS
loaded_opinion = HivemindOpinion(cid=opinion_cid)
```

#### Utility Methods

```python
# Get a JSON-serializable representation
opinion_dict = opinion.to_dict()

# Get formatted information
info_str = opinion.info()
```

### Ranking Class

The `Ranking` class provides three different ways to express preferences:

#### 1. Fixed Ranking

Explicitly specifies the order of preference for options:

```python
# Create an opinion with fixed ranking
opinion = HivemindOpinion()
opinion.ranking.set_fixed([
    "QmOption1Cid",  # First choice
    "QmOption2Cid",  # Second choice
    "QmOption3Cid"   # Third choice
])
```

#### 2. Auto-High Ranking

Automatically ranks options based on proximity to a preferred value, with higher values preferred in case of ties:

```python
# For laptop selection with numeric performance scores
# Assuming options have numeric values (e.g., benchmark scores)
opinion = HivemindOpinion()
opinion.ranking.set_auto_high("QmPreferredOptionCid")

# When get() is called with a list of options, they will be ranked by:
# 1. Proximity to the preferred option's value
# 2. Higher values preferred in case of equal distance
ranked_options = opinion.ranking.get(available_options)
```

#### 3. Auto-Low Ranking

Similar to auto-high, but prefers lower values in case of ties:

```python
# For laptop selection with price values
# Assuming options have numeric values (e.g., prices)
opinion = HivemindOpinion()
opinion.ranking.set_auto_low("QmPreferredOptionCid")

# When get() is called with a list of options, they will be ranked by:
# 1. Proximity to the preferred option's value
# 2. Lower values preferred in case of equal distance
ranked_options = opinion.ranking.get(available_options)
```

#### Practical Example

```python
from hivemind import HivemindIssue, HivemindOption, HivemindOpinion

# Create an issue for laptop selection
issue = HivemindIssue()
issue.name = "Team Laptop Selection"
issue.add_question("Which laptop model is best overall?")
issue.add_question("Which laptop model has the best price-to-performance ratio?")
issue.answer_type = "Integer"  # For benchmark scores or prices
issue_cid = issue.save()

# Create options with benchmark scores
option1 = HivemindOption()
option1.set_issue(issue_cid)
option1.set(9500)  # High-end model benchmark score
option1.text = "Dell XPS 15"
option1_cid = option1.save()

option2 = HivemindOption()
option2.set_issue(issue_cid)
option2.set(8200)  # Mid-range model benchmark score
option2.text = "MacBook Pro 14"
option2_cid = option2.save()

option3 = HivemindOption()
option3.set_issue(issue_cid)
option3.set(7000)  # Budget model benchmark score
option3.text = "Lenovo ThinkPad T14"
option3_cid = option3.save()

# Create an opinion for the first question (best overall)
opinion1 = HivemindOpinion()
opinion1.hivemind_id = issue_cid
opinion1.question_index = 0
opinion1.ranking.set_fixed([option1_cid, option2_cid, option3_cid])
opinion1_cid = opinion1.save()

# Create an opinion for the second question (price-to-performance)
# Using auto-low to prefer options with better value
opinion2 = HivemindOpinion()
opinion2.hivemind_id = issue_cid
opinion2.question_index = 1
opinion2.ranking.set_auto_low(option3_cid)  # Prefer the ThinkPad's value
opinion2_cid = opinion2.save()
```

## HivemindState Class

The `HivemindState` class is the central component of the Hivemind Protocol, managing the entire voting process, including options, opinions, and result calculations.

### Class Structure

```python
from hivemind import HivemindState

# Create a new state
state = HivemindState()

# Associate with an issue
state.set_hivemind_issue(issue_cid)

# Add predefined options (for Bool or choices)
predefined_options = state.add_predefined_options()
```

### Key Properties

- **hivemind_id**: The IPFS hash of the associated hivemind issue
  ```python
  state.hivemind_id = issue.cid()
  ```

- **option_cids**: List of option CIDs in the state
  ```python
  # Access the list of options
  for option_cid in state.option_cids:
      option = state.get_option(option_cid)
      print(option.text)
  ```

- **opinion_cids**: List of dictionaries containing opinions for each question
  ```python
  # Access opinions for a specific question
  for participant, opinion_data in state.opinion_cids[0].items():
      print(f"Participant: {participant}")
      print(f"Opinion CID: {opinion_data['opinion_cid']}")
  ```

- **selected**: List of options that have been selected
  ```python
  # Check which options have been selected
  for selected_option_cid in state.selected:
      option = state.get_option(selected_option_cid)
      print(f"Selected: {option.text}")
  ```

- **final**: Whether the hivemind is finalized
  ```python
  if state.final:
      print("This hivemind is finalized - no more changes allowed")
  ```

### Adding Options and Opinions

```python
# Add an option with signature verification
state.add_option(
    timestamp=int(time.time()),
    option_hash=option.cid(),
    address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    signature="IHh9BMpylbu1DsJiMu+dmLHzoR3HHC0/skxNW/LaJi1K3agNb7mTRTNEfXRGHcLr8V0mSGv8c3XyGWU7bCEdhEE="
)

# Add an opinion with signature verification
state.add_opinion(
    timestamp=int(time.time()),
    opinion_hash=opinion.cid(),
    address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    signature="IHh9BMpylbu1DsJiMu+dmLHzoR3HHC0/skxNW/LaJi1K3agNb7mTRTNEfXRGHcLr8V0mSGv8c3XyGWU7bCEdhEE="
)
```

### Result Calculation

The HivemindState implements the Condorcet method for calculating results:

```python
# Get cached results for all questions
all_results = state.results()

# Calculate results for a specific question
results = state.calculate_results(question_index=0)

# Get the score of a specific option
score = state.get_score(option_hash=option.cid(), question_index=0)

# Get options sorted by score
sorted_options = state.get_sorted_options(question_index=0)

# Get the consensus (winning option value)
consensus_value = state.consensus(question_index=0)

# Get all options in ranked order
ranked_values = state.ranked_consensus(question_index=0)
```

### Selection Modes

The HivemindState supports different selection behaviors based on the issue's `on_selection` property:

```python
# Select the consensus (requires author signature for issues with an author)
selected_options = state.select_consensus(
    timestamp=int(time.time()),
    address=issue.author,
    signature="IHh9BMpylbu1DsJiMu+dmLHzoR3HHC0/skxNW/LaJi1K3agNb7mTRTNEfXRGHcLr8V0mSGv8c3XyGWU7bCEdhEE="
)

# Selection modes:
# - None: No special action
# - Finalize: Locks the hivemind (state.final = True)
# - Exclude: Excludes the selected option of the first question from future results
# - Reset: Clears all opinions
```

### Participant Management

```python
# Update a participant's name
state.update_participant_name(
    timestamp=int(time.time()),
    name="Alice",
    address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    signature="IHh9BMpylbu1DsJiMu+dmLHzoR3HHC0/skxNW/LaJi1K3agNb7mTRTNEfXRGHcLr8V0mSGv8c3XyGWU7bCEdhEE=",
    message="1627184000Alice"
)

# Get the weight of a participant's opinion
weight = state.get_weight(opinionator="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# Get participant contributions to the consensus
contributions = state.contributions(results=results, question_index=0)
```

### IPFS Integration

```python
# Save state to IPFS
state_cid = state.save()

# Load state from IPFS
loaded_state = HivemindState(cid=state_cid)
```

### Practical Example

```python
from hivemind import HivemindIssue, HivemindOption, HivemindOpinion, HivemindState
import time

# Create an issue for laptop selection
issue = HivemindIssue()
issue.name = "Team Laptop Selection"
issue.add_question("Which laptop model is best overall?")
issue.add_question("Which laptop model has the best price-to-performance ratio?")
issue.answer_type = "String"
issue_cid = issue.save()

# Create a state for this issue
state = HivemindState()
state.set_hivemind_issue(issue_cid)

# Create options
option1 = HivemindOption()
option1.set_issue(issue_cid)
option1.set("Dell XPS 15")
option1.text = "High-end model with 32GB RAM"
option1_cid = option1.save()

option2 = HivemindOption()
option2.set_issue(issue_cid)
option2.set("MacBook Pro 14")
option2.text = "Mid-range model with 16GB RAM"
option2_cid = option2.save()

option3 = HivemindOption()
option3.set_issue(issue_cid)
option3.set("Lenovo ThinkPad T14")
option3.text = "Budget model with good value"
option3_cid = option3.save()

# Add options to state (in a real scenario, these would include signatures)
timestamp = int(time.time())
state.add_option(timestamp, option1_cid, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "signature")
state.add_option(timestamp, option2_cid, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "signature")
state.add_option(timestamp, option3_cid, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "signature")

# Create and add opinions (in a real scenario, these would include signatures)
opinion1 = HivemindOpinion()
opinion1.hivemind_id = issue_cid
opinion1.question_index = 0  # First question
opinion1.ranking.set_fixed([option1_cid, option2_cid, option3_cid])
opinion1_cid = opinion1.save()

opinion2 = HivemindOpinion()
opinion2.hivemind_id = issue_cid
opinion2.question_index = 1  # Second question
opinion2.ranking.set_fixed([option3_cid, option2_cid, option1_cid])  # Different ranking for price-performance
opinion2_cid = opinion2.save()

# In a real scenario, add_opinion would include address and signature
state.add_opinion(timestamp, opinion1_cid, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "signature")
state.add_opinion(timestamp, opinion2_cid, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "signature")

# Calculate results
results = state.results()
print(f"Best overall: {state.consensus(question_index=0)}")
print(f"Best price-performance: {state.consensus(question_index=1)}")

# Save the state
state_cid = state.save()
```

## Examples

Detailed examples can be found in the [`examples/`](examples/) directory:

## Requirements

- Python 3.10 or higher
- ipfs-dict-chain >= 1.1.0
- A running IPFS node (see [IPFS Installation Guide](https://docs.ipfs.tech/install/))
  - The IPFS daemon must be running and accessible via the default API endpoint
  - Default endpoint: http://127.0.0.1:5001

## Documentation

Full documentation is available at [https://valyriantech.github.io/hivemind-python/](https://valyriantech.github.io/hivemind-python/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
