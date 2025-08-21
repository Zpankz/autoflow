#!/usr/bin/env python
"""
Knowledge Graph Indexing Diagnostic Script

Diagnoses why KG indexing tasks are queued but not executing.
Checks Celery workers, Redis connectivity, and task status.
"""

import json
import subprocess
import sys
import time
from datetime import datetime

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_docker_containers():
    """Check Docker container status"""
    print("🐳 Checking Docker Container Status...")
    
    # Check running containers
    success, stdout, stderr = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    if success:
        print("📋 Running Containers:")
        print(stdout)
        
        # Check specifically for backend services
        if "backend" in stdout:
            print("✅ Backend container is running")
        else:
            print("❌ Backend container not running")
        
        if "background" in stdout:
            print("✅ Background worker container is running")
        else:
            print("❌ Background worker container NOT running - This is likely the issue!")
            print("💡 Start background workers with: docker-compose up -d background")
        
        if "redis" in stdout:
            print("✅ Redis container is running")
        else:
            print("❌ Redis container not running")
    else:
        print(f"❌ Failed to check containers: {stderr}")
    
    return success

def check_celery_workers():
    """Check Celery worker status"""
    print("\n🔧 Checking Celery Worker Status...")
    
    # Check Celery worker processes
    cmd = "docker-compose exec -T background ps aux | grep celery || echo 'No background container running'"
    success, stdout, stderr = run_command(cmd)
    
    if "celery" in stdout:
        print("✅ Celery workers found in background container:")
        celery_lines = [line for line in stdout.split('\n') if 'celery' in line]
        for line in celery_lines:
            print(f"  {line}")
    else:
        print("❌ No Celery workers running")
        print("💡 This explains why KG indexing tasks aren't being processed!")

def check_redis_connectivity():
    """Check Redis connectivity from backend"""
    print("\n📡 Checking Redis Connectivity...")
    
    # Test Redis connection from backend
    cmd = "docker-compose exec -T backend python -c \"import redis; r=redis.Redis(host='redis', port=6379); print('Redis ping:', r.ping())\""
    success, stdout, stderr = run_command(cmd)
    
    if success and "True" in stdout:
        print("✅ Redis connectivity from backend: OK")
    else:
        print(f"❌ Redis connectivity issue: {stderr}")

def check_celery_queue_status():
    """Check Celery queue status"""
    print("\n📊 Checking Celery Queue Status...")
    
    # Check active tasks
    cmd = "docker-compose exec -T background celery -A app.celery inspect active"
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("📋 Active Celery Tasks:")
        if stdout.strip():
            print(stdout)
        else:
            print("  No active tasks")
    else:
        print(f"❌ Failed to check Celery status: {stderr}")
    
    # Check registered tasks
    cmd = "docker-compose exec -T background celery -A app.celery inspect registered"
    success, stdout, stderr = run_command(cmd)
    
    if success and "build_kg_index_for_chunk" in stdout:
        print("✅ build_kg_index_for_chunk task is registered")
    else:
        print("❌ build_kg_index_for_chunk task not registered")

def check_pending_chunks():
    """Check pending KG index chunks in database"""
    print("\n📋 Checking Pending KG Index Chunks...")
    
    # This would require database access, so provide SQL query instead
    sql_query = """
    SELECT 
        COUNT(*) as pending_chunks,
        index_status,
        kb.name as knowledge_base_name
    FROM chunks_1 c  -- Adjust table name based on KB ID
    JOIN knowledge_bases kb ON kb.id = 1
    WHERE c.index_status IN ('not_started', 'pending', 'failed')
    GROUP BY index_status, kb.name;
    """
    
    print("💡 Run this SQL query in your database to check pending chunks:")
    print(sql_query)

def provide_solutions():
    """Provide solutions for common issues"""
    print("\n🔧 Common Solutions:")
    print()
    print("1. **Start Background Workers** (Most likely issue):")
    print("   docker-compose up -d background")
    print()
    print("2. **Check Background Worker Logs**:")
    print("   docker-compose logs -f background")
    print()
    print("3. **Restart All Services**:")
    print("   docker-compose down && docker-compose up -d")
    print()
    print("4. **Check Celery Worker Status**:")
    print("   docker-compose exec background celery -A app.celery inspect active")
    print()
    print("5. **Monitor Task Processing**:")
    print("   docker-compose exec background celery -A app.celery events")
    print()
    print("6. **Fix Enum Serialization Warnings**:")
    print("   The Pydantic warnings can be fixed by updating model configurations")

def main():
    """Main diagnostic function"""
    print("🩺 AutoFlow Knowledge Graph Indexing Diagnostic")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Run diagnostics
    container_ok = check_docker_containers()
    
    if container_ok:
        check_celery_workers()
        check_redis_connectivity() 
        check_celery_queue_status()
    
    check_pending_chunks()
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS SUMMARY:")
    print("Tasks are being QUEUED but not EXECUTED because:")
    print("❌ Background worker container is likely not running")
    print("💡 SOLUTION: Start background workers with 'docker-compose up -d background'")
    print("=" * 60)

if __name__ == "__main__":
    main()
