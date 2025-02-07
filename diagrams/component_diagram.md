```mermaid
graph TB
    subgraph Hivemind Protocol
        A[HivemindState] --> B[HivemindIssue]
        A --> C[HivemindOption]
        A --> D[HivemindOpinion]
        D --> E[Ranking]
        
        B --> F[Validators]
        C --> F
    end
    
    subgraph Storage Layer
        G[IPFS Dict Chain]
        H[IPFS Network]
        G --> H
    end
    
    subgraph Security Layer
        I[Cryptographic Verification]
        J[Address Validation]
    end
    
    Hivemind Protocol --> Storage Layer
    Hivemind Protocol --> Security Layer
```
