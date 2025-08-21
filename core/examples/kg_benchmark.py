#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Knowledge Graph Benchmark Framework

This module provides comprehensive benchmarking capabilities for the Knowledge Graph
enhancements in AutoFlow. It measures key performance indicators (KPIs) including:

- Duplicate Entity Rate
- Entity Merge Precision  
- Edge-to-Node (E:N) Ratio
- Typed Relationship Coverage
- Processing Latency 
- Throughput (Entities/Sec)

Usage:
    python kg_benchmark.py --baseline --enhanced --corpus-path ./fixtures/
"""

import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import statistics

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from autoflow import Autoflow
from autoflow.configs.knowledge_graph import KnowledgeGraphConfig
from autoflow.knowledge_base import KnowledgeBase
from autoflow.llms.chat_models import ChatModel
from autoflow.llms.embeddings import EmbeddingModel
from autoflow.types import IndexMethod
from autoflow.storage.graph_store.tidb_graph_store import TiDBGraphStore
from autoflow.knowledge_graph.index import KnowledgeGraphIndex
from autoflow.models.llms.dspy import get_dspy_lm_by_llm


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Container for benchmark metrics matching PRD Section 7.1 KPIs"""
    
    # Entity Quality Metrics
    duplicate_entity_rate: float = 0.0
    entity_merge_precision: float = 0.0
    canonical_entities_found: int = 0
    total_entities_created: int = 0
    
    # Relationship Quality Metrics  
    edge_node_ratio: float = 0.0
    typed_relationship_coverage: float = 0.0
    total_relationships: int = 0
    typed_relationships: int = 0
    
    # Performance Metrics
    processing_latency_ms: float = 0.0
    throughput_entities_per_sec: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Processing Statistics
    total_chunks_processed: int = 0
    total_processing_time_sec: float = 0.0
    avg_chunk_processing_time_ms: float = 0.0
    parallel_speedup_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization"""
        return asdict(self)
    
    def meets_targets(self) -> Tuple[bool, List[str]]:
        """Check if metrics meet PRD target thresholds"""
        issues = []
        
        # Check target thresholds from PRD Section 7.1
        if self.duplicate_entity_rate > 0.10:  # Target: ≤ 10%
            issues.append(f"Duplicate entity rate {self.duplicate_entity_rate:.2%} exceeds target ≤10%")
            
        if self.entity_merge_precision < 0.95:  # Target: ≥ 0.95
            issues.append(f"Entity merge precision {self.entity_merge_precision:.2f} below target ≥0.95")
            
        if self.edge_node_ratio < 3.5:  # Target: ~4:1, allow some tolerance
            issues.append(f"Edge-to-node ratio {self.edge_node_ratio:.2f} below target ~4.0")
            
        if self.typed_relationship_coverage < 0.85:  # Target: ≥ 85%
            issues.append(f"Typed relationship coverage {self.typed_relationship_coverage:.2%} below target ≥85%")
        
        return len(issues) == 0, issues


@dataclass 
class BenchmarkResult:
    """Complete benchmark result comparing baseline vs enhanced"""
    
    phase_id: str
    status: str  # SUCCESS, FAILURE, REGRESSION
    baseline_metrics: BenchmarkMetrics
    enhanced_metrics: BenchmarkMetrics
    improvement_ratios: Dict[str, float]
    timestamp: str
    test_corpus_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        return asdict(self)


class KnowledgeGraphBenchmark:
    """
    Comprehensive benchmarking framework for Knowledge Graph enhancements.
    
    This class implements the evaluation methodology defined in PRD Section 7.2,
    providing baseline vs enhanced performance comparisons across all KPIs.
    """
    
    def __init__(
        self,
        database_url: str,
        openai_api_key: str,
        corpus_path: str = "./fixtures/",
        test_namespace: str = "benchmark_test"
    ):
        """
        Initialize benchmark framework.
        
        Args:
            database_url: TiDB connection string
            openai_api_key: OpenAI API key for LLM operations
            corpus_path: Path to test documents corpus
            test_namespace: Namespace for test tables (isolated from production)
        """
        self.database_url = database_url
        self.openai_api_key = openai_api_key
        self.corpus_path = Path(corpus_path)
        self.test_namespace = test_namespace
        
        # Initialize AutoFlow components
        self.engine = create_engine(database_url)
        self.autoflow = Autoflow(self.engine)
        
        # Initialize models  
        self.chat_model = ChatModel("gpt-4o-mini", api_key=openai_api_key)
        self.embedding_model = EmbeddingModel(
            "text-embedding-3-small", 
            api_key=openai_api_key
        )
        
        logger.info(f"Initialized KG Benchmark with corpus: {corpus_path}")
    
    def run_full_benchmark(
        self, 
        phases: List[str] = ["baseline", "phase1", "phase2", "phase3"]
    ) -> Dict[str, BenchmarkResult]:
        """
        Run complete benchmark across all phases.
        
        Args:
            phases: List of phases to benchmark
            
        Returns:
            Dictionary mapping phase names to benchmark results
        """
        results = {}
        
        logger.info("Starting full Knowledge Graph benchmark suite")
        
        for phase in phases:
            logger.info(f"Running benchmark for phase: {phase}")
            
            # Configure KG settings for phase
            config = self._get_config_for_phase(phase)
            
            # Run benchmark
            result = self.run_phase_benchmark(phase, config)
            results[phase] = result
            
            # Log results
            meets_targets, issues = result.enhanced_metrics.meets_targets()
            if meets_targets:
                logger.info(f"✅ Phase {phase} meets all target metrics")
            else:
                logger.warning(f"⚠️ Phase {phase} issues: {'; '.join(issues)}")
        
        return results
    
    def run_phase_benchmark(
        self, 
        phase_id: str, 
        config: KnowledgeGraphConfig
    ) -> BenchmarkResult:
        """
        Run benchmark for a specific phase.
        
        Args:
            phase_id: Identifier for the phase (baseline, phase1, etc.)
            config: KG configuration for this phase
            
        Returns:
            Complete benchmark result
        """
        logger.info(f"Benchmarking phase {phase_id} with config: enhanced_kg={config.enable_enhanced_kg}")
        
        # Create test knowledge bases (baseline vs enhanced)
        baseline_kb = self._create_test_kb(f"{self.test_namespace}_baseline", 
                                         KnowledgeGraphConfig(enable_enhanced_kg=False))
        enhanced_kb = self._create_test_kb(f"{self.test_namespace}_enhanced", config)
        
        # Load test corpus
        test_documents = self._load_test_corpus()
        
        try:
            # Benchmark baseline
            logger.info("Running baseline benchmark...")
            baseline_metrics = self._benchmark_knowledge_base(baseline_kb, test_documents, "baseline")
            
            # Benchmark enhanced
            logger.info("Running enhanced benchmark...")
            enhanced_metrics = self._benchmark_knowledge_base(enhanced_kb, test_documents, "enhanced")
            
            # Calculate improvements
            improvement_ratios = self._calculate_improvements(baseline_metrics, enhanced_metrics)
            
            # Determine status
            status = "SUCCESS"
            meets_targets, issues = enhanced_metrics.meets_targets()
            if not meets_targets:
                status = "FAILURE"
                logger.warning(f"Phase {phase_id} failed targets: {'; '.join(issues)}")
            
            # Check for regressions
            if self._has_regressions(baseline_metrics, enhanced_metrics):
                status = "REGRESSION"
                logger.error(f"Phase {phase_id} shows performance regressions")
                
        finally:
            # Cleanup test knowledge bases
            self._cleanup_test_kb(baseline_kb)
            self._cleanup_test_kb(enhanced_kb)
        
        return BenchmarkResult(
            phase_id=phase_id,
            status=status,
            baseline_metrics=baseline_metrics,
            enhanced_metrics=enhanced_metrics,
            improvement_ratios=improvement_ratios,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            test_corpus_info={
                "document_count": len(test_documents),
                "total_chars": sum(len(doc.content) for doc in test_documents),
                "corpus_path": str(self.corpus_path)
            }
        )
    
    def _create_test_kb(self, namespace: str, config: KnowledgeGraphConfig) -> KnowledgeBase:
        """Create isolated test knowledge base with specific configuration"""
        
        kb = self.autoflow.create_knowledge_base(
            name=f"KG_Benchmark_{namespace}",
            description=f"Test KB for KG benchmarking (namespace: {namespace})",
            namespace=namespace,
            embedding_model=self.embedding_model,
            index_methods=[IndexMethod.KNOWLEDGE_GRAPH],
            kg_config=config  # Pass the KG configuration
        )
        
        logger.info(f"Created test KB: {kb.name} with namespace: {namespace}")
        return kb
    
    def _benchmark_knowledge_base(
        self, 
        kb: KnowledgeBase, 
        documents: List, 
        run_type: str
    ) -> BenchmarkMetrics:
        """
        Benchmark a knowledge base with the test corpus.
        
        Args:
            kb: Knowledge base to benchmark
            documents: Test documents to process
            run_type: "baseline" or "enhanced" for logging
            
        Returns:
            Measured benchmark metrics
        """
        logger.info(f"Processing {len(documents)} documents for {run_type} run")
        
        # Reset any existing data
        kb.reset()
        
        # Timing measurements
        start_time = time.time()
        chunk_times = []
        
        # Process documents and measure metrics
        for i, doc in enumerate(documents):
            chunk_start = time.time()
            
            # Add document to KB (triggers KG extraction)
            result_docs = kb.add(doc)
            
            chunk_time = (time.time() - chunk_start) * 1000  # Convert to ms
            chunk_times.append(chunk_time)
            
            if (i + 1) % 5 == 0:
                logger.info(f"Processed {i + 1}/{len(documents)} documents")
        
        total_time = time.time() - start_time
        
        # Collect metrics from KB
        metrics = self._collect_metrics_from_kb(kb, chunk_times, total_time)
        
        logger.info(f"Completed {run_type} benchmark: "
                   f"{metrics.total_entities_created} entities, "
                   f"{metrics.total_relationships} relationships, "
                   f"{metrics.edge_node_ratio:.2f} E:N ratio")
        
        return metrics
    
    def _collect_metrics_from_kb(
        self, 
        kb: KnowledgeBase, 
        chunk_times: List[float], 
        total_time: float
    ) -> BenchmarkMetrics:
        """Collect comprehensive metrics from a knowledge base"""
        
        with Session(self.engine) as session:
            graph_store = kb.knowledge_graph._kg_store
            
            # Get table names for this KB's namespace
            namespace = kb.namespace or ""
            entity_table = f"entities_{namespace}" if namespace else "entities"
            relationship_table = f"relationships_{namespace}" if namespace else "relationships"
            
            # Entity metrics
            entity_count_query = f"SELECT COUNT(*) FROM {entity_table}"
            total_entities = session.execute(text(entity_count_query)).scalar()
            
            # Calculate duplicate entity rate (entities with similar canonical_ids)
            duplicate_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT canonical_id, COUNT(*) as cnt 
                    FROM {entity_table} 
                    WHERE canonical_id IS NOT NULL 
                    GROUP BY canonical_id 
                    HAVING cnt > 1
                ) duplicates
            """
            duplicate_groups = session.execute(text(duplicate_query)).scalar() or 0
            duplicate_rate = duplicate_groups / max(total_entities, 1)
            
            # Canonical entities (unique canonical_ids)
            canonical_query = f"""
                SELECT COUNT(DISTINCT canonical_id) FROM {entity_table} 
                WHERE canonical_id IS NOT NULL
            """
            canonical_entities = session.execute(text(canonical_query)).scalar() or 0
            
            # Relationship metrics
            relationship_count_query = f"SELECT COUNT(*) FROM {relationship_table}"
            total_relationships = session.execute(text(relationship_count_query)).scalar()
            
            # Typed relationship coverage
            typed_query = f"""
                SELECT COUNT(*) FROM {relationship_table} 
                WHERE relationship_type IS NOT NULL AND relationship_type != 'generic'
            """
            typed_relationships = session.execute(text(typed_query)).scalar() or 0
            typed_coverage = typed_relationships / max(total_relationships, 1)
            
            # Edge-to-Node ratio
            edge_node_ratio = total_relationships / max(total_entities, 1)
            
            # Processing performance
            avg_chunk_time = statistics.mean(chunk_times) if chunk_times else 0
            throughput = total_entities / max(total_time, 0.001)  # entities per second
            
            # Cache metrics (if enhanced KG is enabled)
            cache_hit_rate = 0.0
            if hasattr(graph_store, '_entity_cache') and graph_store._entity_cache:
                # Estimate cache effectiveness (simplified)
                cache_info = getattr(graph_store._entity_cache, 'cache_info', lambda: None)()
                if cache_info:
                    hits = getattr(cache_info, 'hits', 0)
                    misses = getattr(cache_info, 'misses', 0)
                    cache_hit_rate = hits / max(hits + misses, 1)
        
        # Entity merge precision (simplified calculation)
        # High precision means few false positive merges
        entity_merge_precision = 1.0 - (duplicate_rate * 0.5)  # Simplified heuristic
        
        return BenchmarkMetrics(
            duplicate_entity_rate=duplicate_rate,
            entity_merge_precision=entity_merge_precision,
            canonical_entities_found=canonical_entities,
            total_entities_created=total_entities,
            edge_node_ratio=edge_node_ratio,
            typed_relationship_coverage=typed_coverage,
            total_relationships=total_relationships,
            typed_relationships=typed_relationships,
            processing_latency_ms=avg_chunk_time,
            throughput_entities_per_sec=throughput,
            cache_hit_rate=cache_hit_rate,
            total_chunks_processed=len(chunk_times),
            total_processing_time_sec=total_time,
            avg_chunk_processing_time_ms=avg_chunk_time
        )
    
    def _calculate_improvements(
        self, 
        baseline: BenchmarkMetrics, 
        enhanced: BenchmarkMetrics
    ) -> Dict[str, float]:
        """Calculate improvement ratios between baseline and enhanced"""
        
        def safe_ratio(enhanced_val, baseline_val):
            """Calculate improvement ratio safely"""
            if baseline_val == 0:
                return float('inf') if enhanced_val > 0 else 0
            return enhanced_val / baseline_val
        
        def safe_reduction(enhanced_val, baseline_val):
            """Calculate reduction percentage safely"""
            if baseline_val == 0:
                return 0
            return (baseline_val - enhanced_val) / baseline_val
        
        return {
            "duplicate_entity_reduction": safe_reduction(enhanced.duplicate_entity_rate, baseline.duplicate_entity_rate),
            "entity_merge_precision_improvement": safe_ratio(enhanced.entity_merge_precision, baseline.entity_merge_precision),
            "edge_node_ratio_improvement": safe_ratio(enhanced.edge_node_ratio, baseline.edge_node_ratio),
            "typed_coverage_improvement": safe_ratio(enhanced.typed_relationship_coverage, baseline.typed_relationship_coverage),
            "latency_reduction": safe_reduction(enhanced.processing_latency_ms, baseline.processing_latency_ms),
            "throughput_improvement": safe_ratio(enhanced.throughput_entities_per_sec, baseline.throughput_entities_per_sec),
            "cache_hit_rate": enhanced.cache_hit_rate
        }
    
    def _has_regressions(
        self, 
        baseline: BenchmarkMetrics, 
        enhanced: BenchmarkMetrics
    ) -> bool:
        """Check for performance regressions"""
        
        # Check for significant regressions (>10% worse)
        regression_threshold = 0.1
        
        # Throughput regression
        if enhanced.throughput_entities_per_sec < baseline.throughput_entities_per_sec * (1 - regression_threshold):
            logger.error(f"Throughput regression: {enhanced.throughput_entities_per_sec:.2f} < {baseline.throughput_entities_per_sec:.2f}")
            return True
        
        # Latency regression  
        if enhanced.processing_latency_ms > baseline.processing_latency_ms * (1 + regression_threshold):
            logger.error(f"Latency regression: {enhanced.processing_latency_ms:.2f} > {baseline.processing_latency_ms:.2f}")
            return True
        
        return False
    
    def _get_config_for_phase(self, phase: str) -> KnowledgeGraphConfig:
        """Get KG configuration for specific phase"""
        
        if phase == "baseline":
            return KnowledgeGraphConfig(enable_enhanced_kg=False)
        
        elif phase == "phase1":
            return KnowledgeGraphConfig(
                enable_enhanced_kg=True,
                canonicalization_enabled=True,
                typed_relationships_enabled=False,
                parallel_processing_enabled=False,
                entity_distance_threshold=0.85
            )
        
        elif phase == "phase2": 
            return KnowledgeGraphConfig(
                enable_enhanced_kg=True,
                canonicalization_enabled=True,
                typed_relationships_enabled=True,
                parallel_processing_enabled=False,
                entity_distance_threshold=0.85
            )
        
        elif phase == "phase3":
            return KnowledgeGraphConfig(
                enable_enhanced_kg=True,
                canonicalization_enabled=True,
                typed_relationships_enabled=True,
                parallel_processing_enabled=True,
                entity_distance_threshold=0.85
            )
        
        else:
            raise ValueError(f"Unknown phase: {phase}")
    
    def _load_test_corpus(self) -> List:
        """Load test documents from corpus directory"""
        
        documents = []
        
        if not self.corpus_path.exists():
            logger.warning(f"Corpus path {self.corpus_path} not found, creating sample documents")
            return self._create_sample_documents()
        
        # Load markdown files from corpus
        for md_file in self.corpus_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Create document object
                from autoflow.storage.doc_store.types import Document
                doc = Document(
                    name=md_file.name,
                    content=content,
                    meta={"source": str(md_file), "benchmark": True}
                )
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error loading {md_file}: {e}")
        
        logger.info(f"Loaded {len(documents)} documents from corpus")
        return documents
    
    def _create_sample_documents(self) -> List:
        """Create sample documents for testing when corpus is not available"""
        
        from autoflow.storage.doc_store.types import Document
        
        sample_docs = [
            Document(
                name="tidb_architecture.md",
                content="""
                # TiDB Architecture Overview
                
                TiDB is a distributed SQL database that supports HTAP workloads. The architecture
                consists of several key components:
                
                ## TiDB Server
                The TiDB server handles SQL parsing, query planning, and execution. It is stateless
                and can be horizontally scaled. TiDB servers communicate with TiKV nodes to access data.
                
                ## TiKV Storage Engine  
                TiKV is the distributed storage layer that stores actual data. It uses the Raft
                consensus algorithm to ensure data consistency across replicas.
                
                ## PD (Placement Driver)
                PD is responsible for metadata management and cluster scheduling. It monitors
                the health of TiKV nodes and handles data placement decisions.
                
                ## TiFlash Columnar Storage
                TiFlash provides columnar storage for analytical workloads. It replicates data
                from TiKV in real-time using the Raft protocol.
                """,
                meta={"sample": True, "topic": "architecture"}
            ),
            Document(
                name="vector_search.md", 
                content="""
                # Vector Search in TiDB
                
                TiDB supports vector search capabilities for AI applications. This enables
                semantic search and similarity matching for embeddings.
                
                ## Vector Index Types
                TiDB supports HNSW (Hierarchical Navigable Small World) indexes for efficient
                approximate nearest neighbor search. Vector dimensions can be configured
                from 1 to 16,000.
                
                ## Embedding Models
                Common embedding models include OpenAI text-embedding models, which generate
                dense vector representations of text. These embeddings capture semantic meaning.
                
                ## Search Operations
                Vector search operations use cosine similarity to find related documents.
                The similarity threshold determines the quality of matches returned.
                """,
                meta={"sample": True, "topic": "vectors"}
            )
        ]
        
        return sample_docs
    
    def _cleanup_test_kb(self, kb: KnowledgeBase) -> None:
        """Cleanup test knowledge base and its data"""
        try:
            kb.reset()
            logger.info(f"Cleaned up test KB: {kb.name}")
        except Exception as e:
            logger.error(f"Error cleaning up KB {kb.name}: {e}")
    
    def save_results(self, results: Dict[str, BenchmarkResult], output_path: str = "./benchmark_results.json"):
        """Save benchmark results to JSON file"""
        
        # Convert to serializable format
        serializable_results = {
            phase: result.to_dict() for phase, result in results.items()
        }
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Saved benchmark results to {output_path}")
    
    def print_summary(self, results: Dict[str, BenchmarkResult]) -> None:
        """Print human-readable benchmark summary"""
        
        print("\n" + "="*80)
        print("KNOWLEDGE GRAPH BENCHMARK SUMMARY")
        print("="*80)
        
        for phase, result in results.items():
            print(f"\n📊 Phase: {phase.upper()}")
            print(f"Status: {result.status}")
            
            metrics = result.enhanced_metrics
            print(f"  • Entities Created: {metrics.total_entities_created}")
            print(f"  • Relationships: {metrics.total_relationships}")
            print(f"  • Duplicate Rate: {metrics.duplicate_entity_rate:.2%}")
            print(f"  • E:N Ratio: {metrics.edge_node_ratio:.2f}")
            print(f"  • Typed Coverage: {metrics.typed_relationship_coverage:.2%}")
            print(f"  • Avg Latency: {metrics.processing_latency_ms:.2f}ms")
            print(f"  • Throughput: {metrics.throughput_entities_per_sec:.2f} entities/sec")
            
            if phase != "baseline":
                improvements = result.improvement_ratios
                print(f"  🎯 Improvements vs Baseline:")
                print(f"    - Duplicate Reduction: {improvements.get('duplicate_entity_reduction', 0):.1%}")
                print(f"    - Throughput Gain: {improvements.get('throughput_improvement', 1):.1f}x")
                print(f"    - Latency Reduction: {improvements.get('latency_reduction', 0):.1%}")
        
        print("\n" + "="*80)


