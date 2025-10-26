# Technical Context: MCP Memory Server

## Technology Stack

### Core Framework
- **FastAPI 0.115+**: Modern async web framework
  - Native async/await support
  - Automatic OpenAPI docs
  - Pydantic validation
  - CORS middleware
  - Built-in dependency injection

### Databases
- **PostgreSQL 15+**: Primary relational database
  - JSONB columns for flexible metadata
  - UUID primary keys
  - Complex indexes for performance
  - ACID compliance for data integrity
  
- **Qdrant**: Vector similarity search engine
  - OpenAI embeddings (1536 dimensions)
  - HTTP API client
  - Collection per user architecture
  - Payload filtering capabilities

### MCP Implementation
- **fastmcp**: FastMCP library for MCP server
  - Server-Side Events (SSE) transport
  - Tool registration with @mcp.tool decorator
  - Context variable support for user isolation
  - Automatic JSON response formatting

### Memory Management
- **mem0 (mem0ai)**: Memory orchestration layer
  - Vector embedding generation
  - Storage abstraction (Qdrant)
  - Memory lifecycle management
  - Configuration-based setup

### Database Migrations
- **Alembic**: SQLAlchemy migration tool
  - Version-controlled schema changes
  - Auto-generation from models
  - Rollback capability
  - Environment-specific migrations

### Background Processing
- **APScheduler**: Background job scheduler
  - Interval-based jobs (sync every 30 min)
  - In-process scheduler (BackgroundScheduler)
  - Job persistence not required (stateless)

### External Integrations
- **Slack SDK**: Slack API client
  - Channel history fetching
  - User information lookup
  - Thread conversation handling
  - Rate limiting and pagination

### AI/ML
- **OpenAI API**: Text embedding generation
  - text-embedding-3-small model (default)
  - Categorization via GPT models
  - Configurable via environment variables

## Development Environment

### Local Setup

#### Requirements
```bash
Python 3.12+
Docker & Docker Compose
PostgreSQL 15+ (via Docker)
Qdrant (via Docker)
```

#### Environment Configuration
`.env` file structure:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/openmemory

# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=sk-...

# Default User
USER_ID=default-user
DEFAULT_APP_ID=default-app

# Logging
LOG_LEVEL=INFO
```

#### Docker Compose Stack
```yaml
services:
  postgres:
    image: postgres:15
    ports: 5432:5432
    volumes: postgres_data
    
  qdrant:
    image: qdrant/qdrant:latest
    ports: 6333:6333
    volumes: qdrant_data
    
  app:
    build: .
    ports: 8000:8000
    depends_on: [postgres, qdrant]
