import logging
from typing import Any, Dict, List, Optional

import dspy
from dspy import Predict
from pydantic import BaseModel, Field

from autoflow.knowledge_graph.types import (
    GeneratedEntity,
    GeneratedKnowledgeGraph,
    GeneratedRelationship,
)

logger = logging.getLogger(__name__)


class PredictEntity(BaseModel):
    """Entity extracted from the text to form the knowledge graph with enhanced metadata"""

    name: str = Field(
        description="Name of the entity, it should be a clear and concise term"
    )
    description: str = Field(
        description=(
            "Description of the entity, it should be a complete and comprehensive sentence, not few words. "
            "Sample description of entity 'TiDB in-place upgrade': "
            "'Upgrade TiDB component binary files to achieve upgrade, generally use rolling upgrade method'"
        )
    )
    entity_type: Optional[str] = Field(
        default="concept",
        description=(
            "Type or category of the entity. Examples: 'component', 'feature', 'process', 'tool', "
            "'concept', 'configuration', 'protocol', 'algorithm', 'service'"
        )
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Additional structured metadata about the entity as a JSON object. "
            "Include topic classification, technical properties, version info, or other relevant attributes. "
            "Example: {'topic': 'storage', 'type': 'distributed_database', 'supports_transactions': true}"
        )
    )


class PredictRelationship(BaseModel):
    """Relationship extracted from the text to form the knowledge graph with semantic typing"""

    source_entity: str = Field(
        description="Source entity name of the relationship, it should an existing entity in the Entity list"
    )
    target_entity: str = Field(
        description="Target entity name of the relationship, it should an existing entity in the Entity list"
    )
    relationship_desc: str = Field(
        description=(
            "Description of the relationship, it should be a complete and comprehensive sentence, not few words. "
            "For example: 'TiDB will release a new LTS version every 6 months.'"
        )
    )
    relationship_type: str = Field(
        default="generic",
        description=(
            "Semantic type of the relationship. Must be one of: "
            "'hypernym' (is-a, broader concept), 'hyponym' (is-a, narrower concept), "
            "'meronym' (part-of), 'holonym' (has-part), 'synonym' (same-as), 'antonym' (opposite-of), "
            "'causal' (causes/enables), 'temporal' (before/after), 'reference' (mentioned-in), "
            "'dependency' (requires/depends-on), 'generic' (other). "
            "Choose the most specific type that accurately describes the relationship."
        )
    )
    confidence: float = Field(
        default=0.8,
        description=(
            "Confidence score for this relationship (0.0 to 1.0). "
            "Higher scores for clearly stated relationships, lower for inferred ones. "
            "Use 0.9+ for explicit statements, 0.7-0.8 for clear implications, "
            "0.5-0.6 for weak inferences. Minimum threshold is typically 0.3."
        ),
        ge=0.0,
        le=1.0
    )


class PredictKnowledgeGraph(BaseModel):
    """Graph representation of the knowledge for text."""

    entities: List[PredictEntity] = Field(
        description="List of entities in the knowledge graph"
    )
    relationships: List[PredictRelationship] = Field(
        description="List of relationships in the knowledge graph"
    )

    def to_pandas(self):
        from pandas import DataFrame

        return {
            "entities": DataFrame(
                [
                    {
                        "name": entity.name,
                        "description": entity.description,
                    }
                    for entity in self.entities
                ]
            ),
            "relationships": DataFrame(
                [
                    {
                        "source_entity": relationship.source_entity,
                        "relationship_desc": relationship.relationship_desc,
                        "target_entity": relationship.target_entity,
                    }
                    for relationship in self.relationships
                ]
            ),
        }


