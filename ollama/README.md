# Ollama

This folder contains the Docker Compose configuration for deploying [Ollama](https://ollama.ai/), an open-source tool for running large language models locally.

---

## 🚀 Deployment

This service is managed as part of the unified Traefik deployments stack.

To start:
```bash
appctl up ollama
```

Refer to the root [README.md](../README.md) for details on how environment variables are securely injected at runtime.

---

## 🔒 Security & Routing

- **Router 1 (API):** Protected by `X-Ollama-Key` header authentication.
- **Router 2 (Browser):** Protected by [Authelia](https://www.authelia.com/) (external middleware).
- HTTPS is enforced via global redirection.
