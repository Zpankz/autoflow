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
            "Sample description of entity 'Norepinephrine in septic shock': "
            "'First-line vasopressor agent used to restore vascular tone and improve mean arterial pressure in distributive shock states'"
        )
    )
    entity_type: Optional[str] = Field(
        default="concept",
        description=(
            "Type or category of the clinical entity. Examples: 'drug', 'receptor', 'pathway', 'condition', "
            "'procedure', 'biomarker', 'protocol', 'mechanism', 'monitoring_parameter', 'therapeutic_target'"
        )
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Additional structured metadata about the entity as a JSON object. "
            "Include clinical classification, pharmacological properties, dosing info, or other relevant clinical attributes. "
            "Example: {'therapeutic_class': 'vasopressor', 'mechanism': 'alpha_adrenergic_agonist', 'onset_minutes': 1, 'half_life_minutes': 2}"
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
            "For example: 'Norepinephrine activates alpha-1 adrenergic receptors leading to peripheral vasoconstriction and increased systemic vascular resistance.'"
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
    """Carefully analyze the provided text from medical literature, pharmacology references, and critical care guidelines to thoroughly identify all entities related to biophysical pharmacophysiology, including both general concepts and specific clinical details.

    Follow these Step-by-Step Analysis:

    1. Extract Meaningful Entities with Enhanced Metadata:
      - Identify all significant nouns, proper nouns, and technical terminologies that represent medical concepts, pharmacological agents, physiological processes, clinical procedures, pathophysiological mechanisms, treatment protocols, dosing regimens, monitoring parameters, or any substantial clinical entities.
      - Ensure that you capture entities across different levels of detail, from high-level pathophysiological overviews to specific pharmacokinetic parameters and dosing specifications, to create a comprehensive representation of the clinical subject matter.
      - Choose names for entities that are specific enough to indicate their meaning without additional context, avoiding overly generic terms.
      - Consolidate similar entities to avoid redundancy, ensuring each represents a distinct concept at appropriate granularity levels.
      - For each entity, extract relevant metadata including entity type (drug, receptor, pathway, condition, procedure, biomarker, etc.) and other structured clinical attributes such as therapeutic class, mechanism of action, dosing parameters, contraindications, or monitoring requirements.

    2. Establish Typed Relationships with Confidence Scores:
      - Carefully examine the text to identify all relationships between clearly-related entities, ensuring each relationship is correctly captured with accurate details about the interactions.
      - Analyze the context and interactions between the identified entities to determine how they are interconnected, focusing on actions, associations, dependencies, or similarities.
      - Clearly define the relationships, ensuring accurate directionality that reflects the logical or functional dependencies among entities.
      - Classify each relationship using semantic types:
        * 'hypernym' - broader concept (e.g., "Vasopressor" is hypernym of "Norepinephrine")
        * 'hyponym' - narrower concept (e.g., "Alpha-1 Agonist" is hyponym of "Adrenergic Agonist") 
        * 'meronym' - part-of relationship (e.g., "Cardiac Output" is meronym of "Hemodynamic Status")
        * 'holonym' - has-part relationship (e.g., "Cardiovascular System" is holonym of "Myocardium")
        * 'synonym' - equivalent concepts (e.g., "Epinephrine" synonym "Adrenaline")
        * 'antonym' - opposite concepts (e.g., "Vasodilation" antonym "Vasoconstriction")
        * 'causal' - cause-effect relationships (e.g., "Sepsis" causes "Hypotension")
        * 'temporal' - time-based relationships (e.g., "Fluid Resuscitation" before "Vasopressor Initiation")
        * 'dependency' - requires/depends-on (e.g., "Invasive Monitoring" depends on "Central Venous Access")
        * 'reference' - mentioned-in/cites (e.g., "Clinical Guidelines" references "Dosing Protocol")
        * 'generic' - other relationships not fitting above categories
      - Assign confidence scores (0.0-1.0) based on text clarity: 0.9+ for explicit statements, 0.7-0.8 for clear implications, 0.5-0.6 for inferences.

    3. Unified Extraction:
      - Extract both entities with their metadata AND relationships with types/confidence in a single comprehensive analysis.
      - Ensure all extracted information is factual and verifiable within the text itself.
      - Cross-reference entities and relationships to maintain consistency and accuracy.

    Objective: Produce a detailed and comprehensive knowledge graph that captures clinical entities with rich pharmacological metadata and semantically typed relationships with confidence scores, enabling high-quality medical knowledge graph construction and retrieval for critical care applications.

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