class ExtractKnowledgeGraph(dspy.Signature):
    """Carefully analyze the provided text from database documentation and community blogs to thoroughly identify all entities related to database technologies, including both general concepts and specific details.

    Follow these Step-by-Step Analysis:

    1. Extract Meaningful Entities with Enhanced Metadata:
      - Identify all significant nouns, proper nouns, and technical terminologies that represent database-related concepts, objects, components, features, issues, key steps, execute order, user case, locations, versions, or any substantial entities.
      - Ensure that you capture entities across different levels of detail, from high-level overviews to specific technical specifications, to create a comprehensive representation of the subject matter.
      - Choose names for entities that are specific enough to indicate their meaning without additional context, avoiding overly generic terms.
      - Consolidate similar entities to avoid redundancy, ensuring each represents a distinct concept at appropriate granularity levels.
      - For each entity, extract relevant metadata including entity type (component, feature, process, tool, concept, etc.) and other structured attributes that provide context.

    2. Establish Typed Relationships with Confidence Scores:
      - Carefully examine the text to identify all relationships between clearly-related entities, ensuring each relationship is correctly captured with accurate details about the interactions.
      - Analyze the context and interactions between the identified entities to determine how they are interconnected, focusing on actions, associations, dependencies, or similarities.
      - Clearly define the relationships, ensuring accurate directionality that reflects the logical or functional dependencies among entities.
      - Classify each relationship using semantic types:
        * 'hypernym' - broader concept (e.g., "Database" is hypernym of "TiDB")
        * 'hyponym' - narrower concept (e.g., "TiKV" is hyponym of "Storage Engine") 
        * 'meronym' - part-of relationship (e.g., "TiKV" is meronym of "TiDB Cluster")
        * 'holonym' - has-part relationship (e.g., "TiDB Cluster" is holonym of "TiKV")
        * 'synonym' - equivalent concepts (e.g., "TiDB" synonym "TiDB Database")
        * 'antonym' - opposite concepts 
        * 'causal' - cause-effect relationships (e.g., "Index" causes "Fast Query")
        * 'temporal' - time-based relationships (e.g., "Migration" before "Upgrade")
        * 'dependency' - requires/depends-on (e.g., "TiDB" depends on "TiKV")
        * 'reference' - mentioned-in/cites (e.g., "Documentation" references "Feature")
        * 'generic' - other relationships not fitting above categories
      - Assign confidence scores (0.0-1.0) based on text clarity: 0.9+ for explicit statements, 0.7-0.8 for clear implications, 0.5-0.6 for inferences.

    3. Unified Extraction:
      - Extract both entities with their metadata AND relationships with types/confidence in a single comprehensive analysis.
      - Ensure all extracted information is factual and verifiable within the text itself.
      - Cross-reference entities and relationships to maintain consistency and accuracy.

    Objective: Produce a detailed and comprehensive knowledge graph that captures entities with rich metadata and semantically typed relationships with confidence scores, enabling high-quality graph construction and retrieval.

    Please only response in JSON format.
    """

    text = dspy.InputField(
        desc="a paragraph of text to extract entities and relationships to form a knowledge graph"
    )
    knowledge: PredictKnowledgeGraph = dspy.OutputField(
        desc="Graph representation of the knowledge extracted from the text."
    )


class KnowledgeGraphExtractor(dspy.Module):
    def __init__(self, dspy_lm: dspy.LM):
        super().__init__()
        self.dspy_lm = dspy_lm
        self.program = Predict(ExtractKnowledgeGraph)

    def forward(self, text: str) -> GeneratedKnowledgeGraph:
        with dspy.settings.context(lm=self.dspy_lm):
            prediction = self.program(text=text)
            
            # Enhanced entity extraction with metadata
            entities = [
                GeneratedEntity(
                    name=entity.name,
                    description=entity.description,
                    meta={
                        "entity_type": getattr(entity, "entity_type", "concept"),
                        **(getattr(entity, "metadata", {}) or {}),
                        # Add extraction metadata
                        "extraction_method": "enhanced_dspy",
                        "has_covariates": True,  # Mark that metadata is included
                    },
                )
                for entity in prediction.knowledge.entities
            ]
            
            # Enhanced relationship extraction with types and confidence
            relationships = [
                GeneratedRelationship(
                    source_entity_name=relationship.source_entity,
                    target_entity_name=relationship.target_entity,
                    description=relationship.relationship_desc,
                    meta={
                        "relationship_type": getattr(relationship, "relationship_type", "generic"),
                        "confidence": getattr(relationship, "confidence", 0.8),
                        # Add extraction metadata
                        "extraction_method": "enhanced_dspy",
                        "typed_extraction": True,  # Mark that this includes semantic typing
                    },
                )
                for relationship in prediction.knowledge.relationships
            ]
            
            return GeneratedKnowledgeGraph(
                entities=entities,
                relationships=relationships,
            )
