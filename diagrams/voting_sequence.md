```mermaid
sequenceDiagram
    participant User
    participant Validators
    participant HivemindState
    participant HivemindIssue
    participant HivemindOption
    participant HivemindOpinion
    participant Ranking
    participant IPFS
    
    %% Issue Creation and Validation
    User->>HivemindIssue: Create issue
    activate HivemindIssue
    HivemindIssue->>Validators: Validate issue format
    alt Issue Valid
        Validators-->>HivemindIssue: Format valid
        HivemindIssue->>IPFS: Save issue
        IPFS-->>HivemindIssue: Return CID
        HivemindIssue-->>User: Issue created successfully
    else Issue Invalid
        Validators-->>HivemindIssue: Format invalid
        HivemindIssue-->>User: Error: Invalid issue format
    end
    deactivate HivemindIssue
    
    %% State Initialization
    User->>HivemindState: Set issue (CID)
    activate HivemindState
    HivemindState->>IPFS: Load issue
    IPFS-->>HivemindState: Return issue data
    HivemindState-->>User: State initialized
    deactivate HivemindState
    
    %% Option Creation and Validation
    User->>HivemindOption: Create option
    activate HivemindOption
    HivemindOption->>Validators: Validate option
    alt Option Valid
        Validators-->>HivemindOption: Option valid
        HivemindOption->>IPFS: Save option
        IPFS-->>HivemindOption: Return CID
        HivemindOption-->>User: Option created successfully
    else Option Invalid
        Validators-->>HivemindOption: Option invalid
        HivemindOption-->>User: Error: Invalid option
    end
    deactivate HivemindOption
    
    %% Add Option to State
    User->>HivemindState: Add option (CID)
    activate HivemindState
    HivemindState->>IPFS: Load option
    IPFS-->>HivemindState: Return option data
    HivemindState->>Validators: Validate option signature
    alt Signature Valid
        Validators-->>HivemindState: Signature valid
        HivemindState-->>User: Option added to state
    else Signature Invalid
        Validators-->>HivemindState: Signature invalid
        HivemindState-->>User: Error: Invalid signature
    end
    deactivate HivemindState
    
    %% Opinion Creation with Ranking
    User->>HivemindOpinion: Create opinion
    activate HivemindOpinion
    HivemindOpinion->>Ranking: Initialize ranking
    Ranking-->>HivemindOpinion: Ranking initialized
    HivemindOpinion->>Validators: Validate opinion
    alt Opinion Valid
        Validators-->>HivemindOpinion: Opinion valid
        HivemindOpinion->>IPFS: Save opinion
        IPFS-->>HivemindOpinion: Return CID
        HivemindOpinion-->>User: Opinion created successfully
    else Opinion Invalid
        Validators-->>HivemindOpinion: Opinion invalid
        HivemindOpinion-->>User: Error: Invalid opinion
    end
    deactivate HivemindOpinion
    
    %% Add Opinion to State
    User->>HivemindState: Add opinion (CID)
    activate HivemindState
    HivemindState->>IPFS: Load opinion
    IPFS-->>HivemindState: Return opinion data
    HivemindState->>Validators: Validate opinion signature
    alt Signature Valid
        Validators-->>HivemindState: Signature valid
        HivemindState-->>User: Opinion added to state
    else Signature Invalid
        Validators-->>HivemindState: Signature invalid
        HivemindState-->>User: Error: Invalid signature
    end
    deactivate HivemindState
    
    %% Calculate Results
    User->>HivemindState: Calculate results
    activate HivemindState
    
    %% Weight Calculation
    HivemindState->>HivemindState: Calculate voter weights
    
    %% Ranking Aggregation
    HivemindState->>Ranking: Aggregate rankings
    activate Ranking
    loop For each opinion
        Ranking->>Ranking: Process opinion ranking
        Ranking->>Ranking: Apply voter weight
    end
    
    %% Handle Ties
    alt Clear Winner
        Ranking->>Ranking: Determine winner
    else Tie Detected
        Ranking->>Ranking: Apply tie-breaking rules
    end
    Ranking-->>HivemindState: Return final ranking
    deactivate Ranking
    
    %% Finalization
    alt on_selection = Finalize
        HivemindState->>HivemindState: Set state as final
        HivemindState-->>User: Return final results
    else on_selection = Update
        HivemindState->>HivemindState: Keep state updateable
        HivemindState-->>User: Return current results
    end
    deactivate HivemindState
```
