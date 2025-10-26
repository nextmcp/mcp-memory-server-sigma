#!/usr/bin/env python3
"""
Sync Qdrant vector store from PostgreSQL using efficient bulk operations.

This script rebuilds the Qdrant index from all active memories in the PostgreSQL database.
Uses direct Qdrant batch upsert for 10-20x performance improvement over sequential operations.

This is essential when:
- Qdrant container restarts (ephemeral storage)
- Vector store becomes corrupted
- Migrating to a new Qdrant instance
- Recovering from backup

Usage:
    python src/openmemory/sync_qdrant_from_postgres.py [--dry-run]

The script:
1. Connects to PostgreSQL and fetches all active memories
2. Batch generates embeddings via OpenAI (single API call per user)
3. Batch upserts to Qdrant (single operation per user)
4. Reports statistics on sync progress
"""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path / "openmemory"))

# Import AFTER dotenv is loaded and path is set
from app.database import SessionLocal
from app.models import Memory, MemoryState
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User filtering configuration
USERS_TO_SYNC = {"slack-bot", "buy-box-rules", "weather"}

# Date filters for specific users (None = sync all)
DATE_FILTERS = {
    "slack-bot": timedelta(days=7),   # Only last 7 days for Slack
    "buy-box-rules": None,            # All memories for buy-box
    "weather": None                   # All memories for weather user
}


def bulk_sync_user_to_qdrant(memories: list, user_id: str, dry_run: bool = False):
    """
    Efficiently sync a batch of memories to Qdrant using direct bulk operations.
    
    This bypasses mem0's sequential processing and uses:
    - Single OpenAI API call for all embeddings (batch)
    - Single Qdrant upsert operation (batch)
    
    This is 10-20x faster than mem0's add() and avoids socket exhaustion.
    
    Args:
        memories: List of Memory objects to sync
        user_id: User ID for the memories
        dry_run: If True, only report what would be synced
        
    Returns:
        Number of memories successfully synced
    """
    if not memories:
        return 0
    
    if dry_run:
        logger.info(f"[DRY RUN] Would bulk sync {len(memories)} memories for user {user_id}")
        return len(memories)
    
    try:
        # Initialize Qdrant client directly
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_client = QdrantClient(url=qdrant_url)
        
        # Ensure collection exists (create if needed)
        try:
            qdrant_client.get_collection("openmemory")
            logger.info("Collection 'openmemory' exists")
        except Exception:
            # Collection doesn't exist, create it
            logger.info("Creating collection 'openmemory' with 1536-dimensional vectors")
            qdrant_client.create_collection(
                collection_name="openmemory",
                vectors_config=VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )
            logger.info("✓ Collection 'openmemory' created successfully")
        
        # Get OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Prepare texts for embedding
        texts = [m.content for m in memories]
        
        # Batch embed with OpenAI (single API call!)
        logger.info(f"Generating embeddings for {len(texts)} memories...")
        openai_client = openai.OpenAI(api_key=openai_key)
        response = openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        
        # Build points for batch upsert
        points = []
        for memory, embedding in zip(memories, response.data):
            points.append(
                PointStruct(
                    id=str(memory.id),
                    vector=embedding.embedding,
                    payload={
                        "user_id": user_id,
                        "data": memory.content,
                        "metadata": memory.metadata_ or {},
                        "created_at": memory.created_at.isoformat() if memory.created_at else None,
                        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
                    }
                )
            )
        
        # Batch upsert to Qdrant (single operation!)
        logger.info(f"Upserting {len(points)} points to Qdrant...")
        qdrant_client.upsert(
            collection_name="openmemory",
            points=points,
            wait=True
        )
        
        logger.info(f"✓ Successfully synced {len(points)} memories for user {user_id}")
        return len(points)
        
    except Exception as e:
        logger.error(f"Error in bulk sync for user {user_id}: {e}", exc_info=True)
        raise


def sync_qdrant(dry_run: bool = False, batch_size: int = 100):
    """
    Sync Qdrant from PostgreSQL using efficient bulk operations.
    
    This version uses direct Qdrant batch upsert instead of mem0's
    sequential add() calls, providing 10-20x performance improvement.
    
    Args:
        dry_run: If True, only report what would be synced without actually syncing
        batch_size: Not used (kept for API compatibility)
        
    Returns:
        Dictionary with sync statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Qdrant sync from PostgreSQL (bulk upsert)...")
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get all active memories
        logger.info("Fetching active memories from PostgreSQL...")
        memories = db.query(Memory).filter(
            Memory.state == MemoryState.active
        ).all()
        
        logger.info(f"Found {len(memories)} active memories in PostgreSQL")
        
        # Group memories by user and apply filters
        user_memories = {}
        skipped_users = 0
        filtered_count = 0
        
        for memory in memories:
            if memory.user:
                user_id = memory.user.user_id
                
                # Skip users not in whitelist
                if user_id not in USERS_TO_SYNC:
                    if user_id not in user_memories:
                        skipped_users += 1
                    continue
                
                # Apply date filter if configured
                if DATE_FILTERS.get(user_id):
                    cutoff = datetime.utcnow() - DATE_FILTERS[user_id]
                    if memory.created_at < cutoff:
                        filtered_count += 1
                        continue
                
                if user_id not in user_memories:
                    user_memories[user_id] = []
                user_memories[user_id].append(memory)
        
        logger.info(f"Filtered out {skipped_users} users not in whitelist")
        logger.info(f"Filtered out {filtered_count} memories older than date cutoff")
        logger.info(f"Processing {len(user_memories)} users with {sum(len(mems) for mems in user_memories.values())} memories")
        
        stats = {
            "total": len(memories),
            "synced": 0,
            "errors": 0,
            "dry_run": dry_run
        }
        
        # Process each user with efficient bulk sync
        for user_id, user_mems in user_memories.items():
            try:
                logger.info(f"Processing user {user_id} with {len(user_mems)} memories...")
                
                # Use bulk sync for this user
                synced_count = bulk_sync_user_to_qdrant(user_mems, user_id, dry_run)
                stats["synced"] += synced_count
                        
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}", exc_info=True)
                stats["errors"] += len(user_mems)
                continue
        
        logger.info("=" * 60)
        logger.info("Sync complete!")
        logger.info(f"Total memories: {stats['total']}")
        logger.info(f"Memories synced: {stats['synced']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("=" * 60)
        
        return stats
        
    finally:
        db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sync Qdrant vector store from PostgreSQL database using bulk operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Perform actual sync
  python src/openmemory/sync_qdrant_from_postgres.py

  # Dry run to see what would be synced
  python src/openmemory/sync_qdrant_from_postgres.py --dry-run

  # Verbose logging
  python src/openmemory/sync_qdrant_from_postgres.py --verbose

Performance:
  This version uses Qdrant batch upsert which is 10-20x faster than
  the sequential mem0 approach. Expected sync time for 262 memories:
  - Old approach: 20+ minutes with socket exhaustion errors
  - New approach: 2-3 seconds
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually syncing"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="(Deprecated) Not used in bulk sync, kept for compatibility"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run sync
    try:
        stats = sync_qdrant(dry_run=args.dry_run, batch_size=args.batch_size)
        
        if "error" in stats:
            logger.error(f"Sync failed: {stats['error']}")
            sys.exit(1)
        
        # Exit with error code if there were errors
        if stats["errors"] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