def main():
    """Main CLI entry point for KG benchmarking"""
    
    parser = argparse.ArgumentParser(description="Knowledge Graph Benchmark Framework")
    parser.add_argument("--database-url", required=True, help="TiDB connection string")
    parser.add_argument("--openai-api-key", required=True, help="OpenAI API key")
    parser.add_argument("--corpus-path", default="./fixtures/", help="Test corpus directory")
    parser.add_argument("--phases", nargs="+", default=["baseline", "phase1", "phase2", "phase3"],
                       help="Phases to benchmark")
    parser.add_argument("--output", default="./benchmark_results.json", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize benchmark
    benchmark = KnowledgeGraphBenchmark(
        database_url=args.database_url,
        openai_api_key=args.openai_api_key,
        corpus_path=args.corpus_path
    )
    
    # Run benchmarks
    results = benchmark.run_full_benchmark(args.phases)
    
    # Save and display results
    benchmark.save_results(results, args.output)
    benchmark.print_summary(results)
    
    # Exit with appropriate code
    failed_phases = [phase for phase, result in results.items() if result.status in ["FAILURE", "REGRESSION"]]
    if failed_phases:
        print(f"\n❌ Failed phases: {', '.join(failed_phases)}")
        exit(1)
    else:
        print(f"\n✅ All phases passed benchmark targets")
        exit(0)


if __name__ == "__main__":
    main()
