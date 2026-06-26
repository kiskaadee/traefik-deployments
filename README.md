# 🌐 Unified Traefik Deployments

This repository contains a unified, decoupled, and portable suite of self-hosted application stacks designed to run behind a **Traefik Reverse Proxy** in a containerized homelab environment.

---

## 🏗️ Architectural Concept

Unlike core infrastructure systems, these applications run independently in their own directories. They integrate with the host's edge router dynamically via a shared external Docker network (`proxy-net`) and Traefik routing labels.

### 🌟 Host-Agnostic & Portable Design
All service definitions inside this repository are **standard, vanilla Docker Compose configurations**. While configured to read credentials from the environment, they can be deployed on **any Linux distribution** running Docker. 

---

## 🔑 Environment Variable Injection

To prevent secret leakage and configuration duplication, services do not hardcode environment variables or depend on static, plaintext `.env` files in git. Instead, they expect configuration keys (e.g., `PROXY_NETWORK`, `MONGO_ROOT_PASSWORD`, `JELLYFIN_DOMAIN`) to be injected into the shell environment at runtime.

You can manage and inject these variables using several strategies depending on your host OS:

### 1. Environment Managers (e.g., Mozilla SOPS / sops-nix)
* **Our Native Setup**: On NixOS, secrets are securely managed using `sops-nix`. At boot, SOPS decrypts the keys and renders a complete `.env` template to a secure RAM-backed filesystem (`/run/secrets/rendered/traefik-deployments.env`). 
* **The CLI Wrapper**: We use the local `appctl` CLI tool to automatically source this decrypted file and export its values before running the docker compose commands.

### 2. Standard Plaintext `.env` Files (Portable Fallback)
For standard Linux environments (Ubuntu, Debian, Arch, etc.), you can create a single unified `.env` file at the root of this repository and pass it during launch:
```bash
docker compose --env-file ../.env up -d
```

---

## 🛠️ CLI Wrapper (`appctl`)

To simplify service management across the homelab, a lightweight Bash utility named `appctl` is located at the root of this repository.

### Commands
* **`appctl list` / `status`**: Lists all unified services and their active runtime states.
* **`appctl up <service>`**: Sources secrets, injects configurations, and spins up the container stack.
* **`appctl down <service>`**: Stops and cleans up the container resources.
* **`appctl restart <service>`**: Restarts the selected service.
* **`appctl logs <service>`**: Streams real-time logs from the selected service.
* **`appctl config <service>`**: Prints the active environment variables injected for a service.

---

## 📁 Repository Structure

* **`excalidraw/`**: Collaborative whiteboarding tool.
* **`jellyfin/`**: Media server for movies, shows, and music.
* **`learning/`**: Local learning hub dashboard connected to a Turso/SQLite database and docker socket proxy.
* **`mermaid/`**: Live diagramming editor.
* **`mongo-docker/`**: MongoDB instance with replica sets initialized.
* **`pgsql/`**: PostgreSQL database container.
* **`ollama/`**: Local Large Language Model API server.
* **`appctl`**: Custom Bash management CLI.
