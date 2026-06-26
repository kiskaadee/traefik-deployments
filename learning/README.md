# Learning Hub

A FastAPI-based service for managing courses and monitoring system infrastructure. Refactored into a layered architecture for maintainability and type-safety.

---

## 🌟 Features

- **Layered Architecture**: Separation of concerns between Config, Database, Models, Controllers, and Routes.
- **Turso Integration**: Support for LibSQL (Turso) cloud databases with local SQLite fallback.
- **System Monitoring**: CPU, RAM, and Disk usage statistics.
- **Docker Integration**: Monitor status of other containerized services.
- **Strict Typing**: Verified with `pyright` in strict mode.
- **UV Powered**: Managed by `uv` for fast, reproducible builds.

---

## 🛠️ Development

The project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Run tests
uv run python -m unittest discover tests

# Run type checking
uv run pyright
```

---

## 🚀 Deployment

This service is managed as part of the unified Traefik deployments stack.

To start:
```bash
appctl up learning
```

Refer to the root [README.md](../README.md) for details on how environment variables are securely injected at runtime.

---

## 📦 Volumes

- `./data`: Stores the local SQLite database if no remote URL is provided.
- `/home`: Mounted as read-only for system statistics monitoring.
