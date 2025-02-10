# Hivemind Protocol

A decentralized decision-making protocol implementing Condorcet-style Ranked Choice Voting with IPFS-based data storage and Bitcoin-signed message verification.

[![Tests](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/tests.yml)
[![Documentation](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml/badge.svg)](https://github.com/ValyrianTech/hivemind-python/actions/workflows/documentation.yml)

## What is the Hivemind Protocol?

The Hivemind Protocol is a revolutionary approach to decentralized decision-making that combines:
- Condorcet-style ranked choice voting
- Immutable IPFS-based data storage
- Cryptographic verification using Bitcoin signed messages
- Flexible voting mechanisms and constraints

### Key Features

1. **Decentralized & Transparent**
   - All voting data stored on IPFS
   - Complete audit trail of decisions
   - No central authority or server
   - Cryptographically verifiable results

2. **Advanced Voting Mechanisms**
   - Condorcet-style ranked choice voting
   - Multiple ranking strategies (fixed, auto-high, auto-low)
   - Support for various answer types (String, Integer, Float)
   - Weighted voting capabilities
   - Custom voting restrictions and rules

3. **Secure & Verifiable**
   - Bitcoin-style message signing for vote verification
   - Immutable voting history
   - Cryptographic proof of participation
   - Tamper-evident design

## How It Works

### 1. Issue Creation
An issue represents a decision to be made. It can contain:
- Multiple questions
- Answer type constraints (String/Integer/Float)
- Participation rules
- Custom validation rules

```python
issue = HivemindIssue()
issue.name = "Protocol Upgrade"
issue.add_question("Should we implement EIP-1559?")
issue.answer_type = "String"
```

### 2. Option Submission
Participants can submit options as potential answers:
- Each option is stored on IPFS
- Options are validated against issue constraints
- Options require cryptographic signatures
- Options can be added dynamically

```python
option = HivemindOption()
option.set_hivemind_issue(issue.cid)
option.set("Yes, implement EIP-1559")
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
- Option tracking
- Opinion collection
- Signature verification
- Result calculation
- State transitions

```python
state = HivemindState()
state.set_hivemind_issue(issue.cid)
state.add_option(timestamp, option.cid, voter_address, signature)
state.add_opinion(timestamp, opinion.cid, signature, voter_address)
```

### 5. Result Calculation
Results are calculated using Condorcet method:
1. Pairwise comparison of all options
2. Preference matrix creation
3. Winner determination
4. Tie resolution

```python
results = state.calculate_results()
winner = state.consensus()
```

## Examples

Detailed examples can be found in the [`examples/`](examples/) directory:

1. [`basic_voting.py`](examples/basic_voting.py) - Simple voting example
2. [`advanced_features.py`](examples/advanced_features.py) - Advanced protocol features
3. [`protocol_upgrade.py`](examples/protocol_upgrade.py) - Governance decision example

Each example is thoroughly documented and can be run independently. See the [examples README](examples/README.md) for more details.

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
- ipfs-dict-chain >= 1.0.9
- A running IPFS node (see [IPFS Installation Guide](https://docs.ipfs.tech/install/))
  - The IPFS daemon must be running and accessible via the default API endpoint
  - Default endpoint: http://127.0.0.1:5001

## Advanced Features

### Custom Constraints
```python
issue.set_constraints({
    'min_value': 0,
    'max_value': 100,
    'specs': {'type': 'Integer'}
})
```

### Voting Restrictions
```python
issue.set_restrictions({
    'min_participants': 5,
    'allowed_addresses': ['addr1', 'addr2'],
    'min_weight': 10
})
```

### Auto-Ranking with Values
```python
option1.set(75)  # Integer value
option2.set(25)  # Integer value
opinion.ranking.set_auto_high(option1.cid)  # Will rank options by proximity to 75
```

## Use Cases

1. **Governance Decisions**
   - Protocol upgrades
   - Parameter adjustments
   - Resource allocation

2. **Community Polling**
   - Feature prioritization
   - Community preferences
   - Strategic decisions

3. **Multi-stakeholder Decisions**
   - Investment decisions
   - Project prioritization
   - Resource allocation

## Documentation

Full documentation is available at [https://valyriantech.github.io/hivemind-python/](https://valyriantech.github.io/hivemind-python/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
