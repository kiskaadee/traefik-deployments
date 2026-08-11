# Minecraft Server

Minecraft server deployment powered by the highly configurable `itzg/minecraft-server` Docker image.

---

## 🚀 Deployment

This service is managed as part of the unified Traefik deployments stack.

To start:
```bash
./appctl up minecraft
```

Refer to the root [README.md](../README.md) for details on how environment variables are securely injected at runtime.

## ⚙️ Configuration Options

The following environment variables can be customized in your `.env` file (or injected via your environment manager):

| Variable | Description | Default |
|----------|-------------|---------|
| `MINECRAFT_CONTAINER_NAME` | The name of the Docker container | `minecraft-server` |
| `MINECRAFT_TYPE` | Server type (e.g. `VANILLA`, `PAPER`, `FORGE`, `FABRIC`) | `PAPER` |
| `MINECRAFT_VERSION` | Game version (e.g. `1.20.1`, `LATEST`) | `LATEST` |
| `MINECRAFT_MEMORY` | Memory allocation for the server (e.g. `2G`, `4G`) | `2G` |
| `MINECRAFT_PORT` | The host port to expose | `25565` |
| `MINECRAFT_DOMAIN` | Domain routing info (for documentation in `appctl status`) | `minecraft.arch-services.mywire.org` |
