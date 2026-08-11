# Architecture Decision Record (ADR): Security, Concurrency, and Initialization for Web Admin Panel

## Status
Approved

## Context
When running the FastAPI Web Admin Panel container alongside the Paper MC Java container, several system-level issues arose due to shared resource limits, permission boundaries, and asynchronous start sequences:

1. **Cross-Container Permission Deadlock**: The Python FastAPI container runs as `root` by default, whereas the Minecraft server container drops privileges to run as `1000:1000`. When FastAPI writes to the SQLite database, journaling files (`authme.db-journal`, `-wal`, or `-shm`) are created under `root` ownership. The Java server then crashes with a `Permission denied` error when trying to access or clear these database locks.
2. **SQLite Concurrency and Write-Locking**: Multiple processes (the Python API and the Java Minecraft process) access a single SQLite file (`authme.db`) concurrently. This can lead to database locking exceptions (`database is locked`) during write operations.
3. **Database Initialization Race Condition**: If the FastAPI container initializes faster than the Java Minecraft container (which takes up to a minute to download Paper, fetch plugins, and boot the JVM), FastAPI's `init_db()` will connect to a non-existent `authme.db` path, causing SQLite to write a blank database file. When the Java server boots later, it detects this empty database and fails or crashes due to unexpected schema states.
4. **Ephemeral Session State**: The JWT secret was dynamically generated on FastAPI startup. If the container crashed, restarted, or was redeployed, all active user sessions were invalidated, forcing administrators to sign in again.

---

## Decisions

### 1. Unified Container Privileges (Permissions)
We will run the FastAPI web application as `user: "1000:1000"` within `docker-compose.yml`.
* **Reasoning**: This binds the Python process to the same UID/GID as the Minecraft server. Any file written to the shared volume (including SQLite rollback journals) inherits `1000:1000` permissions, resolving any filesystem permission deadlocks.

### 2. SQLite Write-Ahead Logging & Busy Timeout (Concurrency)
We will configure the SQLite connection in `database.py` to enable **Write-Ahead Logging (WAL)** and set a connection busy timeout of **5.0 seconds** (`5000` ms).
* **Reasoning**: WAL mode allows concurrent readers (e.g. players logging in, dashboard list requests) while a write is occurring, and the busy timeout ensures that if the database is temporarily locked, SQLite queues the write instead of failing immediately.

### 3. Asynchronous Schema Polling & 503 Middleware (Initialization)
We will replace the synchronous startup database migration call with an asynchronous background task.
* **Database Polling**: The background loop checks if the `authme.db` file exists and queries SQLite's `sqlite_master` metadata table to ensure the `authme` table exists (which confirms AuthMe has finished setting up the schema). Only then does the web panel run its migrations for auxiliary tables (`user_roles`, `reset_requests`) and mark the database state as `DB_READY`.
* **Readiness Middleware**: Added a FastAPI middleware that intercepts all `/api/` traffic and returns a HTTP `503 Service Unavailable` error if `DB_READY` is still `False`.

### 4. Session Persistence (JWT Secret Injection)
We will inject a static `JWT_SECRET` via the `docker-compose.yml` environment block, mapped to `MINECRAFT_JWT_SECRET` and managed via `.env` or NixOS secrets.
* **Reasoning**: Preserves cryptographical token validity across container updates and restarts.

---

## Consequences
* **Permissions**: Zero file ownership conflict when containers update or write to shared volumes.
* **Parallel Performance**: Excellent multi-process read/write safety under SQLite without locking faults.
* **Resilient Startup**: The FastAPI web admin is start-order independent. It boots gracefully and awaits the Minecraft container's schema preparation before initializing itself, protecting database sanity.
