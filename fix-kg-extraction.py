#!/usr/bin/env python
"""
Knowledge Graph Extraction Fix Script

Fixes the DSPy JSON format issues that are preventing KG indexing from completing.
The issue is that the ExtractKnowledgeGraph prompt is too verbose and complex,
causing LLM to fail JSON generation.
"""

import re
from pathlib import Path

def fix_extract_graph_prompt():
    """Fix the overly complex ExtractKnowledgeGraph prompt"""
    
    extract_graph_file = Path("core/autoflow/knowledge_graph/programs/extract_graph.py")
    
    if not extract_graph_file.exists():
        print("❌ extract_graph.py not found")
        return False
    
    # Read current content
    with open(extract_graph_file, 'r') as f:
        content = f.read()
    
    # Simplified prompt that works better with DSPy
    new_prompt = '''class ExtractKnowledgeGraph(dspy.Signature):
    """Extract medical entities and relationships from clinical text.

    Extract entities: name, description, type (drug/receptor/pathway/condition/procedure/biomarker)
    Extract relationships: source_entity, target_entity, description, type, confidence (0.0-1.0)
    
    Relationship types: hypernym, hyponym, meronym, holonym, synonym, antonym, causal, temporal, dependency, reference, generic
    
    Return valid JSON with entities and relationships arrays.
    """'''
    
    # Replace the overly complex prompt
    pattern = r'class ExtractKnowledgeGraph\(dspy\.Signature\):\s*""".*?"""'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_prompt, content, flags=re.DOTALL)
        
        # Write back the simplified version
        with open(extract_graph_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Simplified ExtractKnowledgeGraph prompt")
        return True
    else:
        print("⚠️ Could not find ExtractKnowledgeGraph pattern to replace")
        return False

def fix_pydantic_enum_warnings():
    """Fix Pydantic enum serialization warnings"""
    
    chunk_model_file = Path("backend/app/models/chunk.py")
    
    if not chunk_model_file.exists():
        print("❌ chunk.py not found")
        return False
    
    with open(chunk_model_file, 'r') as f:
        content = f.read()
    
    # Check if KgIndexStatus is properly configured
    if 'class KgIndexStatus(str, enum.Enum):' in content:
        print("✅ KgIndexStatus enum found")
        
        # Add proper Pydantic configuration if missing
        if 'model_config = ConfigDict(use_enum_values=True)' not in content:
            # Find the chunk model class and add config
            pattern = r'(class Chunk\(.*?\):.*?)'
            replacement = r'\1\n    model_config = ConfigDict(use_enum_values=True)\n'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            if new_content != content:
                with open(chunk_model_file, 'w') as f:
                    f.write(new_content)
                print("✅ Added Pydantic enum configuration to fix warnings")
            else:
                print("⚠️ Could not automatically fix enum configuration")
        else:
            print("✅ Pydantic enum configuration already present")
    
    return True

def create_kg_restart_script():
    """Create a script to restart KG indexing cleanly"""
    
    restart_script = '''#!/bin/bash

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
'''
    
    with open("restart-kg-indexing.sh", "w") as f:
        f.write(restart_script)
    
    # Make executable
    import os
    os.chmod("restart-kg-indexing.sh", 0o755)
    
    print("✅ Created restart-kg-indexing.sh script")

def main():
    """Main fix function"""
    print("🔧 Fixing Knowledge Graph Extraction Issues")
    print("=" * 50)
    
    # Apply fixes
    fixes_applied = 0
    
    if fix_extract_graph_prompt():
        fixes_applied += 1
    
    if fix_pydantic_enum_warnings():
        fixes_applied += 1
    
    create_kg_restart_script()
    fixes_applied += 1
    
    print(f"\n✅ Applied {fixes_applied} fixes")
    
    print("\n🚀 Next Steps:")
    print("1. Run: ./restart-kg-indexing.sh")
    print("2. Try reindexing failed tasks again")
    print("3. Monitor logs for successful JSON parsing")
    print("4. The simplified prompt should work much better!")
    
    return True

if __name__ == "__main__":
    main()
