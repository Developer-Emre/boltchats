# Local Development Guide — BoltChats

Quick start guide for running BoltChats on your local machine.

## Prerequisites

- **Docker** (v24+) and **Docker Compose** (v2+)
- **Make** (usually pre-installed on macOS/Linux)
- **Git**

Optional (for running services outside Docker):
- Python 3.11+
- Node.js 20+
- MongoDB 7.0+
- Redis 7.2+

---

## 🚀 Quick Start (Recommended)

### 1. Clone Repository
```bash
git clone https://github.com/Developer-Emre/boltchats.git
cd boltchats
```

### 2. Start All Services
```bash
make up
```

This will start:
- **MongoDB** (port 27017)
- **Redis** (port 6379)
- **API** (port 8000)
- **WebSocket** (port 8001)
- **Storage Worker** (background)
- **Frontend** (port 3000)

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Next.js web app |
| **API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **WebSocket** | http://localhost:8001 | WebSocket server |
| **MongoDB** | mongodb://localhost:27017 | Database |
| **Redis** | redis://localhost:6379 | Cache & Queue |

### 4. Stop Services
```bash
make down
```

---

## 📋 Makefile Commands

Run `make help` to see all available commands:

### Main Commands
```bash
make up              # Start all services (detached)
make down            # Stop all services
make logs            # Show logs from all services
make build           # Build all Docker images
make rebuild         # Rebuild and restart all services
make restart         # Restart all services
make status          # Show service status with URLs
make health          # Check health of all services
```

### Service-Specific
```bash
make up-api          # Start only API + dependencies
make up-ws           # Start only WebSocket + dependencies
make up-storage      # Start only Storage worker + dependencies
make up-web          # Start only Frontend + dependencies

make logs-api        # Show API logs
make logs-ws         # Show WebSocket logs
make logs-storage    # Show Storage worker logs
make logs-web        # Show Frontend logs
```

### Monitoring
```bash
make up-monitoring   # Start Prometheus + Grafana + Loki
make down-monitoring # Stop monitoring stack
make logs-monitoring # Show monitoring logs
```

After starting monitoring:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Loki**: http://localhost:3100

### Database
```bash
make db-shell        # Open MongoDB shell
make redis-cli       # Open Redis CLI
```

### Development
```bash
make test            # Run all tests
make lint            # Run linters on all services
```

### Cleanup
```bash
make clean           # Stop services and remove volumes (⚠️ data loss)
make prune           # Remove all unused Docker resources
```

---

## 🛠️ Development Workflow

### Option A: Docker (Recommended for Beginners)

All services run in Docker with hot-reload enabled:

```bash
# Start everything
make up

# View logs for a specific service
make logs-api

# Restart a service after config change
docker-compose restart api

# Stop everything
make down
```

### Option B: Hybrid (Docker for infra, local for services)

Run MongoDB/Redis in Docker, services locally:

```bash
# 1. Start infrastructure only
docker-compose up -d mongodb redis

# 2. Run services locally in separate terminals

# Terminal 1: API
cd services/boltchats-api
cp .env.example .env
make dev

# Terminal 2: WebSocket
cd services/boltchats-ws
cp .env.example .env
make dev

# Terminal 3: Storage Worker
cd services/boltchats-storage
cp .env.example .env
make run

# Terminal 4: Frontend
cd services/boltchats-web
npm install
npm run dev
```

---

## 🔧 Configuration

### Environment Variables

Each service has an `.env.example` file:

```bash
# Copy to .env and customize
cp services/boltchats-api/.env.example services/boltchats-api/.env
```

Key variables:
- `MONGODB_URL` — MongoDB connection string
- `REDIS_URL` — Redis connection string
- `SECRET_KEY` — JWT signing key (⚠️ change in production)
- `CORS_ORIGINS` — Allowed frontend origins

### Default Credentials (Local Dev Only)

| Service | Username | Password |
|---------|----------|----------|
| MongoDB | `root` | `rootpassword` |
| Grafana | `admin` | `admin` |

⚠️ **Never use these in production!**

---

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Tests for Specific Service
```bash
cd services/boltchats-api
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
```

### Run Linters
```bash
make lint
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "8080:8000"  # Map to 8080 instead
```

### Services Not Starting
```bash
# Check container logs
docker-compose logs api

# Check container status
make ps

# Rebuild from scratch
make rebuild
```

### Database Connection Issues
```bash
# Verify MongoDB is running
docker-compose ps mongodb

# Check MongoDB logs
docker-compose logs mongodb

# Access MongoDB shell
make db-shell
```

### Frontend Build Errors
```bash
# Clear Next.js cache
cd services/boltchats-web
rm -rf .next node_modules
npm install
```

### Volume Permissions (Linux)
```bash
# Fix volume ownership
sudo chown -R $USER:$USER .
```

---

## 📊 Monitoring & Logging

### Start Monitoring Stack
```bash
make up-monitoring
```

Access dashboards:
- **Grafana**: http://localhost:3001 (login: admin/admin)
- **Prometheus**: http://localhost:9090

### View Logs
```bash
# All services
make logs

# Specific service
make logs-api

# Follow logs with timestamps
docker-compose logs -f --timestamps api
```

---

## 🗄️ Database Management

### MongoDB Shell
```bash
make db-shell

# Inside shell:
> show dbs
> use boltchats
> db.users.find()
```

### Redis CLI
```bash
make redis-cli

# Inside CLI:
127.0.0.1:6379> KEYS *
127.0.0.1:6379> GET some_key
```

### Backup Database
```bash
# Automated backup script
./scripts/backup-mongodb.sh
```

---

## 🚢 Production Deployment

For production deployment, see:
- **Infrastructure**: `terraform/environments/prod/README.md`
- **Kubernetes**: `infrastructure/kubernetes/README.md`
- **CI/CD**: `.github/workflows/README.md`

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture Docs**: `docs/architecture/`
- **Contribution Guide**: `CONTRIBUTING.md`
- **Agent Instructions**: `.github/instructions/`

---

## 🆘 Getting Help

1. Check logs: `make logs`
2. Check health: `make health`
3. Check status: `make status`
4. Read troubleshooting section above
5. Open an issue on GitHub

---

**Happy Coding! 🎉**
