# Hivemind Protocol

A decentralized decision-making protocol implementing Condorcet-style Ranked Choice Voting with IPFS-based data storage and Bitcoin-signed message verification.

[![Tests](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml)
[![Documentation](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/ValyrianTech/hivemind-python)](https://codecov.io/gh/ValyrianTech/hivemind-python)
[![License](https://img.shields.io/github/license/ValyrianTech/hivemind-python)](https://github.com/ValyrianTech/hivemind-python/blob/main/LICENSE)

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

## How It Works

### 1. Issue Creation
An issue represents a decision to be made. It can contain:
- Multiple questions with indices
- Answer type constraints (Boolean/String/Integer/Float)
- Participation rules
- Custom validation rules
- Predefined options for common types

```python
issue = HivemindIssue()
issue.name = "Protocol Upgrade"
issue.add_question("Should we implement EIP-1559?")
issue.answer_type = "Boolean"  # Will auto-create Yes/No options
```

### 2. Option Submission
Options can be predefined or submitted dynamically:
- Automatic options for Boolean types (Yes/No)
- Predefined choices for common scenarios
- Dynamic option submission with validation
- Complex type validation support
- Signature and timestamp verification

```python
# Dynamic option
option = HivemindOption()
option.set_issue(issue.cid)
option.set("Custom implementation approach")

# With signature
option.sign(private_key)
```

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

```python
state = HivemindState()
state.set_hivemind_issue(issue_cid=issue.cid())
state.add_option(timestamp, option.cid(), voter_address, signature)
state.add_opinion(timestamp, opinion.cid(), signature, voter_address)

# State transitions
# Finalize the state with author verification
state.select_consensus(timestamp, author_address, signature)  # on_selection = Finalize

# Results with caching
results = state.results()  # Uses cache if available
consensus = state.consensus()  # Gets highest scoring option
ranked_results = state.ranked_consensus()  # Gets all options in score order
```

### 5. Result Calculation
Results are calculated through multiple steps:
1. Weight calculation for voters
2. Contribution calculation
3. Ranking aggregation
4. Consensus determination
   - Single consensus for clear winners
   - Ranked consensus for preference order
5. Tie resolution if needed

```python
results = state.calculate_results()
consensus = state.calculate_consensus()
winner = consensus.get_winner()
```

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

## Examples

Detailed examples can be found in the [`examples/`](examples/) directory:

## Installation

```bash
pip install hivemind-python
```

## Usage

Import the package:

```python
import hivemind  # Note: Import as 'hivemind', not 'hivemind_python'

# Create a new voting issue
issue = hivemind.HivemindIssue("My voting issue")
```

## Requirements

- Python 3.10 or higher
- ipfs-dict-chain >= 1.1.0
- A running IPFS node (see [IPFS Installation Guide](https://docs.ipfs.tech/install/))
  - The IPFS daemon must be running and accessible via the default API endpoint
  - Default endpoint: http://127.0.0.1:5001

## Advanced Features

### Custom Constraints
```python
issue.set_constraints({
    'min_value': 0,
    'max_value': 100,
    'specs': {'type': 'Integer'},
    'complex_validation': {'custom_rule': 'value % 2 == 0'}  # Even numbers only
})
```

### Voting Restrictions
```python
issue.set_restrictions({
    'addresses': ['1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2'],
    'options_per_address': 5  # Maximum number of options each address can submit
})
```

### Author Specification
```python
# Only this address can finalize the issue
issue.author = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

# Later, when finalizing:
state.select_consensus(timestamp, issue.author, signature)
```

### Auto-Ranking with Values
```python
option1.set(75)  # Integer value
option2.set(25)  # Integer value
opinion.ranking.set_auto_high(option1.cid)  # Will rank options by proximity to 75
```

## Documentation

Full documentation is available at [https://valyriantech.github.io/hivemind-python/](https://valyriantech.github.io/hivemind-python/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
