# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Docker Compose setup for MongoDB 6.0 configured as a single-node replica set, specifically designed to enable transaction support in development environments. The project provides a production-ready MongoDB deployment with authentication, health checks, and automatic replica set initialization.

## Architecture

The setup consists of two Docker services:
- **mongo**: Main MongoDB 6.0 instance configured as replica set `rs0` with authentication
- **mongo-init**: Initialization container that automatically configures the replica set after MongoDB starts

Key architectural decisions:
- Single-node replica set enables transaction support (required for multi-document ACID operations)
- Keyfile-based internal authentication for replica set communication
- Persistent data storage via Docker volumes
- Health check dependencies ensure proper startup sequence

## Environment Setup

1. **Copy environment configuration:**
   ```bash
   cp .env-example .env
   ```

2. **Deploy MongoDB:**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment:**
   ```bash
   docker-compose ps
   docker-compose logs mongo-init
   ```

## Common Commands

### Development Operations

**Start/Stop Services:**
```bash
docker-compose up -d          # Start in background
docker-compose down           # Stop and remove containers
docker-compose restart        # Restart all services
```

**View Logs:**
```bash
docker-compose logs -f        # Follow all logs
docker-compose logs mongo     # View MongoDB logs
docker-compose logs mongo-init # View initialization logs
```

**Health Checks:**
```bash
docker-compose ps                           # Check container status
docker exec mongodb mongosh --username admin --password supersecret --authenticationDatabase admin --eval "db.runCommand('ping')"
```

### Database Operations

**Connect to MongoDB:**
```bash
# Via Docker exec
docker exec -it mongodb mongosh --username admin --password supersecret --authenticationDatabase admin

# Via external mongosh (if installed)
mongosh "mongodb://admin:supersecret@localhost:27017/admin?replicaSet=rs0"
```

**Check Replica Set Status:**
```bash
docker exec mongodb mongosh -u admin -p supersecret --authenticationDatabase admin --eval "rs.status()"
```

**Test Transactions:**
```bash
docker cp test_transaction.js mongodb:/tmp/test_transaction.js
docker exec mongodb mongosh -u admin -p supersecret --authenticationDatabase admin --file /tmp/test_transaction.js
```

### Data Management

**Create Backup:**
```bash
# Create timestamped backup
DATE=$(date +"%Y%m%d_%H%M%S")
docker exec mongodb mongodump --username admin --password supersecret --authenticationDatabase admin --out /tmp/backup_$DATE
docker cp mongodb:/tmp/backup_$DATE ./backups/
docker exec mongodb rm -rf /tmp/backup_$DATE
```

**Restore from Backup:**
```bash
docker cp ./backups/backup_TIMESTAMP mongodb:/tmp/restore
docker exec mongodb mongorestore --username admin --password supersecret --authenticationDatabase admin /tmp/restore
```

**Reset Database (Development):**
```bash
docker-compose down
docker volume rm mongo-docker_mongodb_data
docker-compose up -d
```

### Troubleshooting Commands

**Container Diagnostics:**
```bash
docker stats mongodb                    # Resource usage
docker inspect mongodb                  # Container configuration
docker exec mongodb ps aux             # Running processes
```

**MongoDB Diagnostics:**
```bash
# Check MongoDB configuration
docker exec mongodb mongosh -u admin -p supersecret --authenticationDatabase admin --eval "db.runCommand({getCmdLineOpts: 1})"

# Check database connections
docker exec mongodb mongosh -u admin -p supersecret --authenticationDatabase admin --eval "db.runCommand('connPoolStats')"

# List databases and collections
docker exec mongodb mongosh -u admin -p supersecret --authenticationDatabase admin --eval "show dbs"
```

## Connection Strings

**Development (local applications):**
```
mongodb://admin:supersecret@localhost:27017/your_database?replicaSet=rs0&authSource=admin
```

**Production (secure):**
```
mongodb://admin@your-server.com:27017/your_database?replicaSet=rs0&authSource=admin&ssl=true
```

## File Structure

- `docker-compose.yml`: Service definitions for MongoDB and initialization
- `.env-example`: Template for environment variables (credentials)
- `keyfile`: Pre-generated keyfile for replica set internal authentication (400 permissions)
- `test_transaction.js`: Transaction test script demonstrating multi-document ACID operations
- `README.md`: Comprehensive documentation including production deployment guide

## Security Notes

- Default credentials are in `.env-example` - change these for any non-development use
- The `keyfile` has restrictive permissions (400) and should not be modified
- For production: use Docker secrets, configure firewall rules, enable audit logging
- Authentication is required for all database operations

## Production Deployment

The project includes comprehensive production deployment instructions in README.md covering:
- Server setup and hardening
- SSL/TLS configuration options
- Backup automation scripts
- Monitoring and health checks
- Security considerations and firewall configuration

## Transaction Support

This setup specifically enables MongoDB transactions through replica set configuration. Use the included `test_transaction.js` to verify multi-document ACID operations are working correctly.