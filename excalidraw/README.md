# Excalidraw

Excalidraw is a virtual whiteboard for sketching hand-drawn like diagrams. This folder contains the Docker Compose configuration to run Excalidraw and its backend (room) service, integrated with Traefik for reverse proxying and SSL.

---

## 🚀 Deployment

This service is managed as part of the unified Traefik deployments stack.

To start:
```bash
appctl up excalidraw
```

Refer to the root [README.md](../README.md) for details on how environment variables are securely injected at runtime.

---

## 📦 Services

- **excalidraw**: The main web application.
- **excalidraw-room**: The backend service for real-time collaboration.
