# System Patterns: MCP Memory Server

## Architecture Overview

### High-Level Components
```
┌─────────────────────────────────────────────────────────────┐
│                      AI Assistant/Client                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol (SSE)
┌───────────────────────────┴─────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ MCP Server  │  │  REST API   │  │  Background Jobs │   │
│  │   (SSE)     │  │  Routers    │  │   (Scheduler)    │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└───────┬─────────────────┬──────────────────────────────────┘
        │                 │
        ├─────────────────┴────────────────┐
        │                                  │
┌───────▼──────────┐            ┌─────────▼──────────┐
│   PostgreSQL     │            │      Qdrant        │
│  (Source of      │◄───sync────│  (Vector Search)   │
│    Truth)        │            │                    │
└──────────────────┘            └────────────────────┘
```

### Data Flow

#### Write Path (Add Memory)
```
Client → MCP Tool (add_memories)
  ↓
1. Validate user/app via PostgreSQL
2. Add to mem0 client (generates embedding)
3. mem0 stores in Qdrant
4. Callback: Store in PostgreSQL with state
5. Create history & access log entries
  ↓
Return response to client
```

#### Read Path (Search Memory)
```
Client → MCP Tool (search_memory)
  ↓
1. Check user/app permissions
2. Query Qdrant with embeddings
3. Filter results by ACL (accessible_memory_ids)
4. Log access in PostgreSQL
  ↓
Return filtered results

Fallback: If Qdrant unavailable
  → Query PostgreSQL with ILIKE text search
  → Return database results
```

#### Sync Path (PostgreSQL → Qdrant)
```
Background Job (every 30 min) OR Manual Trigger
  ↓
1. Query all active memories from PostgreSQL
2. Clear Qdrant collection (per user)
3. Batch add to Qdrant with embeddings
4. Log sync statistics
```

## Key Technical Decisions

### 1. Dual Storage Pattern
**Decision**: Use both PostgreSQL and Qdrant
- **PostgreSQL**: Source of truth for relational data, state, ACL
- **Qdrant**: Optimized for vector similarity search

**Rationale**:
- PostgreSQL provides ACID guarantees, relations, complex queries
- Qdrant provides fast semantic search with vector embeddings
- Separation allows independent scaling and optimization

**Trade-off**: Data consistency requires sync mechanism

### 2. Lazy Memory Client Initialization
**Decision**: Don't initialize mem0 client at import time
```python
def get_memory_client_safe():
    try:
        return get_memory_client()
    except Exception as e:
        logging.warning(f"Failed to get memory client: {e}")
        return None
```

**Rationale**:
- Prevents server crash when Qdrant/Ollama unavailable
- Enables graceful degradation to text search
- Better for container restarts and development

### 3. Context Variables for MCP
**Decision**: Use `contextvars` for user_id and client_name
```python
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id")
client_name_var: contextvars.ContextVar[str] = contextvars.ContextVar("client_name")
```

**Rationale**:
- Thread-safe per-request context
- SSE connections maintain user/app isolation
- No global state pollution

### 4. Soft Delete Pattern
**Decision**: Mark memories as deleted, don't remove from database
```python
class MemoryState(enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"
    deleted = "deleted"
```

**Rationale**:
- Enables audit trail and recovery
- Supports state history tracking
- Allows future undelete functionality

### 5. ACL-Based Permissions
**Decision**: Explicit access control lists rather than role-based
```python
def check_memory_access_permissions(db, memory, app_id):
    # Check AccessControl table for explicit allow/deny
    # Default: same app can access
```

**Rationale**:
- Flexible per-memory, per-app permissions
- Supports shared memories across apps
- Can implement deny rules for specific apps

## Design Patterns

### 1. Repository Pattern
**Location**: `app/utils/db.py`, `app/utils/memory.py`
- Encapsulates database access logic
- `get_user_and_app()`: Get or create user/app
- Separates business logic from data access

### 2. Service Layer Pattern
**Location**: `app/mcp_server.py` (MCP tools)
- Tools act as service layer
- Orchestrate database, memory client, permissions
- Return formatted responses

### 3. Background Job Pattern
**Implementation**: APScheduler
```python
scheduler = BackgroundScheduler()
scheduler.add_job(background_sync_job, 'interval', minutes=30)
```
- Periodic sync without blocking requests
- Separate concern from request handling

### 4. Factory Pattern
**Location**: `app/utils/memory.py`
```python
def get_memory_client():
    config = load_config()
    return Memory.from_config(config)
```
- Centralizes client creation
- Handles configuration loading

