# Product Context: MCP Memory Server

## Why This Exists

### The Problem
AI assistants and applications are inherently stateless - they lose context between sessions. Users must repeatedly explain preferences, provide background information, and re-establish context with each interaction. This creates friction and limits the AI's ability to provide personalized, context-aware assistance.

### The Solution
A persistent memory layer that:
- Stores contextual information across sessions
- Enables semantic search to retrieve relevant memories
- Provides standardized MCP interface for AI assistants
- Maintains data consistency and access controls
- Scales to support multiple users and applications

### Target Users
1. **AI Assistant Developers**: Building persistent, context-aware AI applications
2. **Enterprise Teams**: Need shared memory across team members and tools
3. **Integration Developers**: Connecting external systems (Slack, etc.) to memory
4. **Individual Users**: Personal AI assistants with long-term memory

## How It Works

### User Interactions

#### 1. Adding Memories
When a user shares information with an AI assistant:
```
User: "I prefer Python for backend development"
→ Memory stored with user context
→ Embedded for semantic search
→ Categorized automatically (e.g., "preferences", "programming")
```

#### 2. Searching Memories
When the AI needs context:
```
AI Query: "What languages does user prefer?"
→ Semantic search finds: "prefers Python for backend"
→ Returns with relevance score
→ Access logged for audit
```

#### 3. Multi-App Access
Different applications can share or isolate memories:
- **Shared**: Work assistant and personal assistant both see work preferences
- **Isolated**: Private notes stay in notes app only
- **Controlled**: ACL rules determine which app sees what

### Key Workflows

#### Memory Lifecycle
```
[Created] → [Active] → [Paused/Archived] → [Deleted]
     ↓         ↓            ↓                  ↓
  Searchable Searchable  Hidden          Marked deleted
  by all     by all      from search     (soft delete)
```

#### Slack Integration
1. Load channel history: `load_slack_channel(channel_name, days)`
2. Stores messages as memories under "slack-bot" user
3. Search across all Slack data: `search_slack_channels(query)`
4. Returns messages with channel and user context

#### Vector Store Sync
- **Background**: Every 30 minutes, sync PostgreSQL → Qdrant
- **Manual**: `/sync` endpoint or `sync_vector_store()` tool
- **On Restart**: Qdrant container loss triggers automatic resync

### User Experience Goals

#### For AI Assistants
- **Transparent**: Memory operations happen automatically
- **Relevant**: Semantic search finds contextually appropriate memories
- **Fast**: Sub-2-second response times
- **Reliable**: Graceful fallback to text search if vector store down

#### For Developers
- **Simple Integration**: Standard MCP protocol
- **Flexible Deployment**: Docker Compose locally, ECS for production
- **Observable**: Structured JSON logs for debugging
- **Testable**: Full test suite with pytest

#### For Administrators
- **Secure**: IAM roles, secrets management, TLS encryption
- **Scalable**: Auto-scaling based on load
- **Maintainable**: Database migrations, backup/restore
- **Auditable**: Full access logs and state history

## Product Principles

1. **Data Ownership**: Users own their memories, full control over deletion
2. **Privacy by Design**: Explicit access controls, no cross-user leakage
3. **Graceful Degradation**: System remains functional when dependencies fail
4. **Observability First**: Every operation logged and traceable
5. **Convention over Configuration**: Sensible defaults, minimal setup

## Success Metrics

### Technical Metrics
- Memory operation latency < 2s (p95)
- Vector search accuracy > 90%
- System uptime > 99.9%
- Sync lag < 5 minutes

### Business Metrics
- Active users across multiple apps
- Memories created per user per day
- Search queries per session
- User retention week-over-week

### Quality Metrics
- Memory relevance (user feedback)
- Category accuracy
- Zero data loss incidents
- Mean time to recovery < 1 hour