```

### Running Locally

#### Start Services
```bash
cd docker
docker compose up
```

#### Database Migrations
```bash
cd src/openmemory
alembic upgrade head
```

#### Run Tests
```bash
pytest test/
```

#### Access Points
- API: http://localhost:8000
- OpenAPI Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- MCP SSE: http://localhost:8000/mcp/{client_name}/sse/{user_id}

## AWS Deployment Architecture

### Infrastructure Components

#### ECS Service
- **Launch Type**: EC2 (cost-optimized)
- **Networking Mode**: Bridge (dynamic port mapping)
- **Task Definition**: Container specs, environment, secrets
- **Service**: Desired count, health checks, load balancing

#### Application Load Balancer
- **Target Group**: Health checks on /health
- **Listener**: HTTPS:443 → Target Group
- **SSL/TLS**: ACM certificate
- **Health Check**: 30s interval, 5 healthy threshold

#### Networking
- **VPC**: Existing VPC with subnets
- **Security Groups**: ALB → ECS task
- **Route53**: DNS alias to ALB

#### Secrets Management
- **AWS Secrets Manager**: Store sensitive data
- **Pattern**: `{Environment}/{ServiceName}/*`
- **Auto-injection**: ECS task pulls at startup

#### Logging
- **CloudWatch Logs**: Auto-configured log group
- **Retention**: 7 days
- **Format**: JSON structured logs

### CloudFormation Parameters

#### Required Parameters
```yaml
ServiceName: my-memory-service
Environment: dev|staging|production
DesiredCount: 1  # Number of tasks
MemoryReservation: 512  # MB
CpuReservation: 256  # CPU units
```

#### Infrastructure References
```yaml
VpcId: vpc-xxxxx
SubnetIds: subnet-a,subnet-b
ECSCluster: my-cluster-name
HostedZoneId: Z1234567890ABC
CertificateArn: arn:aws:acm:...
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
Trigger: Push to dev/staging/main branches
Steps:
  1. Checkout code
  2. Configure AWS credentials (OIDC)
  3. Login to ECR
  4. Build Docker image
  5. Tag with git SHA
  6. Push to ECR
  7. Update CloudFormation stack
  8. Wait for rollout completion
```

#### Deployment Targets
- `dev` branch → dev environment
- `staging` branch → staging environment  
- `main` branch → production environment

#### Rollback Strategy
- CloudFormation rollback on failure
- ECS circuit breaker stops bad deployments
- Previous task definition retained

## Dependencies

### Python Dependencies (src/requirements.txt)

#### Core Framework
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
pydantic==2.10.4
pydantic-settings==2.6.1
```

#### Database
```
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
```

#### MCP & Memory
```
fastmcp==0.6.1
mcp==1.3.2
mem0ai==0.1.37
qdrant-client==1.12.1
```

#### AI/ML
```
openai==1.57.4
anthropic==0.42.0  # Optional
```

#### Utilities
```
apscheduler==3.10.4
fastapi-pagination==0.12.32
requests==2.32.3
```

#### Slack Integration
```
slack-sdk==3.33.5
```

### System Dependencies
- **libpq-dev**: PostgreSQL client library (for psycopg2)
- **build-essential**: C compiler (for some Python packages)

## Configuration Management

### Config File Structure
`src/openmemory/config.json` or `default_config.json`:
```json
{
  "llm": {
    "provider": "openai",
    "config": {
      "model": "gpt-4o-mini",
      "temperature": 0.1
    }
  },
  "embedder": {
    "provider": "openai",
    "config": {
      "model": "text-embedding-3-small"
    }
  },
  "vector_store": {
    "provider": "qdrant",
    "config": {
      "url": "${QDRANT_URL}",
      "embedding_model_dims": 1536
    }
  }
}
```

### Environment Variable Expansion
- `${VAR_NAME}` in config → replaced with env var value
- Allows environment-specific configuration
- Loaded via `app/config.py`

### Database Configuration
Via SQLAlchemy engine:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections
    echo=False  # Set True for SQL logging
)
```

## Tool Usage Patterns

### Database Migrations

#### Create New Migration
```bash
cd src/openmemory
alembic revision --autogenerate -m "add new column"
```

#### Review Generated Migration
Check `alembic/versions/*.py` for correctness

#### Apply Migration
```bash
alembic upgrade head
```

#### Rollback Migration
```bash
alembic downgrade -1
```

### Docker Operations

#### Build Image
```bash
docker build -f docker/Dockerfile -t memory-server .
```

#### Push to ECR
```bash
./docker/login_to_ecr.sh
docker tag memory-server:latest ${ECR_URL}:latest
docker push ${ECR_URL}:latest
```

#### Local Development
```bash
cd docker
docker compose up --build
docker compose logs -f app  # Follow logs
docker compose down  # Stop services
```

### AWS Deployment

#### Create ECR Repository
```bash
aws cloudformation create-stack \
  --stack-name memory-server-ecr \
  --template-file aws/ecr.yaml
```

#### Deploy Service
```bash
aws cloudformation create-stack \
  --stack-name memory-server-dev \
  --template-file aws/template.yaml \
  --parameters file://aws/parameters.dev.yaml \
  --capabilities CAPABILITY_IAM
```

#### Update Service
```bash
aws cloudformation update-stack \
  --stack-name memory-server-dev \
  --template-file aws/template.yaml \
  --parameters file://aws/parameters.dev.yaml \
  --capabilities CAPABILITY_IAM
```

### Testing

#### Run All Tests
```bash
pytest test/ -v
```

#### Run with Coverage
```bash
pytest test/ --cov=src --cov-report=html
```

#### Run Specific Test
```bash
pytest test/test_th_logging.py::test_function_name
```

## Technical Constraints

### Resource Limits
- **Memory**: Minimum 512MB per container
- **CPU**: Minimum 256 CPU units (0.25 vCPU)
- **Disk**: Ephemeral, no persistent volumes on ECS
- **Connections**: PostgreSQL connection pool (5 base + 10 overflow)

### API Limitations
- **OpenAI**: Rate limits on embeddings API
- **Slack**: Rate limits on API calls (tier-based)
- **Qdrant**: Memory/disk for vector storage

### Security Constraints
- **No root containers**: Run as non-root user
- **Secrets**: Never commit to git, use Secrets Manager
- **TLS**: HTTPS only, no HTTP in production
- **IAM**: Least privilege for ECS task roles

### Network Constraints
- **Outbound**: Needs internet for OpenAI, Slack APIs
- **Inbound**: Only via ALB, no direct container access
- **DNS**: Requires Route53 hosted zone

## Performance Characteristics

### Latency Targets
- Health check: < 50ms
- Memory add: < 2s (including embedding)
- Memory search: < 1s (vector search)
- Memory list: < 500ms
- Sync operation: 1-5 minutes (depends on memory count)

### Throughput
- Concurrent requests: 10-50 (depends on resources)
- Embeddings: Limited by OpenAI API rate
- Database: 100+ queries/second (typical)
- Qdrant: 1000+ vectors/second (search)

### Storage
- PostgreSQL: ~1KB per memory (average)
- Qdrant: ~6KB per vector (1536 dims * 4 bytes)
- Logs: ~1GB per day (active service)

## Monitoring & Debugging

### Logs
- **Format**: JSON structured logs
- **Location**: CloudWatch Logs (AWS) or stdout (local)
- **Library**: Custom `th_logging` framework
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Health Checks
- **Endpoint**: GET /health
- **Response**: `{"status": "healthy", "service": "openmemory"}`
- **Used by**: ALB target group, ECS service

### Metrics (Future)
- Memory operation counts
- Search latency percentiles
- Sync success/failure rates
- Database connection pool usage

### Debugging Tips
1. **Check logs**: `docker compose logs -f app`
2. **Database queries**: Set `echo=True` in SQLAlchemy engine
3. **MCP debugging**: Check SSE connection in browser DevTools
4. **Vector search issues**: Verify Qdrant collection exists
5. **Sync problems**: Check background job logs every 30 min
