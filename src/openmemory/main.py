import datetime
import logging
import sys
from uuid import uuid4

from app.config import DEFAULT_APP_ID, USER_ID
from app.database import Base, SessionLocal, engine
from app.mcp_server import setup_mcp_server
from app.models import App, User
from app.routers import apps_router, backup_router, config_router, memories_router, stats_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

app = FastAPI(title="OpenMemory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Check for USER_ID and create default user if needed
def create_default_user():
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == USER_ID).first()
        if not user:
            # Create default user
            user = User(
                id=uuid4(),
                user_id=USER_ID,
                name="Default User",
                created_at=datetime.datetime.now(datetime.UTC)
            )
            db.add(user)
            db.commit()
    finally:
        db.close()


def create_default_app():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == USER_ID).first()
        if not user:
            return

        # Check if app already exists
        existing_app = db.query(App).filter(
            App.name == DEFAULT_APP_ID,
            App.owner_id == user.id
        ).first()

        if existing_app:
            return

        app = App(
            id=uuid4(),
            name=DEFAULT_APP_ID,
            owner_id=user.id,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        db.add(app)
        db.commit()
    finally:
        db.close()

# Create default user on startup
create_default_user()
create_default_app()

# Background sync function
def background_sync_job():
    """Run sync from PostgreSQL to Qdrant in background"""
    try:
        logger.info("Starting scheduled background sync...")
        from sync_qdrant_from_postgres import sync_qdrant
        result = sync_qdrant(dry_run=False)
        
        if "error" in result:
            logger.error(f"Background sync failed: {result['error']}")
        else:
            logger.info("Background sync completed successfully")
            logger.info(f"Total memories: {result['total']}, Synced: {result['synced']}, Errors: {result['errors']}")
    except Exception as e:
        logger.error(f"Background sync failed: {e}", exc_info=True)

# Initialize background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    background_sync_job,
    'interval',
    minutes=30,
    id='sync_postgres_to_qdrant',
    name='Sync PostgreSQL to Qdrant every 30 minutes'
)
scheduler.start()
logger.info("Background scheduler started - syncing every 30 minutes")

# Setup MCP server
setup_mcp_server(app)

# Include routers
app.include_router(memories_router)
app.include_router(apps_router)
app.include_router(stats_router)
app.include_router(config_router)
app.include_router(backup_router)

# Add pagination support
add_pagination(app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "openmemory"}


# Sync endpoint to trigger Qdrant sync from PostgreSQL
@app.post("/sync")
async def trigger_sync():
    """Trigger Qdrant sync from PostgreSQL database"""
    import logging
    try:
        from sync_qdrant_from_postgres import sync_qdrant
        logging.info("Manual sync triggered via /sync endpoint")
        result = sync_qdrant(dry_run=False)
        
        if "error" in result:
            return {"status": "error", "error": result["error"]}
        
        return {
            "status": "success",
            "statistics": {
                "total_memories": result["total"],
                "memories_synced": result["synced"],
                "errors": result["errors"]
            }
        }
    except Exception as e:
        logging.exception(f"Error during sync: {e}")
        return {"status": "error", "error": str(e)}
