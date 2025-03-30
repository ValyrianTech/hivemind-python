```mermaid
stateDiagram-v2
    [*] --> SystemInitialization
    
    state SystemInitialization {
        [*] --> CheckingIPFS
        CheckingIPFS --> IPFSReady: Connected
        CheckingIPFS --> IPFSError: Connection Failed
        IPFSError --> CheckingIPFS: Retry
        IPFSReady --> [*]
    }
    
    SystemInitialization --> IssueValidation: Create Issue
    
    state IssueValidation {
        [*] --> ValidatingIssue
        ValidatingIssue --> IssueCreated: Valid
        ValidatingIssue --> IssueError: Invalid
        
        state IssueError {
            [*] --> CheckingErrorType
            CheckingErrorType --> InvalidFormat: Format Error
            CheckingErrorType --> InvalidConstraints: Constraint Error
            CheckingErrorType --> InvalidRestrictions: Restriction Error
            CheckingErrorType --> InvalidQuestions: Questions Error
            CheckingErrorType --> InvalidAuthor: Author Error
            
            InvalidFormat --> ValidatingIssue: Fix Format
            InvalidConstraints --> ValidatingIssue: Fix Constraints
            InvalidRestrictions --> ValidatingIssue: Fix Restrictions
            InvalidQuestions --> ValidatingIssue: Fix Questions
            InvalidAuthor --> ValidatingIssue: Fix Author
        }
    }
    
    IssueCreated --> PredefinedOptionsPhase: Check Predefined Options
    
    state PredefinedOptionsPhase {
        [*] --> CheckingIssueType
        CheckingIssueType --> AddingBooleanOptions: Bool Type
        CheckingIssueType --> AddingChoiceOptions: Has Choices
        CheckingIssueType --> SkipPredefined: No Predefined
        
        AddingBooleanOptions --> OptionsPhase
        AddingChoiceOptions --> OptionsPhase
        SkipPredefined --> OptionsPhase
    }
    
    state OptionsPhase {
        [*] --> OptionsAdding
        
        state OptionsAdding {
            [*] --> ValidatingOption
            ValidatingOption --> VerifyingSignature: Option with Signature
            ValidatingOption --> SavingOption: Option without Signature
            VerifyingSignature --> SavingOption: Valid Signature
            VerifyingSignature --> SignatureError: Invalid Signature
            ValidatingOption --> OptionError: Invalid
            SavingOption --> OptionAdded: Save to IPFS
            OptionAdded --> InvalidateCache: Option Added
            InvalidateCache --> [*]
            
            state OptionError {
                [*] --> CheckingOptionError
                CheckingOptionError --> InvalidValue: Value Error
                CheckingOptionError --> InvalidType: Type Error
                CheckingOptionError --> InvalidReference: Reference Error
                CheckingOptionError --> InvalidComplex: Complex Type Error
                CheckingOptionError --> InvalidText: Text Error
                CheckingOptionError --> InvalidFile: File Error
                CheckingOptionError --> InvalidAddress: Address Error
                
                InvalidValue --> ValidatingOption: Fix Value
                InvalidType --> ValidatingOption: Fix Type
                InvalidReference --> ValidatingOption: Fix Reference
                InvalidComplex --> ValidatingOption: Fix Complex
                InvalidText --> ValidatingOption: Fix Text
                InvalidFile --> ValidatingOption: Fix File
                InvalidAddress --> ValidatingOption: Fix Address
            }
            
            state SignatureError {
                [*] --> CheckingSignatureError
                CheckingSignatureError --> InvalidAddress: Address Error
                CheckingSignatureError --> InvalidMessage: Message Error
                CheckingSignatureError --> InvalidTimestamp: Timestamp Error
                
                InvalidAddress --> VerifyingSignature: Fix Address
                InvalidMessage --> VerifyingSignature: Fix Message
                InvalidTimestamp --> VerifyingSignature: Fix Timestamp
            }
        }
        
        OptionsAdding --> [*]: Options Complete
    }
    
    OptionsPhase --> OpinionsPhase: Start Voting
    
    state OpinionsPhase {
        [*] --> OpinionsAdding
        
        state OpinionsAdding {
            [*] --> ValidatingOpinion
            ValidatingOpinion --> ProcessingRanking: Valid
            ProcessingRanking --> FixedRanking: Fixed Ranking
            ProcessingRanking --> AutoHighRanking: Auto High Ranking
            ProcessingRanking --> AutoLowRanking: Auto Low Ranking
            
            FixedRanking --> SavingOpinion
            AutoHighRanking --> SavingOpinion
            AutoLowRanking --> SavingOpinion
            
            ValidatingOpinion --> OpinionError: Invalid
            SavingOpinion --> OpinionAdded: Save to IPFS
            OpinionAdded --> InvalidateCache: Opinion Added
            InvalidateCache --> [*]
            
            state OpinionError {
                [*] --> CheckingOpinionError
                CheckingOpinionError --> InvalidRanking: Ranking Error
                CheckingOpinionError --> InvalidWeight: Weight Error
                CheckingOpinionError --> InvalidSignature: Signature Error
                CheckingOpinionError --> InvalidQuestion: Question Error
                CheckingOpinionError --> InvalidOptions: Invalid Options
                
                InvalidRanking --> ValidatingOpinion: Fix Ranking
                InvalidWeight --> ValidatingOpinion: Fix Weight
                InvalidSignature --> ValidatingOpinion: Fix Signature
                InvalidQuestion --> ValidatingOpinion: Fix Question
                InvalidOptions --> ValidatingOpinion: Fix Options
            }
        }
        
        OpinionsAdding --> [*]: Opinions Complete
    }
    
    OpinionsPhase --> ResultCalculation: Calculate Results
    
    state ResultCalculation {
        [*] --> CheckingCache
        CheckingCache --> CachedResults: Cache Valid
        CheckingCache --> WeightCalculation: Cache Invalid
        
        CachedResults --> [*]
        
        WeightCalculation --> ContributionCalculation
        ContributionCalculation --> RankingAggregation
        RankingAggregation --> ConsensusCalculation
        
        state ConsensusCalculation {
            [*] --> DeterminingType
            DeterminingType --> SingleConsensus: Single Type
            DeterminingType --> RankedConsensus: Ranked Type
            
            SingleConsensus --> WinnerDetermination
            RankedConsensus --> WinnerDetermination
        }
        
        state WinnerDetermination {
            [*] --> CheckingWinner
            CheckingWinner --> SingleWinner: Clear Winner
            CheckingWinner --> TieBreak: Tie Detected
            
            TieBreak --> SingleWinner: Tie Resolved
            TieBreak --> Deadlock: Tie Unresolvable
            
            SingleWinner --> [*]
            Deadlock --> [*]
        }
        
        WinnerDetermination --> StoreInCache: Results Calculated
        StoreInCache --> [*]
    }
    
    ResultCalculation --> FinalState: Results Ready
    
    state FinalState {
        [*] --> CheckingFinalization
        CheckingFinalization --> AuthorVerification: Author Specified
        CheckingFinalization --> NoAuthorCheck: No Author
        
        AuthorVerification --> AuthorVerified: Valid Author
        AuthorVerification --> AuthorRejected: Invalid Author
        
        AuthorVerified --> SelectionProcessing
        NoAuthorCheck --> SelectionProcessing
        
        SelectionProcessing --> Finalized: on_selection = Finalize
        SelectionProcessing --> ExcludeState: on_selection = Exclude
        SelectionProcessing --> ResetState: on_selection = Reset
        SelectionProcessing --> UpdatePending: on_selection = None
        
        ExcludeState --> InvalidateCache: Selection Changed
        InvalidateCache --> ResultCalculation: Recalculate
        
        ResetState --> OpinionsPhase: Clear Opinions
        UpdatePending --> OpinionsPhase: Allow Updates
        Finalized --> [*]
        
        AuthorRejected --> OpinionsPhase: Continue Voting
    }
    
    FinalState --> [*]: Complete
```