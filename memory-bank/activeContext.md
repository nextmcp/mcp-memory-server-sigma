# Active Context: MCP Memory Server

## Current Work Focus

### Memory Bank Creation
Creating comprehensive documentation for the MCP Memory Server project to enable effective context retention across AI assistant sessions.

### System State
The project is in a **production-ready template** state:
- Core functionality implemented and working
- AWS deployment infrastructure complete
- Slack integration functional
- Background sync mechanism operational
- MCP tools fully implemented

## Recent Changes

### Memory Bank Establishment (Current Session)
- Created structured memory bank directory
- Documented project brief, product context, system patterns, and technical context
- Established foundation for future AI assistant interactions

## Next Steps

### Immediate Priorities
1. Complete memory bank with remaining core files (activeContext.md, progress.md)
2. Verify memory bank completeness and accuracy
3. Test memory bank by reading all files in next session

### Future Development Areas
1. **Performance Optimization**
   - Monitor and optimize vector search latency
   - Tune PostgreSQL query performance
   - Optimize sync operation batch sizes

2. **Feature Enhancement**
   - Consider memory versioning/history
   - Explore analytics dashboard
   - Evaluate additional embedding models

3. **Infrastructure Improvements**
   - Multi-region deployment planning
   - Enhanced monitoring and metrics
   - Automated testing in CI/CD

## Active Decisions and Considerations

### Architectural Decisions

#### Dual Storage Strategy
- **Decision**: Maintain both PostgreSQL (source of truth) and Qdrant (vector search)
- **Rationale**: PostgreSQL ensures data durability; Qdrant optimizes search performance
- **Trade-off**: Requires sync mechanism and handles eventual consistency
- **Status**: Working well, sync runs every 30 minutes

#### Graceful Degradation
- **Decision**: System continues functioning when Qdrant unavailable
- **Implementation**: Fallback to PostgreSQL text search (ILIKE)
- **Impact**: Reduced search quality but maintained availability
- **Status**: Tested and operational

#### Lazy Client Initialization
- **Decision**: Don't initialize mem0 client at module import time
- **Rationale**: Prevents server crash when dependencies unavailable
- **Pattern**: `get_memory_client_safe()` returns None on failure
- **Status**: Proven effective during container restarts

### Integration Patterns

#### Slack Integration
- **Approach**: Dedicated "slack-bot" user owns all Slack memories
- **Search**: No ACL filtering for Slack data (all public within workspace)
- **Loading**: Channel history loaded on demand
- **Status**: Working, needs optimization for large channels

#### MCP Context Isolation
- **Pattern**: Context variables for user_id and client_name per SSE connection
- **Security**: Prevents cross-user data leakage
- **Performance**: Minimal overhead
- **Status**: Thread-safe and reliable

## Important Patterns and Preferences

### Code Organization
1. **Router Separation**: Distinct routers for different concerns (memories, apps, stats, config, backup)
2. **Utility Modules**: Shared logic in `app/utils/` (db, memory, permissions, categorization)
3. **Model-Driven**: SQLAlchemy models define structure, Alembic manages migrations
4. **Type Safety**: Pydantic schemas for API validation and serialization

### Error Handling Philosophy
```python
# Preferred pattern: Try-except with logging, return error message
try:
    result = operation()
except Exception as e:
    logging.exception(f"Context: {e}")
    return f"Error: {e}"
```

### Database Access Pattern
```python
# Always use try-finally for session management
db = SessionLocal()
try:
    # operations
    db.commit()
finally:
    db.close()
```

### Logging Standards
- Use structured JSON logging via `th_logging`
- Include context in log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log all errors with stack traces (`logging.exception()`)

## Learnings and Project Insights

### Vector Store Recovery
**Learning**: Qdrant data can be lost on container restart (if no persistent volume)
**Solution**: Background sync rebuilds from PostgreSQL
**Insight**: PostgreSQL as source of truth enables recovery without data loss

### MCP SSE Connection Management
**Learning**: SSE connections require careful context variable handling
**Implementation**: Set context vars at connection start, reset at end
**Insight**: Context variables provide thread-safe per-request state

### Memory Access Control
**Learning**: Default behavior (same app can access) works for most cases
**Enhancement**: AccessControl table enables explicit allow/deny rules
**Insight**: Balance simplicity with flexibility in permission model

