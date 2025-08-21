import dspy
import logging

from autoflow.knowledge_graph.extractors.base import KGExtractor
from autoflow.knowledge_graph.programs.extract_graph import KnowledgeGraphExtractor
from autoflow.knowledge_graph.types import GeneratedKnowledgeGraph


logger = logging.getLogger(__name__)


class SimpleKGExtractor(KGExtractor):
    """
    Simplified Knowledge Graph extractor with unified extraction.
    
    Phase 2 Enhancement: Eliminates dual LLM calls by using enhanced
    KnowledgeGraphExtractor that extracts entities with covariates and 
    typed relationships in a single pass.
    """
    
    def __init__(self, dspy_lm: dspy.LM):
        super().__init__()
        self._dspy_lm = dspy_lm
        self._graph_extractor = KnowledgeGraphExtractor(dspy_lm)
        
        # Note: EntityCovariateExtractor removed for unified extraction
        # All entity metadata and relationship typing now handled by
        # the enhanced KnowledgeGraphExtractor in a single LLM call

    def extract(self, text: str) -> GeneratedKnowledgeGraph:
        """
        Extract knowledge graph using unified approach.
        
        Phase 2 Enhancement: Single LLM call extracts entities with metadata
        AND typed relationships with confidence scores, reducing latency by ~50%.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Generated knowledge graph with enhanced entities and typed relationships
        """
        logger.debug("Starting unified knowledge graph extraction")
        
        # Single LLM call handles both entity extraction with covariates 
        # AND relationship extraction with semantic typing
        knowledge_graph = self._graph_extractor.forward(text)
        
        logger.debug(f"Unified extraction complete: {len(knowledge_graph.entities)} entities, "
                    f"{len(knowledge_graph.relationships)} relationships")
        
        # Phase 2: No separate EntityCovariateExtractor call needed
        # All metadata is now extracted in the unified call above
        
        return knowledge_graph
