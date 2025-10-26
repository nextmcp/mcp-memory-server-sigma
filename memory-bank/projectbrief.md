# Project Brief: MCP Memory Server

## Project Overview
An enterprise-ready Model Context Protocol (MCP) server that provides persistent memory management with semantic search capabilities. The system enables AI assistants and applications to store, retrieve, and manage contextual memories across sessions.

## Core Purpose
Build and deploy a production-grade memory management service that:
- Provides MCP-compliant tools for memory operations (add, search, list, delete)
- Maintains persistent storage with semantic search capabilities
- Supports multi-user, multi-application architecture with access controls
- Deploys to AWS ECS with full CI/CD automation
- Integrates with external systems (Slack, etc.)

## Key Requirements

### Functional Requirements
1. **Memory Operations**: Add, search (semantic/text), list, and delete memories
2. **Multi-tenancy**: Support multiple users and applications with isolation
3. **Semantic Search**: Vector-based search using embeddings (Qdrant)
4. **Access Control**: Granular permissions for memory access across apps
5. **Audit Logging**: Track all memory access and state changes
6. **Categorization**: Automatic categorization of memories using AI
7. **External Integrations**: Slack channel history loading and search
8. **State Management**: Memory lifecycle (active, paused, archived, deleted)

### Technical Requirements
1. **API Framework**: FastAPI with async support
2. **Databases**: 
   - PostgreSQL for persistent relational data
   - Qdrant for vector embeddings and semantic search
3. **MCP Implementation**: Server-Side Events (SSE) transport
4. **Infrastructure**: AWS ECS deployment with CloudFormation
5. **Containerization**: Docker with multi-stage builds
6. **Migrations**: Alembic for database schema management
7. **CI/CD**: GitHub Actions for automated testing and deployment

### Non-Functional Requirements
1. **Reliability**: Graceful degradation when vector store unavailable
2. **Scalability**: Auto-scaling ECS services
3. **Security**: IAM roles, secrets management, HTTPS/TLS
4. **Observability**: JSON structured logging, CloudWatch integration
5. **Development Experience**: Local Docker Compose environment

## Success Criteria
- Deploy successfully to AWS ECS across environments (dev/staging/prod)
- Handle memory operations with < 2s response time
- Support concurrent multi-user access
- Maintain data consistency between PostgreSQL and Qdrant
- Provide 99%+ uptime for production deployments

## Current Scope
✅ Core memory operations via MCP
✅ PostgreSQL + Qdrant dual storage
✅ AWS ECS deployment infrastructure
✅ Slack integration (loading channels, searching)
✅ User and app management
✅ Access control system
✅ Automatic categorization
✅ Sync mechanism (PostgreSQL → Qdrant)

## Out of Scope (Currently)
- Real-time collaboration features
- Memory versioning/history beyond state tracking
- Advanced analytics dashboard
- Multi-region deployment
- Custom embedding models beyond OpenAI
