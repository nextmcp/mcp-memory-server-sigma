# MCP Memory Server Template

A production-ready template for building and deploying FastAPI-based MCP (Model Context Protocol) memory servers to AWS ECS. This template provides complete infrastructure as code, CI/CD pipelines, and best practices for building memory management services.

## What This Template Provides

### Core Application
- **FastAPI** web framework with async support
- **MCP Server** implementation for memory operations
- **PostgreSQL** for persistent storage
- **Qdrant** vector database for semantic search
- **Alembic** database migrations
- Custom logging framework with JSON output

### Infrastructure
- **AWS CloudFormation** templates for ECS deployment
- **Docker** containerization with multi-stage builds
- **Application Load Balancer** with SSL/TLS
- **Route53** DNS management
- **Secrets Manager** integration
- Auto-scaling ECS services

### CI/CD
- **GitHub Actions** workflows
- Automated testing
- Docker image building and pushing to ECR
- Automated stack deployments to dev/staging/production

### Development Tools
- Local development with Docker Compose
- Testing framework (pytest)
- Database migration tools
- Deployment scripts

## Getting Started

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- AWS CLI configured
- GitHub account (for CI/CD)

### Initial Setup

1. **Clone or Fork This Template**
   ```bash
   git clone <your-repo-url>
   cd mcp-memory-server-template
   ```

2. **Configure AWS Account**
   
   Update `.github/workflows/deploy-service.yaml`:
   ```yaml
   role-to-assume: arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/cicd-deployer
   ```

3. **Set Up Parameter Files**
   
   Copy example parameter files:
   ```bash
   cp aws/parameters.dev.yaml.example aws/parameters.dev.yaml
   cp aws/parameters.staging.yaml.example aws/parameters.staging.yaml
   cp aws/parameters.production.yaml.example aws/parameters.production.yaml
   ```
   
   Edit each file and customize:
   - `ServiceName`: Your service name
   - `MemoryReservation` and `CpuReservation`: Resource allocations

4. **Configure Environment Variables**
   
   Copy and customize:
   ```bash
   cp .env.example .env
   cp src/openmemory/.env.example src/openmemory/.env
   ```

5. **Install Dependencies**
   ```bash
   pip install -r src/requirements.txt
   pip install -r test/requirements.txt
   ```

### Local Development

**Run with Docker Compose:**
```bash
cd docker
docker compose up
```

The service will be available at `http://localhost:8000`

**Run Tests:**
```bash
./run_tests.sh
```

**Database Migrations:**
```bash
cd src/openmemory
alembic upgrade head
```

### Deployment to AWS

1. **Create ECR Repository**
   ```bash
   aws cloudformation create-stack \
     --stack-name your-service-ecr \
     --template-file aws/ecr.yaml \
     --parameters file://aws/parameters.ecr.yaml
   ```

2. **Deploy to Development**
   
   Push to the `dev` branch - GitHub Actions will automatically:
   - Build Docker image
   - Push to ECR
   - Deploy CloudFormation stack
   - Update ECS service

3. **Deploy to Staging/Production**
   
   Similar process with respective branches or manual triggers

## Project Structure

```
mcp-memory-server-template/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── aws/
│   ├── template.yaml       # CloudFormation template
│   ├── ecr.yaml           # ECR repository template
│   └── parameters.*.yaml   # Environment configurations
├── docker/
│   ├── Dockerfile         # Production container
│   ├── docker-compose.yaml # Local development
│   └── entrypoint.sh      # Container startup script
├── src/
│   ├── openmemory/        # Main application code
│   │   ├── app/          # FastAPI application
│   │   ├── alembic/      # Database migrations
│   │   └── main.py       # Application entry point
│   └── th_logging/        # Logging framework
├── test/                   # Test suite
├── pyproject.toml         # Python project config
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Key Features

### Memory Operations via MCP
- Add memories
- Search memories (semantic vector search)
- List memories
- Delete memories
- Access control and permissions

### Vector Search
- Qdrant integration for semantic search
- OpenAI embeddings
- Efficient bulk operations
- Automatic sync from PostgreSQL

### Database Management
- PostgreSQL for relational data
- Alembic migrations for schema changes
- User and app management
- Memory state tracking and history

### Deployment Features
- Rolling updates with zero downtime
- Automatic health checks
- Circuit breaker for failed deployments
- CloudWatch logging
- Auto-scaling support

## Configuration

### Required AWS Resources
- ECS Cluster
- VPC and Subnets
- Application Load Balancer
- Route53 Hosted Zone
- ACM Certificate
- Secrets Manager secrets

### Environment Variables
See `.env.example` for required environment variables including:
- Database connection strings
- API keys (OpenAI, Anthropic, etc.)
- Qdrant configuration
- Logging settings

### Secrets Management
Store secrets in AWS Secrets Manager following the pattern:
```
${Environment}/${ServiceName}/*
```

Example:
- `dev/my-service/database-url`
- `dev/my-service/openai-api-key`

## Customization

### Adding New Routes
Add routes in `src/openmemory/app/routers/`

### Database Schema Changes
```bash
cd src/openmemory
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Adding Dependencies
```bash
echo "package-name" >> src/requirements.in
./update_requirements_txt.sh
```

## Monitoring and Debugging

### View Logs
CloudWatch Logs are automatically configured with 7-day retention.

### Health Checks
- Health endpoint: `/health`
- Load balancer performs automatic health checks
- ECS monitors container health

### Deployment Status
Monitor GitHub Actions for deployment progress and status.

## Architecture Decisions

- **ECS on EC2**: More cost-effective than Fargate for sustained workloads
- **Bridge Networking**: Enables dynamic port mapping
- **CloudFormation**: Native AWS IaC with no external dependencies
- **Rolling Updates**: Zero-downtime deployments
- **Structured Logging**: JSON format for easy parsing

## Security

- IAM roles for ECS tasks
- Secrets stored in AWS Secrets Manager
- HTTPS/TLS via ALB
- VPC isolation
- Security groups for network access control

## Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test
pytest test/test_specific.py

# Run with coverage
pytest --cov=src
```

## Contributing

When customizing this template:
1. Update parameter files with your configurations
2. Modify CloudFormation templates as needed
3. Customize application code in `src/openmemory/app/`
4. Update this README with your specific details

## License

[Specify your license]

## Support

[Add your support information]
