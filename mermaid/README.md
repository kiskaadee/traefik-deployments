# Mermaid Live Editor

This folder contains the Docker Compose configuration for deploying the [Mermaid Live Editor](https://github.com/mermaid-js/mermaid-live-editor).

---

## 🚀 Deployment

This service is managed as part of the unified Traefik deployments stack.

To start:
```bash
appctl up mermaid
```

Refer to the root [README.md](../README.md) for details on how environment variables are securely injected at runtime.
