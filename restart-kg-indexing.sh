#!/bin/bash

# Restart Knowledge Graph Indexing Script

echo "🔄 Restarting Knowledge Graph Indexing..."

# 1. Stop background workers
echo "⏹️ Stopping background workers..."
docker-compose stop background

# 2. Clear any stuck Redis queues (optional)
echo "🧹 Clearing Redis queues..."
docker-compose exec redis redis-cli FLUSHDB

# 3. Restart background workers
echo "🚀 Starting background workers..."
docker-compose up -d background

# 4. Wait for workers to be ready
echo "⏳ Waiting for workers to initialize..."
sleep 10

# 5. Check worker status
echo "🔍 Checking worker status..."
docker-compose exec background celery -A app.celery inspect active

# 6. Monitor logs
echo "📊 Monitoring KG indexing logs (Ctrl+C to stop)..."
docker-compose logs -f background | grep -E "(kg_index|build_kg|KG|knowledge_graph)"

echo "✅ KG indexing restart complete!"
