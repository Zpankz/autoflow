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
    """Extract medical entities and relationships from clinical text.

    Extract entities: name, description, type (drug/receptor/pathway/condition/procedure/biomarker)
    Extract relationships: source_entity, target_entity, description, type, confidence (0.0-1.0)
    
    Relationship types: hypernym, hyponym, meronym, holonym, synonym, antonym, causal, temporal, dependency, reference, generic
    
    Return valid JSON with entities and relationships arrays.
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
