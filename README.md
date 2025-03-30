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
state.set_issue(issue.cid)
state.add_option(timestamp, option.cid, voter_address, signature)
state.add_opinion(timestamp, opinion.cid, signature, voter_address)

# State transitions
state.finalize()  # Lock the state
state.reset()  # Clear opinions
state.exclude()  # Exclude options and recalculate

# Results with caching
results = state.results()  # Uses cache if available
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
    'min_participants': 5,
    'allowed_addresses': ['addr1', 'addr2'],
    'min_weight': 10,
    'min_contribution': 5
})
```

### Author Specification
```python
# Only this address can finalize the issue
issue.author = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
```

### Auto-Ranking with Values
```python
option1.set(75)  # Integer value
option2.set(25)  # Integer value
opinion.ranking.set_auto_high(option1.cid)  # Will rank options by proximity to 75
```

### Consensus Configuration
```python
state.set_consensus_config({
    'type': 'ranked',  # or 'single'
    'tie_breaker': 'timestamp',  # or 'random'
    'min_consensus': 0.66  # 66% agreement required
})
```

## Documentation

Full documentation is available at [https://valyriantech.github.io/hivemind-python/](https://valyriantech.github.io/hivemind-python/)

The system architecture is documented through comprehensive diagrams in the `diagrams/` directory:
- `class_diagram.md`: Core components and their relationships
- `component_diagram.md`: System-level architecture
- `state_diagram.md`: State transitions and validation
- `voting_sequence.md`: Detailed process flow

## License

This project is licensed under the MIT License - see the LICENSE file for details.
