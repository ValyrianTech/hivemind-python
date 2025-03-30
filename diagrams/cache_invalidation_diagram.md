```mermaid
flowchart TD
    %% Main States
    Init[Initialize HivemindState] --> InitCache[Initialize Empty Cache]
    InitCache --> CacheState{Cache State}
    
    %% Cache State Transitions
    CacheState --> |Query Results| CheckCache{Cache Valid?}
    CheckCache --> |Yes| UseCache[Use Cached Results]
    CheckCache --> |No| CalcResults[Calculate Results]
    CalcResults --> StoreCache[Store Results in Cache]
    StoreCache --> CacheState
    
    %% Invalidation Triggers
    AddOption[Add Option to State] --> InvalidateCache[Invalidate Cache]
    AddOpinion[Add Opinion to State] --> InvalidateCache
    ExcludeOption[Exclude Option] --> InvalidateCache
    ChangeSelectionMode[Change Selection Mode] --> InvalidateCache
    
    %% Invalidation Process
    InvalidateCache --> SetNullCache[Set _results = None]
    SetNullCache --> CacheState
    
    %% Cache Implementation
    subgraph CacheImplementation[Cache Implementation in HivemindState]
        CacheVar[_results Instance Variable]
        ResultsMethod[results() Method]
        GetScoreMethod[get_score() Method]
        GetSortedMethod[get_sorted_options() Method]
        ConsensusMethod[consensus() Method]
        
        CacheVar --> ResultsMethod
        ResultsMethod --> |Cache Hit| ReturnCache[Return Cached Results]
        ResultsMethod --> |Cache Miss| ComputeResults[Compute and Cache Results]
        GetScoreMethod --> ResultsMethod
        GetSortedMethod --> ResultsMethod
        ConsensusMethod --> ResultsMethod
    end
    
    %% Invalidation Implementation
    subgraph InvalidationPoints[Invalidation Points in Code]
        AddOptionMethod[add_option() Method]
        AddOpinionMethod[add_opinion() Method]
        SetOnSelectionMethod[set_on_selection() Method]
        
        AddOptionMethod --> InvalidateCode[self._results = None]
        AddOpinionMethod --> InvalidateCode
        SetOnSelectionMethod --> InvalidateCode
    end
    
    %% Cache Benefits
    subgraph CacheBenefits[Benefits of Caching]
        ReducedCalculation[Reduced Recalculation]
        ImprovedPerformance[Improved Performance]
        ConsistentResults[Consistent Results]
    end
    
    %% Style Definitions
    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef decision fill:#ff9,stroke:#333,stroke-width:2px;
    classDef action fill:#9f9,stroke:#333,stroke-width:2px;
    classDef implementation fill:#bbf,stroke:#333,stroke-width:2px;
    classDef benefit fill:#bfb,stroke:#333,stroke-width:2px;
    
    class Init,InitCache,CalcResults,StoreCache,AddOption,AddOpinion,ExcludeOption,ChangeSelectionMode,InvalidateCache,SetNullCache process;
    class CheckCache,CacheState decision;
    class UseCache action;
    class CacheVar,ResultsMethod,GetScoreMethod,GetSortedMethod,ConsensusMethod,AddOptionMethod,AddOpinionMethod,SetOnSelectionMethod,InvalidateCode implementation;
    class ReducedCalculation,ImprovedPerformance,ConsistentResults benefit;
```
