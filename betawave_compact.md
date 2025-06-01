```mermaid
graph TD
    subgraph "BETAWAVE"
        direction LR
        subgraph Usuarios[👤 Usuarios]
            direction TB
            U1[Registro]
            U2[Login]
            U3[Perfil]
        end
        
        subgraph Música[🎵 Música]
            direction TB
            M1[YouTube]S
            M2[Reproducir]
            M3[Favoritos]
            M4[Buscar]
        end
        
        subgraph Config[⚙️ Config]
            direction TB
            C1[Modo Oscuro]
            C2[Audio]
            C3[Preferencias]
        end
        
        subgraph Admin[🔒 Admin]
            direction TB
            A1[Usuarios]
            A2[Stats]
        end        style Usuarios fill:#FF9999,stroke:#333,stroke-width:2px,color:#000
        style Música fill:#99FF99,stroke:#333,stroke-width:2px,color:#000
        style Config fill:#9999FF,stroke:#333,stroke-width:2px,color:#000
        style Admin fill:#FFFF99,stroke:#333,stroke-width:2px,color:#000
 
    end
```
