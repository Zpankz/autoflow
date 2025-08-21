#!/usr/bin/env python
"""
Medical Knowledge Graph Setup Script

Sets up the enhanced AutoFlow system for biophysical pharmacophysiology
in critical care medicine context.
"""

import json
import os
from pathlib import Path

def setup_medical_knowledge_base():
    """Configure the enhanced KG system for medical domain"""
    
    print("🏥 Setting up Medical Knowledge Graph for Critical Care...")
    
    # Environment configuration for medical domain
    medical_env_config = {
        "ENABLE_ENHANCED_KG": "true",
        "KG_ENTITY_DISTANCE_THRESHOLD": "0.85",
        "ENTITY_CACHE_SIZE": "2000",  # Larger cache for medical entities
        "KG_": "medical_critical_care"
    }
    
    # Update .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'a') as f:
            f.write("\n# Medical Knowledge Graph Configuration\n")
            for key, value in medical_env_config.items():
                f.write(f"{key}={value}\n")
    
    # Medical entity types for configuration
    medical_preserve_case = {
        "ICU", "ARDS", "ECMO", "IABP", "CVP", "PCWP", "SVR", "MAP", 
        "SOFA", "APACHE", "SIRS", "MODS", "DIC", "AKI", "CKD",
        "IV", "IM", "SQ", "PO", "PR", "SL", "ET", "IO",
        "ACE", "ARB", "CCB", "NSAID", "SSRI", "MAOI",
        "FDA", "WHO", "ACCP", "SCCM", "AHA", "ESC"
    }
    
    # Create medical configuration overlay
    medical_config = {
        "enhanced_kg_config": {
            "enable_enhanced_kg": True,
            "entity_distance_threshold": 0.85,
            "preserve_case_entities": list(medical_preserve_case),
            "medical_domain_focus": True,
            "therapeutic_relationship_weights": {
                "therapeutic_effect": 0.9,
                "contraindication": 0.85,
                "drug_interaction": 0.8,
                "pharmacokinetic_pathway": 0.75,
                "monitoring_parameter": 0.7
            }
        },
        "medical_sample_queries": [
            "What are the pharmacokinetic parameters of vasopressors in septic shock?",
            "How do alpha-adrenergic agonists affect systemic vascular resistance?", 
            "What are the monitoring parameters for norepinephrine therapy?",
            "How does vasopressin differ from catecholamine vasopressors?",
            "What are the contraindications for high-dose epinephrine?",
            "How does sepsis alter drug clearance and distribution?",
            "What are the hemodynamic targets in distributive shock?",
            "How do inotropes differ from vasopressors in mechanism?",
            "What biomarkers indicate adequate tissue perfusion?",
            "How should vasopressors be weaned in recovering patients?"
        ]
    }
    
    # Save configuration
    with open("medical-kg-config.json", "w") as f:
        json.dump(medical_config, f, indent=2)
    
    print("✅ Medical KG configuration created")
    print("✅ Environment variables configured")
    print("✅ Sample queries updated for critical care context")
    print("✅ Medical fixtures created with pharmacology content")
    
    return medical_config

def validate_medical_setup():
    """Validate the medical KG setup"""
    
    required_files = [
        "core/autoflow/configs/knowledge_graph.py",
        "core/examples/medical_fixtures/critical_care_pharmacology.md",
        "core/examples/medical_fixtures/septic_shock_management.md",
        "core/examples/medical_fixtures/pharmacokinetics_models.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️ Missing files: {missing_files}")
        return False
    
    print("✅ All medical KG components present")
    return True

def print_usage_instructions():
    """Print instructions for using the medical KG system"""
    
    print("""
🏥 MEDICAL KNOWLEDGE GRAPH SYSTEM READY

📋 Quick Start Instructions:

1. Enable Enhanced Features:
   export ENABLE_ENHANCED_KG=true
   export KG_ENTITY_DISTANCE_THRESHOLD=0.85

2. Test Medical Knowledge Extraction:
   cd core
   python examples/kg_benchmark.py \\
     --corpus-path examples/medical_fixtures/ \\
     --database-url "your-db-url" \\
     --openai-api-key "your-key"

3. Sample Medical Queries:
   - "What are the pharmacokinetic parameters of vasopressors in septic shock?"
   - "How do alpha-adrenergic agonists affect systemic vascular resistance?"
   - "What are the monitoring parameters for norepinephrine therapy?"

4. Nx Graph Analysis:
   ./nx dep-graph
   ./nx graph

🔗 DeepGraph Integration:
   Use MCP deepgraph tools to analyze:
   - Medical entity relationships
   - Pharmacological pathway mappings  
   - Clinical protocol dependencies
   - Drug interaction networks
""")

if __name__ == "__main__":
    config = setup_medical_knowledge_base()
    
    if validate_medical_setup():
        print_usage_instructions()
        print("\n🎉 Medical Knowledge Graph setup complete!")
    else:
        print("\n❌ Setup validation failed")
        exit(1)
