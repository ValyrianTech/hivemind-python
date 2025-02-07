graph TB
    subgraph HivemindCore[Hivemind Protocol Core]
        direction TB
        A[HivemindState] --> B[HivemindIssue]
        A --> C[HivemindOption]
        A --> D[HivemindOpinion]
        D --> E[Ranking]
        
        B --> |validates through| F[Validators]
        C --> |validates through| F
        D --> |validates through| F
        A --> |validates through| F
    end
    
    subgraph StorageLayer[Storage Layer]
        G[IPFS Dict]
        G2[IPFS Dict Chain]
        H[IPFS Network]
        G --> |stores/retrieves| H
        G2 --> |stores/retrieves| H
    end
    
    subgraph SecurityLayer[Security Layer]
        I[Cryptographic Verification]
        J[Address Validation]
        K[Timestamp Validation]
    end

    subgraph TestingLayer[Testing Framework]
        L[Pytest Fixtures]
        M[Unit Tests]
        N[Integration Tests]
        
        L --> M
        L --> N
        M --> |validates| HivemindCore
        N --> |validates| HivemindCore
    end
    
    F --> I
    F --> J
    F --> K
    
    B --> |persists| G
    C --> |persists| G
    D --> |persists| G
    A --> |persists| G2
    
    E --> |computes| R[Result Calculation]
    R --> |updates| A
    
    subgraph ValidationFlow[Validation Flow]
        V1[Input Validation]
        V2[State Validation]
        V3[Cryptographic Validation]
        V4[Business Rules]
        
        V1 --> V2
        V2 --> V3
        V3 --> V4
    end
    
    F --> ValidationFlow