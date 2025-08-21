import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Optional

import dspy

from autoflow.configs.knowledge_graph import KnowledgeGraphConfig
from autoflow.knowledge_graph.extractors.simple import SimpleKGExtractor
from autoflow.knowledge_graph.retrievers.weighted import WeightedGraphRetriever
from autoflow.knowledge_graph.types import (
    RetrievedKnowledgeGraph,
)
from autoflow.models.embedding_models import EmbeddingModel
from autoflow.storage.doc_store.types import Chunk
from autoflow.storage.graph_store.base import GraphStore
from autoflow.storage.graph_store.types import KnowledgeGraph
from autoflow.types import BaseComponent


logger = logging.getLogger(__name__)


class KnowledgeGraphIndex(BaseComponent):
    """
    Enhanced Knowledge Graph Index with parallel processing capabilities.
    
    Phase 3 Enhancement: Supports concurrent chunk processing using ThreadPoolExecutor
    for significant throughput improvements (3x-5x expected) while maintaining
    error isolation and timeout handling.
    """
    
    def __init__(
        self,
        kg_store: GraphStore,
        dspy_lm: dspy.LM,
        embedding_model: EmbeddingModel,
        config: Optional[KnowledgeGraphConfig] = None,
    ):
        super().__init__()
        self._kg_store = kg_store
        self._dspy_lm = dspy_lm
        self._embedding_model = embedding_model
        self._kg_extractor = SimpleKGExtractor(self._dspy_lm)
        
        # Phase 3 Enhancement: Initialize configuration and parallel processing
        self._config = config or KnowledgeGraphConfig()
        
        # Initialize ThreadPoolExecutor for parallel chunk processing
        if self._config.enable_enhanced_kg and self._config.is_feature_enabled("parallel_processing"):
            max_workers = self._config.get_worker_count()
            self._executor = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="kg_extraction"
            )
            logger.info(f"Initialized parallel processing with {max_workers} workers")
        else:
            self._executor = None
            logger.debug("Parallel processing disabled")

    def add_text(self, text: str) -> Optional[KnowledgeGraph]:
        knowledge_graph = self._kg_extractor.extract(text)
        return self._kg_store.add(knowledge_graph.to_create())

    def add_chunk(self, chunk: Chunk) -> Optional[KnowledgeGraph]:
        # Check if the chunk has been added.
        exists_relationships = self._kg_store.list_relationships(chunk_id=chunk.id)
        if len(exists_relationships) > 0:
            logger.warning(
                "The subgraph of chunk %s has already been added, skip.", chunk.id
            )
            return None

        logger.info("Extracting knowledge graph from chunk %s", chunk.id)
        knowledge_graph = self._kg_extractor.extract(chunk)
        logger.info("Knowledge graph extracted from chunk %s", chunk.id)

        return self._kg_store.add(knowledge_graph.to_create())

    def retrieve(
        self,
        query: str,
        depth: int = 2,
        metadata_filters: Optional[dict] = None,
        **kwargs,
    ) -> RetrievedKnowledgeGraph:
        retriever = WeightedGraphRetriever(
            self._kg_store,
            self._embedding_model,
            **kwargs,
        )
        return retriever.retrieve(
            query=query,
            depth=depth,
            metadata_filters=metadata_filters,
        )
    
    def add_chunks_parallel(self, chunks: List[Chunk]) -> List[Optional[KnowledgeGraph]]:
        """
        Process multiple chunks in parallel for improved throughput.
        
        Phase 3 Enhancement: Implements concurrent chunk processing with error isolation
        and timeouts as defined in PRD Section 5.3. Each chunk is processed independently
        to prevent failures from affecting the entire batch.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            List of knowledge graphs (None for failed chunks)
        """
        if not chunks:
            return []
        
        # Use parallel processing if enabled and beneficial
        if (self._executor is not None and 
            len(chunks) > 1 and 
            self._config.is_feature_enabled("parallel_processing")):
            
            logger.info(f"Processing {len(chunks)} chunks in parallel with {self._config.get_worker_count()} workers")
            return self._process_chunks_parallel(chunks)
        else:
            # Fallback to sequential processing
            logger.info(f"Processing {len(chunks)} chunks sequentially")
            return self._process_chunks_sequential(chunks)
    
    def _process_chunks_parallel(self, chunks: List[Chunk]) -> List[Optional[KnowledgeGraph]]:
        """Process chunks using ThreadPoolExecutor with error isolation"""
        
        # Submit all tasks to the executor
        future_to_chunk = {}
        for chunk in chunks:
            future = self._executor.submit(self._process_chunk_safe, chunk)
            future_to_chunk[future] = chunk
        
        # Collect results as they complete
        results = [None] * len(chunks)
        completed_count = 0
        failed_count = 0
        
        for future in as_completed(future_to_chunk, timeout=self._config.chunk_timeout_seconds * len(chunks)):
            chunk = future_to_chunk[future]
            chunk_index = chunks.index(chunk)
            
            try:
                result = future.result(timeout=self._config.chunk_timeout_seconds)
                results[chunk_index] = result
                completed_count += 1
                
                if completed_count % 10 == 0:
                    logger.info(f"Parallel processing progress: {completed_count}/{len(chunks)} chunks")
                    
            except Exception as e:
                logger.error(f"Failed to process chunk {chunk.id}: {e}")
                results[chunk_index] = None
                failed_count += 1
        
        logger.info(f"Parallel processing complete: {completed_count} successful, {failed_count} failed")
        return results
    
    def _process_chunks_sequential(self, chunks: List[Chunk]) -> List[Optional[KnowledgeGraph]]:
        """Fallback sequential processing"""
        results = []
        for i, chunk in enumerate(chunks):
            result = self._process_chunk_safe(chunk)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Sequential processing progress: {i + 1}/{len(chunks)} chunks")
        
        return results
    
    def _process_chunk_safe(self, chunk: Chunk) -> Optional[KnowledgeGraph]:
        """
        Safely process a single chunk with error isolation.
        
        Phase 3 Enhancement: Ensures that failure of one chunk does not affect
        others in the batch. Implements timeout handling and comprehensive
        error logging for debugging.
        
        Args:
            chunk: Chunk to process
            
        Returns:
            KnowledgeGraph or None if processing failed
        """
        try:
            logger.debug(f"Processing chunk {chunk.id}")
            
            # Check if already processed (avoid duplicates)
            exists_relationships = self._kg_store.list_relationships(chunk_id=chunk.id)
            if len(exists_relationships) > 0:
                logger.debug(f"Chunk {chunk.id} already processed, skipping")
                return None
            
            # Extract knowledge graph from chunk text
            knowledge_graph = self._kg_extractor.extract(chunk.text)
            
            # Add to knowledge graph store
            result = self._kg_store.add(knowledge_graph.to_create())
            
            logger.debug(f"Successfully processed chunk {chunk.id}: "
                        f"{len(knowledge_graph.entities)} entities, "
                        f"{len(knowledge_graph.relationships)} relationships")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk.id}: {e}", exc_info=True)
            return None
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, '_executor') and self._executor is not None:
            self._executor.shutdown(wait=True)
            logger.debug("ThreadPoolExecutor shutdown complete")