### 5. Event Listener Pattern
**Location**: `app/models.py`
```python
@event.listens_for(Memory, 'after_insert')
def after_memory_insert(mapper, connection, target):
    categorize_memory(target, db)
```
- Automatic categorization on memory changes
- Decoupled from main business logic

## Component Relationships

### Database Models Hierarchy
```
User (1) ──── (N) App
  │               │
  │               │
  └───(N)    (N)──┘
       │    │
       Memory (N) ──── (N) Category
          │
          ├── (N) MemoryAccessLog
          ├── (N) MemoryStatusHistory
          └── (N) AccessControl
```

### Router Organization
```
app/routers/
├── memories.py    # CRUD operations on memories
├── apps.py        # App management, pause/resume
├── stats.py       # Access logs, statistics
├── config.py      # System configuration
└── backup.py      # Backup and restore
```

### Utility Modules
```
app/utils/
├── memory.py         # Memory client initialization
├── db.py            # Database helpers (get_user_and_app)
├── permissions.py   # ACL checking
├── categorization.py # AI categorization
└── prompts.py       # Prompt templates
```

## Critical Implementation Paths

### 1. Memory Access Control Flow
```
1. Tool called (e.g., search_memory)
2. Extract user_id and client_name from context vars
3. get_user_and_app(db, user_id, app_id)
   - Creates user/app if doesn't exist
   - Returns UUID references
4. Query memories with filters
5. check_memory_access_permissions(db, memory, app.id)
   - Checks AccessControl table
   - Default: same app can access
6. Filter results to accessible only
7. Log access in MemoryAccessLog
```

### 2. Graceful Degradation Path
```
1. search_memory called
2. get_memory_client_safe() returns None
3. Log warning: "Using database fallback"
4. Query PostgreSQL:
   - Filter by user_id, app_id, state=active
   - ILIKE text search on content
5. Check permissions per memory
6. Return with note: "Using text search"
```

### 3. Slack Integration Path
```
1. load_slack_channel(channel_name, days)
2. SlackChannelLoader fetches via Slack API
3. For each message:
   - Store as memory under "slack-bot" user
   - Metadata: channel, user, timestamp
4. search_slack_channels(query)
   - Always uses user_id="slack-bot"
   - Filters by metadata.slack_channel_name
   - No ACL filtering (all Slack data public)
```

### 4. Sync Recovery Path
```
1. Container restart → Qdrant data lost
2. Background job triggers sync_qdrant()
3. For each user in PostgreSQL:
   - Clear Qdrant collection for user
   - Query active memories
   - Batch add to Qdrant with embeddings
4. Log: total, synced, errors
5. System operational with restored vectors
```

## Indexing Strategy

### PostgreSQL Indexes
```sql
-- User lookups
idx_users_user_id (user_id)

-- Memory queries
idx_memory_user_state (user_id, state)
idx_memory_app_state (app_id, state)
idx_memory_user_app (user_id, app_id)

-- Access logs
idx_access_memory_time (memory_id, accessed_at)
idx_access_app_time (app_id, accessed_at)

-- History tracking
idx_history_memory_state (memory_id, new_state)
```

### Qdrant Collection Strategy
- One collection per user (named by user_id)
- Vectors: OpenAI embeddings (1536 dimensions)
- Payload: memory content, metadata, timestamps
- Filters: user_id, metadata fields

## Error Handling Patterns

### 1. Try-Except with Logging
```python
try:
    result = memory_client.add(text, user_id=uid)
except Exception as e:
    logging.exception(f"Error adding to memory: {e}")
    return f"Error: {e}"
```

### 2. Safe Client Retrieval
```python
memory_client = get_memory_client_safe()
if not memory_client:
    return "Error: Memory system currently unavailable"
```

### 3. Database Transaction Management
```python
db = SessionLocal()
try:
    # operations
    db.commit()
finally:
    db.close()
```

## Performance Considerations

### 1. Connection Pooling
- PostgreSQL: SQLAlchemy connection pool
- Qdrant: Persistent HTTP client
- Prevents connection overhead per request

### 2. Batch Operations
- Sync: Batch add to Qdrant (not one-by-one)
- Reduces network overhead
- Improves sync speed

### 3. Lazy Loading
- Memory client initialized on first use
- Embeddings computed on demand
- Reduces startup time

### 4. Caching Strategy
- Config: Load once, cache in memory
- User/App: Cache hit via get_user_and_app
- Categories: Reuse existing via query
