```mermaid
classDiagram
    class IPFSDict {
        +str cid
        +load(cid: str) Dict
        +save() str
    }
    
    class IPFSDictChain {
        +str cid
        +load(cid: str) Dict
        +save() str
    }
    
    class HivemindIssue {
        +List[str] questions
        +str name
        +str description
        +List[str] tags
        +str answer_type
        +Optional[Dict[str, Union[str, int, float, list]]] constraints
        +Optional[Dict[str, Union[List[str], int]]] restrictions
        +str on_selection
        +add_question(question: str) None
        +set_constraints(constraints: Dict) None
        +set_restrictions(restrictions: Dict) None
        +valid() bool
        +info() Dict
    }
    
    class HivemindOption {
        +Union[str, int, float] value
        +str text
        +str hivemind_id
        +set_hivemind_issue(hivemind_issue_hash: str) None
        +is_valid_string_option() bool
        +is_valid_float_option() bool
        +is_valid_integer_option() bool
        +is_valid_address_option() bool
        +is_valid_hivemind_option() bool
        +info() Dict
        +valid() bool
    }
    
    class HivemindOpinion {
        +str hivemind_id
        +int question_index
        +Ranking ranking
        +set_question_index(question_index: int) None
        +get() Dict
        +info() Dict
        +valid() bool
    }
    
    class Ranking {
        +List[str] fixed
        +str auto
        +str type
        +set_fixed(ranked_choice: List[str]) None
        +set_auto_high(choice: str) None
        +set_auto_low(choice: str) None
        +get(options: List[str]) List[str]
        +valid() bool
    }
    
    class HivemindState {
        +str hivemind_id
        +List[str] options
        +List[str] opinions
        +Dict[str, str] signatures
        +Dict[str, float] participants
        +List[str] selected
        +bool final
        +add_option(timestamp: int, option_hash: str, address: str, signature: str) None
        +add_opinion(timestamp: int, opinion_hash: str, address: str, signature: str) None
        +calculate_results(question_index: int) Dict[str, float]
        +get_weight(opinionator: str) float
        +get_opinion(opinionator: str, question_index: int) Optional[Dict]
        +valid() bool
        +info() Dict
    }

    class validators {
        <<module>>
        +valid_address(address: str, testnet: bool) bool
        +valid_bech32_address(address: str, testnet: bool) bool
        +bech32_decode(bech: str) Tuple[Optional[str], Optional[list]]
    }
    
    IPFSDict <|-- HivemindIssue
    IPFSDict <|-- HivemindOption
    IPFSDict <|-- HivemindOpinion
    IPFSDictChain <|-- HivemindState
    HivemindOpinion *-- Ranking
    HivemindOption --> HivemindIssue : references
    HivemindState ..> validators : uses
    HivemindOption ..> validators : uses
    HivemindOpinion ..> validators : uses
    HivemindIssue ..> validators : uses
```