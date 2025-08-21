import os
from typing import Optional
from pydantic import BaseModel, Field


# Determine the master switch state from ENV variable
ENABLE_ENHANCED_KG = os.getenv("ENABLE_ENHANCED_KG", "False").lower() == "true"


class KnowledgeGraphConfig(BaseModel):
    """Configuration for enhanced knowledge graph features
    
    This configuration class controls all aspects of the knowledge graph enhancement
    features, including entity canonicalization, relationship typing, and performance
    optimizations. All features are gated behind the enable_enhanced_kg flag for
    backward compatibility.
    """
    
    # Feature Toggles
    enable_enhanced_kg: bool = Field(
        default=ENABLE_ENHANCED_KG,
        description="Master switch for all enhanced KG features"
    )
    canonicalization_enabled: bool = Field(
        default=True,
        description="Enable entity name normalization and canonicalization"
    )
    typed_relationships_enabled: bool = Field(
        default=True,
        description="Enable semantic relationship typing with confidence scores"
    )
    alias_tracking_enabled: bool = Field(
        default=True,
        description="Enable tracking of entity aliases for improved matching"
    )
    parallel_processing_enabled: bool = Field(
        default=True,
        description="Enable parallel chunk processing for improved throughput"
    )
    create_symmetric_relationships: bool = Field(
        default=True,
        description="Automatically create symmetric relationships for certain types"
    )
    
    # Entity Thresholds
    # Default to 0.85 if enhanced KG is enabled, otherwise fallback to legacy 0.1. 
    # Allow override via ENV.
    entity_distance_threshold: float = Field(
        default=float(os.getenv(
            "KG_ENTITY_DISTANCE_THRESHOLD", 
            0.85 if ENABLE_ENHANCED_KG else 0.1
        )),
        description="Cosine similarity threshold for entity deduplication",
        ge=0.0,
        le=1.0
    )
    
    # Performance Tuning
    entity_cache_size: int = Field(
        default=int(os.getenv("ENTITY_CACHE_SIZE", "1000")),
        description="Size of the LRU cache for entities",
        gt=0
    )
    max_workers: Optional[int] = Field(
        default=None,
        description="Maximum number of worker threads for parallel processing (defaults to CPU count + 4)"
    )
    chunk_timeout_seconds: int = Field(
        default=30,
        description="Timeout for individual chunk processing in parallel mode",
        gt=0
    )
    
    # Quality Guardrails
    min_relationship_confidence: float = Field(
        default=0.3,
        description="Minimum confidence score for relationships to be stored",
        ge=0.0,
        le=1.0
    )
    max_edges_per_entity: int = Field(
        default=50,
        description="Maximum number of edges per entity to prevent degree explosion",
        gt=0
    )
    
    # Database Configuration
    enable_cache_warmup: bool = Field(
        default=True,
        description="Enable cache warmup during initialization"
    )
    
    # Normalization Settings
    preserve_case_entities: set[str] = Field(
        default_factory=lambda: {
            # Medical/Clinical Abbreviations
            "ICU", "ARDS", "ECMO", "IABP", "CVP", "PCWP", "SVR", "MAP", 
            "SOFA", "APACHE", "SIRS", "MODS", "DIC", "AKI", "CKD",
            "IV", "IM", "SQ", "PO", "PR", "SL", "ET", "IO",
            "ACE", "ARB", "CCB", "NSAID", "SSRI", "MAOI", "MAO", "COMT",
            "FDA", "WHO", "ACCP", "SCCM", "AHA", "ESC", "NICE",
            # Technical/Database (Legacy)
            "SQL", "API", "JSON", "XML", "HTTP", "HTTPS"
        },
        description="Entity names that should preserve their original case (medical abbreviations and technical terms)"
    )
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled
        
        Args:
            feature_name: The name of the feature to check
            
        Returns:
            bool: True if the feature is enabled, False otherwise
        """
        if not self.enable_enhanced_kg:
            return False
            
        feature_map = {
            "canonicalization": self.canonicalization_enabled,
            "typed_relationships": self.typed_relationships_enabled,
            "alias_tracking": self.alias_tracking_enabled,
            "parallel_processing": self.parallel_processing_enabled,
            "symmetric_relationships": self.create_symmetric_relationships,
        }
        
        return feature_map.get(feature_name, False)
    
    def get_effective_threshold(self) -> float:
        """Get the effective entity distance threshold
        
        Returns the appropriate threshold based on whether enhanced KG is enabled.
        Legacy behavior uses 0.1, enhanced uses the configured threshold.
        """
        if not self.enable_enhanced_kg:
            return 0.1  # Legacy behavior
        return self.entity_distance_threshold
    
    def get_worker_count(self) -> int:
        """Get the effective number of worker threads
        
        Returns:
            int: Number of worker threads to use
        """
        if self.max_workers is not None:
            return self.max_workers
        
        # Default to CPU count + 4 as recommended for I/O bound tasks
        import os
        return os.cpu_count() + 4
    
    class Config:
        """Pydantic configuration"""
        env_prefix = "KG_"
        case_sensitive = False
        validate_assignment = True

