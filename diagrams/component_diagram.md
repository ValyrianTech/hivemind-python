graph TB
    subgraph HivemindProtocol[Hivemind Protocol]
        A[HivemindState] --> B[HivemindIssue]
        A --> C[HivemindOption]
        A --> D[HivemindOpinion]
        D --> E[Ranking]
        
        B --> F[Validators]
        C --> F
    end
    
    subgraph StorageLayer[Storage Layer]
        G[IPFS Dict Chain]
        H[IPFS Network]
        G --> H
    end
    
    subgraph SecurityLayer[Security Layer]
        I[Cryptographic Verification]
        J[Address Validation]
    end
    
    A --> G
    F --> I
    F --> J