### Slack Virtual User Pattern
**Learning**: Treating Slack as a virtual user simplifies permission model
**Implementation**: "slack-bot" user with no ACL filtering
**Benefit**: All users can search Slack without complex permission logic

### Sync Performance
**Learning**: Batch operations significantly faster than individual adds
**Implementation**: Collect all memories, batch add to Qdrant
**Insight**: 30-minute sync interval balances freshness with overhead

### Categorization Overhead
**Learning**: Automatic categorization on every insert/update can be expensive
**Implementation**: Event listeners trigger categorization
**Consideration**: May need throttling or async processing for high-volume scenarios

## Environment-Specific Notes

### Local Development
- Docker Compose provides complete local stack
- Use `.env` file for configuration
- Qdrant data persists in Docker volume
- PostgreSQL data persists in Docker volume

### AWS Deployment
- Secrets in AWS Secrets Manager (never in code)
- CloudWatch Logs with 7-day retention
- ECS task auto-restarts on failure
- ALB handles SSL/TLS termination

## Known Considerations

### Performance
- Vector search latency depends on collection size
- OpenAI API rate limits affect throughput
- PostgreSQL connection pool size affects concurrency
- Sync operation blocks on large memory sets

### Scalability
- Single instance handles 10-50 concurrent requests
- Horizontal scaling possible via ECS service desired count
- Qdrant can scale independently
- PostgreSQL may need read replicas for high load

### Reliability
- Container restarts trigger Qdrant resync
- PostgreSQL is single point of failure (needs RDS for HA)
- OpenAI API outages prevent embeddings
- Graceful degradation maintains core functionality

### Security
- All sensitive data in Secrets Manager
- HTTPS only in production
- IAM roles for least privilege
- No direct container access (ALB only)

## Current Configuration

### Default Settings
```python
USER_ID = "default-user"  # Default user for testing
DEFAULT_APP_ID = "default-app"  # Default app
LOG_LEVEL = "INFO"  # Logging verbosity
```

### Sync Schedule
- Background sync: Every 30 minutes
- Manual sync: `/sync` endpoint or `sync_vector_store()` tool
- On startup: No automatic sync (waits for first interval)

### Database Indexes
- Critical indexes on user_id, app_id, state
- Composite indexes for common query patterns
- Access log indexes for time-series queries
- History indexes for audit queries

### MCP Tools Available
1. `add_memories`: Store new memory with embedding
2. `search_memory`: Semantic search with fallback
3. `list_memories`: Get all accessible memories
4. `delete_all_memories`: Bulk delete with audit
5. `load_slack_channel`: Import Slack history
6. `search_slack_channels`: Search all Slack data
7. `sync_vector_store`: Manual Qdrant resync

## Integration Points

### External APIs
- OpenAI: Embeddings (text-embedding-3-small) and categorization (GPT models)
- Slack: Channel history and user information
- Qdrant: Vector storage and search (HTTP API)

### Database Connections
- PostgreSQL: Main connection via SQLAlchemy
- Qdrant: HTTP client via qdrant-client library

### MCP Clients
- SSE endpoint: `/mcp/{client_name}/sse/{user_id}`
- Context isolation per connection
- JSON response format

## Troubleshooting Checklist

### Common Issues

**Vector search returns no results**
- Check if Qdrant is running: `curl http://localhost:6333/collections`
- Verify collection exists for user
- Check if sync has run successfully
- Review access permissions

**Memory not being created**
- Check OpenAI API key is valid
- Verify Qdrant connection
- Check logs for exceptions
- Ensure app is not paused

**Sync failing**
- Check PostgreSQL connection
- Verify Qdrant is accessible
- Review sync logs for specific errors
- Check memory count (very large sets may timeout)

**SSE connection issues**
- Verify URL format correct
- Check CORS settings
- Review browser console for errors
- Test with direct curl request

## Documentation Status

### Completed
- ✅ projectbrief.md - Foundation document
- ✅ productContext.md - Product vision and UX
- ✅ systemPatterns.md - Architecture and patterns
- ✅ techContext.md - Technology stack and tools
- ✅ activeContext.md - Current state and decisions

### Remaining
- ⏳ progress.md - Feature status and roadmap
